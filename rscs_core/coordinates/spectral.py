"""Spectral coordinates: RSCS-C.2 time, C.3 phase, C.4 angular frequency,
C.5 wavevector.

These are the base-space continuous coordinates. Phase lives on S^1 and is
stored wrapped to [0, 2*pi); angular frequency is the 2*pi*f image of a v2 Hz
frequency; the wavevector is the oriented-frame element {k_i} adapted from the
source plane-wave bases (EP-07-01) and the phase-matching wavevectors
(EP-02-01), unit rad/mm.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar

import numpy as np

from .. import units as U
from ._base import RSCSCoordinate, require_finite

__all__ = ["TimeCoordinate", "PhaseCoordinate", "AngularFrequency",
           "Wavevector"]


@dataclass(frozen=True)
class TimeCoordinate(RSCSCoordinate):
    """RSCS-C.2. A time value in seconds (real line)."""

    registry_id: ClassVar[str] = "RSCS-C.2"
    t_s: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "t_s", require_finite("t_s", self.t_s))

    def components(self) -> dict[str, Any]:
        return {"t_s": self.t_s}


@dataclass(frozen=True)
class PhaseCoordinate(RSCSCoordinate):
    """RSCS-C.3. A phase on S^1, stored wrapped to [0, 2*pi) rad.

    Generalizes the v2 compact phase ``chi`` and phase residue ``r_phi``;
    those keep their v2 definitions and are specific instances of this."""

    registry_id: ClassVar[str] = "RSCS-C.3"
    phi_rad: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "phi_rad",
                           U.wrap_phase(require_finite("phi_rad", self.phi_rad)))

    def components(self) -> dict[str, Any]:
        return {"phi_rad": self.phi_rad}


@dataclass(frozen=True)
class AngularFrequency(RSCSCoordinate):
    """RSCS-C.4. Angular frequency omega (rad/s); omega = 2*pi*f, f in Hz."""

    registry_id: ClassVar[str] = "RSCS-C.4"
    omega_rad_s: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "omega_rad_s",
                           require_finite("omega_rad_s", self.omega_rad_s))

    @classmethod
    def from_hz(cls, f_hz: float) -> "AngularFrequency":
        return cls(U.hz_to_rad_s(f_hz))

    @property
    def f_hz(self) -> float:
        return U.rad_s_to_hz(self.omega_rad_s)

    def components(self) -> dict[str, Any]:
        return {"omega_rad_s": self.omega_rad_s, "f_hz": self.f_hz}


@dataclass(frozen=True)
class Wavevector(RSCSCoordinate):
    """RSCS-C.5. A wavevector / oriented-frame element k (rad/mm) in R^3."""

    registry_id: ClassVar[str] = "RSCS-C.5"
    k_rad_mm: tuple[float, float, float] = (0.0, 0.0, 0.0)

    def __post_init__(self) -> None:
        object.__setattr__(self, "k_rad_mm",
                           self._seq("k_rad_mm", self.k_rad_mm, 3))

    @property
    def vector(self) -> np.ndarray:
        return np.asarray(self.k_rad_mm, dtype=float)

    @property
    def magnitude_rad_mm(self) -> float:
        return float(np.linalg.norm(self.vector))

    def components(self) -> dict[str, Any]:
        return {"k_rad_mm": self.vector, "magnitude_rad_mm":
                self.magnitude_rad_mm}
