"""R10.8.5A §4 — magnetic shell geometry: a bounded corrective family.

Magnetics enter the **geometry**, not merely an orientation overlay:
epoch-dependent shell boundaries are level sets of a declared
functional of the gravity and magnetic scalars,

    Sigma_s(t) = { x : W(x, t) + kappa * M(x, t) = C_s(t) }

with ``M`` one member of a bounded, named scalar family and ``kappa`` a
declared coupling. Every family member's result is retained
separately; nothing selects "the best scalar" after seeing the training
anchor, and there are **no free per-vector offsets** — the correction
is a function of position, epoch and declared model only.

**What the magnetic model is.** No real IGRF-14 Gauss coefficient set
ships in this repository (:mod:`r12.igrf14root` is
``BLOCKED_MISSING_DATA`` by design, and that block is honoured, not
worked around). The scalars here therefore come from a declared
**tilted centred dipole** with linear epoch drift of moment and tilt —
conventional first-order geomagnetism (SOURCE_ESTABLISHED_PHYSICS as a
model class; the specific numbers are declared approximations with
stated uncertainty). The crust-corrected and combined core+lithosphere
members of the family are declared and **BLOCKED** rather than faked.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from cwatlas.claims import ClaimError
from cwatlas.r1085a.gravity_field_line import potential_w

# Declared tilted-dipole parameters with linear epoch drift.
# Approximate IGRF-era public values; uncertainty declared below.
T0_YEAR = 2025.0
DIPOLE_MOMENT_AM2_T0 = 7.71e22          # ~2025 dipole moment
DIPOLE_MOMENT_RATE_AM2_YR = -2.7e19     # secular decay (~0.035 %/yr)
DIPOLE_TILT_DEG_T0 = 9.7                # tilt from rotation axis, ~2025
DIPOLE_TILT_RATE_DEG_YR = -0.05         # declared linear tilt drift
DIPOLE_LON_DEG_T0 = -72.7               # boreal dipole-axis longitude
DIPOLE_LON_RATE_DEG_YR = 0.0
MU0_OVER_4PI = 1.0e-7                   # T m / A

#: Fractional uncertainty declared for every dipole-derived scalar: a
#: centred dipole omits all non-dipole structure (~10-20 % of |B| at the
#: surface, larger locally over anomalies).
DIPOLE_MODEL_FRACTIONAL_UNCERTAINTY = 0.2


def dipole_axis(epoch_year: float) -> np.ndarray:
    """Unit vector of the boreal dipole axis at the epoch (body frame)."""
    dt = float(epoch_year) - T0_YEAR
    tilt = math.radians(DIPOLE_TILT_DEG_T0 + DIPOLE_TILT_RATE_DEG_YR * dt)
    lon = math.radians(DIPOLE_LON_DEG_T0 + DIPOLE_LON_RATE_DEG_YR * dt)
    return np.array([math.sin(tilt) * math.cos(lon),
                     math.sin(tilt) * math.sin(lon),
                     math.cos(tilt)])


def dipole_moment(epoch_year: float) -> float:
    dt = float(epoch_year) - T0_YEAR
    m = DIPOLE_MOMENT_AM2_T0 + DIPOLE_MOMENT_RATE_AM2_YR * dt
    if m <= 0:
        raise ClaimError("dipole moment non-positive; the linear drift "
                         "model is outside its validity window")
    return m


def b_field_t(x: np.ndarray, epoch_year: float) -> np.ndarray:
    """Dipole B(x) in tesla: mu0/4pi * (3(m.r)r - m) / r^3 (m at centre)."""
    x = np.asarray(x, dtype=float)
    r = float(np.linalg.norm(x))
    if r < 1e3:
        raise ClaimError("field requested unreasonably near the centre")
    m_vec = dipole_moment(epoch_year) * dipole_axis(epoch_year)
    rhat = x / r
    return MU0_OVER_4PI * (3.0 * np.dot(m_vec, rhat) * rhat - m_vec) / r ** 3


def b_magnitude_t(x: np.ndarray, epoch_year: float) -> float:
    return float(np.linalg.norm(b_field_t(x, epoch_year)))


def scalar_potential_tm(x: np.ndarray, epoch_year: float) -> float:
    """Dipole magnetic scalar potential (valid outside sources)."""
    x = np.asarray(x, dtype=float)
    r = float(np.linalg.norm(x))
    m_vec = dipole_moment(epoch_year) * dipole_axis(epoch_year)
    return MU0_OVER_4PI * float(np.dot(m_vec, x)) / r ** 3


def inclination_rad(x: np.ndarray, epoch_year: float) -> float:
    """Magnetic inclination (dip) of the dipole field at x."""
    x = np.asarray(x, dtype=float)
    b = b_field_t(x, epoch_year)
    rhat = x / np.linalg.norm(x)
    b_down = -float(np.dot(b, rhat))
    b_h = float(np.linalg.norm(b - np.dot(b, rhat) * rhat))
    return math.atan2(b_down, b_h)


@dataclass(frozen=True)
class MagneticShellCorrection:
    """One declared member of the bounded corrective family.

    ``kappa`` couples the scalar into the boundary functional in
    potential units (m^2/s^2 per scalar unit). ``status`` is ``ACTIVE``
    or ``BLOCKED_MISSING_DATA``; a BLOCKED member refuses evaluation
    instead of inventing coefficients.
    """

    member_id: str
    scalar: str          # B_MAGNITUDE | SCALAR_POTENTIAL | INCLINATION | ...
    kappa: float
    status: str
    fractional_uncertainty: float
    note: str = ""

    def m_scalar(self, x: np.ndarray, epoch_year: float) -> float:
        if self.status != "ACTIVE":
            raise ClaimError(
                f"magnetic family member {self.member_id} is "
                f"{self.status}: no real coefficient set ships in this "
                f"repository and none is fabricated (r12.igrf14root "
                f"block honoured).")
        if self.scalar == "NONE":
            return 0.0
        if self.scalar == "B_MAGNITUDE":
            return b_magnitude_t(x, epoch_year)
        if self.scalar == "SCALAR_POTENTIAL":
            return scalar_potential_tm(x, epoch_year)
        if self.scalar == "INCLINATION":
            return inclination_rad(x, epoch_year)
        raise ClaimError(f"unknown scalar {self.scalar!r}")

    def functional(self, x: np.ndarray, epoch_year: float) -> float:
        """F(U, M) = W(x,t) + kappa * M(x,t) — the boundary functional."""
        base = potential_w(x, epoch_year)
        if self.kappa == 0.0:
            return base
        return base + self.kappa * self.m_scalar(x, epoch_year)


#: The bounded family. kappa values are declared engineering couplings
#: sized so the magnetic term deforms a boundary by O(km), stated up
#: front; kappa is NEVER fitted to a source vector.
FAMILY: tuple[MagneticShellCorrection, ...] = (
    MagneticShellCorrection(
        "GRAVITY_ONLY", "NONE", 0.0, "ACTIVE", 0.0,
        "null member: pure gravity level surfaces (kappa = 0)."),
    MagneticShellCorrection(
        "DIPOLE_B_MAGNITUDE", "B_MAGNITUDE", 2.0e8, "ACTIVE",
        DIPOLE_MODEL_FRACTIONAL_UNCERTAINTY,
        "kappa*|B| ~ 1e4 m^2/s^2 at the surface (~1 km of geopotential)."),
    MagneticShellCorrection(
        "DIPOLE_SCALAR_POTENTIAL", "SCALAR_POTENTIAL", 2.0e-3, "ACTIVE",
        DIPOLE_MODEL_FRACTIONAL_UNCERTAINTY,
        "signed hemispheric deformation via the dipole scalar potential."),
    MagneticShellCorrection(
        "DIPOLE_INCLINATION", "INCLINATION", 6.0e3, "ACTIVE",
        DIPOLE_MODEL_FRACTIONAL_UNCERTAINTY,
        "dip-angle-derived correction, kappa*I ~ 1e4 m^2/s^2 at the pole."),
    MagneticShellCorrection(
        "CRUST_CORRECTED", "B_MAGNITUDE", 2.0e8, "BLOCKED_MISSING_DATA",
        float("nan"),
        "requires a lithospheric anomaly model; none ships, none is "
        "fabricated."),
    MagneticShellCorrection(
        "CORE_PLUS_LITHOSPHERE", "B_MAGNITUDE", 2.0e8,
        "BLOCKED_MISSING_DATA", float("nan"),
        "requires real IGRF-14 Gauss coefficients plus a crustal model; "
        "r12.igrf14root records the coefficient block and it is honoured."),
)

_BY_ID = {m.member_id: m for m in FAMILY}


def member(member_id: str) -> MagneticShellCorrection:
    try:
        return _BY_ID[member_id]
    except KeyError:
        raise ClaimError(
            f"unknown magnetic family member {member_id!r}; declared: "
            f"{sorted(_BY_ID)}") from None


def active_members() -> tuple[MagneticShellCorrection, ...]:
    return tuple(m for m in FAMILY if m.status == "ACTIVE")


def boundary_radius_m(direction: np.ndarray, epoch_year: float,
                      nominal_radius_m: float,
                      correction: MagneticShellCorrection,
                      window_m: float = 50_000.0) -> float:
    """Radius along ``direction`` where the member's level surface sits.

    The level constant ``C_s(t)`` is set by the nominal radius on the
    dipole axis (the declared reference azimuth), then the boundary
    radius along the requested direction is solved by bisection of
    ``F(r * u) = C_s``. Deformation is the difference from nominal.
    """
    u = np.asarray(direction, dtype=float)
    u = u / np.linalg.norm(u)
    ref = dipole_axis(epoch_year) * nominal_radius_m
    c_s = correction.functional(ref, epoch_year)

    def f(r: float) -> float:
        return correction.functional(r * u, epoch_year) - c_s

    lo, hi = nominal_radius_m - window_m, nominal_radius_m + window_m
    flo, fhi = f(lo), f(hi)
    if flo * fhi > 0:
        raise ClaimError(
            f"{correction.member_id}: level surface not bracketed within "
            f"±{window_m/1000:.0f} km of nominal — the declared kappa is "
            f"outside its stated O(km) deformation regime; refuse rather "
            f"than widen silently.")
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        fm = f(mid)
        if flo * fm <= 0:
            hi, fhi = mid, fm
        else:
            lo, flo = mid, fm
    return 0.5 * (lo + hi)


def refuse_post_reveal_scalar_selection(*_a, **_k) -> None:
    """Refuse choosing the family member by training-anchor fit."""
    raise ClaimError(
        "refused: the magnetic scalar family is run in full and every "
        "member's result retained. Selecting the best-fitting scalar "
        "after seeing the training anchor is post-reveal tuning and is "
        "banned by the R10.8.5A lock.")
