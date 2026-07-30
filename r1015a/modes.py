"""R10.15A — analytic mode families, crowding, and mode identity.

Before a 3D anisotropic FEM is worth running, it is worth knowing what
ELSE lives near 4096 Hz. A slender-body analytic screen answers that
cheaply, and its answer here is the important one: the target mode is
not alone.

Families screened (all DECLARED slender-body approximations):

  extensional/longitudinal   f_n = n v_L / (2L)
  shear/torsional            f_n = n v_T / (2L)
  flexural (free-free)       f_n = (beta_n L)^2 / (2 pi L^2)
                                   * sqrt(E/rho) * sqrt(I/A)

Every one of these is a ONE-DIMENSIONAL model applied to a tapered,
anisotropic, three-dimensional body. They screen; they do not decide.
Timoshenko shear and rotary-inertia corrections reduce the flexural
predictions, increasingly so for higher modes and thicker bodies, so
the flexural numbers here are UPPER bounds.
"""

from __future__ import annotations

import math

from r1015a import ScaleAError
from r1015a.design import ScaleAGeometry

#: Free-free Euler-Bernoulli eigenvalues (beta_n * L).
BETA_L_FREE_FREE = (4.730040745, 7.853204624, 10.995607838,
                    14.137165491, 17.278759657)

#: Scalar proxies. Quartz is anisotropic; these stand in until the
#: tensor solve runs.
V_LONGITUDINAL_M_S = 5700.0
V_SHEAR_M_S = 3800.0
YOUNGS_PA = 78.0e9
DENSITY_KG_M3 = 2650.0


def section_radius_of_gyration_mm(geo: ScaleAGeometry) -> float:
    """sqrt(I/A) for a regular n-gon at the average diameter.

    For a regular polygon with circumradius R the second moment about
    a centroidal axis and the area give I/A independent of the axis
    direction (a regular polygon's inertia tensor is isotropic in
    plane), which is why a single radius of gyration is meaningful.
    """
    n = geo.facets
    R = geo.avg_diameter_mm / 2.0
    if geo.diameter_mode == "across_flats":
        R = R / math.cos(math.pi / n)
    # A = (n/2) R^2 sin(2pi/n)
    A = 0.5 * n * R ** 2 * math.sin(2 * math.pi / n)
    # I = (n/24) R^4 (sin(2pi/n))(1 + 2 cos^2(pi/n))  [standard n-gon]
    I = (n / 24.0) * R ** 4 * math.sin(2 * math.pi / n) * \
        (1.0 + 2.0 * math.cos(math.pi / n) ** 2)
    return math.sqrt(I / A)


def mode_families(geo: ScaleAGeometry, n_modes: int = 5) -> list:
    """Analytic mode screen across the three slender-body families."""
    L = geo.length_mm / 1000.0
    modes = []
    for n in range(1, n_modes + 1):
        modes.append({"family": "extensional", "index": n,
                      "frequency_hz": n * V_LONGITUDINAL_M_S / (2 * L),
                      "model": "f = n v_L / (2 L)"})
        modes.append({"family": "shear_torsional", "index": n,
                      "frequency_hz": n * V_SHEAR_M_S / (2 * L),
                      "model": "f = n v_T / (2 L)"})
    k = section_radius_of_gyration_mm(geo) / 1000.0
    c_bar = math.sqrt(YOUNGS_PA / DENSITY_KG_M3)
    for n, bl in enumerate(BETA_L_FREE_FREE[:n_modes], start=1):
        f = (bl ** 2) / (2 * math.pi * L ** 2) * c_bar * k
        modes.append({"family": "flexural_free_free", "index": n,
                      "frequency_hz": f,
                      "model": "Euler-Bernoulli free-free; UPPER bound "
                               "(Timoshenko corrections reduce it)"})
    modes.sort(key=lambda d: d["frequency_hz"])
    return modes


