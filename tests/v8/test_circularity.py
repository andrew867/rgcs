"""P22 — the circularity and leakage audit: POWER (each planted leak kind
caught by its detector), negative (clean pipeline passes; circular result
refused as confirmatory), and determinism tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

try:
    import jsonschema
except ImportError:  # pragma: no cover
    jsonschema = None

from r15 import circularity as X

_SCHEMA_DIR = Path(__file__).resolve().parents[2] / "r15" / "schemas"


# --- POWER: each planted leak kind is caught by its own detector ----------

@pytest.mark.parametrize("kind", list(X.LeakKind))
def test_planted_leak_is_caught_by_its_detector(kind):
    steps = X.planted_leak_pipeline(kind)
    detector = X.DETECTORS[kind]
    if kind is X.LeakKind.TARGET_LEAKAGE:
        finding = detector(steps, X.PLANTED_TARGET_FEATURES)
    else:
        finding = detector(steps)
    assert finding.circular is True
    assert finding.kind is kind
    assert finding.steps, "the offending step must be named"


@pytest.mark.parametrize("kind", list(X.LeakKind))
def test_planted_leak_flags_pipeline_as_circular(kind):
    audit = X.audit_pipeline(X.planted_leak_pipeline(kind),
                             target_features=X.PLANTED_TARGET_FEATURES)
    assert audit.circular is True
    assert kind.value in audit.leak_kinds
    assert audit.circular_steps


def test_train_test_leakage_planted_id_overlap():
    steps = X.planted_leak_pipeline(X.LeakKind.TRAIN_TEST_LEAKAGE)
    f = X.detect_train_test_leakage(steps)
    assert f.circular is True
    assert "fit" in f.steps


def test_train_test_leakage_label_derived_feature():
    # a training-side fit step reading a label-derived feature is caught
    steps = (
        X.PipelineStep("split", X.StepRole.SPLIT, X.Fold.FULL,
                       item_ids=("A", "B")),
        X.PipelineStep("fit", X.StepRole.FIT, X.Fold.TRAIN,
                       item_ids=("A",), features=("y_hat",),
                       derived_from_labels=("y_hat",)),
    )
    f = X.detect_train_test_leakage(steps)
    assert f.circular is True
    assert "fit" in f.steps


def test_double_dipping_selection_on_full_data():
    steps = X.planted_leak_pipeline(X.LeakKind.DOUBLE_DIPPING)
    f = X.detect_double_dipping(steps)
    assert f.circular is True
    assert "select" in f.steps


def test_target_leakage_proxy_predictor():
    steps = X.planted_leak_pipeline(X.LeakKind.TARGET_LEAKAGE)
    f = X.detect_target_leakage(steps, X.PLANTED_TARGET_FEATURES)
    assert f.circular is True


def test_preprocessing_before_split_full_fold():
    steps = X.planted_leak_pipeline(X.LeakKind.PREPROCESSING_BEFORE_SPLIT)
    f = X.detect_preprocessing_before_split(steps)
    assert f.circular is True
    assert "normalize" in f.steps


def test_preprocessing_before_split_by_order():
    # a preprocess step positioned before the split is caught even on TRAIN
    steps = (
        X.PipelineStep("normalize", X.StepRole.PREPROCESS, X.Fold.TRAIN,
                       item_ids=("A",), features=("x",)),
        X.PipelineStep("split", X.StepRole.SPLIT, X.Fold.FULL,
                       item_ids=("A", "B")),
    )
    f = X.detect_preprocessing_before_split(steps)
    assert f.circular is True
    assert "normalize" in f.steps


def test_temporal_leakage_train_after_test():
    steps = X.planted_leak_pipeline(X.LeakKind.TEMPORAL_LEAKAGE)
    f = X.detect_temporal_leakage(steps)
    assert f.circular is True


# --- negative: the clean split-before-fit pipeline passes every detector --

@pytest.mark.parametrize("kind", list(X.LeakKind))
def test_clean_pipeline_passes_every_detector(kind):
    steps = X.clean_pipeline()
    detector = X.DETECTORS[kind]
    finding = detector(steps)
    assert finding.circular is False
    assert finding.steps == ()


def test_clean_pipeline_audit_is_not_circular():
    audit = X.audit_pipeline(X.clean_pipeline())
    assert audit.circular is False
    assert audit.leak_kinds == ()
    assert audit.circular_steps == ()


def test_clean_pipeline_target_leakage_negative_with_declared_targets():
    # even declaring target features, the clean pipeline uses none of them
    audit = X.audit_pipeline(X.clean_pipeline(),
                             target_features=("label_proxy",))
    assert audit.circular is False


def test_only_the_planted_kind_fires():
    # a single planted leak fires exactly one kind, not the others
    for kind in X.LeakKind:
        audit = X.audit_pipeline(X.planted_leak_pipeline(kind),
                                 target_features=X.PLANTED_TARGET_FEATURES)
        assert audit.leak_kinds == (kind.value,), (
            f"{kind} should fire exactly one kind, got {audit.leak_kinds}")


# --- refusal: a circular result is not confirmatory -----------------------

def test_refuse_circular_result_as_confirmatory_raises():
    audit = X.audit_pipeline(
        X.planted_leak_pipeline(X.LeakKind.TRAIN_TEST_LEAKAGE))
    with pytest.raises(X.CircularityError):
        X.refuse_circular_result_as_confirmatory(audit, "the hypothesis")


@pytest.mark.parametrize("kind", list(X.LeakKind))
def test_every_circular_audit_is_refused_as_confirmatory(kind):
    audit = X.audit_pipeline(X.planted_leak_pipeline(kind),
                             target_features=X.PLANTED_TARGET_FEATURES)
    with pytest.raises(X.CircularityError):
        X.refuse_circular_result_as_confirmatory(audit)


def test_clean_result_is_not_refused_as_confirmatory():
    audit = X.audit_pipeline(X.clean_pipeline())
    # a clean audit passes silently
    X.refuse_circular_result_as_confirmatory(audit, "the hypothesis")


def test_refuse_model_as_measurement_raises():
    with pytest.raises(X.claims.ClaimError if hasattr(X, "claims")
                       else Exception):
        X.refuse_model_as_measurement()


def test_refuse_phryll_detected_raises():
    import r15.claims as C
    with pytest.raises(C.ClaimError):
        X.refuse_phryll_detected()


# --- determinism ----------------------------------------------------------

def test_audit_is_deterministic():
    a = X.audit_pipeline(X.clean_pipeline())
    b = X.audit_pipeline(X.clean_pipeline())
    assert a.content_hash == b.content_hash


def test_planted_audit_is_deterministic():
    for kind in X.LeakKind:
        a = X.audit_pipeline(X.planted_leak_pipeline(kind),
                             target_features=X.PLANTED_TARGET_FEATURES)
        b = X.audit_pipeline(X.planted_leak_pipeline(kind),
                             target_features=X.PLANTED_TARGET_FEATURES)
        assert a.content_hash == b.content_hash


def test_clean_and_leaky_hashes_differ():
    clean = X.audit_pipeline(X.clean_pipeline())
    leaky = X.audit_pipeline(
        X.planted_leak_pipeline(X.LeakKind.DOUBLE_DIPPING))
    assert clean.content_hash != leaky.content_hash


# --- validation and hygiene -----------------------------------------------

def test_empty_pipeline_refused():
    with pytest.raises(X.CircularityError):
        X.audit_pipeline(())


def test_non_step_element_refused():
    with pytest.raises(X.CircularityError):
        X.audit_pipeline(("not a step",))


def test_step_needs_a_name():
    with pytest.raises(X.CircularityError):
        X.PipelineStep("  ", X.StepRole.FIT)


def test_report_claims_nothing():
    r = X.circularity_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["claim_class"] == "SOFTWARE_IMPLEMENTED"
    assert r["clean_pipeline_is_circular"] is False
    assert r["all_planted_leaks_caught"] is True
    assert r["has_phryll_detected_state"] is False
    assert r["verdict"] == X.VERDICT


def test_report_reuses_r13_authorities():
    r = X.circularity_report()
    joined = " ".join(r["reuses"])
    assert "r13.holdout" in joined
    assert "r13.serialize" in joined


def test_audit_serializes_to_schema_shaped_dict():
    audit = X.audit_pipeline(X.clean_pipeline())
    d = audit.as_dict()
    assert d["circular"] is False
    assert isinstance(d["findings"], list) and len(d["findings"]) == 5
    assert d["measured_here"] == "nothing"


# --- the terminal receipt conforms to the phase-receipt schema ------------

def test_receipt_conforms_to_phase_receipt_schema():
    if jsonschema is None:  # pragma: no cover
        pytest.skip("jsonschema not installed")
    schema = json.loads((_SCHEMA_DIR / "phase_receipt.schema.json")
                        .read_text(encoding="utf-8"))
    receipt = json.loads(
        (Path(__file__).resolve().parents[2] / "docs" / "v8" / "receipts"
         / "P22.json").read_text(encoding="utf-8"))
    jsonschema.validate(receipt, schema)
    assert receipt["phase_id"] == "P22"
    assert receipt["status"] == "COMPLETE"
    assert receipt["blocked_reason"] is None
    assert receipt["commit"] is None
