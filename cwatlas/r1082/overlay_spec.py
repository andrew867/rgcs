"""P24 — Dynamic globe, shell, and magnetic overlay (rendering-contract spec).

The browser globe view is untestable in this environment, so P24 delivers the
**rendering contract** the view draws against: a deterministic, fully
serializable data-structure generator, :func:`build_overlay_state`, with no DOM
and no canvas. It makes the locked **two-layer root** visible and debuggable as
plain data:

* a **FIXED** layer — the Wilkes gravity-anomaly root marker and its icosa face
  centre. It is epoch-independent: animating the epoch never rotates it.
* a **DYNAMIC** layer — the South Atlantic Anomaly phase-zero direction resolved
  at ``(epoch, shell)``. It moves as the epoch and shell change.
* an **ORIENTATION** frame — the South-Up basis with viewpoint-safe handedness:
  clockwise-positive arrows from the Antarctic external viewpoint and the
  corresponding anticlockwise labels from the North-down inverse view.
* a **SHELL** layer — the shell index and the radius it supplies.
* a **CANDIDATE** layer — pins/regions from the forward geocoder (P21), if any.

Every layer is typed with a ``kind`` and carries only JSON-native values, so the
whole state round-trips through ``json.dumps``. The generator is deterministic
(``resolve`` is cached by ``(epoch, shell)``; no wall-clock is read) and returns
a typed refusal layer when the field model is out of validity rather than
inventing a direction.

Nothing here is measured. The candidate layer is ``CALIBRATED_CANDIDATE`` at
most and validates no source origin; the overlay asserts no physical effect.
"""

from __future__ import annotations

import json
from typing import Optional, Sequence

from cwatlas.r1082 import claims as _claims
from cwatlas.r1082 import root_certificate, southup
from cwatlas.r1082.semantic_expand import SHELL_MAX, SHELL_MIN

OVERLAY_CONTRACT_ID = "CW-R1082-OVERLAY"
OVERLAY_CONTRACT_VERSION = "1.0.0"

#: The arrow bearings (deg) the view draws around the phase-zero direction to
#: show the positive rotation sense. A declared, fixed set (deterministic).
_ARROW_BEARINGS_DEG = (0.0, 90.0, 180.0, 270.0)


def _orientation_arrows() -> list[dict]:
    """Clockwise-positive arrows (Antarctic view) + North-down inverse labels.

    The SAME physical positive rotation is CLOCKWISE from the Antarctic external
    viewpoint and ANTICLOCKWISE from North-down (the locked equivalence). Each
    arrow records both labels so the view never renders an ambiguous sign.
    """
    arrows = []
    for bearing in _ARROW_BEARINGS_DEG:
        antarctic = southup.describe_sense(bearing, southup.Viewpoint.ANTARCTIC_EXTERNAL)
        north_down = southup.describe_sense(bearing, southup.Viewpoint.NORTH_DOWN)
        arrows.append({
            "bearing_deg": bearing,
            "antarctic_external_sense": antarctic.value,
            "north_down_sense": north_down.value,
        })
    return arrows


def _fixed_root_layer(cert) -> dict:
    """The FIXED Wilkes root marker — epoch-independent by construction."""
    return {
        "kind": "FIXED_ROOT_MARKER",
        "type": "WILKES_GRAVITY_ANOMALY_CENTROID",
        "wilkes_selected_id": cert.wilkes_selected_id,
        "wilkes_ensemble_hash": cert.wilkes_ensemble_hash,
        "root_face_id": cert.root_face_id,
        "direction_unit": list(cert.root_face_center_direction),
        "epoch_independent": True,
        "note": "fixed spatial anchor; does not rotate as the epoch animates",
    }


