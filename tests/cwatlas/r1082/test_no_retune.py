"""P26 — no-retune enforcement.

Every frozen-parameter change is detected and refused, moving a label between
training and holdout is a retune, the holdout comparison is invalidated after a
mutation, a clean after-set passes, and determinism holds.
"""

from __future__ import annotations

import pytest

from cwatlas.r1082 import calibration_fit, calibration_freeze
from cwatlas.r1082 import claims, no_retune as N


def _frozen_receipt():
    frozen = calibration_freeze.freeze_calibration(calibration_fit.fit_all())
    return frozen.receipt()


def _frozen_params(receipt):
    return dict(receipt["parameters"]["frozen"])


def test_clean_after_set_passes_no_retune():
    receipt = _frozen_receipt()
    after = _frozen_params(receipt)
    report = N.detect_retune(receipt, after)
    assert report["retuned"] is False
    assert report["verdict"] == N.NO_RETUNE_DETECTED
    assert report["changed_parameters"] == []
    assert report["holdout_comparison"] == "VALID"
    assert report["before_hash"] == report["after_hash"]


def test_every_frozen_parameter_change_detected_and_refused():
    receipt = _frozen_receipt()
    base = _frozen_params(receipt)
    for param in claims.FROZEN_PARAMETERS:
        after = dict(base)
        # Mutate this one frozen parameter to a clearly different value.
        after[param] = "TAMPERED" if not isinstance(after[param], (int, float)) \
            else float(after[param]) + 1.0
        with pytest.raises(N.RetuneError) as exc:
            N.detect_retune(receipt, after)
        assert param in exc.value.changed_parameters
        assert exc.value.verdict == N.RETUNED_AFTER_REVEAL
        # RetuneError is an R1082ClaimError (routed through the locked refusal).
        assert isinstance(exc.value, claims.R1082ClaimError)


def test_label_move_between_train_and_holdout_is_a_retune():
    receipt = _frozen_receipt()
    after = _frozen_params(receipt)  # frozen params unchanged
    with pytest.raises(N.RetuneError) as exc:
        N.detect_retune(receipt, after, label_moves=["HOLDOUT_SYN_0001"])
    assert "HOLDOUT_SYN_0001" in exc.value.moved_labels
    assert exc.value.verdict == N.RETUNED_AFTER_REVEAL


def test_refuse_label_move_helper():
    with pytest.raises(N.RetuneError) as exc:
        N.refuse_label_move("V1", frm="training", to="holdout")
    assert "V1" in exc.value.moved_labels


def test_holdout_comparison_invalidated_after_mutation():
    receipt = _frozen_receipt()
    base = _frozen_params(receipt)
    assert N.holdout_comparison_status(receipt, base) == "VALID"
    tampered = dict(base)
    tampered["epoch_choice"] = 9999.0
    assert N.holdout_comparison_status(receipt, tampered) == "INVALIDATED"
    assert N.holdout_comparison_status(
        receipt, base, label_moves=["X"]) == "INVALIDATED"


def test_diff_frozen_parameters_pure():
    a = {k: i for i, k in enumerate(claims.FROZEN_PARAMETERS)}
    b = dict(a)
    b["handedness"] = "OTHER"
    assert N.diff_frozen_parameters(a, b) == ("handedness",)
    assert N.diff_frozen_parameters(a, a) == ()


def test_parameter_hash_deterministic_and_sensitive():
    receipt = _frozen_receipt()
    p = _frozen_params(receipt)
    assert N.parameter_hash(p) == N.parameter_hash(dict(p))
    q = dict(p)
    q["root_feature"] = "SOMETHING_ELSE"
    assert N.parameter_hash(p) != N.parameter_hash(q)


def test_new_profile_required_on_change():
    assert N.new_profile_required(("grid_rotation",)) is True
    assert N.new_profile_required(()) is False


def test_accepts_bare_frozen_mapping_forms():
    receipt = _frozen_receipt()
    base = _frozen_params(receipt)
    # Bare mapping before, wrapped-frozen after — both normalise identically.
    report = N.detect_retune(base, {"frozen": base})
    assert report["retuned"] is False


def test_report_governance_fields():
    r = N.no_retune_report()
    assert r["phase_id"] == "P26"
    assert r["tranche"] == "T07"
    assert r["violation_verdict"] == N.RETUNED_AFTER_REVEAL
    assert r["label_move_is_retune"] is True
    assert r["post_freeze_retuning"] == "REFUSED"
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["physical_effects"] == "PHYSICAL_EFFECTS_NOT_CLAIMED"
    assert r["source_origin"] == "SOURCE_ORIGIN_NOT_VALIDATED"
