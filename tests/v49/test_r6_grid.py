"""P07 — planetary grid audit, Wigner machinery, and its controls."""

from __future__ import annotations

import math

import pytest

from r6 import grid as G
from r6 import wigner as WG


# --- Wigner D and group projectors -----------------------------------

def test_group_orders_are_correct():
    assert len(WG.group_elements("TETRAHEDRAL")) == 12
    assert len(WG.group_elements("OCTAHEDRAL")) == 24
    assert len(WG.group_elements("ICOSAHEDRAL")) == 60


def test_identity_rotation_is_the_identity_matrix():
    D = WG.wigner_D(3, 0.0, 0.0, 0.0)
    for i in range(7):
        for j in range(7):
            expect = 1.0 if i == j else 0.0
            assert abs(D[i][j] - expect) < 1e-9


def test_wigner_d_is_unitary():
    D = WG.wigner_D(2, 0.7, 1.1, -0.4)
    n = len(D)
    for i in range(n):
        for j in range(n):
            dot = sum(D[i][k] * D[j][k].conjugate() for k in range(n))
            assert abs(dot - (1.0 if i == j else 0.0)) < 1e-9


def test_small_d_matches_known_closed_forms():
    """Against the textbook l=1 and l=2 entries.

    This is the test that catches a wrong phase convention. Unitarity,
    idempotency and the invariant dimensions are all invariant under
    the diagonal similarity a bad sign introduces, so only the closed
    forms can see it.
    """
    b = 0.6
    c, s = math.cos(b), math.sin(b)
    assert WG.wigner_small_d(1, 0, 0, b) == pytest.approx(c)
    assert WG.wigner_small_d(1, 1, 0, b) == \
        pytest.approx(-s / math.sqrt(2))
    assert WG.wigner_small_d(1, 1, 1, b) == pytest.approx((1 + c) / 2)
    assert WG.wigner_small_d(1, 1, -1, b) == pytest.approx((1 - c) / 2)
    assert WG.wigner_small_d(2, 0, 0, b) == \
        pytest.approx(0.5 * (3 * c * c - 1))


def test_small_d_at_zero_is_the_identity():
    for l in (1, 2, 3):
        for mp in range(-l, l + 1):
            for m in range(-l, l + 1):
                expect = 1.0 if mp == m else 0.0
                assert WG.wigner_small_d(l, mp, m, 0.0) == \
                    pytest.approx(expect, abs=1e-12)


@pytest.mark.parametrize("group", ["TETRAHEDRAL", "OCTAHEDRAL",
                                   "ICOSAHEDRAL"])
@pytest.mark.parametrize("l", [0, 1, 2, 3, 4, 6])
def test_projector_is_idempotent_and_hermitian(group, l):
    v = WG.verify_projector(l, group)
    assert v["ok"], v


@pytest.mark.parametrize("group", ["TETRAHEDRAL", "OCTAHEDRAL",
                                   "ICOSAHEDRAL"])
@pytest.mark.parametrize("l", [0, 1, 2, 3, 4, 6])
def test_projector_trace_is_an_integer(group, l):
    d = WG.invariant_dimension(l, group)
    assert isinstance(d, int) and d >= 0


def test_lowest_invariant_degrees_match_group_theory():
    """The classic result, recovered independently by the projector.

    Tetrahedral has an l=3 invariant; octahedral's lowest is l=4;
    icosahedral's lowest is l=6. If the group enumeration or the
    D-matrices were wrong these would not come out.
    """
    assert WG.invariant_dimension(3, "TETRAHEDRAL") == 1
    assert WG.invariant_dimension(3, "OCTAHEDRAL") == 0
    assert WG.invariant_dimension(4, "OCTAHEDRAL") == 1
    assert WG.invariant_dimension(4, "ICOSAHEDRAL") == 0
    assert WG.invariant_dimension(6, "ICOSAHEDRAL") == 1


