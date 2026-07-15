"""Optical coordinates (Agent 06):
  RSCS-C.16 OpticalCarrier    - carrier wavelength + envelope bandwidth,
  RSCS-C.17 DirectionalPropagation - propagation-constant pair (beta, dbeta).

The carrier/envelope split keeps the fast optical oscillation (lambda_0,
omega_0 = 2*pi*c/lambda_0) separate from the slow envelope the RSCS modal
layer manipulates. The directional pair encodes beta_f = beta + dbeta,
beta_b = beta - dbeta (EP-06-01, TMOKE perturbation form) as MATH ONLY:
delta_beta != 0 is a model parameter, never an asserted quartz property
(reciprocity posture D6-003).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar

from ._base import RSCSCoordinate, require_finite

__all__ = ["OpticalCarrier", "DirectionalPropagation", "SPEED_OF_LIGHT_M_S"]

#: Vacuum speed of light (m/s), exact by SI definition.
SPEED_OF_LIGHT_M_S = 299_792_458.0


@dataclass(frozen=True)
class OpticalCarrier(RSCSCoordinate):
    """RSCS-C.16. Optical carrier: vacuum wavelength (nm) + envelope bandwidth.

    The envelope bandwidth (Hz, >= 0) bounds the slow modulation carried on
    the carrier; 0 means an unmodulated CW carrier."""

    registry_id: ClassVar[str] = "RSCS-C.16"
    wavelength_nm: float = 632.8
    envelope_bandwidth_hz: float = 0.0

    def __post_init__(self) -> None:
        wl = require_finite("wavelength_nm", self.wavelength_nm)
        if wl <= 0:
            raise ValueError("wavelength_nm must be > 0")
        bw = require_finite("envelope_bandwidth_hz", self.envelope_bandwidth_hz)
        if bw < 0:
            raise ValueError("envelope_bandwidth_hz must be >= 0")
        object.__setattr__(self, "wavelength_nm", wl)
        object.__setattr__(self, "envelope_bandwidth_hz", bw)

    @property
    def frequency_hz(self) -> float:
        """Carrier frequency f0 = c / lambda_0 (Hz)."""
        return SPEED_OF_LIGHT_M_S / (self.wavelength_nm * 1e-9)

    @property
    def omega0_rad_s(self) -> float:
        """Carrier angular frequency omega_0 = 2*pi*f0 (rad/s)."""
        from .. import units as U
        return U.hz_to_rad_s(self.frequency_hz)

    def components(self) -> dict[str, Any]:
        return {"wavelength_nm": self.wavelength_nm,
                "envelope_bandwidth_hz": self.envelope_bandwidth_hz,
                "frequency_hz": self.frequency_hz}


@dataclass(frozen=True)
class DirectionalPropagation(RSCSCoordinate):
    """RSCS-C.17. Directional propagation-constant pair (rad/mm).

    beta_f = beta + delta_beta (forward), beta_b = beta - delta_beta
    (backward); the nonreciprocal split is 2*delta_beta (EP-06-01).
    delta_beta = 0 is the reciprocal case, the D6-003 null expectation."""

    registry_id: ClassVar[str] = "RSCS-C.17"
    beta_rad_mm: float = 0.0
    delta_beta_rad_mm: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "beta_rad_mm",
                           require_finite("beta_rad_mm", self.beta_rad_mm))
        object.__setattr__(
            self, "delta_beta_rad_mm",
            require_finite("delta_beta_rad_mm", self.delta_beta_rad_mm))

    @property
    def forward_rad_mm(self) -> float:
        return self.beta_rad_mm + self.delta_beta_rad_mm

    @property
    def backward_rad_mm(self) -> float:
        return self.beta_rad_mm - self.delta_beta_rad_mm

    @property
    def nonreciprocal_split_rad_mm(self) -> float:
        """The 2*delta_beta forward/backward split (0 = reciprocal)."""
        return self.forward_rad_mm - self.backward_rad_mm

    @property
    def is_reciprocal(self) -> bool:
        return self.delta_beta_rad_mm == 0.0

    def components(self) -> dict[str, Any]:
        return {"beta_rad_mm": self.beta_rad_mm,
                "delta_beta_rad_mm": self.delta_beta_rad_mm,
                "forward_rad_mm": self.forward_rad_mm,
                "backward_rad_mm": self.backward_rad_mm}
