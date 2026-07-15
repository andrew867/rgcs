"""Optical properties and ray/path model for alpha-quartz (RGCS v3 optical
application, Agent 06).

Provides the crystal-side inputs the RSCS optical operators need:
  - alpha-quartz refractive indices (uniaxial positive: n_o, n_e) and the
    photoelastic (Pockels elasto-optic) constants, Established handbook
    values with the reference/wavelength dependence declared (D6-002);
  - a straight-ray entry-facet path model: given an entry point on a facet
    and an interior target (geometric centre, predicted node, or measured
    node -- three distinct locations per the node menu of
    docs/RGCS_CRYSTAL_APPLICATION.md section 3), the geometric length,
    optical path length, transit time, and optical phase;
  - Snell refraction at the entry facet;
  - the photoelastic index shift delta_n = -1/2 n^3 p S (the conventional
    mechanism by which an acoustic strain field modulates a probe beam) and
    the acousto-optic figure of merit M2 = n^6 p^2 / (rho v^3).

Reciprocity posture (DECISION_LOG D6-003): a passive, lossless, unbiased
quartz path is reciprocal; every directional observable's null expectation
is NO asymmetry. Nothing here imports a source-device conclusion.

Handbook values: n_o = 1.5443, n_e = 1.5534 at 589.3 nm (sodium D), room
temperature (e.g. Hecht, Optics; Landolt-Boernstein). Photoelastic constants
p11 = 0.16, p12 = 0.27, p13 = 0.27, p14 = -0.030, p31 = 0.29, p33 = 0.10,
p41 = -0.047, p44 = -0.079 (Narasimhamurty, Photoelastic and Electro-Optic
Properties of Crystals; class 32). Third-decimal values depend on the
reference, wavelength, and temperature -- declared, not hidden.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from rgcs_core.provenance import classified

__all__ = ["QUARTZ_N_O", "QUARTZ_N_E", "QUARTZ_PHOTOELASTIC",
           "quartz_indices", "quartz_birefringence", "snell_refraction",
           "optical_path_length_mm", "optical_phase_rad", "ray_to_target",
           "photoelastic_index_shift", "acousto_optic_m2",
           "quartz_acousto_optic_m2"]

#: alpha-quartz ordinary / extraordinary refractive indices at 589.3 nm.
QUARTZ_N_O = 1.5443
QUARTZ_N_E = 1.5534

#: alpha-quartz photoelastic (elasto-optic) constants, class 32 (Pockels
#: p_ij, dimensionless). Narasimhamurty; standard handbook values.
QUARTZ_PHOTOELASTIC = {
    "p11": 0.16, "p12": 0.27, "p13": 0.27, "p14": -0.030,
    "p31": 0.29, "p33": 0.10, "p41": -0.047, "p44": -0.079,
}

_C_M_S = 299_792_458.0  # vacuum speed of light (SI exact)


@classified("Established", sources=("Hecht Optics", "Landolt-Boernstein"),
            note="alpha-quartz uniaxial-positive indices at 589.3 nm; "
                 "wavelength/temperature dependence declared (D6-002)")
def quartz_indices() -> dict[str, float]:
    """alpha-quartz ordinary/extraordinary indices (589.3 nm, room temp)."""
    return {"n_o": QUARTZ_N_O, "n_e": QUARTZ_N_E}


@classified("Established", sources=("Hecht Optics",),
            note="uniaxial positive: n_e - n_o = +0.0091 at 589.3 nm")
def quartz_birefringence() -> float:
    """Birefringence delta_n = n_e - n_o (positive uniaxial)."""
    return QUARTZ_N_E - QUARTZ_N_O


@classified("Established", sources=("Snell's law",),
            note="refraction at the entry facet; raises on total internal "
                 "reflection (only possible going high->low index)")
def snell_refraction(theta_incidence_deg: float, n_outside: float,
                     n_inside: float) -> float:
    """Refraction angle (deg) inside the crystal for a given incidence angle
    from the facet normal: n1 sin(t1) = n2 sin(t2)."""
    if not (math.isfinite(theta_incidence_deg)
            and 0.0 <= theta_incidence_deg < 90.0):
        raise ValueError("incidence angle must be in [0, 90) deg")
    for name, n in (("n_outside", n_outside), ("n_inside", n_inside)):
        if not (math.isfinite(n) and n >= 1.0):
            raise ValueError(f"{name} must be finite and >= 1")
    s = n_outside * math.sin(math.radians(theta_incidence_deg)) / n_inside
    if s > 1.0:
        raise ValueError("total internal reflection: no transmitted ray")
    return math.degrees(math.asin(s))


@classified("Established", sources=("optical path length definition",),
            note="OPL = n * geometric length; the phase-relevant length")
def optical_path_length_mm(geometric_length_mm: float,
                           refractive_index: float) -> float:
    """Optical path length OPL = n * L_geo (mm)."""
    if not (math.isfinite(geometric_length_mm) and geometric_length_mm > 0):
        raise ValueError("geometric_length_mm must be positive and finite")
    if not (math.isfinite(refractive_index) and refractive_index >= 1.0):
        raise ValueError("refractive_index must be finite and >= 1")
    return geometric_length_mm * refractive_index


@classified("Established", sources=("optical phase definition",),
            note="phi = 2*pi * OPL / lambda0")
def optical_phase_rad(opl_mm: float, wavelength_nm: float) -> float:
    """Accumulated optical phase phi = 2*pi*OPL/lambda_0 (rad, unwrapped)."""
    if not (math.isfinite(opl_mm) and opl_mm > 0):
        raise ValueError("opl_mm must be positive and finite")
    if not (math.isfinite(wavelength_nm) and wavelength_nm > 0):
        raise ValueError("wavelength_nm must be positive and finite")
    return 2.0 * math.pi * (opl_mm * 1e-3) / (wavelength_nm * 1e-9)


@classified("Established", sources=("geometry",),
            note="straight-ray entry-facet path to an interior target; the "
                 "target is a LOCATION CHOICE (geometric centre / predicted "
                 "node / measured node are distinct, node menu section 3)")
def ray_to_target(entry_point_mm: np.ndarray, target_point_mm: np.ndarray,
                  refractive_index: float = QUARTZ_N_O,
                  wavelength_nm: float = 632.8) -> dict[str, Any]:
    """Straight-ray path from an entry-facet point to an interior target.

    Answers the geometric half of 'can an optical path address a measured
    mode-overlap region': the path, its direction, geometric length, OPL,
    transit time, and accumulated phase. Whether anything MEASURABLE happens
    at the target is a separate, classified question (H-20..H-23)."""
    p0 = np.asarray(entry_point_mm, dtype=float)
    p1 = np.asarray(target_point_mm, dtype=float)
    if p0.shape != (3,) or p1.shape != (3,):
        raise ValueError("points must be 3-vectors (mm)")
    if not (np.all(np.isfinite(p0)) and np.all(np.isfinite(p1))):
        raise ValueError("points must be finite")
    seg = p1 - p0
    length_mm = float(np.linalg.norm(seg))
    if length_mm == 0.0:
        raise ValueError("entry and target coincide: no ray")
    opl_mm = optical_path_length_mm(length_mm, refractive_index)
    transit_s = (opl_mm * 1e-3) / _C_M_S
    return {
        "direction": seg / length_mm,
        "geometric_length_mm": length_mm,
        "optical_path_length_mm": opl_mm,
        "transit_time_s": transit_s,
        "phase_rad": optical_phase_rad(opl_mm, wavelength_nm),
    }


@classified("Derived",
            sources=("photoelastic effect (standard)", "QUARTZ_PHOTOELASTIC"),
            note="delta_n = -1/2 n^3 p S: the conventional mechanism by "
                 "which acoustic strain modulates a probe; magnitude "
                 "estimate for H-20 pre-registration")
def photoelastic_index_shift(refractive_index: float, p_constant: float,
                             strain: float) -> float:
    """Photoelastic index change delta_n = -(1/2) n^3 p S for strain S.
    With quartz p11 = 0.16 and a typical acoustic strain S ~ 1e-7 the shift
    is ~ -3e-8: small but standard interferometry territory."""
    if not (math.isfinite(refractive_index) and refractive_index >= 1.0):
        raise ValueError("refractive_index must be finite and >= 1")
    if not math.isfinite(p_constant) or not math.isfinite(strain):
        raise ValueError("p_constant and strain must be finite")
    return -0.5 * refractive_index ** 3 * p_constant * strain


@classified("Derived", sources=("acousto-optic figure of merit (standard)",),
            note="M2 = n^6 p^2 / (rho v^3), s^3/kg; ranks how efficiently a "
                 "material converts acoustic power to optical modulation")
def acousto_optic_m2(refractive_index: float, p_constant: float,
                     density_kg_m3: float, wave_speed_m_s: float) -> float:
    """Acousto-optic figure of merit M2 = n^6 p^2 / (rho v^3) (s^3/kg)."""
    if not (math.isfinite(refractive_index) and refractive_index >= 1.0):
        raise ValueError("refractive_index must be finite and >= 1")
    if not math.isfinite(p_constant):
        raise ValueError("p_constant must be finite")
    for name, v in (("density_kg_m3", density_kg_m3),
                    ("wave_speed_m_s", wave_speed_m_s)):
        if not (math.isfinite(v) and v > 0):
            raise ValueError(f"{name} must be positive and finite")
    return (refractive_index ** 6 * p_constant ** 2
            / (density_kg_m3 * wave_speed_m_s ** 3))


@classified("Derived",
            sources=("QUARTZ_PHOTOELASTIC", "rgcs_core.anisotropy"),
            note="quartz M2 with n_o, p11, handbook density, and the "
                 "anisotropic X-axis quasi-longitudinal speed; small vs "
                 "dedicated AO materials -- an honest sensitivity bound")
def quartz_acousto_optic_m2() -> float:
    """M2 of alpha-quartz for an X-propagating longitudinal wave with an
    ordinary-polarized probe (n_o, p11). Uses the Agent 05 anisotropic
    X-axis quasi-longitudinal speed, closing the loop with RSCS-O.17."""
    from rgcs_core.anisotropy import ALPHA_QUARTZ_DENSITY_KG_M3, AXIS_X, wave_speeds
    v_x = wave_speeds(AXIS_X)["v_quasi_long_m_s"]
    return acousto_optic_m2(QUARTZ_N_O, QUARTZ_PHOTOELASTIC["p11"],
                            ALPHA_QUARTZ_DENSITY_KG_M3, v_x)