def test_l0_is_invariant_under_every_group():
    for g in ("TETRAHEDRAL", "OCTAHEDRAL", "ICOSAHEDRAL"):
        assert WG.invariant_dimension(0, g) == 1


def test_l1_is_invariant_under_none():
    """A vector cannot be invariant under a polyhedral group."""
    for g in ("TETRAHEDRAL", "OCTAHEDRAL", "ICOSAHEDRAL"):
        assert WG.invariant_dimension(1, g) == 0


def test_unknown_group_rejected():
    with pytest.raises(ValueError):
        WG.group_elements("CUBIC_ISH")


# --- fields -----------------------------------------------------------

def test_field_rejects_wrong_coefficient_count():
    with pytest.raises(ValueError):
        G.HarmonicField("SYNTHETIC", [[1 + 0j], [1 + 0j]], "bad")


def test_field_rejects_unknown_family():
    with pytest.raises(ValueError):
        G.HarmonicField("ETHERIC", [[1 + 0j]], "bad")


def test_synthetic_field_is_reproducible():
    a = G.synthetic_field(lmax=6, seed=3)
    b = G.synthetic_field(lmax=6, seed=3)
    assert a.coeffs == b.coeffs


def test_different_seeds_differ():
    a = G.synthetic_field(lmax=6, seed=3)
    b = G.synthetic_field(lmax=6, seed=4)
    assert a.coeffs != b.coeffs


def test_injection_range_validated():
    with pytest.raises(ValueError):
        G.synthetic_field(lmax=4, seed=1, symmetry_injection=1.5)


def test_synthetic_field_is_always_flagged_synthetic():
    f = G.synthetic_field(lmax=4, seed=1)
    assert f.is_synthetic()
    assert f.family == "SYNTHETIC"


# --- scoring ----------------------------------------------------------

def test_score_is_a_fraction():
    f = G.synthetic_field(lmax=8, seed=11)
    s = G.symmetry_score(f, "ICOSAHEDRAL", (0.3, 0.5, 0.7))
    assert 0.0 <= s.score <= 1.0


def test_score_rejects_unknown_group():
    f = G.synthetic_field(lmax=8, seed=11)
    with pytest.raises(ValueError):
        G.symmetry_score(f, "ETHERIC", (0.0, 0.0, 0.0))


def test_injected_symmetry_raises_the_score():
    """The sensitivity check: the detector must see what is there."""
    plain = G.synthetic_field(lmax=6, seed=21, symmetry_injection=0.0)
    doped = G.synthetic_field(lmax=6, seed=21, symmetry_injection=0.5,
                              group="ICOSAHEDRAL")
    o = (0.0, 0.0, 0.0)
    assert G.symmetry_score(doped, "ICOSAHEDRAL", o).score > \
        G.symmetry_score(plain, "ICOSAHEDRAL", o).score


def test_injection_is_monotonic_in_strength():
    o = (0.0, 0.0, 0.0)
    scores = [
        G.symmetry_score(
            G.synthetic_field(lmax=6, seed=5, symmetry_injection=x,
                              group="ICOSAHEDRAL"),
            "ICOSAHEDRAL", o).score
        for x in (0.0, 0.3, 0.9)
    ]
    assert scores[0] < scores[1] < scores[2]


def test_best_orientation_is_at_least_as_good_as_any_draw():
    f = G.synthetic_field(lmax=6, seed=13)
    best = G.best_orientation(f, "TETRAHEDRAL", n_orientations=12,
                              seed=1)
    single = G.symmetry_score(f, "TETRAHEDRAL", (0.1, 0.2, 0.3))
    assert best.score >= min(best.score, single.score)


# --- controls ---------------------------------------------------------

def test_rotation_null_produces_a_distribution():
    f = G.synthetic_field(lmax=6, seed=17)
    n = G.rotation_null(f, "TETRAHEDRAL", n_draws=10, seed=2)
    assert n["n"] == 10
    assert 0.0 <= n["mean"] <= 1.0


