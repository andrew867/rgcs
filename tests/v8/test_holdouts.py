"""R15 P20 — the holdout dataset authority.

Focused tests (deterministic disjoint five-way partition; the commitment
matches the true holdout and rejects a tampered one; power on planted
development data), negative and refusal tests (leakage refused; a score
before the model is frozen refused; a second one-shot score refused;
development data cannot be relabelled holdout; unauthorized access
detected; sequential testing spends an error budget; overfit is not
generalization), and determinism.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

try:
    import jsonschema
except ImportError:  # pragma: no cover
    jsonschema = None

from r13 import holdout as _holdout
from r15 import holdouts as H

_ROOT = Path(__file__).resolve().parents[2]
_SCHEMA_DIR = _ROOT / "r15" / "schemas"


# -- fixtures -----------------------------------------------------------

def _ids(n=300):
    return _holdout.synthetic_ids(n)


def _partition(n=300):
    return H.partition_dataset(_ids(n))


def _sealed_authority(policy=H.ScoringPolicy.ONE_SHOT, epoch=20260724):
    return H.build_synthetic_authority(policy=policy, epoch=epoch)


def _rule_aware(item_id):
    return _holdout.planted_label(item_id, H.DEFAULT_PLANTING_SALT,
                                  H.DEFAULT_NUM_CLASSES)


# -- focused: deterministic, disjoint five-way partition ----------------

def test_partition_is_disjoint_and_covers_all_items():
    ids = _ids()
    part = H.partition_dataset(ids)
    assert part.is_disjoint()
    assert part.covers(ids)
    # every named partition is present
    assert {name for name, _ in part.members} == {p.value for p in H.Partition}


def test_partition_is_deterministic():
    ids = _ids()
    a = H.partition_dataset(ids)
    b = H.partition_dataset(ids)
    assert a == b
    assert a.holdout_ids() == b.holdout_ids()


def test_partition_fractions_are_approximately_honoured():
    part = H.partition_dataset(_ids(4000))
    frac = part.actual_fraction(H.Partition.HOLDOUT)
    assert abs(frac - H.DEFAULT_FRACTIONS[H.Partition.HOLDOUT]) < 0.03


def test_partition_rejects_bad_fractions():
    with pytest.raises(H.HoldoutAuthorityError):
        H.partition_dataset(_ids(10), fractions={
            H.Partition.DEVELOPMENT: 0.5, H.Partition.CALIBRATION: 0.5,
            H.Partition.CONTROL: 0.5, H.Partition.HOLDOUT: 0.5,
            H.Partition.FUTURE_MEASUREMENT: 0.5})


def test_partition_needs_at_least_five_items():
    with pytest.raises(H.HoldoutAuthorityError):
        H.partition_dataset(["a", "b", "c"])


# -- focused: the seal matches the true holdout, rejects a tampered one --

def test_commitment_matches_true_holdout():
    part, authority = _sealed_authority()
    assert authority.manifest.verify(authority.manifest.holdout_labeled)


def test_commitment_rejects_tampered_holdout():
    part, authority = _sealed_authority()
    rows = authority.manifest.holdout_labeled
    tampered = ((rows[0][0], (rows[0][1] + 1) % H.DEFAULT_NUM_CLASSES),
                ) + tuple(rows[1:])
    assert not authority.manifest.verify(tampered)


def test_manifest_carries_source_and_epoch():
    _, authority = _sealed_authority(epoch=12345)
    assert authority.manifest.source == H.HoldoutSource.SYNTHETIC_PLANTED.value
    assert authority.manifest.epoch == 12345
    assert authority.manifest.committed is True


def test_external_physical_holdout_source_supported():
    labeled = (("X0", 1), ("X1", 0), ("X2", 2))
    m = H.seal_holdout(labeled, epoch=1, source=H.HoldoutSource.EXTERNAL_PHYSICAL)
    assert m.source == "EXTERNAL_PHYSICAL"
    assert m.verify(labeled)


# -- focused: score once after freezing, only against committed labels --

def test_score_after_freeze_uses_committed_labels():
    _, authority = _sealed_authority()
    authority.freeze({"model": "rule_aware"}, epoch=1)
    result = authority.score(_rule_aware, authority.manifest.holdout_labeled,
                             requester="analyst", epoch=2)
    assert result["labels_match_commitment"] is True
    assert result["accuracy"] == pytest.approx(1.0)
    assert result["score_index"] == 1


def test_score_rejects_labels_that_break_the_seal():
    _, authority = _sealed_authority()
    authority.freeze({"model": "rule_aware"}, epoch=1)
    rows = authority.manifest.holdout_labeled
    tampered = ((rows[0][0], (rows[0][1] + 1) % H.DEFAULT_NUM_CLASSES),
                ) + tuple(rows[1:])
    with pytest.raises(_holdout.HoldoutError):
        authority.score(_rule_aware, tampered, requester="analyst", epoch=2)


# -- focused: power on planted development data -------------------------

def test_power_rule_aware_decoder_detected_on_development():
    part = _partition()
    good = H.development_power_check(part, _rule_aware)
    assert good["detected"] is True
    assert good["development_accuracy"] == pytest.approx(1.0)


def test_power_null_decoder_not_detected():
    part = _partition()
    null = H.development_power_check(part, H.constant_decoder(0))
    assert null["detected"] is False
    assert null["development_accuracy"] < H.POWER_DETECTION_THRESHOLD


# -- negative: leakage refused ------------------------------------------

def test_holdout_in_training_is_refused():
    part = _partition()
    leaked_train = part.development_ids() + part.holdout_ids()[:1]
    with pytest.raises(_holdout.HoldoutError):
        H.refuse_holdout_in_training(leaked_train, part.holdout_ids())


def test_clean_split_has_no_leakage():
    part = _partition()
    # development and holdout are disjoint, so no refusal
    H.refuse_holdout_in_training(part.development_ids(), part.holdout_ids())


# -- negative: a score before the model is frozen is refused ------------

def test_score_before_model_frozen_is_refused():
    _, authority = _sealed_authority()
    assert not authority.model_is_frozen
    with pytest.raises(H.HoldoutAuthorityError):
        authority.score(_rule_aware, authority.manifest.holdout_labeled,
                        requester="analyst", epoch=1)


def test_refuse_score_before_model_frozen_direct():
    _, authority = _sealed_authority()
    with pytest.raises(H.HoldoutAuthorityError):
        H.refuse_score_before_model_frozen(authority)


# -- negative: a second one-shot score is refused -----------------------

def test_second_one_shot_score_is_refused():
    _, authority = _sealed_authority()
    authority.freeze({"model": "rule_aware"}, epoch=1)
    authority.score(_rule_aware, authority.manifest.holdout_labeled,
                    requester="analyst", epoch=2)
    with pytest.raises(H.HoldoutAuthorityError):
        authority.score(_rule_aware, authority.manifest.holdout_labeled,
                        requester="analyst", epoch=3)


def test_refuse_multiple_holdout_scoring_direct():
    with pytest.raises(H.HoldoutAuthorityError):
        H.refuse_multiple_holdout_scoring(1)


# -- negative: development data cannot be relabelled holdout ------------

def test_development_cannot_be_relabelled_holdout():
    with pytest.raises(H.HoldoutAuthorityError):
        H.refuse_relabel_partition_as_holdout(H.Partition.DEVELOPMENT,
                                              H.Partition.HOLDOUT)


@pytest.mark.parametrize("current", [H.Partition.DEVELOPMENT,
                                     H.Partition.CALIBRATION,
                                     H.Partition.CONTROL])
def test_any_seen_partition_cannot_become_holdout(current):
    with pytest.raises(H.HoldoutAuthorityError):
        H.refuse_relabel_partition_as_holdout(current, H.Partition.HOLDOUT)


def test_holdout_staying_holdout_is_allowed():
    # a no-op relabel of holdout -> holdout does not raise
    H.refuse_relabel_partition_as_holdout(H.Partition.HOLDOUT,
                                          H.Partition.HOLDOUT)


# -- negative: unauthorized access is detected and logged ---------------

@pytest.mark.parametrize("purpose", [H.AccessPurpose.TRAINING,
                                     H.AccessPurpose.MODEL_SELECTION])
def test_unauthorized_access_is_refused(purpose):
    _, authority = _sealed_authority()
    with pytest.raises(H.HoldoutAuthorityError):
        authority.request_access(purpose, requester="analyst", epoch=1)
    # the refused attempt was still logged
    assert authority.accesses[-1].purpose == purpose.value
    assert authority.accesses[-1].granted is False


def test_authorized_access_is_granted_and_logged():
    _, authority = _sealed_authority()
    rec = authority.request_access(H.AccessPurpose.AUDIT, requester="auditor",
                                   epoch=1)
    assert rec.granted is True
    assert len(authority.accesses) == 1


def test_every_score_attempt_is_logged():
    _, authority = _sealed_authority()
    authority.freeze({"model": "rule_aware"}, epoch=1)
    authority.score(_rule_aware, authority.manifest.holdout_labeled,
                    requester="analyst", epoch=2)
    score_accesses = [a for a in authority.accesses
                      if a.purpose == H.AccessPurpose.SCORE.value]
    assert len(score_accesses) == 1


# -- negative: sequential testing spends an error budget ----------------

def test_sequential_scoring_spends_the_error_budget():
    _, authority = _sealed_authority(policy=H.ScoringPolicy.SEQUENTIAL)
    authority.freeze({"model": "rule_aware"}, epoch=1)
    r1 = authority.score(_rule_aware, authority.manifest.holdout_labeled,
                         requester="analyst", epoch=2, alpha_spend=0.03)
    assert r1["alpha_spent"] == pytest.approx(0.03)
    assert r1["budget_remaining"] == pytest.approx(0.02)


def test_sequential_budget_exhaustion_refuses_further_looks():
    _, authority = _sealed_authority(policy=H.ScoringPolicy.SEQUENTIAL)
    authority.freeze({"model": "rule_aware"}, epoch=1)
    authority.score(_rule_aware, authority.manifest.holdout_labeled,
                    requester="analyst", epoch=2, alpha_spend=0.03)
    with pytest.raises(H.HoldoutAuthorityError):
        authority.score(_rule_aware, authority.manifest.holdout_labeled,
                        requester="analyst", epoch=3, alpha_spend=0.03)


def test_sequential_score_requires_declared_alpha():
    _, authority = _sealed_authority(policy=H.ScoringPolicy.SEQUENTIAL)
    authority.freeze({"model": "rule_aware"}, epoch=1)
    with pytest.raises(H.HoldoutAuthorityError):
        authority.score(_rule_aware, authority.manifest.holdout_labeled,
                        requester="analyst", epoch=2)


def test_sequential_policy_needs_a_budget():
    _, authority = _sealed_authority()
    with pytest.raises(H.HoldoutAuthorityError):
        H.HoldoutAuthority(manifest=authority.manifest,
                           policy=H.ScoringPolicy.SEQUENTIAL)


def test_alpha_budget_rejects_non_positive_spend():
    b = H.AlphaBudget(total=0.05)
    with pytest.raises(H.HoldoutAuthorityError):
        b.spend(0.0, epoch=1, label="x")


# -- negative: overfit is not generalization ----------------------------

def test_overfit_is_not_generalization():
    with pytest.raises(_holdout.HoldoutError):
        H.refuse_overfit_as_generalization(1.0, holdout_score=None)


# -- negative: a decode before the holdout is committed is refused ------

def test_decode_before_commit_is_refused():
    # an uncommitted r13 protocol is refused (reused machinery)
    protocol = _holdout.HoldoutProtocol(holdout_labeled=(("A", 1), ("B", 2)))
    assert not protocol.committed
    with pytest.raises(_holdout.HoldoutError):
        H.refuse_decode_before_commit(protocol)


# -- model freeze is content-bound and deterministic --------------------

def test_model_freeze_is_content_bound():
    f1 = H.freeze_model({"a": 1, "b": [2, 3]}, epoch=10)
    f2 = H.freeze_model({"b": [2, 3], "a": 1}, epoch=10)  # key order flipped
    assert f1.model_hash == f2.model_hash
    assert f1.matches({"a": 1, "b": [2, 3]})
    assert not f1.matches({"a": 1, "b": [2, 4]})


# -- determinism and non-claims -----------------------------------------

def test_report_is_deterministic_and_claims_nothing():
    r1 = H.holdouts_report()
    r2 = H.holdouts_report()
    assert r1 == r2
    assert r1["measured_here"] == "nothing"
    assert r1["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r1["claim_class"] == "SOFTWARE_IMPLEMENTED"
    assert r1["verdict"] == "HOLDOUT_DATASET_AUTHORITY_SEALED"
    # the report's own self-checks all hold
    assert r1["partition_is_disjoint"] is True
    assert r1["partition_covers_all_items"] is True
    assert r1["true_holdout_matches_commitment"] is True
    assert r1["tampered_holdout_matches_commitment"] is False
    assert r1["development_cannot_be_relabelled_holdout"] is True
    assert r1["score_before_model_frozen_refused"] is True
    assert r1["second_one_shot_score_refused"] is True
    assert r1["unauthorized_access_refused"] is True
    assert r1["power_rule_aware_detected"] is True
    assert r1["power_null_detected"] is False
    assert r1["sequential_budget_exhausted_refused"] is True


def test_report_uses_only_r13_and_r15_claims_no_sibling_phases():
    # the reused refusals are the r13 authority's own functions
    assert H.refuse_holdout_in_training is _holdout.refuse_holdout_in_training
    assert H.refuse_decode_before_commit is _holdout.refuse_decode_before_commit
    assert H.refuse_overfit_as_generalization is \
        _holdout.refuse_overfit_as_generalization


# -- schema conformance -------------------------------------------------

def test_receipt_conforms_to_phase_receipt_schema():
    if jsonschema is None:  # pragma: no cover
        pytest.skip("jsonschema not installed")
    schema = json.loads((_SCHEMA_DIR / "phase_receipt.schema.json")
                        .read_text(encoding="utf-8"))
    receipt = json.loads(
        (_ROOT / "docs" / "v8" / "receipts" / "P20.json")
        .read_text(encoding="utf-8"))
    jsonschema.validate(receipt, schema)
    assert receipt["phase_id"] == "P20"
    assert receipt["status"] == "COMPLETE"
    assert receipt["blocked_reason"] is None
    assert receipt["commit"] is None
