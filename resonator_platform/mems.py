"""MEMS/NEMS resonators and post-fabrication tuning (Agent R09).

A microdevice digital twin with the real damping terms, the standard
trim methods, and a foundry handoff that is INTERFACE_ONLY: this
programme has no cleanroom, and the interface says so instead of
pretending."""

from __future__ import annotations

import math


class MemsError(RuntimeError):
    pass


SI_E = 169e9          # <110> silicon Young's modulus
SI_RHO = 2329.0


def beam_resonator(length_um: float, width_um: float,
                   thickness_um: float, gap_um: float = 2.0,
                   pressure_pa: float = 101325.0,
                   temperature_k: float = 300.0) -> dict:
    """Clamped-clamped silicon beam twin:
    f1 = 1.028 * (t/L^2) * sqrt(E/rho)   (standard CC-beam formula)

    with the three dominant loss channels estimated:
    - gas (squeeze-film, ~1/pressure at low vacuum);
    - anchor (scales as (t/L)^3, geometry-dominated);
    - thermoelastic (Zener peak; crude Lorentzian in f/f_TED).
    """
    L, t = length_um * 1e-6, thickness_um * 1e-6
    f1 = 1.028 * t / L ** 2 * math.sqrt(SI_E / SI_RHO)
    # gas damping: Q_gas ~ k / p (declared coefficient, order-level)
    q_gas = 3e8 / max(pressure_pa, 1e-3)
    # anchor loss
    q_anchor = 2.0 / (t / L) ** 3
    # thermoelastic (Zener): f_TED where thermal diffusion time
    # matches the period
    kappa, cp = 148.0, 700.0
    f_ted = math.pi * kappa / (2 * SI_RHO * cp * (t) ** 2)
    x = f1 / f_ted
    q_ted = 1.0 / (0.04 * (x / (1 + x ** 2)))   # Zener form
    q_total = 1.0 / (1 / q_gas + 1 / q_anchor + 1 / q_ted)
    return {"f1_hz": f1, "q_gas": q_gas, "q_anchor": q_anchor,
            "q_ted": q_ted, "q_total": q_total,
            "dominant_loss": min(
                [("gas", q_gas), ("anchor", q_anchor),
                 ("thermoelastic", q_ted)], key=lambda t_: t_[1])[0],
            "note": "order-of-magnitude twin; a foundry PDK would "
                    "replace every coefficient here"}


TRIM_METHODS = {
    "laser_ablation": {"direction": "+f (mass removal)",
                       "resolution_ppm": 10,
                       "risk": "debris redeposition, local stress"},
    "focused_ion_beam": {"direction": "+f", "resolution_ppm": 0.1,
                         "risk": "Ga implantation changes damping"},
    "selective_deposition": {"direction": "-f (mass addition)",
                             "resolution_ppm": 1,
                             "risk": "stress in the deposited film"},
    "oxidation_trim": {"direction": "±f (stress + mass)",
                       "resolution_ppm": 5,
                       "risk": "slow, batch-level only"},
    "joule_annealing": {"direction": "±f (stress relaxation)",
                        "resolution_ppm": 1,
                        "risk": "aging reset, one-shot"},
}


def trim_budget(f0_hz: float, initial_error_ppm: float,
                method: str) -> dict:
    """Can this method's resolution close the fabrication error?"""
    if method not in TRIM_METHODS:
        raise MemsError(f"unknown trim method {method}")
    m = TRIM_METHODS[method]
    steps = initial_error_ppm / m["resolution_ppm"]
    return {"method": method, **m,
            "initial_error_hz": f0_hz * initial_error_ppm * 1e-6,
            "n_steps_needed": math.ceil(steps),
            "feasible": steps >= 1.0,
            "note": "an error below the method resolution cannot be "
                    "trimmed by it — pick a finer method or accept"}


def foundry_handoff() -> dict:
    """INTERFACE_ONLY: what a real MEMS collaboration would need.
    No cleanroom, no PDK, no fab run exists in this programme."""
    return {"classification": "INTERFACE_ONLY",
            "value": None,
            "declares": {
                "inputs": ["design (GDS)", "PDK + design rules",
                           "target f0 and Q", "package spec"],
                "outputs": ["fabricated wafer", "wafer map",
                            "per-die measured f0/Q"],
                "requirements": ["foundry MPW slot", "budget",
                                 "packaging partner",
                                 "probe-station access"]},
            "note": "no MEMS device can be produced by this "
                    "repository; the handoff exists so a future "
                    "collaboration starts from a typed contract "
                    "instead of a conversation"}
