from __future__ import annotations

from fractions import Fraction

import pytest

from rgcs_ardk.geometry import AnnularGeometry
from rgcs_ardk.params import LOCKS, load_locked_parameters


def test_parameter_files_reproduce_all_core_locks():
    params = load_locked_parameters()
    assert params == LOCKS
    assert params.sector_count == 37
    assert params.active_count == 33
    assert params.active_floor >= 0.5
    assert params.carrier_hz == 1_683_456
    assert params.envelope_hz == 4_096
    assert params.outer_diameter_mm == 288.0
    assert params.inner_diameter_mm == 188.0
    assert params.mean_radius_mm == 119.0
    assert params.publication_hold is True


def test_exact_pitch_and_ratio_are_rational():
    geometry = AnnularGeometry()
    assert geometry.pitch_deg_exact == Fraction(360, 37)
    assert LOCKS.inner_outer_ratio == Fraction(47, 72)
    assert geometry.pitch_deg == pytest.approx(360 / 37, abs=1e-15)


def test_geometry_has_exactly_37_deterministic_sector_polygons():
    geometry = AnnularGeometry()
    first = geometry.sector_ring(110.0, 128.0)
    second = geometry.sector_ring(110.0, 128.0)
    assert first == second
    assert len(first) == 37
    assert all(len(sector.points) == 10 for sector in first)


def test_stationary_sensor_geometry_is_complete():
    geometry = AnnularGeometry()
    assert len(geometry.sector_pickups()) == 37
    assert len(geometry.compass_pickups()) == 8
    assert len(geometry.mounting_holes()) == 4
    assert geometry.as_dict()["mechanical_rotation"] is False


@pytest.mark.parametrize("index", [-1, 37])
def test_sector_index_out_of_range_refused(index):
    with pytest.raises(ValueError, match="out of range"):
        AnnularGeometry().sector_center(index)
