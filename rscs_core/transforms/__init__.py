"""RSCS transform operators:
  RSCS-O.1 frame transform (SpatialCoordinate under an OrientationFrame),
  RSCS-O.2 time<->frequency map (analytic signal; wraps v2 RGCS-M.55),
  RSCS-O.3 space->phase map (HYP; NHT-seeded, EP-07-01).

O.1 and O.2 are EST and invertible; O.2 delegates to the frozen v2
``analytic_signal`` so the spectral map is byte-identical to RGCS-M.55.
O.3 is a HYPOTHESIS operator (space-to-phase encoding). It is implemented as
an explicit, well-defined map phi = k . x - omega t, but is CLASS = HYP and
carries the NHT/HAL exclusion: it is a candidate encoding, not a claim that
quartz performs it.
"""

from __future__ import annotations

import numpy as np

from rgcs_core.coherence.metrics import analytic_signal as _v2_analytic_signal

from .. import units as U
from ..coordinates import (SpatialCoordinate, OrientationFrame, PhaseCoordinate,
                           Wavevector)
from ..registry import rscs_classified

__all__ = ["frame_transform", "time_to_frequency", "space_to_phase"]


@rscs_classified("EST", registry=("RSCS-O.1",), provenance=("EP-08-01",),
                 units="mm -> mm",
                 exclusions=("no visual-perception import (SRC-3-08)",),
                 note="rigid frame transform x' = R x, R from OrientationFrame; "
                      "invertible (round-trip identity)")
def frame_transform(point: SpatialCoordinate,
                    frame: OrientationFrame) -> SpatialCoordinate:
    """Apply an orientation frame to a spatial coordinate: x' = R x (mm).
    The result is tagged with the frame name; inverse is frame.inverse()."""
    if not isinstance(point, SpatialCoordinate):
        raise TypeError("point must be a SpatialCoordinate (RSCS-C.1)")
    if not isinstance(frame, OrientationFrame):
        raise TypeError("frame must be an OrientationFrame (RSCS-C.8)")
    x_new = frame.rotation @ point.vector
    return SpatialCoordinate(tuple(float(v) for v in x_new), frame.name)


@rscs_classified("EST", registry=("RSCS-O.2",), provenance=(),
                 units="X(t) -> complex X(t) (analytic signal)",
                 note="time->analytic-signal map; delegates to the frozen v2 "
                      "RGCS-M.55 analytic_signal (byte-identical)")
def time_to_frequency(record: np.ndarray) -> np.ndarray:
    """Analytic signal z(t) of a real record via the FFT Hilbert transform.
    Thin RSCS wrapper over the frozen v2 implementation (RGCS-M.55) so the
    Conservative Extension Property holds exactly."""
    return _v2_analytic_signal(record)


@rscs_classified("HYP", registry=("RSCS-O.3",), provenance=("EP-07-01",),
                 units="(rad/mm, mm, rad/s, s) -> rad",
                 exclusions=("NHT/HAL: no consciousness/brain/memory import "
                             "(SRC-3-07)",),
                 note="space->phase encoding phi = k.x - omega t; CANDIDATE "
                      "only, requires observable + failure condition before "
                      "any physical use (notation ledger 1.5)")
def space_to_phase(position: SpatialCoordinate, k: Wavevector,
                   omega_rad_s: float, t_s: float) -> PhaseCoordinate:
    """Space-to-phase map phi = k . x - omega t (wrapped to [0, 2*pi)).

    HYPOTHESIS operator seeded from NHT (EP-07-01). Well-defined as
    mathematics; it makes NO physical claim. Do not route its output into
    EST/DER conclusions without an explicit HYP boundary."""
    if not isinstance(position, SpatialCoordinate):
        raise TypeError("position must be a SpatialCoordinate (RSCS-C.1)")
    if not isinstance(k, Wavevector):
        raise TypeError("k must be a Wavevector (RSCS-C.5)")
    if not (np.isfinite(omega_rad_s) and np.isfinite(t_s)):
        raise ValueError("omega_rad_s and t_s must be finite")
    phi = float(k.vector @ position.vector) - float(omega_rad_s) * float(t_s)
    return PhaseCoordinate(U.wrap_phase(phi))
