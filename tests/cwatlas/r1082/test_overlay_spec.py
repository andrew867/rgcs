"""P24 — dynamic globe/shell/magnetic overlay rendering-contract spec.

Covers: build_overlay_state yields the five typed layers (fixed root, dynamic
SAA, orientation frame, shell, candidates); the fixed root is epoch-independent
while the dynamic SAA moves with epoch and shell (animation contract); the
viewpoint-safe clockwise/anticlockwise arrows; the shell supplies the radius;
the whole state is JSON-serializable and deterministic; out-of-validity yields a
typed refusal layer, not an invented direction.
"""

from __future__ import annotations

import pytest

from cwatlas.r1082 import geocode_forward as G
from cwatlas.r1082 import overlay_spec as O
from cwatlas.r1082 import root_certificate


@pytest.fixture(autouse=True)
def _clear_cache():
    root_certificate.cache_clear()
    yield


def _layer(state, kind):
    return next(l for l in state["layers"] if l["kind"] == kind)


def test_build_overlay_has_all_layers():
    state = O.build_overlay_state(2020.0, 3)
    kinds = [l["kind"] for l in state["layers"]]
    assert kinds == ["FIXED_ROOT_MARKER", "DYNAMIC_SAA_PHASE_ZERO",
                     "ORIENTATION_FRAME", "SHELL_SURFACE", "CANDIDATE_OUTPUTS"]
    assert state["in_validity"] is True
    assert state["contract_id"] == O.OVERLAY_CONTRACT_ID


def test_fixed_root_epoch_independent_dynamic_saa_moves():
    a = O.build_overlay_state(1990.0, 3)
    b = O.build_overlay_state(2050.0, 3)
    fa, fb = _layer(a, "FIXED_ROOT_MARKER"), _layer(b, "FIXED_ROOT_MARKER")
    # The fixed root does NOT rotate as the epoch animates.
    assert fa["direction_unit"] == fb["direction_unit"]
    assert fa["root_face_id"] == fb["root_face_id"]
    assert fa["wilkes_ensemble_hash"] == fb["wilkes_ensemble_hash"]
    # The dynamic SAA phase-zero DOES move with epoch.
    da, db = _layer(a, "DYNAMIC_SAA_PHASE_ZERO"), _layer(b, "DYNAMIC_SAA_PHASE_ZERO")
    assert (da["latitude_deg"], da["longitude_deg"]) != \
           (db["latitude_deg"], db["longitude_deg"])


def test_dynamic_saa_shifts_with_shell():
    a = O.build_overlay_state(2020.0, 6)
    b = O.build_overlay_state(2020.0, 7)
    da, db = _layer(a, "DYNAMIC_SAA_PHASE_ZERO"), _layer(b, "DYNAMIC_SAA_PHASE_ZERO")
    assert da["radius_m"] != db["radius_m"]
    assert (da["latitude_deg"], da["longitude_deg"]) != \
           (db["latitude_deg"], db["longitude_deg"])


def test_epoch_series_fixed_root_invariant():
    frames = O.overlay_epoch_series([2000.0, 2010.0, 2020.0, 2030.0], 3)
    fixed = [_layer(f, "FIXED_ROOT_MARKER")["direction_unit"] for f in frames]
    assert all(d == fixed[0] for d in fixed)
    dyn = [tuple(_layer(f, "DYNAMIC_SAA_PHASE_ZERO")["direction_ecef"])
           for f in frames]
    assert len(set(dyn)) == len(dyn)     # every epoch a distinct phase-zero


def test_orientation_arrows_viewpoint_safe():
    state = O.build_overlay_state(2020.0, 3)
    ori = _layer(state, "ORIENTATION_FRAME")
    assert ori["pole"] == "SOUTH_UP"
    assert ori["positive_rotation"] == "CLOCKWISE"
    for arrow in ori["arrows"]:
        # The same physical positive rotation reads opposite from each viewpoint.
        assert arrow["antarctic_external_sense"] != arrow["north_down_sense"]


def test_shell_layer_supplies_radius():
    state = O.build_overlay_state(2020.0, 6)
    shell = _layer(state, "SHELL_SURFACE")
    assert shell["radius_m"] is not None
    assert shell["shell_supplies_radius"] is True
    assert shell["altitude_missing"] is False


def test_candidate_layer_from_forward_geocode():
    sf = G.single_family_stub()
    fwd = G.geocode("165876523", sf, shell=3)
    state = O.build_overlay_state(2020.0, 3, candidates=[fwd])
    cand = _layer(state, "CANDIDATE_OUTPUTS")
    assert len(cand["pins"]) >= 1
    assert cand["max_evidence"] == "CALIBRATED_CANDIDATE"


def test_serializable_and_deterministic():
    a = O.build_overlay_state(2020.0, 3)
    b = O.build_overlay_state(2020.0, 3)
    assert O.is_serializable(a) is True
    assert a == b                                    # deterministic
    assert a["certificate_hash"] == b["certificate_hash"]


def test_out_of_validity_refusal_not_invented():
    # Epoch far outside the SAA model validity -> a typed refusal layer.
    state = O.build_overlay_state(3000.0, 3)
    assert state["in_validity"] is False
    kinds = [l["kind"] for l in state["layers"]]
    assert kinds == ["MODEL_VALIDITY_REFUSAL"]
    assert "validity" in state["layers"][0]["reason"].lower()


def test_bad_shell_refused():
    with pytest.raises(ValueError):
        O.build_overlay_state(2020.0, 9)


def test_report_seals_claims():
    r = O.overlay_spec_report()
    assert r["phase_id"] == "P24"
    assert r["tranche"] == "T06"
    assert r["fixed_root_epoch_independent"] is True
    assert r["dynamic_saa_epoch_and_shell_dependent"] is True
    assert r["viewpoint_safe_arrows"] is True
    assert r["shell_supplies_radius"] is True
    assert r["serializable"] is True
    assert r["measured_here"] == "nothing"
    assert r["physical_effects"] == "PHYSICAL_EFFECTS_NOT_CLAIMED"
    assert r["source_origin"] == "SOURCE_ORIGIN_NOT_VALIDATED"
