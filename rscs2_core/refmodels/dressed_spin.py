"""Mechanically dressed spin-coherence reference (Agent M4;
material reference.soe_phonon 'spin' via magnetic_order? NO —
this reference uses reference.exciton_magnon's magnetic_order or its
own gate: it is gated on magnetic_order of the chosen REFERENCE
material and returns NOT_APPLICABLE for quartz. No claim of a spin
qubit in the macroscopic quartz specimen (explicit exclusion).

Bloch equations with continuous mechanical drive and deterministic
low-frequency dephasing noise:

    dS/dt = (delta(t) z_hat + Omega x_hat) x S - Gamma2 S_perp

delta(t) = quasi-static Ornstein-Uhlenbeck-like noise (fixed seed).
Dressing (Omega >> sigma_delta) suppresses dephasing by low-frequency
noise — the declared regime; off-resonant/no-drive limits recover bare
decay."""

from __future__ import annotations

import numpy as np

from ..multiphysics import applicability, get_material
from ..multiphysics import make_result, not_applicable_result

MODULE_ID = "rscs2.refmodels.dressed_spin"


def _ou_noise(n: int, dt: float, sigma: float, tau_s: float,
              seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    x = np.zeros(n)
    a = np.exp(-dt / tau_s)
    b = sigma * np.sqrt(1 - a * a)
    for i in range(1, n):
        x[i] = a * x[i - 1] + b * rng.standard_normal()
    return x


def bloch_coherence(material_id: str, omega_drive_rad_s: float,
                    noise_sigma_rad_s: float, noise_tau_s: float,
                    duration_s: float, n: int = 20000,
                    seed: int = 20260716) -> dict:
    """Integrate the Bloch equation from S=(1,0,0) and report the
    coherence metric C = |<S_x + i S_y>| decay time-scale proxy
    (time to fall below 1/e), comparing dressed vs undriven."""
    mat = get_material(material_id)
    app = applicability(mat, "magnetic_order")
    if app["applicability"] == "NOT_APPLICABLE":
        return not_applicable_result(MODULE_ID, material_id,
                                     app["reason_code"], app["reason"])
    dt = duration_s / n
    t = np.arange(n) * dt
    delta = _ou_noise(n, dt, noise_sigma_rad_s, noise_tau_s, seed)

    def integrate(omega):
        S = np.array([1.0, 0.0, 0.0])
        cx = np.empty(n)
        for i in range(n):
            B = np.array([omega, 0.0, delta[i]])
            # RK2 midpoint on dS/dt = B x S
            k1 = np.cross(B, S)
            k2 = np.cross(B, S + 0.5 * dt * k1)
            S = S + dt * k2
            S /= max(np.linalg.norm(S), 1e-300)
            cx[i] = S[0]
        return cx

    bare = integrate(0.0)
    dressed = integrate(omega_drive_rad_s)

    def coherence_time(cx):
        # envelope proxy: first time |windowed mean| < 1/e
        w = max(n // 200, 5)
        env = np.abs(np.convolve(cx, np.ones(w) / w, mode="same"))
        below = np.nonzero(env < np.exp(-1.0))[0]
        return float(t[below[0]]) if len(below) else float(t[-1])

    t_bare = coherence_time(bare)
    t_dressed = coherence_time(dressed)
    return make_result(
        MODULE_ID, material_id, "REDUCED_ORDER_VALIDATED",
        ["DER", "ENG"],
        {"t_coh_bare_s": t_bare, "t_coh_dressed_s": t_dressed,
         "protection_factor": t_dressed / max(t_bare, 1e-300),
         "regime": "dressed" if omega_drive_rad_s
         > 3 * noise_sigma_rad_s else "undressed"},
        {"time": "s", "rates": "rad/s"},
        source_ids=["SRC-V4-10"],
        assumptions=["classical Bloch reduced model; deterministic "
                     "seeded noise; NOT a claim of a spin qubit in "
                     "macroscopic quartz"]) | {
        "t_s": t, "sx_bare": bare, "sx_dressed": dressed}
