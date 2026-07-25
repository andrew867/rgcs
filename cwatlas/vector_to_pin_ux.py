"""P48 — Vector-to-pin UX state machine and refusal states.

The logic (not the GUI) behind Workflow B "vector to map". Given a decode
result and the calibration/CRS/epoch context, it selects one user-experience
state and explains, in plain terms, *why* a stronger state is unavailable.

States:

* ``UNIQUE_POINT`` — exactly one candidate **and** a prospective calibration is
  available **and** a CRS and epoch are declared. Only here is a single pin
  shown.
* ``ALIAS_SET`` — a small number of admissible candidates shown side by side.
* ``REGION`` — one arithmetic candidate but no calibration: a point pin would
  invent precision, so an error region is shown instead.
* ``HEATMAP`` — many candidates: a density map, never a forced pin.
* ``REFUSAL`` — no admissible decode, or missing CRS/epoch. A refusal (for
  example ``NO_UNIQUE_GEOGRAPHIC_DECODE``) is a normal, successful result.

The state machine never forces a pin: a single candidate without calibration
falls to ``REGION``, not ``UNIQUE_POINT``. This backs the UI; the browser
widget is out of scope.

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from cwatlas.claims import ClaimClass

#: A candidate set at or above this size renders as a heatmap, not an alias set.
DEFAULT_HEATMAP_THRESHOLD = 6

#: Standard message shown when a unique point is blocked by missing calibration.
CALIBRATION_UNAVAILABLE_MSG = (
    "A single pin is unavailable because this source vector has no prospective "
    "calibration. Without a calibrated mapping, an exact point would invent "
    "precision the data do not support; an error region is shown instead. "
    "Run a prospective known-destination challenge to enable a point.")

NO_UNIQUE_DECODE_MSG = (
    "NO_UNIQUE_GEOGRAPHIC_DECODE: no admissible decode was produced. This is a "
    "normal, successful result, not a failure.")

MISSING_CRS_EPOCH_MSG = (
    "A map pin may not be produced without a declared coordinate-reference-"
    "system and an epoch receipt (System Contract invariant 9).")


class PinState(Enum):
    """The vector-to-pin UX states."""

    UNIQUE_POINT = "UNIQUE_POINT"
    ALIAS_SET = "ALIAS_SET"
    REGION = "REGION"
    HEATMAP = "HEATMAP"
    REFUSAL = "REFUSAL"


@dataclass(frozen=True)
class UxDecision:
    """The chosen UX state, with a reason and a why-unavailable explanation."""

    state: PinState
    reason: str
    why_unavailable: str
    candidate_count: int
    calibration_available: bool
    crs: Optional[str]
    epoch: Optional[object]
    claim_class: str

    def is_refusal(self) -> bool:
        return self.state is PinState.REFUSAL


def decide_pin_state(candidate_count: int,
                     calibration_available: bool,
                     crs: Optional[str] = None,
                     epoch: Optional[object] = None,
                     heatmap_threshold: int = DEFAULT_HEATMAP_THRESHOLD
                     ) -> UxDecision:
    """Select the UX state from the decode result and calibration context.

    Precedence: a missing CRS/epoch, or an empty candidate set, is a REFUSAL.
    Otherwise many candidates -> HEATMAP; several -> ALIAS_SET; exactly one ->
    UNIQUE_POINT when calibration is available, else REGION.
    """
    if candidate_count < 0:
        raise ValueError("candidate_count must be non-negative.")
    if heatmap_threshold < 2:
        raise ValueError("heatmap_threshold must be >= 2.")

    # Refusal: no admissible decode.
    if candidate_count == 0:
        return UxDecision(
            state=PinState.REFUSAL,
            reason="no admissible candidate decode",
            why_unavailable=NO_UNIQUE_DECODE_MSG,
            candidate_count=0,
            calibration_available=calibration_available,
            crs=crs, epoch=epoch,
            claim_class=ClaimClass.REFUSAL.value,
        )

    # Refusal: a pin needs a CRS and an epoch (invariant 9).
    if not crs or epoch is None:
        return UxDecision(
            state=PinState.REFUSAL,
            reason="missing coordinate-reference-system or epoch",
            why_unavailable=MISSING_CRS_EPOCH_MSG,
            candidate_count=candidate_count,
            calibration_available=calibration_available,
            crs=crs, epoch=epoch,
            claim_class=ClaimClass.REFUSAL.value,
        )

    # Many candidates -> heatmap.
    if candidate_count >= heatmap_threshold:
        return UxDecision(
            state=PinState.HEATMAP,
            reason=f"{candidate_count} candidates render as a density heatmap",
            why_unavailable=(
                "A single pin or a side-by-side alias set is unavailable "
                "because the candidate set is too large; a heatmap avoids "
                "forcing false precision."),
            candidate_count=candidate_count,
            calibration_available=calibration_available,
            crs=crs, epoch=epoch,
            claim_class=ClaimClass.LEGACY_ALIAS_CANDIDATE.value,
        )

    # Several candidates -> alias set.
    if candidate_count >= 2:
        return UxDecision(
            state=PinState.ALIAS_SET,
            reason=f"{candidate_count} admissible candidates shown side by side",
            why_unavailable=(
                "A single pin is unavailable because more than one decode is "
                "admissible; forcing one pin would invent precision."),
            candidate_count=candidate_count,
            calibration_available=calibration_available,
            crs=crs, epoch=epoch,
            claim_class=ClaimClass.LEGACY_ALIAS_CANDIDATE.value,
        )

    # Exactly one candidate: calibration decides point vs region.
    if calibration_available:
        return UxDecision(
            state=PinState.UNIQUE_POINT,
            reason="one candidate with a prospective calibration and CRS/epoch",
            why_unavailable="",
            candidate_count=1,
            calibration_available=True,
            crs=crs, epoch=epoch,
            claim_class=ClaimClass.CALIBRATED_MAPPING.value,
        )
    return UxDecision(
        state=PinState.REGION,
        reason="one candidate but no calibration; an error region is shown",
        why_unavailable=CALIBRATION_UNAVAILABLE_MSG,
        candidate_count=1,
        calibration_available=False,
        crs=crs, epoch=epoch,
        claim_class=ClaimClass.MATHEMATICAL_TRANSLATION.value,
    )


def render_message(decision: UxDecision) -> str:
    """A single human-readable line describing the decision."""
    base = f"[{decision.state.value}] {decision.reason}"
    if decision.why_unavailable:
        return f"{base} — {decision.why_unavailable}"
    return base


def vector_to_pin_ux_report() -> dict:
    """P48 declaration receipt."""
    return {
        "phase_id": "P48",
        "what_this_is": (
            "the vector-to-pin UX state machine: UNIQUE_POINT / ALIAS_SET / "
            "REGION / HEATMAP / REFUSAL chosen from the decode result and "
            "calibration availability, with why-unavailable messages when "
            "calibration or a CRS/epoch is missing. A single candidate without "
            "calibration falls to REGION, never a forced pin."),
        "claim_class": ClaimClass.REFUSAL.value,
        "states": [s.value for s in PinState],
        "forces_a_pin": False,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "VECTOR_TO_PIN_UX_STATES_NO_FORCED_PIN",
    }
