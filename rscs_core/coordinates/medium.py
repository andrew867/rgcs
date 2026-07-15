"""Medium/preparation coordinates: RSCS-C.9 polarization/spin,
C.10 selection coordinate, C.11 group-delay coordinate.

All three are ADAPTED math from the reference optics/atomic papers; the
physical conclusions of those papers do NOT transfer (EXCLUSION_MATRIX):
- C.9 circular polarization / spin preparation (Wang, EP-04-02, concept 2);
- C.10 velocity/detuning selection class v = Delta_p/k (Zhang, EP-05-01,
  concept 11) -- generalized to any labelled selection coordinate;
- C.11 per-mode group delay tau_g (Cheng, EP-02-03, concept 6).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar

import numpy as np

from ._base import RSCSCoordinate, require_finite, require_finite_array

__all__ = ["PolarizationState", "SelectionCoordinate", "GroupDelay"]


@dataclass(frozen=True)
class PolarizationState(RSCSCoordinate):
    """RSCS-C.9. Polarization/spin state on the Poincare sphere S^2.

    Stored as a normalized Stokes 3-vector (s1, s2, s3), |s| = 1 for a pure
    state. s3 = +1/-1 are the circular sigma+/sigma- preparations."""

    registry_id: ClassVar[str] = "RSCS-C.9"
    stokes: tuple[float, float, float] = (0.0, 0.0, 1.0)

    def __post_init__(self) -> None:
        vec = require_finite_array("stokes", self.stokes, ndim=1, shape=(3,))
        norm = float(np.linalg.norm(vec))
        if norm == 0.0:
            raise ValueError("stokes vector must be non-zero")
        object.__setattr__(self, "stokes", tuple(float(v) for v in vec / norm))

    @classmethod
    def sigma_plus(cls) -> "PolarizationState":
        return cls((0.0, 0.0, 1.0))

    @classmethod
    def sigma_minus(cls) -> "PolarizationState":
        return cls((0.0, 0.0, -1.0))

    @property
    def helicity(self) -> float:
        """Circular component s3 in [-1, 1]."""
        return self.stokes[2]

    def components(self) -> dict[str, Any]:
        return {"stokes": list(self.stokes), "helicity": self.helicity}


@dataclass(frozen=True)
class SelectionCoordinate(RSCSCoordinate):
    """RSCS-C.10. A labelled selection coordinate over an internal-state
    population (generalizes the atomic velocity class v = Delta_p/k).

    ``value`` is the class label in ``unit``; ``population`` in [0, 1] is the
    occupancy of that class. Abstracted: the selector need not be a velocity."""

    registry_id: ClassVar[str] = "RSCS-C.10"
    value: float = 0.0
    population: float = 1.0
    unit: str = "arb"

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", require_finite("value", self.value))
        pop = require_finite("population", self.population)
        if not 0.0 <= pop <= 1.0:
            raise ValueError("population must be in [0, 1]")
        object.__setattr__(self, "population", pop)
        if not isinstance(self.unit, str) or not self.unit:
            raise ValueError("unit must be a non-empty string")

    def components(self) -> dict[str, Any]:
        return {"value": self.value, "population": self.population,
                "unit": self.unit}


@dataclass(frozen=True)
class GroupDelay(RSCSCoordinate):
    """RSCS-C.11. Per-mode group delay tau_g (s), one entry per mode."""

    registry_id: ClassVar[str] = "RSCS-C.11"
    tau_g_s: np.ndarray = ()  # type: ignore[assignment]

    def __post_init__(self) -> None:
        arr = require_finite_array("tau_g_s", self.tau_g_s, ndim=1)
        if arr.size < 1:
            raise ValueError("tau_g_s must be non-empty")
        object.__setattr__(self, "tau_g_s", arr)

    @property
    def imbalance_s(self) -> float:
        """Max minus min group delay: the quantity O.8 drives to zero."""
        return float(np.max(self.tau_g_s) - np.min(self.tau_g_s))

    def components(self) -> dict[str, Any]:
        return {"tau_g_s": self.tau_g_s, "imbalance_s": self.imbalance_s}
