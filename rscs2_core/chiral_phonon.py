"""Chiral two-mode phonon reference (Agent M3/M4 boundary;
RGCS-V4-EQ-013; quantity angular_momentum.phonon.chiral_mode;
material reference.chiral_phonon — REFERENCE_ONLY, never quartz by
default)."""

from __future__ import annotations

import math

import numpy as np

from .multiphysics import applicability, get_material, make_result
from .multiphysics import not_applicable_result


def trajectory(q0: float, omega_rad_s: float, phase_rad: float,
               t_s: np.ndarray) -> dict:
    """Degenerate pair qx = q0 cos(wt), qy = q0 cos(wt - phase).
    phase = +pi/2 -> counterclockwise circular; -pi/2 -> clockwise;
    0 or pi -> linear (zero angular momentum)."""
    qx = q0 * np.cos(omega_rad_s * t_s)
    qy = q0 * np.cos(omega_rad_s * t_s - phase_rad)
    px = -q0 * omega_rad_s * np.sin(omega_rad_s * t_s)
    py = -q0 * omega_rad_s * np.sin(omega_rad_s * t_s - phase_rad)
    lz = qx * py - qy * px
    return {"qx": qx, "qy": qy, "lz_t": lz,
            "lz_cycle_mean": float(lz.mean())}


def angular_momentum(q0: float, omega_rad_s: float,
                     phase_rad: float) -> float:
    """Closed form: <L_z> = q0^2 * omega * sin(phase) (unit mass)."""
    return q0 ** 2 * omega_rad_s * math.sin(phase_rad)


def zeeman_splitting_interface(material_id: str, g_eff: float | None,
                               b_field_t: float, q0: float,
                               omega_rad_s: float,
                               phase_rad: float) -> dict:
    """Capability-gated Zeeman splitting dE = g_eff * B * sign(<L_z>).
    Requires a material whose record supports chiral_phonons AND a
    material-specific g_eff; alpha quartz gets NOT_APPLICABLE."""
    mat = get_material(material_id)
    app = applicability(mat, "chiral_phonons")
    if app["applicability"] == "NOT_APPLICABLE":
        return not_applicable_result(
            "rscs2.chiral_phonon.zeeman", material_id,
            app["reason_code"], app["reason"])
    if g_eff is None:
        return not_applicable_result(
            "rscs2.chiral_phonon.zeeman", material_id,
            "MATERIAL_G_FACTOR_ABSENT",
            "no material-specific effective g factor registered; the "
            "Zeeman interface refuses defaults")
    lz = angular_momentum(q0, omega_rad_s, phase_rad)
    de = g_eff * b_field_t * float(np.sign(lz))
    return make_result(
        "rscs2.chiral_phonon.zeeman", material_id,
        "REDUCED_ORDER_VALIDATED", ["DER"],
        {"lz_norm": lz, "delta_e_units_of_g": de,
         "sign_flips_with_field": True,
         "sign_flips_with_phase": True},
        {"lz": "q0^2 * rad/s (unit mass)", "delta_e": "g_eff*B units"},
        source_ids=["SRC-V4-13"], equation_ids=["RGCS-V4-EQ-013"],
        assumptions=["degenerate two-mode pair",
                     "linear Zeeman interface; g_eff supplied by "
                     "material record"])
