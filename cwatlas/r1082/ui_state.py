"""P30 — Atlas UI view-model (the code-backed UI contract).

The browser Atlas UI is untestable in this environment (no DOM, and the browser
UI stays spec-level — see ``docs/cwatlas/r1082/ATLAS_UI_SPEC.md``). So P30's
*testable* deliverable is the **serializable view-model** the UI would bind to:
:func:`build_view_model` produces the exact data the map-to-vector and
vector-to-map screens render, with **no hidden defaults** — every control value
and every assumption is stated in the model *before* an operation runs.

The view-model reuses the engine, it does not reimplement it:

* the **globe overlay** (fixed Wilkes root marker, dynamic SAA phase-zero,
  South-Up orientation frame, shell surface, candidate pins/regions) comes from
  :func:`cwatlas.r1082.overlay_spec.build_overlay_state`;
* the **agreement surface** (per-cell variance / angular dispersion across the
  retained families, and the ``CANDIDATE_ALIAS_SET`` membership) comes from
  :func:`cwatlas.r1082.candidate_ensemble.build_candidate_map`;
* the optional **decoded candidate** for a pasted source vector comes from the
  forward geocoder (:mod:`cwatlas.r1082.geocode_forward`).

Every panel carries the three seals and ``measured_here == "nothing"``. Candidate
pins are ``CALIBRATED_CANDIDATE`` at most: the UI renders regions and alias sets,
never a false-exact pin, and never a measured or origin-validated coordinate.
"""

from __future__ import annotations

import json
from typing import Optional, Sequence

from cwatlas.r1082 import (
    calibration_fit,
    calibration_freeze,
    candidate_ensemble,
    claims as _claims,
    geocode_forward,
    overlay_spec,
)
from cwatlas.r1082.route_core import RouteError, parse_five_token
from cwatlas.r1082.semantic_expand import SHELL_MAX, SHELL_MIN

UI_STATE_CONTRACT_ID = "CW-R1082-UISTATE"
UI_STATE_CONTRACT_VERSION = "1.0.0"

#: The controls the operator drives, surfaced with no hidden defaults.
_CONTROL_SPEC = {
    "shell": {"kind": "integer", "min": SHELL_MIN, "max": SHELL_MAX,
              "supplies_radius": True},
    "epoch": {"kind": "decimal_year",
              "note": "conventional epoch; never a wall-clock read"},
    "profile": {"kind": "enum",
                "choices": ["none", "single", "all", "frozen"],
                "note": "the calibration profile; 'none' yields regions"},
    "packet_depth": {"kind": "enum",
                     "choices": ["SHELL_ONLY", "SHELL_PLUS_COARSE", "FULL"]},
    "mode": {"kind": "enum",
             "choices": ["MAP_TO_VECTOR", "VECTOR_TO_MAP"]},
}

#: The seven-field-label surface the vector-to-map view exposes on decode.
_SEMANTIC_FIELDS = ("route_core", "shell", "epoch_coarse", "epoch_fine",
                    "body", "family", "profile")

_SEALS = {
    "measured_here": "nothing",
    "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
    "physical_effects": "PHYSICAL_EFFECTS_NOT_CLAIMED",
    "source_origin": "SOURCE_ORIGIN_NOT_VALIDATED",
}


def _assumptions(epoch_year: float, shell: int, profile_kind: str) -> dict:
    """State every assumption BEFORE execution (no hidden defaults)."""
    return {
        "profile_id": "EARTH_ROOT_D_V1",
        "epoch_year": float(epoch_year),
        "shell_index": int(shell),
        "shell_supplies_radius": True,
        "altitude_missing": False,
        "calibration_profile": profile_kind,
        "frozen_parameters": list(_claims.FROZEN_PARAMETERS),
        "locked_decisions_reopened": False,
        "candidate_max_evidence": _claims.MAX_CANDIDATE_EVIDENCE.value,
        "note": ("these assumptions are shown before any encode/decode runs; "
                 "the UI exposes no hidden default"),
    }


def _candidate_panel(fwd) -> dict:
    """The vector-to-map candidate panel: pins, regions, alias set, uncertainty."""
    if fwd is None:
        return {"present": False,
                "note": "no source vector pasted; paste a vector to decode"}
    ser = fwd.to_serializable()
    geometry = ser.get("geometry")
    pins: list[dict] = []
    if isinstance(geometry, dict) and geometry.get("type") == "POINT":
        pins.append({"latitude_deg": geometry["latitude_deg"],
                     "longitude_deg": geometry["longitude_deg"]})
    elif isinstance(geometry, list):
        for g in geometry:
            pins.append({"latitude_deg": g.get("latitude_deg"),
                         "longitude_deg": g.get("longitude_deg")})
    return {
        "present": True,
        "source_vector": fwd.source_vector,
        "result_type": fwd.result_type,
        "is_candidate": fwd.is_candidate(),
        "is_alias_set": (fwd.result_type
                         == _claims.ResultClass.CANDIDATE_ALIAS_SET.value),
        "pins": pins,
        "region": ser.get("uncertainty"),
        "reason": fwd.reason,
        "max_evidence": _claims.MAX_CANDIDATE_EVIDENCE.value,
        "rendered_as_measured": False,
    }


