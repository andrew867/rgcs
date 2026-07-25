"""P12 — the residual classifier: one honest class per residual, capped at
UNEXPLAINED_INSTRUMENT_RESIDUAL. Focused, negative, and determinism tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

try:
    import jsonschema
except ImportError:  # pragma: no cover
    jsonschema = None

from r15 import claims as C
from r15 import residuals as R


# --- fixtures -------------------------------------------------------------

def _budget(*, calibration_bound=True, model_adequate=True, small=True):
    """A synthetic error budget. ``small`` keeps the combined uncertainty
    modest so a large residual can exceed it in the ceiling tests."""
    comps = {
        "instrument_resolution": 0.10,
        "calibration": 0.10,
        "clock": 0.05,
        "environment": 0.05,
        "model_residual": 0.05,
    }
    return R.ErrorBudget(components=comps,
                         calibration_bound=calibration_bound,
                         model_adequate=model_adequate)


def _clean_attacks(fired=False, cause=C.ClaimClass.KNOWN_ORDINARY_EFFECT):
    """A battery of ordinary-explanation attack results (P11 concept, in)."""
    return (
        R.OrdinaryAttackResult("known_thermal_drift",
                               C.ClaimClass.KNOWN_ORDINARY_EFFECT,
                               fired and cause is C.ClaimClass.KNOWN_ORDINARY_EFFECT),
        R.OrdinaryAttackResult("model_misfit", C.ClaimClass.MODEL_ERROR,
                               fired and cause is C.ClaimClass.MODEL_ERROR),
        R.OrdinaryAttackResult("cal_drift", C.ClaimClass.CALIBRATION_ERROR,
                               fired and cause is C.ClaimClass.CALIBRATION_ERROR),
        R.OrdinaryAttackResult("mount_resonance", C.ClaimClass.FIXTURE_EFFECT,
                               fired and cause is C.ClaimClass.FIXTURE_EFFECT),
    )


def _classifier():
    return R.ResidualClassifier()


# --- focused: within-budget ----------------------------------------------

def test_within_budget_is_known_ordinary_effect_not_anomalous():
    rec = _classifier().classify(
        residual_id="r1", observation_ids=["o1"],
        residual_magnitude=0.01,  # well below combined uncertainty
        error_budget=_budget(), attacks=_clean_attacks())
    assert rec.classification.claim_class is C.ClaimClass.KNOWN_ORDINARY_EFFECT
    assert rec.classification.anomalous is False
    assert rec.classification.exceeds_uncertainty is False


def test_residual_below_uncertainty_is_never_anomalous_even_surviving_attacks():
    # survives every attack, but is within the budget -> not anomalous
    rec = _classifier().classify(
        residual_id="r1", observation_ids=["o1"],
        residual_magnitude=0.0, error_budget=_budget(),
        attacks=_clean_attacks(fired=False))
    assert rec.classification.anomalous is False
    assert rec.classification.claim_class is not R.RESIDUAL_CEILING


# --- focused: each ordinary cause ----------------------------------------

@pytest.mark.parametrize("cause", [
    C.ClaimClass.KNOWN_ORDINARY_EFFECT,
    C.ClaimClass.MODEL_ERROR,
    C.ClaimClass.CALIBRATION_ERROR,
    C.ClaimClass.FIXTURE_EFFECT,
])
def test_a_fired_ordinary_attack_yields_its_cause(cause):
    rec = _classifier().classify(
        residual_id="r1", observation_ids=["o1"],
        residual_magnitude=5.0,  # exceeds uncertainty
        error_budget=_budget(), attacks=_clean_attacks(fired=True, cause=cause))
    assert rec.classification.claim_class is cause
    assert rec.classification.anomalous is False
    assert rec.classification.exceeds_uncertainty is True


def test_multiple_fired_attacks_use_deterministic_precedence():
    attacks = (
        R.OrdinaryAttackResult("m", C.ClaimClass.MODEL_ERROR, True),
        R.OrdinaryAttackResult("c", C.ClaimClass.CALIBRATION_ERROR, True),
        R.OrdinaryAttackResult("f", C.ClaimClass.FIXTURE_EFFECT, True),
    )
    rec = _classifier().classify(
        residual_id="r1", observation_ids=["o1"], residual_magnitude=5.0,
        error_budget=_budget(), attacks=attacks)
    # CALIBRATION_ERROR has the highest precedence
    assert rec.classification.claim_class is C.ClaimClass.CALIBRATION_ERROR


def test_missing_calibration_forces_calibration_error_invalid():
    rec = _classifier().classify(
        residual_id="r1", observation_ids=["o1"], residual_magnitude=99.0,
        error_budget=_budget(calibration_bound=False),
        attacks=_clean_attacks(fired=False))
    # even a huge, unexplained residual is invalid without calibration
    assert rec.classification.claim_class is C.ClaimClass.CALIBRATION_ERROR
    assert rec.classification.anomalous is False


def test_inadequate_model_forces_model_error():
    rec = _classifier().classify(
        residual_id="r1", observation_ids=["o1"], residual_magnitude=5.0,
        error_budget=_budget(model_adequate=False),
        attacks=_clean_attacks(fired=False))
    assert rec.classification.claim_class is C.ClaimClass.MODEL_ERROR


# --- focused: the ceiling -------------------------------------------------

def test_survives_all_and_exceeds_and_unreplicated_is_the_ceiling():
    rec = _classifier().classify(
        residual_id="r1", observation_ids=["o1", "o2"],
        residual_magnitude=5.0, error_budget=_budget(),
        attacks=_clean_attacks(fired=False))
    assert rec.classification.claim_class is R.RESIDUAL_CEILING
    assert rec.classification.claim_class is \
        C.ClaimClass.UNEXPLAINED_INSTRUMENT_RESIDUAL
    assert rec.classification.anomalous is True
    assert rec.classification.replicated is False
    assert rec.classification.survived_all_attacks is True


def test_ceiling_reopening_test_demands_independent_replication():
    rec = _classifier().classify(
        residual_id="r1", observation_ids=["o1"], residual_magnitude=5.0,
        error_budget=_budget(), attacks=_clean_attacks(fired=False))
    assert "independent replication" in rec.reopening_test.lower()
    assert str(R.MIN_INDEPENDENT_LABS) in rec.reopening_test


# --- focused: replicated anomaly (only via replication) ------------------

def test_two_independent_labs_reach_replicated_anomaly():
    rep = R.ReplicationEvidence((
        R.ReplicationRecord("labA", independent=True, confirmed=True),
        R.ReplicationRecord("labB", independent=True, confirmed=True),
    ))
    rec = _classifier().classify(
        residual_id="r1", observation_ids=["o1"], residual_magnitude=5.0,
        error_budget=_budget(), attacks=_clean_attacks(fired=False),
        replication=rep)
    assert rec.classification.claim_class is C.ClaimClass.REPLICATED_ANOMALY
    assert rec.classification.replicated is True


# --- negative: one lab / one run cannot reach replicated anomaly ---------

def test_one_lab_repeated_cannot_reach_replicated_anomaly():
    rep = R.ReplicationEvidence((
        R.ReplicationRecord("labA", independent=True, confirmed=True),
        R.ReplicationRecord("labA", independent=True, confirmed=True),
    ))
    rec = _classifier().classify(
        residual_id="r1", observation_ids=["o1"], residual_magnitude=5.0,
        error_budget=_budget(), attacks=_clean_attacks(fired=False),
        replication=rep)
    # distinct-lab count is 1 -> not replicated -> still the ceiling
    assert rec.classification.claim_class is R.RESIDUAL_CEILING


def test_non_independent_replication_cannot_reach_replicated_anomaly():
    rep = R.ReplicationEvidence((
        R.ReplicationRecord("labA", independent=False, confirmed=True),
        R.ReplicationRecord("labB", independent=False, confirmed=True),
    ))
    rec = _classifier().classify(
        residual_id="r1", observation_ids=["o1"], residual_magnitude=5.0,
        error_budget=_budget(), attacks=_clean_attacks(fired=False),
        replication=rep)
    assert rec.classification.claim_class is R.RESIDUAL_CEILING


# --- negative: the ceiling is never promoted -----------------------------

def test_ceiling_is_not_promoted_to_new_physics():
    with pytest.raises(R.ResidualError):
        R.refuse_residual_as_new_physics()


def test_ceiling_is_not_replicated_without_replication():
    with pytest.raises(R.ResidualError):
        R.refuse_unexplained_as_replicated_without_replication(
            R.ReplicationEvidence())


def test_there_is_no_phryll_detected_state():
    with pytest.raises(C.ClaimError):
        R.refuse_phryll_detected()
    assert R.residuals_report()["has_phryll_detected_state"] is False


def test_report_claims_nothing():
    r = R.residuals_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["residual_ceiling"] == "UNEXPLAINED_INSTRUMENT_RESIDUAL"
    assert "REPLICATED_ANOMALY" in r["claim_classes_emitted"]


# --- versioning -----------------------------------------------------------

def test_classification_is_versioned():
    rec = _classifier().classify(
        residual_id="r1", observation_ids=["o1"], residual_magnitude=5.0,
        error_budget=_budget(), attacks=_clean_attacks(fired=False))
    assert rec.classifier_version == R.CLASSIFIER_VERSION
    assert rec.as_dict()["classifier_version"] == R.CLASSIFIER_VERSION


# --- determinism ----------------------------------------------------------

def test_classification_is_deterministic():
    args = dict(residual_id="r1", observation_ids=["o1", "o2"],
                residual_magnitude=5.0, error_budget=_budget(),
                attacks=_clean_attacks(fired=False))
    a = _classifier().classify(**args).as_dict()
    b = _classifier().classify(**args).as_dict()
    assert a == b
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


# --- input validation -----------------------------------------------------

def test_empty_error_budget_is_refused():
    with pytest.raises(R.ResidualError):
        R.ErrorBudget(components={})


def test_unknown_budget_component_is_refused():
    with pytest.raises(R.ResidualError):
        R.ErrorBudget(components={"not_a_real_component": 1.0})


def test_negative_residual_is_refused():
    with pytest.raises(R.ResidualError):
        _classifier().classify(
            residual_id="r1", observation_ids=["o1"],
            residual_magnitude=-1.0, error_budget=_budget())


def test_residual_needs_an_observation():
    with pytest.raises(R.ResidualError):
        _classifier().classify(
            residual_id="r1", observation_ids=[],
            residual_magnitude=1.0, error_budget=_budget())


def test_attack_cause_must_be_an_ordinary_cause():
    with pytest.raises(R.ResidualError):
        R.OrdinaryAttackResult("bad", C.ClaimClass.PHYSICAL_MEASUREMENT, True)


# --- schema conformance ---------------------------------------------------

def test_residual_record_conforms_to_schema():
    if jsonschema is None:  # pragma: no cover
        pytest.skip("jsonschema not installed")
    schema_path = (Path(__file__).resolve().parents[2]
                   / "r15" / "schemas" / "residual_record.schema.json")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    rec = _classifier().classify(
        residual_id="r1", observation_ids=["o1"], residual_magnitude=5.0,
        error_budget=_budget(), attacks=_clean_attacks(fired=False))
    jsonschema.validate(rec.as_dict(), schema)
