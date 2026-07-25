"""P10 -- ITRS/ITRF, epoch, and plate-motion semantics.

An Earth coordinate is never timeless. The same crustal point has a
*different* ECEF position in ITRF at epoch t1 than at epoch t2, because the
tectonic plate it sits on drifts. This module makes epoch a first-class,
mandatory part of a coordinate and provides a simple linear (constant-
velocity) plate-motion model so that difference is explicit and reversible.

Legacy interpretations are preserved as named realizations (ITRF2008,
ITRF2014, ITRF2020, ...), not overwritten. Nothing here claims a geographic
or extraordinary source semantics; propagating a coordinate through time is
arithmetic on a *declared* model.

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED

Epochs are decimal years (e.g. 2020.0) and are always passed in -- never a
wall-clock read. Velocities are metres/year; positions are ECEF metres.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from typing import Dict, Tuple

import numpy as np

from cwatlas import claims

#: Time scale for the decimal-year epochs used here.
TIME_SCALE = "TT_DECIMAL_YEAR"
BODY_ID = "EARTH"


class FrameError(ValueError):
    """Raised on an invalid frame, epoch, or plate-motion input."""


@dataclass(frozen=True)
class ITRFRealization:
    """A named ITRF realization, preserved as a versioned interpretation.

    ``reference_epoch`` is the realization's conventional reference epoch in
    decimal years. Keeping realizations named prevents the newest model from
    silently rewriting older coordinates.
    """

    frame_id: str
    reference_epoch: float

    def __post_init__(self) -> None:
        if not self.frame_id:
            raise FrameError("frame_id must be a non-empty string")
        if not math.isfinite(self.reference_epoch):
            raise FrameError("reference_epoch must be a finite decimal year")


#: The realization registry. Legacy realizations are retained, never dropped.
ITRF_REALIZATIONS: Dict[str, ITRFRealization] = {
    "ITRF2008": ITRFRealization("ITRF2008", 2005.0),
    "ITRF2014": ITRFRealization("ITRF2014", 2010.0),
    "ITRF2020": ITRFRealization("ITRF2020", 2015.0),
}


def get_realization(frame_id: str) -> ITRFRealization:
    try:
        return ITRF_REALIZATIONS[frame_id]
    except KeyError:
        raise FrameError(
            f"unknown ITRF realization {frame_id!r}; known: "
            f"{sorted(ITRF_REALIZATIONS)}")


@dataclass(frozen=True)
class PlateMotionModel:
    """A linear constant-velocity plate-motion model for one site.

    ``velocity_ecef_m_per_yr`` is a 3-vector of ECEF drift in metres/year.
    A coordinate propagated with a zero velocity is unchanged; a non-zero
    velocity makes t1 and t2 differ by exactly ``velocity * (t2 - t1)``.
    """

    plate_id: str
    velocity_ecef_m_per_yr: Tuple[float, float, float]

    def __post_init__(self) -> None:
        if not self.plate_id:
            raise FrameError("plate_id must be a non-empty string")
        v = self.velocity_ecef_m_per_yr
        if len(v) != 3 or not all(math.isfinite(c) for c in v):
            raise FrameError(
                "velocity_ecef_m_per_yr must be three finite components")

    def displacement(self, from_epoch: float, to_epoch: float) -> np.ndarray:
        """Modelled drift vector (metres) from ``from_epoch`` to ``to_epoch``."""
        if not (math.isfinite(from_epoch) and math.isfinite(to_epoch)):
            raise FrameError("epochs must be finite decimal years")
        dt = to_epoch - from_epoch
        return np.array(self.velocity_ecef_m_per_yr, dtype=float) * dt


@dataclass(frozen=True)
class EpochStampedPoint:
    """An ECEF position that carries its frame and epoch (invariant 9).

    A position without an epoch is not representable here: epoch is required.
    """

    x_m: float
    y_m: float
    z_m: float
    frame_id: str
    epoch: float

    def __post_init__(self) -> None:
        for name, value in (
            ("x_m", self.x_m), ("y_m", self.y_m), ("z_m", self.z_m),
            ("epoch", self.epoch),
        ):
            if not math.isfinite(value):
                raise FrameError(f"{name} must be finite, got {value!r}")
        # Validates the realization exists.
        get_realization(self.frame_id)

    def as_array(self) -> np.ndarray:
        return np.array([self.x_m, self.y_m, self.z_m], dtype=float)


def propagate(
    point: EpochStampedPoint, model: PlateMotionModel, to_epoch: float,
) -> EpochStampedPoint:
    """Propagate ``point`` to ``to_epoch`` under the plate-motion model.

    The result is a new stamped point at ``to_epoch``; its position differs
    from the input by exactly the modelled drift. Reversible: propagating
    back to the original epoch recovers the original position.
    """
    disp = model.displacement(point.epoch, to_epoch)
    return EpochStampedPoint(
        point.x_m + float(disp[0]),
        point.y_m + float(disp[1]),
        point.z_m + float(disp[2]),
        frame_id=point.frame_id,
        epoch=to_epoch,
    )


@dataclass(frozen=True)
class FrameEpochCertificate:
    """A certificate conforming to ``frame_epoch.schema.json``.

    ``epoch`` is stored as a string (decimal year) per the schema. The
    ``hash`` is a deterministic digest over the identifying fields.
    """

    body_id: str
    frame_id: str
    epoch: str
    time_scale: str
    orientation_profile_id: str
    ephemeris_id: str | None = None
    hash: str = field(default="", compare=False)

    def to_dict(self) -> dict:
        d = {
            "body_id": self.body_id,
            "frame_id": self.frame_id,
            "epoch": self.epoch,
            "time_scale": self.time_scale,
            "orientation_profile_id": self.orientation_profile_id,
            "ephemeris_id": self.ephemeris_id,
            "hash": self.hash,
        }
        return d


def _certificate_hash(payload: dict) -> str:
    material = {k: payload[k] for k in (
        "body_id", "frame_id", "epoch", "time_scale",
        "orientation_profile_id", "ephemeris_id")}
    blob = json.dumps(material, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()


def make_certificate(
    frame_id: str,
    epoch: float,
    orientation_profile_id: str,
    ephemeris_id: str | None = None,
    body_id: str = BODY_ID,
) -> FrameEpochCertificate:
    """Build a hashed :class:`FrameEpochCertificate` for a frame at an epoch."""
    get_realization(frame_id)
    if not math.isfinite(epoch):
        raise FrameError("epoch must be a finite decimal year")
    if not orientation_profile_id:
        raise FrameError("orientation_profile_id is required")
    payload = {
        "body_id": body_id,
        "frame_id": frame_id,
        "epoch": repr(float(epoch)),
        "time_scale": TIME_SCALE,
        "orientation_profile_id": orientation_profile_id,
        "ephemeris_id": ephemeris_id,
    }
    digest = _certificate_hash(payload)
    return FrameEpochCertificate(
        body_id=payload["body_id"],
        frame_id=payload["frame_id"],
        epoch=payload["epoch"],
        time_scale=payload["time_scale"],
        orientation_profile_id=payload["orientation_profile_id"],
        ephemeris_id=payload["ephemeris_id"],
        hash=digest,
    )


def frames_report() -> dict:
    """What this module claims -- and what it refuses to claim."""
    return {
        "module": "cwatlas.frames",
        "phase_id": "P10",
        "body_id": BODY_ID,
        "time_scale": TIME_SCALE,
        "realizations": sorted(ITRF_REALIZATIONS),
        "claim_class": claims.ClaimClass.MATHEMATICAL_TRANSLATION.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "note": (
            "epoch is mandatory; a coordinate at t1 differs from the same "
            "coordinate at t2 by the modelled plate drift. The plate-motion "
            "model is a declared MODEL, not a measurement."),
        "verdict": "EPOCH_DEPENDENT_FRAME_NO_TIMELESS_COORDINATE",
    }
