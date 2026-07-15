"""Canonical units, tolerances, and unit-safe helpers for RSCS 1.0.

RSCS reuses the RGCS v2 unit conventions verbatim (docs/NOTATION_AND_UNITS.md,
FROZEN) and adds NOTHING incompatible: frequency in Hz, angular frequency in
rad/s, phase in rad, geometry lengths in mm, wave-formula lengths in m, time
in s. Code identifiers keep the unit suffix (`_hz`, `_rad_s`, `_mm`, `_s`).

This module is deliberately tiny and dependency-light: it holds the shared
numeric constants and the conversions that must be identical across every
RSCS coordinate and operator so that the Conservative Extension Property
(docs/RSCS_MATHEMATICAL_MODEL.md) compares like against like.
"""

from __future__ import annotations

import math

__all__ = [
    "TWO_PI", "CONSERVATIVE_EXTENSION_RTOL", "CONSERVATIVE_EXTENSION_ATOL",
    "hz_to_rad_s", "rad_s_to_hz", "wrap_phase", "is_finite_number",
]

#: 2*pi, the single source of the Hz<->rad/s and phase-winding factor.
TWO_PI = 2.0 * math.pi

#: Default tolerances for the RSCS Conservative Extension Property
#: (O_RSCS(iota(x)) == iota(O_RGCS(x))). Relative 1e-9 / absolute 1e-12 is
#: tight enough to catch any structural error while absorbing the last-ulp
#: float drift documented for the frozen baseline (NR3-001). New v3 numeric
#: tests use tolerance-aware checks (migration rule MIG-TEST-02); the frozen
#: v2 byte-equality tests are retained separately and untouched.
CONSERVATIVE_EXTENSION_RTOL = 1.0e-9
CONSERVATIVE_EXTENSION_ATOL = 1.0e-12


def is_finite_number(value: float) -> bool:
    """True iff ``value`` is a finite real number (rejects NaN/inf)."""
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def hz_to_rad_s(f_hz: float) -> float:
    """Angular frequency omega = 2*pi*f (rad/s) from f in Hz (RSCS-C.4)."""
    if not is_finite_number(f_hz):
        raise ValueError(f"f_hz must be a finite number; got {f_hz!r}")
    return TWO_PI * float(f_hz)


def rad_s_to_hz(omega_rad_s: float) -> float:
    """f = omega/(2*pi) (Hz) from angular frequency in rad/s (RSCS-C.4)."""
    if not is_finite_number(omega_rad_s):
        raise ValueError(f"omega must be a finite number; got {omega_rad_s!r}")
    return float(omega_rad_s) / TWO_PI


def wrap_phase(phi_rad: float) -> float:
    """Wrap a phase to the canonical S^1 chart [0, 2*pi) (RSCS-C.3)."""
    if not is_finite_number(phi_rad):
        raise ValueError(f"phi_rad must be a finite number; got {phi_rad!r}")
    return float(phi_rad) % TWO_PI
