"""Resonator electrical model and measurement plan, v0.7.

Symbolic/numeric scaffolding around the standard relations

    f0 = 1 / (2*pi*sqrt(L*C))
    P_ring = omega * U / Q
    U_L = L_eff * I_rms^2        U_C = C_eff * V_rms^2

with the five unknowns named as unknowns: L_eff, C_eff, Q_L, R_loss,
eta_couple. The one thing the carrier lock DOES pin down is the LC
product -- if the ring is to resonate at 1,683,456 Hz then

    L_eff * C_eff = 1 / (2*pi*f0)^2

exactly one degree of freedom short of a design. Everything else is a
measurement, and ``measurement_plan`` says how to take each one.
"""

from __future__ import annotations

import math

from rgcs_phyrll_v06.resonance import (F_EXT, ring_power,  # noqa: F401
                                       ring_power_from_wall, stored_energy)

UNKNOWNS = ("L_eff", "C_eff", "Q_L", "R_loss", "eta_couple")


def f0_from_lc(l_eff: float, c_eff: float) -> float:
    if l_eff <= 0 or c_eff <= 0:
        raise ValueError("L and C must be positive")
    return 1.0 / (2.0 * math.pi * math.sqrt(l_eff * c_eff))


def lc_product_from_lock(f0: float = float(F_EXT)) -> float:
    """The LC product the carrier lock imposes: 1/(2*pi*f0)^2."""
    return 1.0 / (2.0 * math.pi * f0) ** 2


def l_for_c(c_eff: float, f0: float = float(F_EXT)) -> float:
    """The L that resonates a given C at the locked carrier."""
    return lc_product_from_lock(f0) / c_eff


def r_loss_from_q(q_l: float, l_eff: float,
                  f0: float = float(F_EXT)) -> float:
    """Series-model loss resistance: R = omega*L/Q."""
    if q_l <= 0:
        raise ValueError("Q must be positive")
    return 2.0 * math.pi * f0 * l_eff / q_l


def design_point(c_eff: float, q_l: float,
                 f0: float = float(F_EXT)) -> dict:
    """One consistent (L, C, Q, R) point on the locked-carrier line."""
    l_eff = l_for_c(c_eff, f0)
    return {"f0_hz": f0, "C_eff_F": c_eff, "L_eff_H": l_eff,
            "Q_L": q_l, "R_loss_ohm": r_loss_from_q(q_l, l_eff, f0),
            "LC_product_s2": l_eff * c_eff,
            "claim": "MODEL_OUTPUT",
            "note": "a consistency point, not a measured device"}


def measurement_plan() -> list:
    """How each unknown is to be extracted on the bench. BENCH_REQUIRED."""
    plan = [
        {"unknown": "L_eff", "method": "impedance-analyzer sweep",
         "protocol": "small-signal |Z|(f) and phase from f0/10 to 10*f0; "
                     "fit the series-RLC model; L from the inductive "
                     "slope well below resonance",
         "instrument": "impedance/network analyzer",
         "target_uncertainty": "2%"},
        {"unknown": "C_eff", "method": "same sweep, capacitive branch",
         "protocol": "C from the capacitive slope well above resonance; "
                     "cross-check L*C against the measured f0",
         "instrument": "impedance/network analyzer",
         "target_uncertainty": "2%"},
        {"unknown": "Q_L", "method": "ring-down AND 3 dB bandwidth",
         "protocol": "excite at f0, cut drive, fit exponential decay "
                     "tau -> Q = pi*f0*tau; confirm with f0/BW(-3dB). "
                     "The two must agree or the discrepancy is reported",
         "instrument": "oscilloscope + gated drive",
         "target_uncertainty": "5%"},
        {"unknown": "R_loss", "method": "derived",
         "protocol": "R = 2*pi*f0*L_eff/Q_L from the measured pair; "
                     "sanity-check against DC + skin-effect estimate",
         "instrument": "derived", "target_uncertainty": "propagated"},
        {"unknown": "eta_couple", "method": "power accounting",
         "protocol": "wall power in vs ring stored-energy turnover "
                     "(omega*U/Q) at steady state; calorimetry on the "
                     "drive chain closes the budget",
         "instrument": "power analyzer + calorimetry",
         "target_uncertainty": "10%"},
    ]
    for row in plan:
        row["claim"] = "BENCH_REQUIRED"
    return plan


__all__ = ["UNKNOWNS", "f0_from_lc", "lc_product_from_lock", "l_for_c",
           "r_loss_from_q", "design_point", "measurement_plan"]