def _agreement_panel(epoch_profiles: Sequence[float]) -> dict:
    """The agreement surface across retained families (per-cell variance).

    Reuses the frozen calibration + candidate ensemble; deterministic. Shows how
    the CANDIDATE_ALIAS_SET / agreement surface is surfaced to the operator.
    """
    fit = calibration_fit.fit_all()
    frozen = calibration_freeze.freeze_calibration(fit)
    result = candidate_ensemble.build_candidate_map(
        (7, 7, 7, 7, 7), frozen, epoch_profiles=tuple(epoch_profiles))
    surface = result.surface.to_dict()
    return {
        "result_type": result.result_type,
        "member_count": surface["member_count"],
        "cluster_count": surface["cluster_count"],
        "agreement_fraction": surface["agreement_fraction"],
        "dispersion_deg": surface["dispersion_deg"],
        "per_component_variance": surface["per_component_variance"],
        "collapsed_to_point": False,
        "freeze_hash": result.freeze_hash,
        "note": ("tightly clustered members agree; spread members disagree; the "
                 "complete bounded alias set is shown, never collapsed"),
    }


def build_view_model(epoch_year: float = 2020.0, shell: int = 3, *,
                     source_vector: Optional[str] = None,
                     profile_kind: str = "single",
                     family: Optional[str] = None,
                     epoch_profiles: Sequence[float] =
                     candidate_ensemble.DEFAULT_EPOCH_PROFILES,
                     body_id: str = "EARTH") -> dict:
    """Build the serializable view-model the Atlas UI binds to.

    The UI never invents state: this model carries the controls (with their
    domains), the stated assumptions, the globe overlay (the two-layer root
    layers), an optional decoded-candidate panel for a pasted source vector, and
    the agreement surface across the retained families. It round-trips through
    JSON and is deterministic.
    """
    if not SHELL_MIN <= shell <= SHELL_MAX:
        raise ValueError(f"shell {shell} out of range [{SHELL_MIN}, {SHELL_MAX}].")

    fwd = None
    decode_error = None
    if source_vector is not None:
        profile = None
        if profile_kind == "single":
            profile = (geocode_forward.single_family_stub(family) if family
                       else geocode_forward.single_family_stub())
        elif profile_kind == "all":
            profile = geocode_forward.default_frozen_stub()
        elif profile_kind == "frozen":
            profile = geocode_forward.load_frozen_profile()
        try:
            parse_five_token(source_vector)
            fwd = geocode_forward.geocode(
                source_vector, profile, shell=shell, epoch_year=epoch_year,
                body=body_id)
        except RouteError as exc:
            decode_error = f"INVALID_SOURCE_VECTOR: {exc}"

    overlay = overlay_spec.build_overlay_state(
        epoch_year, shell, candidates=[fwd] if fwd is not None else None,
        body_id=body_id)

    model = {
        "contract_id": UI_STATE_CONTRACT_ID,
        "contract_version": UI_STATE_CONTRACT_VERSION,
        "profile_id": "EARTH_ROOT_D_V1",
        "mode": ("VECTOR_TO_MAP" if source_vector is not None
                 else "MAP_TO_VECTOR"),
        "controls": _CONTROL_SPEC,
        "control_values": {
            "epoch": float(epoch_year), "shell": int(shell),
            "profile": profile_kind, "family": family, "body": body_id,
        },
        "semantic_fields": list(_SEMANTIC_FIELDS),
        "assumptions": _assumptions(epoch_year, shell, profile_kind),
        "overlay": overlay,
        "candidate_panel": _candidate_panel(fwd),
        "agreement_surface": _agreement_panel(epoch_profiles),
        "decode_error": decode_error,
        "export": {"formats": ["JSON", "GeoJSON", "KML"], "one_click": True},
    }
    model.update(_SEALS)
    return model


def is_serializable(model: dict) -> bool:
    """True iff the view-model round-trips through JSON (contract guarantee)."""
    try:
        json.loads(json.dumps(model, default=float))
        return True
    except (TypeError, ValueError):
        return False


def ui_state_report() -> dict:
    """P30 declaration receipt. A code-backed UI contract; nothing measured."""
    return {
        "phase_id": "P30",
        "tranche": "T08",
        "what_this_is": (
            "the Atlas UI view-model: a deterministic, serializable "
            "build_view_model(epoch, shell) that yields the data the "
            "map-to-vector and vector-to-map screens bind to — controls with "
            "their domains, assumptions stated before execution, the two-layer "
            "root globe overlay, a decoded-candidate panel, and the "
            "agreement/alias-set surface — with no hidden defaults."),
        "contract_id": UI_STATE_CONTRACT_ID,
        "contract_version": UI_STATE_CONTRACT_VERSION,
        "panels": ["controls", "assumptions", "overlay", "candidate_panel",
                   "agreement_surface", "export"],
        "reused_engine": (
            "cwatlas.r1082.overlay_spec.build_overlay_state + "
            "candidate_ensemble.build_candidate_map + geocode_forward "
            "(NOT reimplemented)"),
        "browser_ui": ("OUT_OF_SCOPE_SPEC_LEVEL_ONLY — the live browser UI is "
                       "untestable; see docs/cwatlas/r1082/ATLAS_UI_SPEC.md"),
        "hidden_defaults": False,
        "assumptions_shown_before_execution": True,
        "alias_set_and_agreement_surface_shown": True,
        "uncertainty_collapsed_to_point": False,
        "one_click_export": True,
        "evidence_class": _claims.EvidenceClass.SOFTWARE_RESULT.value,
        "max_evidence": _claims.MAX_CANDIDATE_EVIDENCE.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "physical_effects": "PHYSICAL_EFFECTS_NOT_CLAIMED",
        "source_origin": "SOURCE_ORIGIN_NOT_VALIDATED",
        "verdict": "R1082_UI_VIEW_MODEL_CODE_BACKED_NO_HIDDEN_DEFAULTS",
        "what_this_does_not_say": (
            "The view-model is the serializable contract a globe UI binds to; it "
            "renders no pixels, measures nothing, asserts no physical effect, "
            "and validates no source origin. Candidate pins are software results "
            "under a declared calibration."),
    }
