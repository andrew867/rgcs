"""Display formatting rules (binding requirements from the Agent 04 handoff).

* Ladder/compact outputs are ``UncertainValue`` objects: always render the
  1-sigma interval, never a bare point value.
* ``measured_node_mm`` may be ``None``: render "not measured", never NaN.
* Classification labels map to fixed badge colors.
"""
from __future__ import annotations

import math
from typing import Any

from rgcs_core.uncertainty import UncertainValue

#: Badge colors per docs/SCIENTIFIC_CLASSIFICATION_POLICY.md labels.
CLASSIFICATION_COLORS: dict[str, str] = {
    "Established": "#1e7d32",   # green
    "Derived": "#1258a8",       # blue
    "Hypothesis": "#b26a00",    # amber
    "Source claim": "#8e24aa",  # purple
}

VALID_LABELS = tuple(CLASSIFICATION_COLORS)


def classification_label(text: str) -> str:
    """Extract the bare label from a classification string like
    'Hypothesis H-01 [RGCS-M.13]' or 'Derived [RG-12]'."""
    for label in VALID_LABELS:
        if text.startswith(label):
            return label
    return "Source claim" if "source" in text.lower() else "Derived"


def format_uncertain(value: UncertainValue | dict | float, unit: str = "",
                     digits: int = 4) -> str:
    """Render an UncertainValue as 'mean ± sigma UNIT [lo, hi] (1σ)'.

    Never renders a bare point value for uncertain quantities.
    """
    if isinstance(value, UncertainValue):
        mean, sigma = value.mean, value.sigma
        lo, hi = value.interval(1)
    elif isinstance(value, dict) and "mean" in value:
        mean = value["mean"]
        sigma = value.get("sigma", abs(mean) * value.get("u_rel", 0.0))
        lo = value.get("lo_1sigma", mean - sigma)
        hi = value.get("hi_1sigma", mean + sigma)
    else:  # plain float given by caller that has no uncertainty model
        v = float(value)
        u = f" {unit}" if unit else ""
        return f"{v:.{digits}g}{u}"
    u = f" {unit}" if unit else ""
    return (f"{mean:.{digits}f} ± {sigma:.{digits}f}{u} "
            f"[{lo:.{digits}f}, {hi:.{digits}f}] (1σ)")


def format_node_mm(value: float | None, digits: int = 3) -> str:
    """measured_node_mm may be None: display 'not measured', never NaN."""
    if value is None:
        return "not measured"
    if isinstance(value, float) and math.isnan(value):
        # NaN must never reach the display layer; treat as absent.
        return "not measured"
    return f"{value:.{digits}f} mm"


def format_scalar(value: Any, unit: str = "", digits: int = 6) -> str:
    if value is None:
        return "—"
    if isinstance(value, (int,)) and not isinstance(value, bool):
        return f"{value}{' ' + unit if unit else ''}"
    if isinstance(value, float):
        if math.isnan(value):
            return "—"
        return f"{value:.{digits}g}{' ' + unit if unit else ''}"
    return str(value)