def _dynamic_saa_layer(cert) -> dict:
    """The DYNAMIC SAA phase-zero direction at this (epoch, shell)."""
    saa = cert.saa
    region = saa.uncertainty_region
    return {
        "kind": "DYNAMIC_SAA_PHASE_ZERO",
        "type": "SAA_FIELD_MAGNITUDE_MINIMUM",
        "field_model": saa.field_model,
        "field_model_version": saa.field_model_version,
        "epoch_year": cert.epoch_year,
        "shell_index": cert.shell_index,
        "radius_m": cert.radius_m,
        "latitude_deg": saa.latitude_deg,
        "longitude_deg": saa.longitude_deg,
        "direction_ecef": list(saa.direction_ecef),
        "field_nt": saa.field_nt,
        "uncertainty": {
            "kind": region.kind.value,
            "center": [region.center[0], region.center[1]],
            "radius_m": region.radius_m,
            "area_m2": region.area_m2,
        },
        "result_class": saa.result_class,
        "epoch_dependent": True,
        "shell_dependent": True,
    }


def _orientation_layer(cert) -> dict:
    return {
        "kind": "ORIENTATION_FRAME",
        "pole": cert.orientation_pole,
        "positive_rotation": cert.orientation_positive_rotation,
        "positive_rotation_viewpoint": cert.orientation_viewpoint,
        "south_up_basis": [list(row) for row in cert.south_up_basis],
        "arrows": _orientation_arrows(),
        "north_down_inverse_view": True,
    }


def _shell_layer(cert) -> dict:
    return {
        "kind": "SHELL_SURFACE",
        "shell_index": cert.shell_index,
        "radius_m": cert.radius_m,
        "shell_supplies_radius": True,
        "altitude_missing": False,
    }


def _candidate_layer(candidates: Optional[Sequence]) -> dict:
    """Pins/regions from the forward geocoder (P21). Candidates only."""
    pins: list[dict] = []
    regions: list[dict] = []
    for cand in candidates or ():
        ser = cand.to_serializable() if hasattr(cand, "to_serializable") else cand
        geom = ser.get("geometry")
        if isinstance(geom, dict) and geom.get("type") == "POINT":
            pins.append({"latitude_deg": geom["latitude_deg"],
                         "longitude_deg": geom["longitude_deg"],
                         "result_type": ser.get("result_type"),
                         "profile_id": ser.get("profile_id")})
        elif isinstance(geom, list):
            for g in geom:
                pins.append({"latitude_deg": g.get("latitude_deg"),
                             "longitude_deg": g.get("longitude_deg"),
                             "result_type": ser.get("result_type"),
                             "profile_id": ser.get("profile_id")})
        unc = ser.get("uncertainty")
        if isinstance(unc, dict) and unc.get("kind"):
            regions.append(unc)
    return {
        "kind": "CANDIDATE_OUTPUTS",
        "pins": pins,
        "regions": regions,
        "max_evidence": _claims.MAX_CANDIDATE_EVIDENCE.value,
        "note": "candidate pins/regions are software results, never measured",
    }


def build_overlay_state(epoch_year: float, shell: int, *,
                        candidates: Optional[Sequence] = None,
                        body_id: str = "EARTH",
                        radius_m: Optional[float] = None) -> dict:
    """Build the serializable overlay state a globe view would draw.

    Resolves the two-layer root at ``(epoch, shell)`` via the cached root
    certificate. Returns a typed refusal layer (not an invented direction) when
    the field model is out of validity. The FIXED root layer is epoch-independent
    so the view can animate the epoch without rotating the root.
    """
    if not SHELL_MIN <= shell <= SHELL_MAX:
        raise ValueError(f"shell {shell} out of range [{SHELL_MIN}, {SHELL_MAX}].")

    cert = root_certificate.resolve_or_refuse(
        epoch_year, shell, body_id=body_id, radius_m=radius_m)

    header = {
        "contract_id": OVERLAY_CONTRACT_ID,
        "contract_version": OVERLAY_CONTRACT_VERSION,
        "profile_id": root_certificate.PROFILE_ID,
        "epoch_year": float(epoch_year),
        "shell_index": int(shell),
        "body_id": body_id,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "physical_effects": "PHYSICAL_EFFECTS_NOT_CLAIMED",
        "source_origin": "SOURCE_ORIGIN_NOT_VALIDATED",
    }

    if cert.is_refusal():
        header["result_type"] = cert.result_class
        header["layers"] = [{
            "kind": "MODEL_VALIDITY_REFUSAL",
            "epoch_year": cert.epoch_year,
            "shell_index": cert.shell_index,
            "radius_m": cert.radius_m,
            "reason": cert.reason,
            "note": "out of field-model validity; no direction is invented",
        }]
        header["in_validity"] = False
        return header

    header["in_validity"] = True
    header["certificate_hash"] = cert.certificate_hash
    header["layers"] = [
        _fixed_root_layer(cert),
        _dynamic_saa_layer(cert),
        _orientation_layer(cert),
        _shell_layer(cert),
        _candidate_layer(candidates),
    ]
    return header


