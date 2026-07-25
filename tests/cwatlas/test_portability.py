"""P31 — Same API on Earth and Mars; cross-body mixing refused."""

from __future__ import annotations

import pytest

from cwatlas import portability as P
from cwatlas.claims import ClaimClass
from cwatlas.mars_frame import EARTH, MARS, HeightConvention


# --- Same addressing API on both bodies ---------------------------------------

def test_same_api_addresses_earth_and_mars():
    e = P.address_on_body(EARTH, 45.0, 10.0, 100.0)
    m = P.address_on_body(MARS, 45.0, 10.0, 100.0)
    assert e.body_id == "EARTH"
    assert m.body_id == "MARS"
    # Same call, same numbers, different declared body -> different Cartesian.
    pe = P.to_bodyfixed(e, EARTH)
    pm = P.to_bodyfixed(m, MARS)
    assert pe.body_id == "EARTH" and pm.body_id == "MARS"
    assert pe.x_m != pytest.approx(pm.x_m)  # different body constants


def test_a_coordinate_carries_its_body():
    c = P.address_on_body(MARS, 12.0, 34.0, 0.0)
    assert c.body_id == "MARS"


# --- Cell-size scale factor between bodies ------------------------------------

def test_cell_scale_factor_is_radius_ratio():
    factor = P.cell_scale_factor(EARTH, MARS)
    assert factor == pytest.approx(
        MARS.semi_major_axis_m / EARTH.semi_major_axis_m)
    # Mars is smaller: the same angular cell is smaller in metres on Mars.
    assert factor < 1.0


def test_scale_cell_size_round_trips_across_bodies():
    size_earth = 1000.0
    size_mars = P.scale_cell_size_m(size_earth, EARTH, MARS)
    back = P.scale_cell_size_m(size_mars, MARS, EARTH)
    assert back == pytest.approx(size_earth)


def test_scale_cell_size_refuses_nonpositive():
    with pytest.raises(P.PortabilityError):
        P.scale_cell_size_m(0.0, EARTH, MARS)


# --- Negative: cross-body mixing is refused -----------------------------------

def test_cross_body_mixing_is_refused():
    e = P.address_on_body(EARTH, 1.0, 2.0, 0.0)
    m = P.address_on_body(MARS, 1.0, 2.0, 0.0)
    with pytest.raises(P.PortabilityError):
        P.refuse_cross_body_mixing(e, m, op="distance")


def test_to_bodyfixed_refuses_body_mismatch():
    e = P.address_on_body(EARTH, 1.0, 2.0, 0.0)
    with pytest.raises(P.PortabilityError):
        P.to_bodyfixed(e, MARS)  # coordinate is EARTH, body is MARS


def test_coordinate_requires_a_body():
    with pytest.raises(P.PortabilityError):
        P.BodyBoundCoordinate(
            body_id="", latitude_deg=0.0, longitude_deg=0.0, height_m=0.0)


# --- Explicit conversion is the only sanctioned crossing ----------------------

def test_explicit_conversion_records_the_crossing():
    e = P.address_on_body(EARTH, 40.0, -75.0, 200.0)
    crossing = P.convert_coordinate_to_body(e, MARS)
    assert crossing.from_body_id == "EARTH"
    assert crossing.to_body_id == "MARS"
    assert crossing.result.body_id == "MARS"
    assert crossing.claim_class is ClaimClass.MATHEMATICAL_TRANSLATION
    # The crossing reuses the numbers deliberately; it is not silent.
    assert crossing.result.latitude_deg == 40.0


def test_height_convention_is_preserved_by_addressing():
    c = P.address_on_body(
        MARS, 0.0, 0.0, 0.0, height_convention=HeightConvention.AREOID)
    assert c.height_convention is HeightConvention.AREOID


# --- Determinism + report -----------------------------------------------------

def test_report_claims_nothing_physical():
    r = P.portability_report()
    assert r["phase_id"] == "P31"
    assert r["cross_body_mixing_refused"] is True
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"


def test_report_is_deterministic():
    assert P.portability_report() == P.portability_report()


def test_import_surface():
    from cwatlas import portability  # noqa: F401
