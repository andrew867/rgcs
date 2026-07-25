"""P08 — the randomization engine: reproducible under a committed seed,
balanced designs, sealed before runs, and refusing premature reads,
post-commit reordering, and confirmatory claims after unblinding."""

from __future__ import annotations

import pytest

from r15 import randomization as R
from r15 import claims as C


# =======================================================================
# Reproducibility / determinism
# =======================================================================

def test_same_seed_reproduces_the_same_order():
    conds = tuple(f"C{i}" for i in range(12))
    assert R.randomize(conds, seed=123) == R.randomize(conds, seed=123)


def test_different_seed_generally_gives_a_different_order():
    conds = tuple(f"C{i}" for i in range(12))
    assert R.randomize(conds, seed=1) != R.randomize(conds, seed=2)


def test_randomize_is_a_permutation():
    conds = tuple(f"C{i}" for i in range(20))
    order = R.randomize(conds, seed=99)
    assert sorted(order) == sorted(conds)


def test_per_factor_orders_are_reproducible_and_independent():
    specimens = ("S1", "S2", "S3", "S4")
    a = R.specimen_order(specimens, seed=55)
    b = R.specimen_order(specimens, seed=55)
    assert a == b
    # a different factor stream off the same master seed is independent
    assert R.frequency_order(specimens, seed=55) != a or \
        R.sensor_permutation(specimens, seed=55) != a


def test_full_plan_reproduces_from_one_master_seed():
    factors = {
        "specimen": ("S1", "S2", "S3"),
        "frequency": (1000, 2000, 3000),
        "orientation": ("X", "Y", "Z"),
        "sensor": ("ch0", "ch1"),
    }
    assert R.randomization_plan(factors, seed=7) == \
        R.randomization_plan(factors, seed=7)


# =======================================================================
# Balance
# =======================================================================

def test_random_blocks_are_balanced():
    conds = tuple(f"C{i}" for i in range(5))
    blocks = R.random_blocks(conds, n_blocks=4, seed=3)
    assert len(blocks) == 4
    assert R.is_balanced_blocks(blocks, conds)
    # each condition appears exactly once per block => n_blocks times total
    flat = [c for block in blocks for c in block]
    for c in conds:
        assert flat.count(c) == 4


def test_latin_square_is_balanced():
    syms = tuple("ABCDE")
    square = R.latin_square(syms, seed=17)
    assert R.is_latin_square(square, syms)


def test_latin_square_rejects_duplicate_symbols():
    with pytest.raises(R.RandomizationError):
        R.latin_square(("A", "A", "B"), seed=1)


def test_a_non_latin_grid_fails_the_check():
    # a constant grid is not a Latin square
    bad = (("A", "A"), ("A", "A"))
    assert not R.is_latin_square(bad, ("A", "B"))


# =======================================================================
# Sealing, design hash, and tamper-evidence
# =======================================================================

def test_manifest_seals_and_verifies_its_own_schedule():
    m = R.build_manifest(R.DesignType.COMPLETE_RANDOM,
                         {"conditions": tuple(f"C{i}" for i in range(8))},
                         seed=42)
    assert not m.committed
    commitment = m.seal()
    assert m.committed
    assert isinstance(commitment, str) and len(commitment) == 64
    assert m.verify() is True


def test_a_swapped_schedule_fails_the_commitment():
    m = R.build_manifest(R.DesignType.COMPLETE_RANDOM,
                         {"conditions": tuple(f"C{i}" for i in range(8))},
                         seed=42)
    m.seal()
    swapped = (m.schedule[1], m.schedule[0]) + tuple(m.schedule[2:])
    assert m.verify(swapped) is False
    assert m.verify() is True


def test_design_hash_changes_with_the_seed():
    factors = {"conditions": ("A", "B", "C")}
    h1 = R.design_hash(R.DesignType.COMPLETE_RANDOM, factors, seed=1)
    h2 = R.design_hash(R.DesignType.COMPLETE_RANDOM, factors, seed=2)
    assert h1 != h2


def test_resealing_is_refused():
    m = R.build_manifest(R.DesignType.COMPLETE_RANDOM,
                         {"conditions": ("A", "B", "C")}, seed=1)
    m.seal()
    with pytest.raises(R.RandomizationError):
        m.seal()


# =======================================================================
# Negative / refusal paths
# =======================================================================

