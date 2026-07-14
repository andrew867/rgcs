"""rgcs_core.geometry — facets, frusta, terminations, spiral/cone path,
node coordinates, and the density inverse (RGCS-M.1..M.7, M.30..M.41).

Units: mm / mm^2 / cm^3 / g / deg; see each submodule's docstring.
"""

from .crystal import (CrystalGeometry, polygon_area_mm2, apothem_mm,
                      termination_height_mm, crystal_geometry,
                      solve_diameter_scale_for_mass)
from .spiral import (SpiralGeometry, spiral_pitch_parameter, spiral_curve,
                     spiral_path_length_3d_mm, spiral_metrics)
from .nodes import (metric_center_mm, node_prior_mm, female_to_male_frame_mm,
                    node_positions, node_alignment_factor)
from .angles import GOLDEN_RATIO, angle_audit

__all__ = [
    "CrystalGeometry", "polygon_area_mm2", "apothem_mm",
    "termination_height_mm", "crystal_geometry",
    "solve_diameter_scale_for_mass",
    "SpiralGeometry", "spiral_pitch_parameter", "spiral_curve",
    "spiral_path_length_3d_mm", "spiral_metrics",
    "metric_center_mm", "node_prior_mm", "female_to_male_frame_mm",
    "node_positions", "node_alignment_factor",
    "GOLDEN_RATIO", "angle_audit",
]
