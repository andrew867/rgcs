"""P32 — Error regions: area scales with sigma; invented precision refused."""

from __future__ import annotations

import math

import pytest

from cwatlas import uncertainty as U
from cwatlas.claims import ClaimClass, ClaimError


CENTER = (45.0, 10.0)


# --- POWER: region area scales with sigma -------------------------------------

def test_circle_area_scales_with_sigma_squared():
    r1 = U.propagate_circle(CENTER, input_sigma_m=10.0, quantization_m=0.0,
                            cell_size_m=1.0)
    r2 = U.propagate_circle(CENTER, input_sigma_m=20.0, quantization_m=0.0,
                            cell_size_m=1.0)
    assert r2.area_m2 > r1.area_m2
    # Doubling sigma quadruples the area (area ~ r^2 ~ sigma^2).
    assert r2.area_m2 == pytest.approx(4.0 * r1.area_m2, rel=1e-9)


def test_larger_sigma_gives_larger_search_space():
    r1 = U.propagate_circle(CENTER, 10.0, 0.0, cell_size_m=5.0)
    r2 = U.propagate_circle(CENTER, 40.0, 0.0, cell_size_m=5.0)
    assert r2.search_space_count > r1.search_space_count


def test_quantization_widens_the_region():
    no_q = U.propagate_circle(CENTER, 10.0, quantization_m=0.0, cell_size_m=1.0)
    with_q = U.propagate_circle(CENTER, 10.0, quantization_m=50.0, cell_size_m=1.0)
    assert with_q.combined_sigma_m > no_q.combined_sigma_m
    assert with_q.area_m2 > no_q.area_m2


def test_combined_sigma_is_quadrature():
    sigma = U.combine_sigma(30.0, quantization_m=math.sqrt(12.0))
    # quant sigma = sqrt(12)/sqrt(12) = 1 -> hypot(30, 1)
    assert sigma == pytest.approx(math.hypot(30.0, 1.0))


# --- Ellipse and cell polygon -------------------------------------------------

def test_ellipse_area_is_pi_a_b():
    r = U.propagate_ellipse(CENTER, sigma_major_m=20.0, sigma_minor_m=10.0,
                            orientation_deg=30.0, quantization_m=0.0,
                            cell_size_m=1.0, k_sigma=1.0)
    assert r.kind is U.RegionKind.ELLIPSE
    assert r.area_m2 == pytest.approx(math.pi * 20.0 * 10.0)
    assert r.orientation_deg == 30.0


def test_cell_polygon_has_four_vertices_and_cell_area():
    r = U.cell_polygon(CENTER, cell_size_m=100.0)
    assert r.kind is U.RegionKind.CELL_POLYGON
    assert len(r.vertices_m) == 4
    assert r.area_m2 == pytest.approx(100.0 * 100.0)
    assert r.search_space_count == 1


# --- Negative: invented precision is refused ----------------------------------

def test_point_region_without_justification_is_refused():
    # Zero sigma and zero quantization -> zero-area region -> invented precision.
    with pytest.raises(ClaimError):
        U.propagate_circle(CENTER, input_sigma_m=0.0, quantization_m=0.0,
                           cell_size_m=1.0)


def test_point_region_allowed_only_with_justification():
    r = U.propagate_circle(CENTER, 0.0, 0.0, cell_size_m=1.0,
                           justification="surveyed benchmark, sub-mm control")
    assert r.area_m2 == 0.0
    assert r.justification


def test_refuse_invented_precision_helper_raises():
    with pytest.raises(ClaimError):
        U.refuse_invented_precision()


def test_negative_sigma_is_refused():
    with pytest.raises(U.UncertaintyError):
        U.combine_sigma(-1.0, 0.0)


def test_nonpositive_cell_size_refused():
    with pytest.raises(U.UncertaintyError):
        U.propagate_circle(CENTER, 10.0, 0.0, cell_size_m=0.0)


def test_out_of_range_center_latitude_refused():
    with pytest.raises(U.UncertaintyError):
        U.propagate_circle((91.0, 0.0), 10.0, 0.0, cell_size_m=1.0)


# --- Determinism + report -----------------------------------------------------

def test_regions_are_deterministic():
    a = U.propagate_circle(CENTER, 12.0, 3.0, cell_size_m=2.0)
    b = U.propagate_circle(CENTER, 12.0, 3.0, cell_size_m=2.0)
    assert a == b


def test_report_claims_nothing_physical():
    r = U.uncertainty_report()
    assert r["phase_id"] == "P32"
    assert r["invented_precision_refused"] is True
    assert r["claim_class"] == ClaimClass.MATHEMATICAL_TRANSLATION.value
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"


def test_import_surface():
    from cwatlas import uncertainty  # noqa: F401