def test_reading_the_schedule_before_the_seal_is_refused():
    m = R.build_manifest(R.DesignType.COMPLETE_RANDOM,
                         {"conditions": ("A", "B", "C")}, seed=1)
    with pytest.raises(R.RandomizationError):
        m.reveal_schedule()
    # sealing unlocks the read
    m.seal()
    assert set(m.reveal_schedule()) == {"A", "B", "C"}


def test_post_commit_reorder_is_refused():
    m = R.build_manifest(R.DesignType.COMPLETE_RANDOM,
                         {"conditions": tuple(f"C{i}" for i in range(6))},
                         seed=9)
    m.seal()
    reordered = tuple(reversed(m.schedule))
    with pytest.raises(R.RandomizationError):
        R.refuse_post_commit_reorder(m, reordered)


def test_reorder_before_seal_is_allowed():
    # before the commit there is nothing to protect; no refusal
    m = R.build_manifest(R.DesignType.COMPLETE_RANDOM,
                         {"conditions": ("A", "B", "C")}, seed=1)
    R.refuse_post_commit_reorder(m, ("C", "B", "A"))  # must not raise


def test_unblinding_invalidates_confirmatory_status():
    with pytest.raises(R.RandomizationError):
        R.refuse_confirmatory_after_unblind(True)
    # still blind: no refusal
    R.refuse_confirmatory_after_unblind(False)


def test_analysis_status_tracks_seal_and_blind():
    m = R.build_manifest(R.DesignType.COMPLETE_RANDOM,
                         {"conditions": ("A", "B", "C")}, seed=1)
    assert R.analysis_status(m) == "NOT_YET_SEALED"
    m.seal()
    assert R.analysis_status(m) == "CONFIRMATORY_ELIGIBLE"
    m.unblinded = True
    assert R.analysis_status(m) == "EXPLORATORY_ONLY"


def test_empty_condition_set_is_refused():
    with pytest.raises(R.RandomizationError):
        R.randomize((), seed=1)


# =======================================================================
# Restart / deviation policy
# =======================================================================

def test_restart_derives_a_new_seed_and_logs_a_deviation():
    m = R.build_manifest(R.DesignType.COMPLETE_RANDOM,
                         {"conditions": tuple(f"C{i}" for i in range(6))},
                         seed=100)
    m.seal()
    fresh = R.restart(m, reason="aborted acquisition", epoch=5, restart_index=1)
    # a new, unsealed manifest under a different seed
    assert not fresh.committed
    assert fresh.seed != m.seed
    # the original seal is untouched
    assert m.committed
    # the deviation is recorded, never dropped
    assert any(d.kind == "RESTART" for d in fresh.deviations)


def test_restart_is_deterministic():
    m = R.build_manifest(R.DesignType.COMPLETE_RANDOM,
                         {"conditions": ("A", "B", "C")}, seed=100)
    s1 = R.restart_seed(m.seed, 1)
    s2 = R.restart_seed(m.seed, 1)
    assert s1 == s2
    assert R.restart_seed(m.seed, 1) != R.restart_seed(m.seed, 2)


def test_recorded_deviations_survive():
    m = R.build_manifest(R.DesignType.COMPLETE_RANDOM,
                         {"conditions": ("A", "B", "C")}, seed=1)
    m.record_deviation("BALANCE_FAILURE", "block short by one", epoch=3)
    m.record_deviation("MANUAL", "operator note", epoch=4)
    assert len(m.deviations) == 2
    assert m.deviations[0].epoch == 3


# =======================================================================
# Report and claim discipline
# =======================================================================

def test_report_claims_nothing_and_is_consistent():
    r = R.randomization_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["verdict"] == R.VERDICT
    assert r["same_seed_same_order"] is True
    assert r["different_seed_different_order"] is True
    assert r["blocks_balanced"] is True
    assert r["latin_square_valid"] is True
    assert r["true_schedule_matches_commitment"] is True
    assert r["swapped_schedule_matches_commitment"] is False
    assert r["post_commit_reorder_refused"] is True
    assert r["read_before_seal_refused"] is True
    assert r["confirmatory_after_unblind_refused"] is True


def test_report_claim_class_is_a_software_class_not_a_measurement():
    r = R.randomization_report()
    assert r["claim_class"] == C.ClaimClass.SOFTWARE_IMPLEMENTED.value
    assert R.CLAIM_CLASS not in C.MEASUREMENT_CLASSES
    assert R.CLAIM_CLASS in C.SOFTWARE_CLASSES
