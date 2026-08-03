"""Force firewall, v0.6 -- the conventional-subtraction ledger.

The public lane keeps the small conventional arithmetic local so it does
not depend on the mixed R10.62-R10.70 research branch. These functions
remain subtraction controls, never a device-performance model.

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


def arl_force_from_mobility(current: float, gap: float,
                            mobility: float) -> float:
    """Conventional ion-drift momentum term, valid only in a medium."""
    if mobility <= 0.0:
        raise ValueError("mobility must be positive")
    return current * gap / mobility


def nonlinear_dielectric_force(voltage: float, c1: float, c2: float,
                               c3: float) -> float:
    """Diagnostic polynomial used only to separate reversal parity."""
    return c1 * voltage + c2 * voltage ** 2 + c3 * voltage ** 3


def polarity_classification(voltage: float, c1: float, c2: float,
                            c3: float) -> dict:
    """Split the diagnostic response into polarity-even and odd parts."""
    plus = nonlinear_dielectric_force(voltage, c1, c2, c3)
    minus = nonlinear_dielectric_force(-voltage, c1, c2, c3)
    even = (plus + minus) / 2.0
    odd = (plus - minus) / 2.0
    return {
        "even_E2_like": even,
        "odd_current_like": odd,
        "even_is_quadratic_term": c2 * voltage ** 2,
        "classification": (
            "EVEN_DOMINANT_FIELD_STRESS"
            if abs(even) > abs(odd)
            else "ODD_DOMINANT_CURRENT_LIKE"
        ),
    }


def momentum_accounting(current: float, voltage: float, gap: float,
                        mobility: float, measured_force: float) -> dict:
    """Close the conventional momentum budget; a residual is not evidence."""
    del voltage  # API parity; the mobility form already uses I*d/mu.
    predicted = arl_force_from_mobility(current, gap, mobility)
    residual = measured_force - predicted
    fraction = residual / measured_force if measured_force else float("nan")
    return {
        "predicted_ion_drift_force": predicted,
        "measured_force": measured_force,
        "residual": residual,
        "residual_fraction": fraction,
        "budget_closed": abs(fraction) < 0.10 if measured_force else False,
        "interpretation": "RESIDUAL_IS_NOT_EVIDENCE_OF_NEW_PHYSICS",
        "next_terms_to_subtract": (
            "Maxwell/electrostrictive stress, piezoelectric response, "
            "charge memory, chamber-wall and cable forces, thermal, "
            "acoustic and vibration artifacts"
        ),
    }


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
    """F ~ I*d/mu_i as a conventional subtraction control."""
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