def crowding_report(geo: ScaleAGeometry, target_hz: float = 4096.0,
                    window_fraction: float = 0.25,
                    n_modes: int = 5) -> dict:
    """Which modes sit near the target, and can it be identified?"""
    if window_fraction <= 0:
        raise ScaleAError("window_fraction must be positive")
    modes = mode_families(geo, n_modes)
    lo, hi = target_hz * (1 - window_fraction), \
        target_hz * (1 + window_fraction)
    near = [m for m in modes if lo <= m["frequency_hz"] <= hi]
    for m in near:
        m["separation_hz"] = m["frequency_hz"] - target_hz
        m["separation_fraction"] = m["separation_hz"] / target_hz
    target = min(modes, key=lambda m: abs(m["frequency_hz"] - target_hz))
    others = [m for m in near if m is not target]
    nearest_other = (min(others,
                         key=lambda m: abs(m["separation_hz"]))
                     if others else None)
    # identifiability: a mode is separable if its neighbours are
    # further away than the resonance half-linewidth for a plausible Q
    verdicts = {}
    for q in (100, 1000, 10000):
        half_lw = target_hz / (2 * q)
        verdicts[str(q)] = bool(
            nearest_other is None
            or abs(nearest_other["separation_hz"]) > half_lw)
    return {
        "schema": "rgcs.r1015a.mode-crowding.v1",
        "target_hz": target_hz,
        "window": [lo, hi],
        "target_mode": target,
        "modes_in_window": near,
        "modes_in_window_count": len(near),
        "nearest_other_mode": nearest_other,
        "separable_at_q": verdicts,
        "mode_identity_risk": (
            "LOW" if not others else
            "HIGH" if abs(nearest_other["separation_fraction"]) < 0.05
            else "MODERATE"),
        "interpretation": (
            "the target 4096 Hz shear/torsional half-wave mode is NOT "
            "isolated: a flexural mode of the same body lies nearby. "
            "Flexural modes of a free-free bar are easy to excite and "
            "easy to mistake for the intended mode on an impedance "
            "sweep, so mode IDENTITY (not just frequency) must be "
            "established by full-field mapping or by a 3D eigenvector, "
            "not by a peak position alone."
            if others else
            "no other screened family lands inside the window"),
        "limitations": [
            "slender-body 1D models applied to a tapered 3D body",
            "scalar velocities for an anisotropic material",
            "flexural values are Euler-Bernoulli UPPER bounds; a thick "
            f"body (L/d = {geo.length_to_avg_diameter}) needs "
            "Timoshenko corrections that push them DOWN, which can "
            "move them closer to the target",
            "termination cones are not in any of these models",
        ],
        "proxy_artifact_warning": proxy_ratio_artifact(),
        "evidence_class": "ANALYTIC_SCREEN",
        "requires": "full anisotropic 3D eigenmode solve",
    }


def proxy_ratio_artifact() -> dict:
    """The two proxy velocities are in an exact 3:2 ratio.

    5700 / 3800 = 3/2 exactly, so the extensional and shear ladders
    fall on top of each other at every third shear mode (12288 Hz,
    24576 Hz, ...). Those degeneracies are an ARTIFACT of choosing two
    round proxy numbers, not a property of quartz: real alpha-quartz
    has v_L / v_T of roughly 1.9, which produces no such coincidence.
    Any 'harmonic alignment' read off this screen is therefore an
    artifact and must not be reported as structure.
    """
    from fractions import Fraction
    ratio = Fraction(int(V_LONGITUDINAL_M_S), int(V_SHEAR_M_S))
    return {
        "v_longitudinal_over_v_shear": [ratio.numerator,
                                        ratio.denominator],
        "is_small_integer_ratio": ratio.denominator <= 4,
        "first_spurious_degeneracy_hz": None if ratio.denominator > 4
        else 4096.0 * ratio.numerator,
        "real_quartz_ratio_approx": 1.9,
        "warning": "the exact 3:2 proxy ratio creates degeneracies "
                   "between the extensional and shear ladders that do "
                   "NOT exist in real quartz. Do not report any "
                   "harmonic alignment from this screen as physical.",
    }
