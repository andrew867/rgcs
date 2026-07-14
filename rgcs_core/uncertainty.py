"""Uncertain scalar values for RGCS v2 (RGCS-M.10/M.11/M.15).

Units: carried by the caller; an UncertainValue stores a mean in the
caller's canonical unit plus a RELATIVE standard uncertainty (1-sigma).
Every ladder/compact frequency or length output of rgcs_core is an
UncertainValue, never a bare float (binding handoff requirement, D-05).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

__all__ = ["UncertainValue", "DEFAULT_WAVE_SPEED_M_S", "DEFAULT_WAVE_SPEED_U_REL",
           "default_wave_speed"]

#: Central longitudinal wave speed (m/s). Source claim (RG-01, uncited corpus
#: import, consistent with alpha-quartz Z-axis longitudinal speed; D-19a).
DEFAULT_WAVE_SPEED_M_S = 6310.0
#: Default relative standard uncertainty of the wave speed (RGCS-M.10):
#: covers the X-Z longitudinal spread of alpha-quartz until a specimen's
#: crystallographic orientation is measured.
DEFAULT_WAVE_SPEED_U_REL = 0.05


@dataclass(frozen=True)
class UncertainValue:
    """A scalar with a relative standard uncertainty (RGCS-M.10).

    mean:  central value in the caller's canonical unit.
    u_rel: relative standard uncertainty (1-sigma), >= 0.
    """

    mean: float
    u_rel: float = 0.0

    def __post_init__(self) -> None:
        if not math.isfinite(self.mean):
            raise ValueError(f"mean must be finite; got {self.mean!r}")
        if not (math.isfinite(self.u_rel) and 0.0 <= self.u_rel < 1.0):
            raise ValueError(f"u_rel must be in [0, 1); got {self.u_rel!r}")

    @property
    def sigma(self) -> float:
        """Absolute standard uncertainty |mean| * u_rel."""
        return abs(self.mean) * self.u_rel

    def interval(self, k: float = 1.0) -> tuple[float, float]:
        """k-sigma interval (lo, hi). Default k = 1."""
        return (self.mean - k * self.sigma, self.mean + k * self.sigma)

    def scale(self, factor: float) -> "UncertainValue":
        """Multiply by an exact factor: relative uncertainty is unchanged
        (RGCS-M.11: f proportional to v_L keeps u_rel)."""
        if not math.isfinite(factor):
            raise ValueError("factor must be finite")
        return UncertainValue(self.mean * factor, self.u_rel)

    def reciprocal_scale(self, numerator: float) -> "UncertainValue":
        """numerator / value: first-order relative uncertainty unchanged."""
        if self.mean == 0.0:
            raise ZeroDivisionError("cannot take reciprocal of zero mean")
        return UncertainValue(numerator / self.mean, self.u_rel)

    def to_dict(self) -> dict[str, Any]:
        lo, hi = self.interval()
        return {"mean": self.mean, "u_rel": self.u_rel, "sigma": self.sigma,
                "lo_1sigma": lo, "hi_1sigma": hi}


def default_wave_speed() -> UncertainValue:
    """v_L as a first-class uncertain parameter (RGCS-M.10; closes D-05)."""
    return UncertainValue(DEFAULT_WAVE_SPEED_M_S, DEFAULT_WAVE_SPEED_U_REL)