def overlay_epoch_series(epochs: Sequence[float], shell: int, *,
                         body_id: str = "EARTH") -> list[dict]:
    """Overlay states across epochs (for the animation contract).

    The FIXED root layer is identical across every frame (it does not rotate);
    only the DYNAMIC SAA layer changes. This is the property the animation relies
    on and the tests assert.
    """
    return [build_overlay_state(e, shell, body_id=body_id) for e in epochs]


def is_serializable(state: dict) -> bool:
    """True iff the overlay state round-trips through JSON (contract guarantee)."""
    try:
        json.loads(json.dumps(state))
        return True
    except (TypeError, ValueError):
        return False


def overlay_spec_report() -> dict:
    """P24 declaration receipt. Pure data contract; two-layer root visible."""
    return {
        "phase_id": "P24",
        "tranche": "T06",
        "what_this_is": (
            "the dynamic globe/shell/magnetic overlay as a rendering-contract "
            "spec: a deterministic, fully serializable build_overlay_state(epoch, "
            "shell) that yields the FIXED Wilkes root marker, the DYNAMIC SAA "
            "phase-zero direction at that epoch+shell, the South-Up orientation "
            "frame with viewpoint-safe clockwise/anticlockwise arrows, the shell "
            "radius, and candidate pins/regions — pure data, no DOM/canvas."),
        "contract_id": OVERLAY_CONTRACT_ID,
        "contract_version": OVERLAY_CONTRACT_VERSION,
        "layers": ["FIXED_ROOT_MARKER", "DYNAMIC_SAA_PHASE_ZERO",
                   "ORIENTATION_FRAME", "SHELL_SURFACE", "CANDIDATE_OUTPUTS"],
        "reused_engine": (
            "cwatlas.r1082.root_certificate.resolve (cached) + southup; "
            "wilkes / saa via the certificate (NOT reimplemented)"),
        "fixed_root_epoch_independent": True,
        "dynamic_saa_epoch_and_shell_dependent": True,
        "viewpoint_safe_arrows": True,
        "shell_supplies_radius": True,
        "refuses_outside_validity": True,
        "serializable": True,
        "browser_ui": "OUT_OF_SCOPE_SPEC_LEVEL_ONLY (node exists, UI untestable)",
        "evidence_class": _claims.EvidenceClass.SOFTWARE_RESULT.value,
        "max_evidence": _claims.MAX_CANDIDATE_EVIDENCE.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "physical_effects": "PHYSICAL_EFFECTS_NOT_CLAIMED",
        "source_origin": "SOURCE_ORIGIN_NOT_VALIDATED",
        "verdict": "R1082_OVERLAY_RENDERING_CONTRACT_TWO_LAYER_ROOT_VISIBLE",
        "what_this_does_not_say": (
            "The overlay is a serializable data contract for a globe view; it "
            "renders no pixels, measures nothing, asserts no physical effect, "
            "and validates no source origin. Candidate pins are software results "
            "under a declared calibration."),
    }
