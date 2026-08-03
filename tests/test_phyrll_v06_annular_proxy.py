"""Brown annular proxy -- symmetry, displacement, mask, and the no-force rule."""

from __future__ import annotations

import pytest

from rgcs_phyrll_v06 import brown_annular_proxy as B
from rgcs_phyrll_v06 import ring37 as R

# One small deterministic solve shared across tests (n=31 keeps it fast).
GRID_N, ITERS = 31, 400


@pytest.fixture(scope="module")
def comparison():
    return B.compare_configurations(
        n=GRID_N, outer_r=12.0, inner_r=3.0, displacement=4.0,
        cell_mask=R.mask_with_blanks([0, 1, 2, 3]), iters=ITERS)


def test_centered_configuration_is_symmetric(comparison):
    assert comparison["centered_symmetric"]["asymmetry_scalar"] < 1e-3


def test_off_center_breaks_symmetry_measurably(comparison):
    assert comparison["off_center_inner"]["asymmetry_scalar"] > 0.05
    assert comparison["comparison"]["centered_lt_offcenter"] is True


def test_mask_displacement_is_weaker_than_physical_displacement(comparison):
    assert (comparison["masked_37_cells"]["asymmetry_scalar"]
            < comparison["off_center_inner"]["asymmetry_scalar"])


def test_off_center_direction_follows_the_displacement_axis(comparison):
    d = comparison["off_center_inner"]["direction_deg"]
    assert min(d, 360 - d) < 15.0     # displacement is along +x (0 deg)


def test_no_output_claims_a_force(comparison):
    for k in ("centered_symmetric", "off_center_inner", "masked_37_cells"):
        assert comparison[k]["is_a_force"] is False


def test_module_exposes_no_force_function():
    """By construction: no public name computes thrust or force."""
    for name in dir(B):
        if not name.startswith("_"):
            assert "force" not in name.lower()
            assert "thrust" not in name.lower()


def test_electrode_potentials_are_held_fixed():
    v = B.solve_potential(21, 8.0, 2.0, 1.0, -1.0, iters=200)
    c = 10
    assert v[c][c] == -1.0            # centre of the inner disc
    flat = [x for row in v for x in row]
    assert max(flat) <= 1.0 and min(flat) >= -1.0   # maximum principle
