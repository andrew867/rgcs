"""P46 — Synthetic anchor tests: planted signal recovered; no site decoded.

POWER: a planted hidden mapping is recovered by the P45 pipeline. Negative:
asserting a real site was decoded is refused; a close arithmetic match to the
synthetic control is refused as intent. Deterministic.
"""

from __future__ import annotations

import pytest

from cwatlas import anchor_tests as AT
from cwatlas.claims import ClaimClass, ClaimError


# --- POWER: planted-signal recovery ------------------------------------------

def test_planted_signal_recovered_noise_free():
    planted = AT.plant_signal(n_anchors=12, dim=3, seed=42, noise_deg=0.0)
    res = AT.recover_signal(planted, holdout=3)
    assert res.recovered is True
    assert res.max_param_abs_error < 1e-6
    assert res.holdout_rms_m < 1.0  # metres


def test_recovery_degrades_with_noise():
    clean = AT.recover_signal(AT.plant_signal(seed=7, noise_deg=0.0))
    noisy = AT.recover_signal(AT.plant_signal(seed=7, noise_deg=0.05))
    assert noisy.max_param_abs_error > clean.max_param_abs_error


def test_recovery_claim_class_is_translation():
    res = AT.recover_signal(AT.plant_signal(seed=3))
    assert res.claim_class == ClaimClass.MATHEMATICAL_TRANSLATION.value


# --- Negative: Stonehenge is a synthetic control, not a decode ---------------

def test_stonehenge_is_named_synthetic_control():
    anchor = AT.stonehenge_synthetic_anchor()
    assert "SYNTHETIC" in anchor.label.upper()
    assert anchor.known_point == AT.STONEHENGE_SYNTHETIC_POINT


def test_assert_site_decoded_is_refused():
    with pytest.raises(ClaimError):
        AT.assert_site_decoded("Stonehenge", assert_real=True)


def test_close_match_is_refused_as_intent():
    control = AT.STONEHENGE_SYNTHETIC_POINT
    # A prediction arithmetically on top of the synthetic control.
    with pytest.raises(ClaimError):
        AT.close_match_is_not_intent(control, control, radius_m=5_000.0)


def test_far_prediction_is_not_flagged_as_match():
    control = AT.STONEHENGE_SYNTHETIC_POINT
    far = (control[0] + 40.0, control[1] + 40.0)
    # Far away -> no refusal raised (not a close match).
    AT.close_match_is_not_intent(far, control, radius_m=5_000.0)


# --- Determinism --------------------------------------------------------------

def test_plant_signal_is_deterministic():
    a = AT.plant_signal(seed=99)
    b = AT.plant_signal(seed=99)
    assert a.true_transform == b.true_transform
    assert a.anchors == b.anchors


def test_report_declares_boundary():
    r = AT.anchor_tests_report()
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"
    assert r["stonehenge_is"] == "NAMED_SYNTHETIC_CONTROL_NOT_A_DECODE"
