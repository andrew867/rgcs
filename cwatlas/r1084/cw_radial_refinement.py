"""Radial shell refinement — decimal Z instruction per level (§5).

Each Z digit selects one tenth of the current radial interval (nested,
half-open). The ROOT interval is a *declared* profile, not a derived fact:
the source lane never states the radial datum, so the finite candidate set
below is carried explicitly and every radial statement is conditional on it.
"""

from __future__ import annotations

from fractions import Fraction

from cwatlas.r1084.cw_hedron_state import RadialInterval, RadialShellState

F = Fraction
R_EARTH_KM = F(63710, 10)  # 6371.0 km, mean radius (shell index 3 datum)

#: Declared root radial profiles (finite ambiguity, §6 / §9 reporting).
ROOT_RADIAL_PROFILES = {
    "ROOT_R0_FULL_DIAMETER": RadialInterval(F(0), 2 * R_EARTH_KM),
    "ROOT_R1_BODY_INTERIOR": RadialInterval(F(0), R_EARTH_KM),
    "ROOT_R2_SURFACE_BAND_10PCT": RadialInterval(
        R_EARTH_KM * F(9, 10), R_EARTH_KM * F(11, 10)),
    "ROOT_R3_ALTITUDE_0_1000KM": RadialInterval(
        R_EARTH_KM, R_EARTH_KM + 1000),
}
PRIMARY_ROOT = "ROOT_R0_FULL_DIAMETER"


def root_state(profile: str = PRIMARY_ROOT) -> RadialShellState:
    return RadialShellState(interval=ROOT_RADIAL_PROFILES[profile],
                            root_profile=profile, depth=0)


def refine(state: RadialShellState, z: int, *,
           radial_scale: Fraction = F(1)) -> tuple[RadialShellState, dict]:
    """Apply one Z instruction: the z-th tenth of the current interval.

    ``radial_scale`` is the C2 compensation on the sub-interval origin
    displacement (1 = none); clipping preserves containment and is recorded.
    """
    if not 0 <= z <= 9:
        raise ValueError(f"Z digit out of range: {z}")
    iv = state.interval
    step = iv.thickness / 10
    lo = iv.r_min + F(z) * step * radial_scale
    clipped = False
    if lo + step > iv.r_max:
        lo, clipped = iv.r_max - step, True
    child = RadialShellState(
        interval=RadialInterval(lo, lo + step),
        root_profile=state.root_profile, depth=state.depth + 1)
    rec = {"z_digit": z, "clipped": clipped,
           "interval_km": (float(lo), float(lo + step))}
    return child, rec
