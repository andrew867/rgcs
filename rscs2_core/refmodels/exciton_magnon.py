"""Exciton-magnon modulation reference (Agent M4; RGCS-V4-EQ-004;
material reference.exciton_magnon).

E_x(t) = E0 + A cos^2(theta(t)/2), theta(t) = theta0 + dth cos(w_m t).
Exact and small-angle forms, sideband spectrum, damping/linewidth."""

from __future__ import annotations

import math

import numpy as np

from ..multiphysics import applicability, get_material, make_result
from ..multiphysics import not_applicable_result

MODULE_ID = "rscs2.refmodels.exciton_magnon"


def _gate(material_id: str):
    mat = get_material(material_id)
    return applicability(mat, "exciton_magnon_coupling")


def exciton_energy(theta_rad) -> np.ndarray:
    """Exact declared form (per unit modulation depth A, E0 = 0)."""
    return np.cos(np.asarray(theta_rad) / 2.0) ** 2


def small_angle_expansion(theta0_rad: float, dtheta_rad: float):
    """Second-order expansion about theta0:
    E(th0+x) ~ E(th0) - sin(th0)/2 * x - cos(th0)/4 * x^2."""
    e0 = math.cos(theta0_rad / 2) ** 2
    c1 = -math.sin(theta0_rad) / 2.0
    c2 = -math.cos(theta0_rad) / 4.0
    return e0, c1, c2


def modulated_trace(material_id: str, e0: float, a_mod: float,
                    theta0_rad: float, dtheta_rad: float,
                    f_magnon_hz: float, damping_hz: float = 0.0,
                    duration_s: float | None = None,
                    n: int = 8192) -> dict:
    """Time trace + spectrum of the modulated exciton energy. The
    magnon coordinate theta(t) decays with `damping_hz` -> finite
    sideband linewidth."""
    app = _gate(material_id)
    if app["applicability"] == "NOT_APPLICABLE":
        return not_applicable_result(MODULE_ID, material_id,
                                     app["reason_code"], app["reason"])
    if duration_s is None:
        duration_s = 200.0 / f_magnon_hz
    t = np.linspace(0.0, duration_s, n, endpoint=False)
    envl = np.exp(-damping_hz * t)
    theta = theta0_rad + dtheta_rad * envl * np.cos(
        2 * np.pi * f_magnon_hz * t)
    e_t = e0 + a_mod * exciton_energy(theta)
    spec = np.abs(np.fft.rfft(e_t - e_t.mean())) / n
    freqs = np.fft.rfftfreq(n, t[1] - t[0])
    return make_result(
        MODULE_ID, material_id, "REDUCED_ORDER_VALIDATED",
        ["DER"],
        {"t_s": t.tolist()[:0],           # arrays returned separately
         "sideband_peak_hz": float(freqs[np.argmax(spec[1:]) + 1])},
        {"energy": "declared units (E0, A)", "frequency": "Hz"},
        source_ids=["SRC-V4-06"], equation_ids=["RGCS-V4-EQ-004"],
        assumptions=["reduced-order; theta driven by a single magnon "
                     "coordinate; no microscopic BSE content"]) | {
        "t_s": t, "energy_t": e_t, "freqs_hz": freqs,
        "spectrum": spec}


def sideband_amplitudes(theta0_rad: float, dtheta_rad: float,
                        n_harmonics: int = 3) -> dict:
    """Analytic harmonic content via cos^2(theta/2) = (1+cos theta)/2
    and the Jacobi-Anger expansion:
    cos(th0 + d cos(x)) = sum_k J_k(d) * [cos th0, sin th0 terms].
    Returns |c_k| for k = 0..n (per unit A)."""
    from scipy.special import jv
    d = dtheta_rad
    amps = {0: abs(0.5 + 0.5 * math.cos(theta0_rad) * jv(0, d))}
    for k in range(1, n_harmonics + 1):
        base = 0.5 * jv(k, d)
        if k % 2 == 1:                       # odd harmonics ~ sin(th0)
            amps[k] = abs(base * math.sin(theta0_rad))
        else:                                # even ~ cos(th0)
            amps[k] = abs(base * math.cos(theta0_rad))
    return amps
