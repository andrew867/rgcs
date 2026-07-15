"""Hydrogenuine (HG) memory record and store/replay/update semantics.

RSCS-C.15 (record) and RSCS-O.14/15/16 (store/replay/update). CLASS = ENG:
this is an engineering memory data structure -- a spatial-memory record akin
to a SLAM keyframe or an event-sourced entry -- useful independently of any
neuroscience interpretation. It is NEVER evidence.

The Arisaka NHT/HAL proposal (SRC-3-07/08) motivates the *fields* (allocentric
+ egocentric coordinates, a frame transform between them, an event time and a
phase representation, orientation/scale, a predicted vs observed state). But:
- the space-to-phase encoding (RSCS-O.3) that fills the phase field is HYP;
- the HAL lattice (RSCS-C.14 / RSCS-O.13) is HYP and quarantined;
- NO consciousness/brain/memory conclusion is imported into RGCS physics, and
  nothing here claims quartz realizes memory (docs/EXCLUSION_MATRIX.md).

Replay/update semantics are deterministic and testable; the falsifiable
software claims (H-15..H-19) live in docs/NHT_HAL_RSCS_MAPPING.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, ClassVar

import numpy as np

from ..coordinates import (SpatialCoordinate, OrientationFrame, TimeCoordinate,
                           PhaseCoordinate, ModalState, Uncertainty,
                           ProvenanceTag)
from ..coordinates._base import RSCSCoordinate
from ..registry import rscs_classified
from ..transforms import frame_transform

__all__ = ["HydrogenuineRecord", "store", "replay", "update"]


@dataclass(frozen=True)
class HydrogenuineRecord(RSCSCoordinate):
    """RSCS-C.15. An engineering memory record (ENG, never evidence).

    Fields (all typed RSCS coordinates):
      allocentric  : SpatialCoordinate (C.1) -- world/map frame position;
      egocentric   : SpatialCoordinate (C.1) -- sensor/observer frame position;
      frame        : OrientationFrame (C.8)  -- ego -> allo transform;
      event_time   : TimeCoordinate (C.2);
      phase        : PhaseCoordinate (C.3)   -- OPTIONAL NHT space-to-phase
                     encoding; HYP when populated via RSCS-O.3;
      predicted    : ModalState (C.7)        -- expected observation;
      observed     : ModalState (C.7) | None -- actual observation (None until
                     seen);
      uncertainty  : Uncertainty (C.12)      -- localization uncertainty;
      provenance   : ProvenanceTag (C.13).

    The record enforces frame consistency: allocentric == frame . egocentric
    within tolerance (checked at store time, not construction, so partially
    built records are allowed).
    """

    registry_id: ClassVar[str] = "RSCS-C.15"

    allocentric: SpatialCoordinate
    egocentric: SpatialCoordinate
    frame: OrientationFrame
    event_time: TimeCoordinate
    predicted: ModalState
    observed: ModalState | None = None
    phase: PhaseCoordinate | None = None
    uncertainty: Uncertainty = field(
        default_factory=lambda: Uncertainty(0.0, 0.0))
    provenance: ProvenanceTag = field(
        default_factory=lambda: ProvenanceTag("internal", "ENG"))

    def __post_init__(self) -> None:
        for name, obj, typ in (
            ("allocentric", self.allocentric, SpatialCoordinate),
            ("egocentric", self.egocentric, SpatialCoordinate),
            ("frame", self.frame, OrientationFrame),
            ("event_time", self.event_time, TimeCoordinate),
            ("predicted", self.predicted, ModalState),
            ("uncertainty", self.uncertainty, Uncertainty),
            ("provenance", self.provenance, ProvenanceTag),
        ):
            if not isinstance(obj, typ):
                raise TypeError(f"{name} must be a {typ.__name__}")
        if self.observed is not None and not isinstance(self.observed,
                                                        ModalState):
            raise TypeError("observed must be a ModalState or None")
        if self.phase is not None and not isinstance(self.phase,
                                                     PhaseCoordinate):
            raise TypeError("phase must be a PhaseCoordinate or None")

    @property
    def is_observed(self) -> bool:
        return self.observed is not None

    def frame_consistent(self, atol_mm: float = 1e-6) -> bool:
        """True iff allocentric == frame . egocentric within tolerance."""
        mapped = frame_transform(self.egocentric, self.frame)
        return bool(np.allclose(mapped.vector, self.allocentric.vector,
                                atol=atol_mm))

    def components(self) -> dict[str, Any]:
        return {
            "allocentric": self.allocentric.to_dict(),
            "egocentric": self.egocentric.to_dict(),
            "frame": self.frame.to_dict(),
            "event_time": self.event_time.to_dict(),
            "phase": self.phase.to_dict() if self.phase else None,
            "predicted": self.predicted.to_dict(),
            "observed": self.observed.to_dict() if self.observed else None,
            "uncertainty": self.uncertainty.to_dict(),
            "provenance": self.provenance.to_dict(),
        }


@rscs_classified("ENG", registry=("RSCS-O.14",),
                 units="engineering record",
                 exclusions=("NHT/HAL: no consciousness/brain/memory import "
                             "into RGCS physics (SRC-3-07)",
                             "no claim quartz realizes memory"),
                 note="HG memory store (write); engineering abstraction, never "
                      "evidence; enforces frame consistency")
def store(allocentric: SpatialCoordinate, egocentric: SpatialCoordinate,
          frame: OrientationFrame, event_time: TimeCoordinate,
          predicted: ModalState, *, observed: ModalState | None = None,
          phase: PhaseCoordinate | None = None,
          uncertainty: Uncertainty | None = None,
          provenance: ProvenanceTag | None = None,
          require_consistent: bool = True) -> HydrogenuineRecord:
    """RSCS-O.14. Write a Hydrogenuine memory record.

    If ``require_consistent`` (default), the allocentric position must equal
    frame . egocentric within tolerance (the frame transform must actually
    relate the two representations); otherwise a ValueError is raised."""
    rec = HydrogenuineRecord(
        allocentric=allocentric, egocentric=egocentric, frame=frame,
        event_time=event_time, predicted=predicted, observed=observed,
        phase=phase,
        uncertainty=uncertainty if uncertainty is not None
        else Uncertainty(0.0, 0.0),
        provenance=provenance if provenance is not None
        else ProvenanceTag("internal", "ENG"))
    if require_consistent and not rec.frame_consistent():
        raise ValueError("frame inconsistency: allocentric != frame . "
                         "egocentric; set require_consistent=False to store "
                         "an unreconciled record")
    return rec


@rscs_classified("ENG", registry=("RSCS-O.15",),
                 units="engineering record",
                 note="HG memory replay (recall) into a query frame; "
                      "re-references the egocentric position, allocentric "
                      "anchor is invariant (localization/replay fidelity H-18)")
def replay(record: HydrogenuineRecord,
           query_frame: OrientationFrame) -> HydrogenuineRecord:
    """RSCS-O.15. Replay a record as seen from ``query_frame``.

    The allocentric (world) position is the invariant anchor; the egocentric
    position is recomputed as query_frame^-1 . allocentric, and the stored
    frame is replaced by query_frame. Replaying with the original frame
    returns an equivalent record (replay fidelity, tested)."""
    if not isinstance(query_frame, OrientationFrame):
        raise TypeError("query_frame must be an OrientationFrame")
    new_ego_vec = query_frame.inverse().rotation @ record.allocentric.vector
    new_ego = SpatialCoordinate(tuple(float(v) for v in new_ego_vec),
                                f"ego:{query_frame.name}")
    return HydrogenuineRecord(
        allocentric=record.allocentric, egocentric=new_ego,
        frame=query_frame, event_time=record.event_time,
        predicted=record.predicted, observed=record.observed,
        phase=record.phase, uncertainty=record.uncertainty,
        provenance=record.provenance.extend_path("replay"))


@rscs_classified("ENG", registry=("RSCS-O.16",),
                 units="engineering record",
                 note="HG memory update: fold an observation into the record; "
                      "observed replaces the prediction, uncertainty is "
                      "reconciled (calibration H-19)")
def update(record: HydrogenuineRecord, observed: ModalState,
           updated_uncertainty: Uncertainty | None = None
           ) -> HydrogenuineRecord:
    """RSCS-O.16. Fold a new observation into a record.

    The observed state is recorded; the uncertainty is updated (default: the
    caller supplies the reconciled uncertainty; if omitted, the prior is
    kept). Prediction error is available as predicted vs observed by the
    caller. Deterministic, no hidden state."""
    if not isinstance(observed, ModalState):
        raise TypeError("observed must be a ModalState")
    return HydrogenuineRecord(
        allocentric=record.allocentric, egocentric=record.egocentric,
        frame=record.frame, event_time=record.event_time,
        predicted=record.predicted, observed=observed, phase=record.phase,
        uncertainty=updated_uncertainty if updated_uncertainty is not None
        else record.uncertainty,
        provenance=record.provenance.extend_path("update"))
