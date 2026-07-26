"""R10.8.5A §3 — gravity vertical and inward field-line integration.

The vertical is ``GRAVITY_VERTICAL`` first:

    v_g(x, t) = -grad U(x, t) / |grad U(x, t)|

with ``U`` the potential-energy convention (equivalently ``+grad W`` in
the geodetic gravity-potential convention used internally, ``W = V +
centrifugal``; the sign mapping is stated here once so no caller has to
guess). Distance inward is measured **along the gravity-field line**
through the shell system — not necessarily a straight radial line
toward the geometric centre, and the production path never assumes it
is.

The potential model is the conventional normal-field truncation:

    W(x, t) = GM/r * (1 - J2(t) * (a/r)^2 * P2(sin phi)) + w^2 rho^2 / 2

with a declared linear secular ``J2`` rate (real, cited, tiny). This is
SOURCE_ESTABLISHED_PHYSICS carried as a model, not a repository
measurement; no gravimeter is read anywhere in this package.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from cwatlas.claims import ClaimError

# Conventional constants (SOURCE_ESTABLISHED_PHYSICS).
GM_M3_S2 = 3.986004418e14          # Earth GM
A_EQ_M = 6378137.0                 # equatorial radius (scale for J2 term)
OMEGA_RAD_S = 7.2921159e-5         # mean rotation rate
J2_T0 = 1.08262668e-3              # J2 at the reference epoch
J2_RATE_PER_YEAR = -2.6e-11        # cited secular J2 trend (~ -2.6e-11/yr)
T0_YEAR = 2025.0

#: The declared vertical convention. Production code checks this string.
GRAVITY_VERTICAL = "GRAVITY_VERTICAL"


def j2(epoch_year: float) -> float:
    """Epoch-dependent J2 under the declared linear secular rate."""
    return J2_T0 + J2_RATE_PER_YEAR * (float(epoch_year) - T0_YEAR)


def potential_w(x: np.ndarray, epoch_year: float) -> float:
    """Geodetic gravity potential W (positive; g = +grad W points down)."""
    x = np.asarray(x, dtype=float)
    r = float(np.linalg.norm(x))
    if r < 1e3:
        raise ClaimError("potential requested unreasonably near the "
                         "geometric centre; the outer-in decoder never "
                         "goes there.")
    sin_phi = x[2] / r
    p2 = 0.5 * (3.0 * sin_phi * sin_phi - 1.0)
    v = GM_M3_S2 / r * (1.0 - j2(epoch_year) * (A_EQ_M / r) ** 2 * p2)
    rho2 = float(x[0] * x[0] + x[1] * x[1])
    return v + 0.5 * OMEGA_RAD_S ** 2 * rho2


def gravity_vector(x: np.ndarray, epoch_year: float,
                   step_m: float = 1.0) -> np.ndarray:
    """g = grad W by central differences (points downward / inward)."""
    x = np.asarray(x, dtype=float)
    g = np.zeros(3)
    for i in range(3):
        e = np.zeros(3)
        e[i] = step_m
        g[i] = (potential_w(x + e, epoch_year)
                - potential_w(x - e, epoch_year)) / (2.0 * step_m)
    return g


def gravity_down(x: np.ndarray, epoch_year: float) -> np.ndarray:
    """Unit gravity vertical, pointing down (equals -grad U / |grad U|)."""
    g = gravity_vector(x, epoch_year)
    n = float(np.linalg.norm(g))
    if n == 0.0:
        raise ClaimError("zero gravity gradient; no vertical exists here")
    return g / n


def deflection_from_radial_rad(x: np.ndarray, epoch_year: float) -> float:
    """Angle between gravity-down and the geocentric inward radial."""
    x = np.asarray(x, dtype=float)
    inward = -x / np.linalg.norm(x)
    d = gravity_down(x, epoch_year)
    c = float(np.clip(np.dot(inward, d), -1.0, 1.0))
    return math.acos(c)


@dataclass(frozen=True)
class FieldLineResult:
    """One inward field-line integration, receipted."""

    epoch_year: float
    start_m: tuple[float, float, float]
    end_m: tuple[float, float, float]
    path_distance_m: float
    straight_radial_end_m: tuple[float, float, float]
    lateral_deviation_m: float
    steps: int


def integrate_inward(start_m: np.ndarray, epoch_year: float,
                     distance_m: float,
                     step_m: float = 1000.0) -> FieldLineResult:
    """Follow the gravity-field line inward for ``distance_m`` of arc.

    RK4 on ``dx/ds = gravity_down(x)``. The comparison endpoint of a
    straight geocentric radial of the same length is computed alongside
    so the deviation the gravity model predicts is visible in every
    receipt — never asserted, always recomputed.
    """
    if distance_m < 0:
        raise ClaimError("inward distance must be non-negative")
    x = np.asarray(start_m, dtype=float).copy()
    start = x.copy()
    remaining = float(distance_m)
    steps = 0
    while remaining > 1e-9:
        h = min(step_m, remaining)
        k1 = gravity_down(x, epoch_year)
        k2 = gravity_down(x + 0.5 * h * k1, epoch_year)
        k3 = gravity_down(x + 0.5 * h * k2, epoch_year)
        k4 = gravity_down(x + h * k3, epoch_year)
        x = x + (h / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
        remaining -= h
        steps += 1
    radial_end = start - distance_m * start / np.linalg.norm(start)
    return FieldLineResult(
        epoch_year=float(epoch_year),
        start_m=tuple(map(float, start)),
        end_m=tuple(map(float, x)),
        path_distance_m=float(distance_m),
        straight_radial_end_m=tuple(map(float, radial_end)),
        lateral_deviation_m=float(np.linalg.norm(x - radial_end)),
        steps=steps)


def refuse_ellipsoid_normal_vertical(*_a, **_k) -> None:
    """The vertical is the gravity vertical, not the ellipsoid normal."""
    raise ClaimError(
        "refused: the projection vertical is GRAVITY_VERTICAL "
        "(-grad U / |grad U|), not the ellipsoid normal. The two differ "
        "by the deflection of the vertical; substituting the normal "
        "silently would hide exactly the deviation this layer exists to "
        "carry.")
