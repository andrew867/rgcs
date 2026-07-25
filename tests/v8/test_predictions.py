"""R15 P19 — prospective prediction registry: seal-before-run discipline.

Focused tests (the seal is deterministic; a sealed prediction verifies; the
power-on-planted check is present and passes), negative tests (a prediction
with no null is refused; a prediction with no power is refused; an edit after
the seal is detected as HARKing; a post-run result with no prior seal is
exploratory, not confirmatory; a stale prediction is detected after a model
change), and a determinism check.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

try:
    import jsonschema
except ImportError:  # pragma: no cover
    jsonschema = None

from r13 import preregister as _prereg
from r13 import serialize as _serialize
from r15 import predictions as P

_SCHEMA_DIR = Path(__file__).resolve().parents[2] / "r15" / "schemas"


# -- fixtures -----------------------------------------------------------

def _prediction() -> P.RegisteredPrediction:
    return P.EXAMPLE_PREDICTION


def _fingerprint() -> P.ArtifactFingerprint:
    return P.EXAMPLE_FINGERPRINT


# -- focused: the seal is deterministic and tamper-evident --------------

def test_seal_is_deterministic():
    a = P.seal(_prediction())
    b = P.seal(_prediction())
    assert a == b
    assert isinstance(a, str) and len(a) == 64


def test_sealed_prediction_verifies():
    pred = _prediction()
    commitment = P.seal(pred)
    assert P.is_sealed(pred)
    assert P.is_sealed(commitment)


def test_any_input_change_alters_the_hash():
    pred = _prediction()
    base = P.seal(pred)
    # change the hypothesis
    edited = P.RegisteredPrediction(
        prediction_id=pred.prediction_id,
        hypothesis=pred.hypothesis + " CHANGED",
        predicted_signature=pred.predicted_signature,
        quantities=pred.quantities, null_model=pred.null_model,
        decision_rule=pred.decision_rule, analysis_plan=pred.analysis_plan,
        power_on_planted=pred.power_on_planted, fingerprint=pred.fingerprint,
        stopping_rule=pred.stopping_rule, mode=pred.mode,
        epoch_committed=pred.epoch_committed)
    assert P.seal(edited) != base


def test_changing_a_predicted_quantity_alters_the_hash():
    pred = _prediction()
    base = P.seal(pred)
    q0 = pred.quantities[0]
    changed_q = P.PredictedQuantity(
        name=q0.name, unit=q0.unit, tolerance=q0.tolerance + 0.01,
        mode=q0.mode, frequency_hz=q0.frequency_hz, direction=q0.direction,
        null_expectation=q0.null_expectation)
    edited = P.RegisteredPrediction(
        prediction_id=pred.prediction_id, hypothesis=pred.hypothesis,
        predicted_signature=pred.predicted_signature,
        quantities=(changed_q,) + pred.quantities[1:],
        null_model=pred.null_model, decision_rule=pred.decision_rule,
        analysis_plan=pred.analysis_plan,
        power_on_planted=pred.power_on_planted, fingerprint=pred.fingerprint,
        stopping_rule=pred.stopping_rule, mode=pred.mode,
        epoch_committed=pred.epoch_committed)
    assert P.seal(edited) != base


def test_changing_the_model_fingerprint_alters_the_hash():
    pred = _prediction()
    base = P.seal(pred)
    other_model = dict(P.EXAMPLE_MODEL)
    other_model["order"] = 9
    fp = P.ArtifactFingerprint.over(
        other_model, P.EXAMPLE_CODE, P.EXAMPLE_DATA, P.EXAMPLE_PARAMS)
    edited = P.RegisteredPrediction(
        prediction_id=pred.prediction_id, hypothesis=pred.hypothesis,
        predicted_signature=pred.predicted_signature,
        quantities=pred.quantities, null_model=pred.null_model,
        decision_rule=pred.decision_rule, analysis_plan=pred.analysis_plan,
        power_on_planted=pred.power_on_planted, fingerprint=fp,
        stopping_rule=pred.stopping_rule, mode=pred.mode,
        epoch_committed=pred.epoch_committed)
    assert P.seal(edited) != base


# -- focused: power on planted data is present and passes ---------------

def test_power_on_planted_check_present_and_passes():
    planted = np.concatenate([np.zeros(64), 8.0 * np.ones(64)])

    def detect(x: np.ndarray) -> bool:
        half = x.size // 2
        return bool(abs(x[half:].mean() - x[:half].mean()) > 3.0)

    result = P.power_on_planted_check(detect, planted)
    assert result["detects_planted_effect"] is True
    assert result["detects_pure_noise"] is False
    assert result["has_power"] is True


def test_powerless_detector_has_no_power():
    planted = np.concatenate([np.zeros(64), 8.0 * np.ones(64)])
    # a detector that never fires has no power
    result = P.power_on_planted_check(lambda x: False, planted)
    assert result["has_power"] is False


# -- focused: registry validation ---------------------------------------

def test_registry_registers_and_validates():
    reg = P.PredictionRegistry()
    commitment = reg.register(_prediction())
    assert commitment == P.seal(_prediction())
    v = reg.validate()
    assert v["prediction_count"] == 1
    assert v["all_have_null_model"] is True
    assert v["all_prove_power_on_planted_data"] is True
    assert v["all_prospective"] is True


# -- focused: exploratory vs confirmatory separation --------------------

def test_sealed_analysis_is_confirmatory_unsealed_is_exploratory():
    commitment = P.seal(_prediction())
    assert P.classify_analysis(commitment) == "CONFIRMATORY"
    assert P.classify_analysis("not-a-real-commitment") == "EXPLORATORY"


# -- negative: a prediction with no null model is refused ---------------

def test_prediction_without_null_is_refused():
    with pytest.raises(P.PredictionError):
        P.RegisteredPrediction(
            prediction_id="NO_NULL", hypothesis="h", predicted_signature="s",
            quantities=P.example_quantities(), null_model="   ",
            decision_rule="d", analysis_plan="a", power_on_planted="p",
            fingerprint=_fingerprint())


def test_refuse_prediction_without_null_direct():
    with pytest.raises(P.PredictionError):
        # a lightweight stand-in object carrying an empty null_model
        class _Stub:
            null_model = ""
        P.refuse_prediction_without_null(_Stub())


# -- negative: a prediction with no proven power is refused -------------

def test_prediction_without_power_is_refused():
    with pytest.raises(P.PredictionError):
        P.RegisteredPrediction(
            prediction_id="NO_POWER", hypothesis="h", predicted_signature="s",
            quantities=P.example_quantities(), null_model="n",
            decision_rule="d", analysis_plan="a", power_on_planted="",
            fingerprint=_fingerprint())


# -- negative: a predicted quantity with no null expectation is refused -

def test_quantity_without_null_expectation_is_refused():
    with pytest.raises(P.PredictionError):
        P.PredictedQuantity(
            name="q", unit="arb", tolerance=0.1, mode="MODE",
            frequency_hz=10.0, direction=P.Direction.NONZERO,
            null_expectation="")


# -- negative: a measurement claim class is refused ---------------------

def test_prediction_cannot_carry_a_measurement_claim_class():
    with pytest.raises(P.PredictionError):
        P.RegisteredPrediction(
            prediction_id="M", hypothesis="h", predicted_signature="s",
            quantities=P.example_quantities(), null_model="n",
            decision_rule="d", analysis_plan="a", power_on_planted="p",
            fingerprint=_fingerprint(), claim_class="BENCH_MEASUREMENT")


# -- negative: post-run predictions cannot be prospective ---------------

def test_edit_after_seal_is_detected_as_harking():
    pred = _prediction()
    P.seal(pred)  # seal it first
    edited = P.RegisteredPrediction(
        prediction_id=pred.prediction_id,
        hypothesis=pred.hypothesis + " (rewritten after the results)",
        predicted_signature=pred.predicted_signature,
        quantities=pred.quantities, null_model=pred.null_model,
        decision_rule=pred.decision_rule, analysis_plan=pred.analysis_plan,
        power_on_planted=pred.power_on_planted, fingerprint=pred.fingerprint,
        stopping_rule=pred.stopping_rule, mode=pred.mode,
        epoch_committed=pred.epoch_committed)
    with pytest.raises(P.PredictionError):
        P.refuse_edit_after_seal(pred, edited)


def test_edit_before_seal_is_allowed():
    pred = _prediction()
    edited = P.RegisteredPrediction(
        prediction_id=pred.prediction_id,
        hypothesis=pred.hypothesis + " draft change",
        predicted_signature=pred.predicted_signature,
        quantities=pred.quantities, null_model=pred.null_model,
        decision_rule=pred.decision_rule, analysis_plan=pred.analysis_plan,
        power_on_planted=pred.power_on_planted, fingerprint=pred.fingerprint,
        stopping_rule=pred.stopping_rule, mode=pred.mode,
        epoch_committed=pred.epoch_committed)
    # editing is legal before the seal
    result = P.refuse_edit_after_seal(pred, edited, already_sealed=False)
    assert result["allowed"] is True
    assert "hypothesis" in result["changed_fields"]


def test_result_without_prior_seal_is_exploratory_not_confirmatory():
    with pytest.raises(P.PredictionError):
        P.refuse_result_without_prior_seal("never-sealed-commitment")
    with pytest.raises(P.PredictionError):
        P.refuse_result_without_prior_seal(None)


def test_sealed_prediction_is_never_a_result():
    with pytest.raises(P.PredictionError):
        P.refuse_prediction_as_result(_prediction())


# -- negative: stale predictions are detected ---------------------------

def test_stale_prediction_detected_after_model_change():
    pred = _prediction()
    # same fingerprint -> not stale
    assert P.is_stale(pred, pred.fingerprint) is False
    # change the model -> stale
    changed = dict(P.EXAMPLE_MODEL)
    changed["order"] = 5
    current = P.ArtifactFingerprint.over(
        changed, P.EXAMPLE_CODE, P.EXAMPLE_DATA, P.EXAMPLE_PARAMS)
    assert P.is_stale(pred, current) is True
    report = P.staleness_report(pred, current)
    assert report["stale"] is True
    assert "model_hash" in report["changed_components"]
    with pytest.raises(P.PredictionError):
        P.refuse_stale_prediction(pred, current)


def test_fresh_prediction_is_not_refused_as_stale():
    pred = _prediction()
    # identical fingerprint does not raise
    P.refuse_stale_prediction(pred, pred.fingerprint)


# -- sealed bundle on an R13 hash chain ---------------------------------

def test_sealed_bundle_verifies_on_hash_chain():
    bundle = P.seal_bundle(_prediction(), epoch=20260724)
    assert P.verify_bundle(bundle) is True
    assert bundle.commitment == P.seal(_prediction())


def test_tampered_bundle_chain_fails_verification():
    b1 = P.seal_bundle(_prediction(), epoch=1)
    b2 = P.seal_bundle(_prediction(), epoch=2, chain=b1.chain)
    assert P.verify_bundle(b2) is True
    # tamper: swap the tip's payload for a mutated record
    tip = b2.chain[-1]
    forged = _serialize.Record(
        payload={"prediction_id": "FORGED"}, claim_class=tip.claim_class,
        epoch=tip.epoch, prev_hash=tip.prev_hash,
        record_hash=tip.record_hash)
    forged_bundle = P.SealedBundle(
        prediction_id=b2.prediction_id, commitment=b2.commitment,
        fingerprint_combined=b2.fingerprint_combined, epoch=b2.epoch,
        chain=b2.chain[:-1] + (forged,))
    assert P.verify_bundle(forged_bundle) is False


# -- reuse of R13, not duplication --------------------------------------

def test_base_preregistration_is_a_genuine_r13_prereg():
    pred = _prediction()
    base = pred.base_preregistration()
    assert isinstance(base, _prereg.Preregistration)
    # the R13 seal of the base plan is part of the R15 commitment
    assert _prereg.is_sealed(base) or _prereg.seal(base)  # seals without error


# -- determinism and the report -----------------------------------------

def test_report_is_deterministic_and_claims_nothing():
    r1 = P.predictions_report()
    r2 = P.predictions_report()
    assert r1 == r2
    assert r1["measured_here"] == "nothing"
    assert r1["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r1["claim_class"] == "MODEL_PREDICTION"
    assert r1["prediction_claim_class"] == "PROSPECTIVE_PREDICTION"
    assert r1["verdict"] == "PROSPECTIVE_PREDICTION_REGISTRY_SEALED"
    # every self-check in the report holds
    assert r1["seal_is_deterministic"] is True
    assert r1["unsealed_analysis_is_exploratory"] is True
    assert r1["sealed_analysis_is_confirmatory"] is True
    assert r1["result_without_prior_seal_refused"] is True
    assert r1["edit_after_seal_refused"] is True
    assert r1["prediction_is_stale_after_model_change"] is True
    assert r1["stale_prediction_refused"] is True
    assert r1["prediction_as_result_refused"] is True
    assert r1["prediction_without_null_refused"] is True
    assert r1["prediction_without_power_refused"] is True
    assert r1["sealed_bundle_verifies"] is True
    assert r1["power_discipline_demo"]["has_power"] is True


def test_report_uses_only_r13_and_r15_claims_no_sibling_phases():
    import r15.predictions as mod
    src = Path(mod.__file__).read_text(encoding="utf-8")
    # imports r13 authorities and r15.claims only; no sibling r15 phase module
    assert "from r13 import" in src
    assert "from r15 import claims" in src
    for sibling in ("r15.blinding", "r15.clock_phase", "r15.protocols",
                    "r15.instruments"):
        assert f"import {sibling}" not in src


# -- receipt conforms to the phase receipt schema -----------------------

def test_receipt_conforms_to_phase_receipt_schema():
    if jsonschema is None:  # pragma: no cover
        pytest.skip("jsonschema not installed")
    schema = json.loads((_SCHEMA_DIR / "phase_receipt.schema.json")
                        .read_text(encoding="utf-8"))
    receipt = json.loads(
        (Path(__file__).resolve().parents[2] / "docs" / "v8" / "receipts"
         / "P19.json").read_text(encoding="utf-8"))
    jsonschema.validate(receipt, schema)
    assert receipt["phase_id"] == "P19"
    assert receipt["status"] == "COMPLETE"
    assert receipt["blocked_reason"] is None
    assert receipt["commit"] is None
