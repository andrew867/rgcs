"""Conventional force firewall, v0.7 -- the six-term decomposition.

    F_measured = F_charged_fluid
               + F_grad_epsilon
               + F_electrostriction
               + F_Maxwell
               + F_boundaries
               + F_residual

with the residual quotable ONLY when every required control test is
present. A missing control does not shrink the residual; it voids it.

Reuses the public conventional-subtraction arithmetic from
``rgcs_phyrll_v06.force_firewall`` -- one implementation, several lanes.
"""

from __future__ import annotations

import math

from rgcs_phyrll_v06.force_firewall import (even_odd_decomposition,  # noqa: F401
                                            ehd_drift_force,
                                            harmonic_coefficients)

#: The six conventional terms, in the declared order.
TERMS = ("F_charged_fluid", "F_grad_epsilon", "F_electrostriction",
         "F_Maxwell", "F_boundaries")

#: Controls that must exist before any residual may be quoted.
REQUIRED_CONTROLS = ("polarity_reversal", "pressure_gas_variation",
                     "thermal", "vibration", "electrostatic_attraction",
                     "ion_wind", "cable_forces")


def decompose(f_measured_N: float, terms_N: dict,
              controls: dict) -> dict:
    """Close the six-term budget, or refuse to quote a residual.

    ``terms_N`` supplies the five conventional terms (NaN = unmeasured);
    ``controls`` maps each required control test to its receipt (any
    truthy record). The residual is the sixth term, and it exists only
    when the other five are numbers and all controls are present.
    """
    missing_terms = [t for t in TERMS
                     if t not in terms_N or _is_nan(terms_N[t])]
    missing_controls = [c for c in REQUIRED_CONTROLS
                        if not controls.get(c)]
    quotable = not missing_terms and not missing_controls
    conventional_sum = (sum(terms_N[t] for t in TERMS)
                        if not missing_terms else float("nan"))
    residual = (f_measured_N - conventional_sum
                if quotable else float("nan"))
    return {
        "F_measured_N": f_measured_N,
        "conventional_sum_N": conventional_sum,
        "F_residual_N": residual,
        "residual_quotable": quotable,
        "missing_terms": missing_terms,
        "missing_controls": missing_controls,
        "interpretation": "RESIDUAL_IS_NOT_EVIDENCE_OF_NEW_PHYSICS",
        "claim": "BENCH_REQUIRED",
    }


def control_checklist() -> list:
    """The bench checklist, one row per required control."""
    detail = {
        "polarity_reversal": "repeat at -V; even/odd split via the "
                             "audited decomposition",
        "pressure_gas_variation": "vacuum + at least two gas pressures; "
                                  "an ion-wind force dies with the medium",
        "thermal": "thermal ramp with drive off; IR map under drive",
        "vibration": "accelerometer + contact mic during every run",
        "electrostatic_attraction": "grounded-shroud comparison run",
        "ion_wind": "airflow measurement + reversed-polarity comparison",
        "cable_forces": "cable-drape permutations and force-null check",
    }
    return [{"control": c, "protocol": detail[c],
             "claim": "BENCH_REQUIRED"} for c in REQUIRED_CONTROLS]


def _is_nan(x) -> bool:
    try:
        return math.isnan(float(x))
    except (TypeError, ValueError):
        return True


__all__ = ["TERMS", "REQUIRED_CONTROLS", "decompose", "control_checklist",
           "even_odd_decomposition", "harmonic_coefficients",
           "ehd_drift_force"]
