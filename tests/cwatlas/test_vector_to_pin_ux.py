"""P48 — Vector-to-pin UX state machine and refusal states.

POWER: each state is reachable from the decode result + calibration context.
Negative: a single candidate without calibration falls to REGION (never a
forced pin) with a why-unavailable message; missing CRS/epoch and empty decodes
are REFUSAL. Deterministic.
"""

from __future__ import annotations

import pytest

from cwatlas import vector_to_pin_ux as UX
from cwatlas.claims import ClaimClass


CRS = "EPSG:4326"
EPOCH = "2026-07-25T00:00:00Z"


# --- POWER: each state reachable ---------------------------------------------

def test_unique_point_when_calibrated_single_candidate():
    d = UX.decide_pin_state(1, calibration_available=True, crs=CRS, epoch=EPOCH)
    assert d.state is UX.PinState.UNIQUE_POINT
    assert d.claim_class == ClaimClass.CALIBRATED_MAPPING.value
    assert d.why_unavailable == ""


def test_region_when_single_candidate_no_calibration():
    d = UX.decide_pin_state(1, calibration_available=False, crs=CRS, epoch=EPOCH)
    assert d.state is UX.PinState.REGION
    assert "calibration" in d.why_unavailable.lower()


def test_alias_set_for_few_candidates():
    d = UX.decide_pin_state(3, calibration_available=True, crs=CRS, epoch=EPOCH)
    assert d.state is UX.PinState.ALIAS_SET
    assert d.claim_class == ClaimClass.LEGACY_ALIAS_CANDIDATE.value


def test_heatmap_for_many_candidates():
    d = UX.decide_pin_state(20, calibration_available=True, crs=CRS, epoch=EPOCH)
    assert d.state is UX.PinState.HEATMAP


def test_refusal_when_no_candidates():
    d = UX.decide_pin_state(0, calibration_available=True, crs=CRS, epoch=EPOCH)
    assert d.state is UX.PinState.REFUSAL
    assert "NO_UNIQUE_GEOGRAPHIC_DECODE" in d.why_unavailable
    assert d.is_refusal()


# --- Negative: refusals and no forced pin ------------------------------------

def test_refusal_when_missing_crs():
    d = UX.decide_pin_state(1, calibration_available=True, crs=None, epoch=EPOCH)
    assert d.state is UX.PinState.REFUSAL
    assert "coordinate-reference-system" in d.why_unavailable


def test_refusal_when_missing_epoch():
    d = UX.decide_pin_state(1, calibration_available=True, crs=CRS, epoch=None)
    assert d.state is UX.PinState.REFUSAL


def test_no_calibration_never_forces_unique_point():
    # Even with CRS/epoch and one candidate, no calibration => not a pin.
    d = UX.decide_pin_state(1, calibration_available=False, crs=CRS, epoch=EPOCH)
    assert d.state is not UX.PinState.UNIQUE_POINT


def test_heatmap_threshold_boundary():
    thr = UX.DEFAULT_HEATMAP_THRESHOLD
    below = UX.decide_pin_state(thr - 1, True, CRS, EPOCH)
    at = UX.decide_pin_state(thr, True, CRS, EPOCH)
    assert below.state is UX.PinState.ALIAS_SET
    assert at.state is UX.PinState.HEATMAP


def test_negative_count_refused():
    with pytest.raises(ValueError):
        UX.decide_pin_state(-1, True, CRS, EPOCH)


# --- render + determinism -----------------------------------------------------

def test_render_message_includes_state():
    d = UX.decide_pin_state(1, calibration_available=False, crs=CRS, epoch=EPOCH)
    msg = UX.render_message(d)
    assert d.state.value in msg


def test_decision_is_deterministic():
    a = UX.decide_pin_state(3, True, CRS, EPOCH)
    b = UX.decide_pin_state(3, True, CRS, EPOCH)
    assert a == b


def test_report_declares_boundary():
    r = UX.vector_to_pin_ux_report()
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"
    assert r["forces_a_pin"] is False
    assert set(r["states"]) == {s.value for s in UX.PinState}