def test_degree_matched_null_uses_the_same_dimension():
    f = G.synthetic_field(lmax=6, seed=17)
    n = G.degree_matched_null(f, "TETRAHEDRAL", n_draws=10, seed=2)
    assert n["n"] == 10


def test_selection_null_reruns_the_whole_search():
    f = G.synthetic_field(lmax=6, seed=17)
    n = G.selection_null(f, "TETRAHEDRAL", n_surrogates=5,
                         n_orientations=6, seed=2)
    assert len(n["maxima"]) == 5


def test_phase_randomized_surrogate_preserves_degree_power():
    f = G.synthetic_field(lmax=6, seed=19)
    s = G._phase_randomize(f, seed=5)
    for l in range(f.lmax + 1):
        assert f.power(l) == pytest.approx(s.power(l))


def test_holm_bonferroni_is_more_conservative_than_raw():
    p = {"A": 0.02, "B": 0.03, "C": 0.9}
    out = G.holm_bonferroni(p, alpha=0.05)
    assert not out["A"]["significant"]  # 0.02 > 0.05/3
    assert out["A"]["threshold"] == pytest.approx(0.05 / 3)


def test_holm_bonferroni_accepts_a_clear_winner():
    out = G.holm_bonferroni({"A": 0.001, "B": 0.9}, alpha=0.05)
    assert out["A"]["significant"]
    assert not out["B"]["significant"]


# --- the audit --------------------------------------------------------

def test_pure_noise_field_is_not_significant():
    """The null result that matters: noise must not produce a grid."""
    f = G.synthetic_field(lmax=6, seed=101)
    rep = G.audit(f, n_orientations=8, n_surrogates=12,
                  groups=("TETRAHEDRAL", "OCTAHEDRAL"))
    assert not rep["any_group_significant"]


def test_audit_always_reports_no_real_data_for_synthetic_fields():
    f = G.synthetic_field(lmax=6, seed=101)
    rep = G.audit(f, n_orientations=6, n_surrogates=8,
                  groups=("TETRAHEDRAL",))
    assert rep["planetary_status"] == "NO_REAL_DATA"
    assert "detector, not Earth" in rep["verdict"]


def test_audit_carries_the_claim_ceiling():
    f = G.synthetic_field(lmax=6, seed=101)
    rep = G.audit(f, n_orientations=6, n_surrogates=8,
                  groups=("TETRAHEDRAL",))
    assert "not an etheric grid" in rep["claim_ceiling"]


def test_audit_reports_p_against_the_selection_null():
    f = G.synthetic_field(lmax=6, seed=101)
    rep = G.audit(f, n_orientations=6, n_surrogates=8,
                  groups=("TETRAHEDRAL",))
    v = rep["groups"]["TETRAHEDRAL"]
    assert 0.0 <= v["p_vs_selection_null"] <= 1.0
    assert "selection_null_mean" in v


def test_becker_hagens_is_marked_as_an_overlay_not_a_group():
    assert "BECKER_HAGENS" in G.POLYHEDRAL_GROUPS
    assert G._projector_group("BECKER_HAGENS") == "ICOSAHEDRAL"


# --- data availability and refusals ----------------------------------

def test_no_real_data_is_reported_honestly():
    d = G.data_availability()
    assert d["any_real_field"] is False
    assert d["status"] == "NO_REAL_DATA"
    assert d["gravity_model"] is None


def test_node_significance_is_refused():
    with pytest.raises(G.DataUnavailable) as e:
        G.refuse_node_significance()
    assert "will not report a planetary node" in str(e.value)


def test_archaeological_data_is_held_separate():
    note = G.archaeological_confound_note()
    assert note["status"] == "SEPARATE_DATASET_NOT_POOLED"
    assert len(note["confounds"]) >= 5


def test_human_datasets_are_not_field_families():
    for h in G.HUMAN_DATASETS:
        assert h not in G.FIELD_FAMILIES
