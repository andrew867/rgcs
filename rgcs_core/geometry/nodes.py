"""Non-metric node coordinate and measurement precedence (RGCS-M.38..M.41).

Units: all coordinates in mm. Frame: x measured from the FEMALE (wide)
apex toward the male (narrow) apex, 0 <= x <= L; conversion to the male
frame is L - x (NOTATION_AND_UNITS.md section 2.6, closes D-01).

Retired estimators are documented, never computed:
* ``geometry_balance_node_mm`` (70.806 mm) had no derivation and is DELETED;
* the WB5 Sheet 13 value 75.7250 mm equals L - x_g (frame conversion of the
  same shaft midpoint), not a separate quantity.
"""

from __future__ import annotations

import math
from typing import Any

from ..provenance import classified, classification_string

__all__ = ["metric_center_mm", "node_prior_mm", "female_to_male_frame_mm",
           "node_positions", "node_alignment_factor"]


@classified("Established", registry=("RGCS-M.38",))
def metric_center_mm(length_mm: float) -> float:
    """Metric center x_m = L/2 (RGCS-M.38)."""
    if not (math.isfinite(length_mm) and length_mm > 0):
        raise ValueError("length_mm must be positive")
    return length_mm / 2.0


@classified("Derived", registry=("RGCS-M.39",), sources=("RG-11",),
            note="a PRIOR only (shaft midpoint of the free-free fundamental); "
                 "JH-001 Source claim says the eye is not the metric center, "
                 "but nothing establishes it is the shaft midpoint either")
def node_prior_mm(length_mm: float, female_height_mm: float,
                  male_height_mm: float) -> float:
    """Geometry node prior x_g = (L + h_f - h_m)/2, female-apex frame
    (RGCS-M.39). Golden: N=5 defaults -> 78.3277 mm; the male-frame
    expression L - x_g reproduces the retired WB5 value 75.7250 mm."""
    for name, v in (("length_mm", length_mm),
                    ("female_height_mm", female_height_mm),
                    ("male_height_mm", male_height_mm)):
        if not (math.isfinite(v) and v > 0):
            raise ValueError(f"{name} must be positive")
    if female_height_mm + male_height_mm >= length_mm:
        raise ValueError("cap heights exceed total length")
    return (length_mm + female_height_mm - male_height_mm) / 2.0


@classified("Established", note="frame conversion x -> L - x (D-01)")
def female_to_male_frame_mm(x_female_mm: float, length_mm: float) -> float:
    """Convert a female-frame coordinate to the male-end frame: L - x."""
    if not (math.isfinite(length_mm) and length_mm > 0):
        raise ValueError("length_mm must be positive")
    if not (0.0 <= x_female_mm <= length_mm):
        raise ValueError("coordinate must lie inside [0, L]")
    return length_mm - x_female_mm


@classified("Derived", registry=("RGCS-M.38", "RGCS-M.39", "RGCS-M.40"),
            sources=("RG-11",),
            note="measured node takes precedence (RGCS-M.40); JSON uses "
                 "null, never NaN (D-03)")
def node_positions(length_mm: float, female_height_mm: float,
                   male_height_mm: float,
                   measured_from_female_mm: float | None = None
                   ) -> dict[str, Any]:
    """Node coordinate summary (female-apex frame): metric center x_m,
    geometry prior x_g, selected node x_* (measured value takes precedence,
    RGCS-M.40) and node fraction c_g = x_*/L."""
    xm = metric_center_mm(length_mm)
    xg = node_prior_mm(length_mm, female_height_mm, male_height_mm)
    if measured_from_female_mm is not None:
        if not (math.isfinite(measured_from_female_mm)
                and 0.0 <= measured_from_female_mm <= length_mm):
            raise ValueError("measured node must lie inside [0, L]")
    selected = (measured_from_female_mm
                if measured_from_female_mm is not None else xg)
    inside_shaft = female_height_mm < selected < length_mm - male_height_mm
    return {
        "frame": "female_apex",
        "metric_center_mm": xm,
        "node_prior_mm": xg,
        "node_prior_male_frame_mm": length_mm - xg,
        "measured_node_mm": measured_from_female_mm,   # None -> JSON null
        "selected_node_mm": selected,
        "selected_source": ("measured" if measured_from_female_mm is not None
                            else "geometry_prior"),
        "node_fraction": selected / length_mm,
        "offset_from_metric_mm": selected - xm,
        "inside_shaft": inside_shaft,
        "classification": classification_string(node_positions),
    }


@classified("Derived", registry=("RGCS-M.41",),
            note="engineering heuristic - not evidence; feeds only the "
                 "merit score S")
def node_alignment_factor(drive_position_mm: float, selected_node_mm: float,
                          sigma_x_mm: float) -> dict[str, float | str]:
    """Node alignment factor N_x = exp(-xi^2), xi = (x_d - x_*)/sigma_x
    (RGCS-M.41). Engineering heuristic - not evidence."""
    if not (math.isfinite(sigma_x_mm) and sigma_x_mm > 0):
        raise ValueError("sigma_x_mm must be positive")
    xi = (drive_position_mm - selected_node_mm) / sigma_x_mm
    return {"xi": xi, "node_alignment_factor": math.exp(-xi * xi),
            "classification":
                classification_string(node_alignment_factor)}
