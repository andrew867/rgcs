"""R12 — quaternary triangular refinement on the frozen icosahedron.

Every test can fail: the cell counts are asserted against literal
integers, the address round trip against the exact inverse, the areas
against a strictly positive spread, the completeness against 4*pi, and
the solid against object identity with r11.earthface."""

from __future__ import annotations

import math

import pytest

from r12 import icosarefine as R
from r11.earthface import CANONICAL_ICOSAHEDRON


# --- cell counts, exactly ----------------------------------------------

def test_four_to_the_eleven_is_4194304():
    assert 4 ** 11 == 4194304
    assert R.cells_per_face(11) == 4194304


def test_total_cells_at_level_eleven():
    assert 20 * 4 ** 11 == 83886080
    assert R.total_cells(11) == 83886080


def test_cells_quadruple_each_level():
    for level in range(0, 8):
        assert R.cells_per_face(level) == 4 ** level
        assert R.total_cells(level) == 20 * 4 ** level


# --- the address budget fits 27 bits with stated slack -----------------

def test_capacity_fits_27_bits_with_slack():
    budget = R.address_budget(11)
    assert R.ADDRESS_BITS == 27
    assert budget["address_capacity"] == 2 ** 27 == 134217728
    assert budget["total_cells"] == 83886080
    assert budget["budget_sufficient"] is True
    assert budget["slack_codes"] == 134217728 - 83886080 == 50331648


def test_path_bits_hold_exactly_one_face_at_L11():
    budget = R.address_budget(11)
    assert budget["path_capacity"] == 2 ** 22 == 4194304
    assert budget["cells_per_face"] == 2 ** 22


# --- (face, path) address round trip -----------------------------------

def test_cell_address_round_trip_samples():
    for face in range(0, 20, 3):
        for base in (0, 1, 2, 3):
            path = tuple((face + base + k) % 4 for k in range(11))
            addr = R.cell_address(face, path)
            assert R.address_to_cell(addr) == (face, path)


def test_cell_address_bounds():
    lo = R.cell_address(0, (0,) * 11)
    hi = R.cell_address(19, (3,) * 11)
    assert lo == 0
    assert hi == 20 * 4 ** 11 - 1
    assert R.address_to_cell(hi) == (19, (3,) * 11)


def test_cell_address_rejects_bad_path():
    with pytest.raises(R.IcosaRefineError):
        R.cell_address(0, (0,) * 10)              # too short
    with pytest.raises(R.IcosaRefineError):
        R.cell_address(0, (4,) + (0,) * 10)       # 4 is out of range
    with pytest.raises(R.IcosaRefineError):
        R.cell_address(20, (0,) * 11)             # face out of range


def test_address_to_cell_rejects_out_of_range():
    with pytest.raises(R.IcosaRefineError):
        R.address_to_cell(20 * 4 ** 11)
    with pytest.raises(R.IcosaRefineError):
        R.address_to_cell(-1)


# --- areas are UNEQUAL -------------------------------------------------

def test_areas_are_unequal_from_level_one():
    for level in (1, 2, 3):
        spread = R.area_spread(level)
        assert spread["spread"] > 0.0
        assert spread["is_equal_area"] is False
        assert spread["max_over_min"] > 1.0


def test_cell_area_is_not_the_equal_area_value():
    # The center cell (path all 3s) and a corner cell (path all 0s) at a
    # shallow level differ, and neither equals 4*pi/total.
    level = 2
    equal = 4.0 * math.pi / R.total_cells(level)
    corner = R.cell_area_spherical(0, (0, 0))
    center = R.cell_area_spherical(0, (3, 3))
    assert abs(corner - center) > 1e-6
    assert abs(center - equal) > 1e-6


def test_refuse_equal_area_assumption_raises():
    with pytest.raises(R.IcosaRefineError):
        R.refuse_equal_area_assumption()
    with pytest.raises(R.IcosaRefineError):
        R.refuse_equal_area_assumption(11)


# --- POWER: total solid angle sums to 4*pi -----------------------------

def test_total_solid_angle_is_four_pi():
    for level in (0, 1, 2, 3):
        result = R.total_solid_angle(level)
        assert result["complete"] is True
        assert abs(result["total_solid_angle"] - 4.0 * math.pi) < 1e-9


def test_solid_angle_completeness_can_fail_on_a_subset():
    """A subset of cells does NOT cover 4*pi -- the check is not trivial."""
    areas = R.cell_areas(2)
    partial = math.fsum(areas[:-1])          # drop one cell
    assert abs(partial - 4.0 * math.pi) > 1e-6


# --- identity with r11.earthface ---------------------------------------

def test_icosahedron_is_the_same_object():
    assert R.ICOSAHEDRON is CANONICAL_ICOSAHEDRON
    assert R.assert_same_icosahedron() is True


def test_refuse_a_rebuilt_icosahedron():
    from r11.earthface import _build_canonical_icosahedron
    fresh = _build_canonical_icosahedron()
    assert fresh is not CANONICAL_ICOSAHEDRON
    with pytest.raises(R.IcosaRefineError):
        R.assert_same_icosahedron(fresh)


# --- enumeration guard -------------------------------------------------

def test_enumeration_refused_at_deep_levels():
    with pytest.raises(R.IcosaRefineError):
        R.area_spread(11)          # would expand 83M cells


# --- report ------------------------------------------------------------

def test_report_shape_and_verdict():
    rep = R.icosarefine_report()
    assert rep["verdict"] == "QUATERNARY_REFINEMENT_GEOMETRY_EXACT"
    assert rep["measured_here"] == "nothing"
    assert rep["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert rep["claim_class"] in {c.value for c in R.ClaimClass}
    assert rep["same_icosahedron_as_r11_earthface"] is True
    assert rep["cells_per_face_L11"] == 4194304
    assert rep["total_cells_L11"] == 83886080
    assert rep["total_solid_angle"]["complete"] is True
    assert rep["area_spread"]["spread"] > 0.0
    assert "what_this_does_not_say" in rep


def test_no_private_content_in_module():
    import r12.icosarefine as mod
    text = open(mod.__file__, encoding="utf-8").read().lower()
    for bad in ("c:\\users", "private_do_not_commit", "andrew"):
        assert bad not in text
