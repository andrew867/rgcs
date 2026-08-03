"""Force firewall, v0.6 -- the conventional-subtraction ledger.

Delegates to ``r1070tb.sources`` (the Townsend Brown audit lane) wherever
the arithmetic already exists there, so the same audited code serves both
lanes rather than a second copy drifting.

    measured response
    = ordinary EHD momentum
    + Maxwell/electrostrictive stress
    + piezoelectric response
    + charge memory/hysteresis
    + chamber-wall and cable forces
    + thermal/acoustic/vibration artifacts
    + possible unexplained residual

A residual is never evidence; it is the prompt to find the next
conventional term.
"""

from __future__ import annotations

from r1070tb.sources import (arl_force_from_mobility,  # noqa: F401
                             momentum_accounting, nonlinear_dielectric_force,
                             polarity_classification)


def even_odd_decomposition(y_plus: float, y_minus: float) -> dict:
    """y_even = (y(+V)+y(-V))/2, y_odd = (y(+V)-y(-V))/2."""
    return {"even": (y_plus + y_minus) / 2.0,
            "odd": (y_plus - y_minus) / 2.0,
            "claim": "EXACT_ARITHMETIC"}


def harmonic_coefficients(v_dc: float, v_ac: float, a1: float, a2: float,
                          a3: float) -> dict:
    """Harmonic content of a1*V + a2*V^2 + a3*V^3 under V = Vdc+Vac*cos.

    Standard trigonometric expansion, exact:
      DC   : a1*Vdc + a2*(Vdc^2 + Vac^2/2) + a3*(Vdc^3 + 3*Vdc*Vac^2/2)
      1st  : a1*Vac + 2*a2*Vdc*Vac + 3*a3*(Vdc^2*Vac + Vac^3/4)
      2nd  : a2*Vac^2/2 + 3*a3*Vdc*Vac^2/2
      3rd  : a3*Vac^3/4
    The third harmonic isolates a3 -- the cubic fingerprint the audit
    identified as the discriminating observable.
    """
    dc = (a1 * v_dc + a2 * (v_dc ** 2 + v_ac ** 2 / 2.0)
          + a3 * (v_dc ** 3 + 1.5 * v_dc * v_ac ** 2))
    h1 = (a1 * v_ac + 2.0 * a2 * v_dc * v_ac
          + 3.0 * a3 * (v_dc ** 2 * v_ac + v_ac ** 3 / 4.0))
    h2 = a2 * v_ac ** 2 / 2.0 + 1.5 * a3 * v_dc * v_ac ** 2
    h3 = a3 * v_ac ** 3 / 4.0
    return {"dc": dc, "h1": h1, "h2": h2, "h3": h3,
            "h3_isolates_a3": True, "claim": "EXACT_ARITHMETIC"}


def ehd_drift_force(current: float, gap: float, mobility: float) -> dict:
    """F ~ I*d/mu_i, via the audited r1070tb implementation."""
    return {"force_N": arl_force_from_mobility(current, gap, mobility),
            "claim": "PRIOR_ART_ANALOGUE",
            "vanishes_in_vacuum": True}


def artifact_budget(wall_N: float = 0.0, cable_N: float = 0.0,
                    thermal_N: float = 0.0, vibration_N: float = 0.0,
                    uncertainty_N: float = float("nan")) -> dict:
    """Chamber-wall / cable / thermal / vibration placeholders.

    Placeholders with an explicit uncertainty, BENCH_REQUIRED. NaN
    uncertainty means unmeasured, and an unmeasured artifact budget means
    no residual can be quoted at all.
    """
    import math
    measured = not math.isnan(uncertainty_N)
    return {"wall_N": wall_N, "cable_N": cable_N, "thermal_N": thermal_N,
            "vibration_N": vibration_N, "uncertainty_N": uncertainty_N,
            "budget_measured": measured,
            "residual_quotable": measured,
            "claim": "BENCH_REQUIRED"}


__all__ = ["even_odd_decomposition", "harmonic_coefficients",
           "ehd_drift_force", "artifact_budget", "polarity_classification",
           "momentum_accounting", "nonlinear_dielectric_force"]
