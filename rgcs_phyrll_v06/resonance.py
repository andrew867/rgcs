"""Carrier scheduling and coupled ring power, v0.6.

    f_base = 4096 Hz         f_ext = 4096 * 411 Hz = 1,683,456 Hz
    N = 37 cells             m = 4 (phase winding)
    411/37 = 11 + 4/37       (exact; asserted, not assumed)

    I_k(t) = I0 * a_k * cos(2*pi*f_ext*t - m*phi_k + phi0)

Power bookkeeping:

    omega  = 2*pi*f_ext
    P_ring = omega * U / Q            (stored energy U, quality factor Q)
    U_L    = L_eff * I_rms^2
    U_C    = C_eff * V_rms^2
    F      = eta * P_ring             (a COEFFICIENT relation, not physics)

The wall-power rule is enforced in code: eta may never be applied to
electrical wall power unless a separate coupling efficiency eta_couple is
declared, because ring power and wall power differ by exactly that
unmeasured factor.
"""

from __future__ import annotations

import math
from fractions import Fraction as F

F_BASE = 4096
F_EXT = 4096 * 411
N_CELLS = 37
M_WINDING = 4

#: The exact scheduler relation.
RATIO_411_37 = F(411, 37)


def ratio_is_11_plus_4_over_37() -> bool:
    return RATIO_411_37 == 11 + F(4, 37)


def cell_current(t: float, k: int, active: int = 1, i0: float = 1.0,
                 phi0: float = 0.0, f_ext: float = F_EXT,
                 m: int = M_WINDING, n: int = N_CELLS) -> float:
    """I_k(t) with the m*phi_k progressive phase."""
    phi_k = 2.0 * math.pi * k / n
    return i0 * active * math.cos(2.0 * math.pi * f_ext * t
                                  - m * phi_k + phi0)


def winding_snapshot(t: float = 0.0, i0: float = 1.0, phi0: float = 0.0,
                     n: int = N_CELLS, m: int = M_WINDING) -> list:
    return [cell_current(t, k, 1, i0, phi0, F_EXT, m, n) for k in range(n)]


def stored_energy(l_eff: float, i_rms: float, c_eff: float,
                  v_rms: float) -> dict:
    ul = l_eff * i_rms ** 2
    uc = c_eff * v_rms ** 2
    return {"U_L": ul, "U_C": uc, "U": ul + uc, "claim": "MODEL_OUTPUT"}


def ring_power(u_stored: float, q_factor: float,
               f_ext: float = F_EXT) -> float:
    """P_ring = omega*U/Q. Requires the RING's stored energy, not wall power."""
    if q_factor <= 0:
        raise ValueError("Q must be positive")
    return 2.0 * math.pi * f_ext * u_stored / q_factor


def ring_power_from_wall(p_electrical: float,
                         eta_couple: float | None = None) -> float:
    """Wall power is only usable through a DECLARED coupling efficiency.

    Refusing the undeclared case is the point: silently equating wall and
    ring power inflates every downstream force number by 1/eta_couple.
    """
    if eta_couple is None:
        raise ValueError(
            "eta_couple is undeclared; wall power may not stand in for "
            "ring power without a measured coupling efficiency")
    if not (0.0 < eta_couple <= 1.0):
        raise ValueError("eta_couple must lie in (0, 1]")
    return eta_couple * p_electrical


def force_coefficient_relation(eta: float, p_ring: float) -> dict:
    """F = eta * P_ring, tagged as what it is.

    Dimensionally F [N] = eta [N/W] * P [W]: eta is a coefficient with
    units, whose VALUE only a bench measurement can supply. This function
    exists so the relation is computed in exactly one audited place.
    """
    return {"force_N": eta * p_ring, "eta_units": "N_per_W",
            "claim": "BENCH_REQUIRED",
            "note": "coefficient relation; no propulsion mechanism implied"}


def torque(r_eff: float, f_tangential: float) -> float:
    return r_eff * f_tangential


def power_sweep(l_eff: float, c_eff: float, q_factor: float,
                i_rms_values, v_rms: float, eta: float) -> list:
    """The coupled-ring power sweep for the report. Deterministic."""
    rows = []
    for i_rms in i_rms_values:
        u = stored_energy(l_eff, i_rms, c_eff, v_rms)
        p = ring_power(u["U"], q_factor)
        f = force_coefficient_relation(eta, p)
        rows.append({"I_rms": i_rms, "U_J": u["U"], "P_ring_W": p,
                     "F_N_if_eta_held": f["force_N"],
                     "claim": "MODEL_OUTPUT"})
    return rows


__all__ = ["F_BASE", "F_EXT", "N_CELLS", "M_WINDING", "RATIO_411_37",
           "ratio_is_11_plus_4_over_37", "cell_current",
           "winding_snapshot", "stored_energy", "ring_power",
           "ring_power_from_wall", "force_coefficient_relation", "torque",
           "power_sweep"]
