"""P45 — Known-anchor calibration: sealed selection, no retrospective promotion.

POWER: a well-posed calibration recovers a clean linear anchor mapping and a
prospective challenge promotes it to CALIBRATED_MAPPING. Negative: labels are
sealed during selection; a retrospective fit stays OPERATOR_HYPOTHESIS;
underdetermined and out-of-order inputs fail safely. Deterministic.
"""

from __future__ import annotations

import numpy as np
import pytest

from cwatlas import calibration as C
from cwatlas.claims import ClaimClass, ClaimError


def _linear_anchors(n=10, dim=3, seed=1):
    """Anchors from an exact affine map (no noise) for POWER tests."""
    rng = np.random.default_rng(seed)
    A = rng.uniform(-0.4, 0.4, size=(2, dim))
    b = np.array([3.0, -7.0])
    anchors = []
    for i in range(n):
        v = rng.uniform(-1.0, 1.0, size=dim)
        lat, lon = (A @ v + b).tolist()
        anchors.append(C.Anchor(tuple(v), (float(lat), float(lon)),
                                label=f"secret-label-{i}"))
    return C.AffineTransform(tuple(tuple(r) for r in A), (3.0, -7.0), dim), anchors


# --- POWER --------------------------------------------------------------------

def test_fit_recovers_exact_linear_mapping():
    true, anchors = _linear_anchors()
    cal = C.fit_calibration(C.SealedAnchorSet(anchors), holdout=2)
    assert cal.claim_class == ClaimClass.OPERATOR_HYPOTHESIS.value
    assert cal.train_rms_m < 1.0  # metres — near-exact fit
    assert cal.holdout_rms_m < 1.0
    assert cal.n_train == 8 and cal.n_holdout == 2


def test_prospective_challenge_promotes_to_calibrated_mapping():
    true, anchors = _linear_anchors(n=12)
    sealed = C.SealedAnchorSet(anchors)
    train, _hold = sealed.split(2)
    cal = C.fit_calibration(sealed, holdout=2)
    # A fresh unseen source vector; reveal its true point only after prediction.
    v_new = (0.11, -0.22, 0.33)
    revealed = true.apply(v_new)
    res = C.prospective_challenge(cal, v_new, revealed, tolerance_m=100.0,
                                  training_anchors=train)
    assert res.passed is True
    assert res.claim_class == ClaimClass.CALIBRATED_MAPPING.value


def test_apply_transform_matches_known_points():
    true, anchors = _linear_anchors()
    cal = C.fit_calibration(C.SealedAnchorSet(anchors), holdout=0)
    for a in anchors:
        pred = cal.predict(a.source_vector)
        assert C.great_circle_m(pred, a.known_point) < 1.0


# --- Negative: sealing (invariant 5) -----------------------------------------

def test_labels_sealed_during_selection():
    _true, anchors = _linear_anchors()
    sealed = C.SealedAnchorSet(anchors)
    with pytest.raises(ClaimError):
        sealed.revealed_labels()  # not frozen yet -> refused


def test_labels_revealed_after_freeze():
    _true, anchors = _linear_anchors()
    sealed = C.SealedAnchorSet(anchors)
    C.fit_calibration(sealed, holdout=2)  # freezes selection
    labels = sealed.revealed_labels()
    assert labels[0].startswith("secret-label")


def test_selection_inputs_carry_no_labels():
    _true, anchors = _linear_anchors()
    X, Y = C.SealedAnchorSet(anchors).selection_inputs()
    assert X.shape[0] == len(anchors) and Y.shape == (len(anchors), 2)
    # Arrays are plain floats — no label string can leak through them.
    assert X.dtype == float and Y.dtype == float


# --- Negative: no retrospective promotion ------------------------------------

def test_retrospective_fit_is_not_calibrated():
    _true, anchors = _linear_anchors()
    cal = C.fit_calibration(C.SealedAnchorSet(anchors), holdout=2)
    assert cal.claim_class != ClaimClass.CALIBRATED_MAPPING.value
    assert cal.claim_class == ClaimClass.OPERATOR_HYPOTHESIS.value


def test_refuse_retrospective_fit_as_calibrated_raises():
    with pytest.raises(ClaimError):
        C.refuse_retrospective_fit_as_calibrated()


def test_failed_challenge_stays_hypothesis():
    true, anchors = _linear_anchors(n=12)
    cal = C.fit_calibration(C.SealedAnchorSet(anchors), holdout=2)
    # Reveal a wildly wrong point -> challenge fails, no promotion.
    res = C.prospective_challenge(cal, (0.1, 0.1, 0.1), (80.0, 179.0),
                                  tolerance_m=10.0)
    assert res.passed is False
    assert res.claim_class == ClaimClass.OPERATOR_HYPOTHESIS.value


def test_challenge_refuses_reused_training_anchor():
    _true, anchors = _linear_anchors(n=12)
    sealed = C.SealedAnchorSet(anchors)
    train, _hold = sealed.split(2)
    cal = C.fit_calibration(sealed, holdout=2)
    seen = anchors[0]
    with pytest.raises(C.CalibrationError):
        C.prospective_challenge(cal, seen.source_vector, seen.known_point,
                                tolerance_m=100.0, training_anchors=train)


# --- Negative: malformed / underdetermined -----------------------------------

def test_underdetermined_fit_refused():
    _true, anchors = _linear_anchors(n=3, dim=3)  # need dim+1 = 4
    with pytest.raises(C.CalibrationError):
        C.fit_transform(C.SealedAnchorSet(anchors))


def test_bad_latitude_anchor_refused():
    with pytest.raises(C.CalibrationError):
        C.Anchor((1.0, 2.0), (200.0, 0.0))


def test_empty_anchor_set_refused():
    with pytest.raises(C.CalibrationError):
        C.SealedAnchorSet([])


def test_bad_tolerance_refused():
    _true, anchors = _linear_anchors()
    cal = C.fit_calibration(C.SealedAnchorSet(anchors), holdout=2)
    with pytest.raises(C.CalibrationError):
        C.prospective_challenge(cal, (0.1, 0.2, 0.3), (10.0, 10.0),
                                tolerance_m=0.0)


# --- Determinism --------------------------------------------------------------

def test_fit_is_deterministic():
    _true, anchors = _linear_anchors()
    a = C.fit_calibration(C.SealedAnchorSet(anchors), holdout=2)
    b = C.fit_calibration(C.SealedAnchorSet(anchors), holdout=2)
    assert a.transform == b.transform
    assert a.train_rms_m == b.train_rms_m


def test_report_declares_boundary():
    r = C.calibration_report()
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"
    assert r["retrospective_fit_is_calibrated"] is False
    assert r["labels_sealed_during_selection"] is True
