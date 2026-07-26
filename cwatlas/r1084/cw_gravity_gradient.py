"""Newtonian gravity and radial gradient per shell (R10.8.4 §6).

Conventional baseline only: ``g(r) = mu / r**2``, gradient
``dg/dr = -2 mu / r**3 = -2 g / r``. No anomalous-gravity claim is
established by any number produced here
(``PHYSICAL_ANOMALOUS_GRAVITY_VALIDATED: no``). Speculative
effective-potential terms, if ever supplied, must live in separate columns —
this module refuses to merge them.
"""

from __future__ import annotations

import math

MU_M3_S2 = 3.986004418e14   # Earth GM, m^3/s^2 (conventional)
R_EARTH_KM = 6371.0


def g_of_r(r_km: float) -> float:
    """Gravitational acceleration magnitude at radius r (m/s^2)."""
    if r_km <= 0:
        raise ValueError("radius must be positive")
    return MU_M3_S2 / (r_km * 1000.0) ** 2


def radial_gradient(r_km: float) -> float:
    """dg/dr = -2 mu / r^3 (per metre, negative outward)."""
    return -2.0 * MU_M3_S2 / (r_km * 1000.0) ** 3


def shell_row(shell_id: str, r_min_km: float, r_max_km: float) -> dict:
    """The full §6 report row for one radial interval."""
    if not 0 < r_min_km < r_max_km:
        raise ValueError("invalid radial bounds")
    r_mid = 0.5 * (r_min_km + r_max_km)
    dr_m = (r_max_km - r_min_km) * 1000.0
    g_in, g_mid, g_out = g_of_r(r_min_km), g_of_r(r_mid), g_of_r(r_max_km)
    dg_exact = abs(MU_M3_S2 * (1.0 / (r_min_km * 1000.0) ** 2
                               - 1.0 / (r_max_km * 1000.0) ** 2))
    dg_approx = abs(2.0 * MU_M3_S2 / (r_mid * 1000.0) ** 3) * dr_m
    return {
        "shell_id": shell_id,
        "radial_bounds_km": (r_min_km, r_max_km),
        "midpoint_radius_km": r_mid,
        "altitude_bounds_km": (r_min_km - R_EARTH_KM,
                               r_max_km - R_EARTH_KM),
        "radial_thickness_km": r_max_km - r_min_km,
        "g_inner_m_s2": g_in,
        "g_midpoint_m_s2": g_mid,
        "g_outer_m_s2": g_out,
        "abs_gravity_change_m_s2": dg_exact,
        "gravity_change_midpoint_approx_m_s2": dg_approx,
        "fractional_gravity_change": dg_exact / g_mid,
        "radial_gradient_mid_s2": radial_gradient(r_mid),
    }


def layer_scales(surface_area_km2: float, geodesic_diameter_km: float,
                 dr_km: float) -> dict:
    """§6.1 tangential / radial / explicit 3D effective scales."""
    return {
        "tangential_scale_km": geodesic_diameter_km,
        "radial_scale_km": dr_km,
        "effective_3d_scale_km": (surface_area_km2 * dr_km) ** (1.0 / 3.0),
        "definition": "L3 = (A_T * dr)^(1/3); tangential = max geodesic "
                      "diameter; never collapsed silently",
    }


def layer_hypothesis_rows(shells: list[dict]) -> list[dict]:
    """§6.2 — compare candidate conserved quantities across levels.

    Base-10 nested subdivision fixes Delta r_{j+1} = Delta r_j / 10 by
    construction, so the table shows which candidate quantities that
    construction does / does not hold constant. No candidate is assumed.
    """
    rows = []
    for prev, cur in zip(shells, shells[1:]):
        r_p, r_c = prev["midpoint_radius_km"], cur["midpoint_radius_km"]
        rows.append({
            "from_shell": prev["shell_id"], "to_shell": cur["shell_id"],
            "ratio_dr_over_r": (cur["radial_thickness_km"] / r_c)
            / (prev["radial_thickness_km"] / r_p),
            "ratio_dg_over_g": cur["fractional_gravity_change"]
            / prev["fractional_gravity_change"],
            "ratio_potential_step":
                (cur["g_midpoint_m_s2"] * cur["radial_thickness_km"])
                / (prev["g_midpoint_m_s2"] * prev["radial_thickness_km"]),
            "ratio_log_radius_step":
                math.log(cur["radial_bounds_km"][1]
                         / cur["radial_bounds_km"][0])
                / math.log(prev["radial_bounds_km"][1]
                           / prev["radial_bounds_km"][0]),
            "gamma_L_r": abs(cur["radial_gradient_mid_s2"])
            * cur["radial_thickness_km"] * 1000.0,
        })
    return rows
