"""P12 — Mars IAU body-fixed frame: round-trip, portability, refusals."""

from __future__ import annotations

import math

import pytest

from cwatlas import mars_frame as MF
from cwatlas.claims import ClaimClass


# --- Body model portability ---------------------------------------------------

def test_earth_and_mars_share_one_api_with_different_constants():
    assert MF.MARS.semi_major_axis_m == 3396190.0
    assert MF.MARS.semi_minor_axis_m == 3376200.0
    assert MF.EARTH.body_id == "EARTH" and MF.MARS.body_id == "MARS"
    # same API, different numbers
    assert MF.MARS.flattening != MF.EARTH.flattening
    assert 0.0 < MF.MARS.eccentricity_sq < 1.0


def test_mars_declares_an_iau_convention():
    # invariant 7: a Mars body-fixed convention must be declared.
    assert "IAU Mars" in MF.MARS.iau_convention
    assert MF.MARS.prime_meridian == "AIRY-0"


def test_a_body_without_a_declared_convention_is_refused():
    with pytest.raises(MF.FrameError):
        MF.BodyModel(
            body_id="X", frame_id="X_BF",
            semi_major_axis_m=1000.0, semi_minor_axis_m=900.0,
            iau_convention="")


def test_body_with_polar_exceeding_equatorial_is_refused():
    with pytest.raises(MF.FrameError):
        MF.BodyModel(
            body_id="X", frame_id="X_BF",
            semi_major_axis_m=900.0, semi_minor_axis_m=1000.0,
            iau_convention="declared")


def test_get_body_refuses_unknown_body():
    assert MF.get_body("MARS") is MF.MARS
    with pytest.raises(MF.FrameError):
        MF.get_body("PLUTO")


# --- Round trip ---------------------------------------------------------------

@pytest.mark.parametrize("body", [MF.EARTH, MF.MARS])
@pytest.mark.parametrize("lat,lon,h", [
    (0.0, 0.0, 0.0),
    (45.0, 90.0, 1000.0),
    (-33.3, -70.6, 500.0),
    (12.5, 179.9, -200.0),
    (89.0, 45.0, 250.0),
])
def test_geodetic_bodyfixed_round_trip(body, lat, lon, h):
    bf = MF.geodetic_to_bodyfixed(body, lat, lon, h)
    gd = MF.bodyfixed_to_geodetic(body, bf.x_m, bf.y_m, bf.z_m)
    assert gd.latitude_deg == pytest.approx(lat, abs=1e-7)
    # longitude wraps; compare via cos/sin to avoid +/-180 aliasing
    assert math.cos(math.radians(gd.longitude_deg)) == pytest.approx(
        math.cos(math.radians(lon)), abs=1e-9)
    assert math.sin(math.radians(gd.longitude_deg)) == pytest.approx(
        math.sin(math.radians(lon)), abs=1e-9)
    assert gd.height_m == pytest.approx(h, abs=1e-4)
    assert gd.body_id == body.body_id


@pytest.mark.parametrize("body", [MF.EARTH, MF.MARS])
def test_pole_round_trip(body):
    bf = MF.geodetic_to_bodyfixed(body, 90.0, 0.0, 100.0)
    gd = MF.bodyfixed_to_geodetic(body, bf.x_m, bf.y_m, bf.z_m)
    assert gd.latitude_deg == pytest.approx(90.0, abs=1e-6)
    assert gd.height_m == pytest.approx(100.0, abs=1e-4)


def test_forward_is_deterministic():
    a = MF.geodetic_to_bodyfixed(MF.MARS, 22.0, 33.0, 44.0)
    b = MF.geodetic_to_bodyfixed(MF.MARS, 22.0, 33.0, 44.0)
    assert (a.x_m, a.y_m, a.z_m) == (b.x_m, b.y_m, b.z_m)


def test_equatorial_surface_point_lies_at_semi_major_radius():
    bf = MF.geodetic_to_bodyfixed(MF.MARS, 0.0, 0.0, 0.0)
    assert bf.x_m == pytest.approx(MF.MARS.semi_major_axis_m, abs=1e-6)
    assert bf.y_m == pytest.approx(0.0, abs=1e-6)
    assert bf.z_m == pytest.approx(0.0, abs=1e-6)


# --- Height convention: areoid vs ellipsoid, declared not assumed -------------

def test_areoid_height_is_refused_without_a_separation_model():
    # feeding a Mars AREOID height into ellipsoid math must refuse, not
    # silently assume zero separation.
    with pytest.raises(MF.FrameError):
        MF.geodetic_to_bodyfixed(
            MF.MARS, 10.0, 20.0, 300.0,
            height_convention=MF.HeightConvention.AREOID)


def test_geoid_height_is_refused_without_a_separation_model():
    with pytest.raises(MF.FrameError):
        MF.geodetic_to_bodyfixed(
            MF.EARTH, 10.0, 20.0, 30.0,
            height_convention=MF.HeightConvention.GEOID)


def test_ellipsoidal_height_is_accepted():
    bf = MF.geodetic_to_bodyfixed(
        MF.MARS, 10.0, 20.0, 300.0,
        height_convention=MF.HeightConvention.ELLIPSOIDAL)
    assert bf.body_id == "MARS"


# --- Invalid input fails safely ----------------------------------------------

def test_out_of_range_latitude_is_refused():
    with pytest.raises(MF.FrameError):
        MF.geodetic_to_bodyfixed(MF.MARS, 91.0, 0.0, 0.0)


def test_non_finite_input_is_refused():
    with pytest.raises(MF.FrameError):
        MF.geodetic_to_bodyfixed(MF.MARS, float("nan"), 0.0, 0.0)
    with pytest.raises(MF.FrameError):
        MF.bodyfixed_to_geodetic(MF.MARS, float("inf"), 0.0, 0.0)


# --- Latitude convention helpers ---------------------------------------------

def test_planetographic_planetocentric_round_trip():
    for lat in (-60.0, -12.0, 0.0, 33.0, 80.0):
        pc = MF.planetographic_to_planetocentric_deg(MF.MARS, lat)
        pg = MF.planetocentric_to_planetographic_deg(MF.MARS, pc)
        assert pg == pytest.approx(lat, abs=1e-9)


def test_planetocentric_differs_from_planetographic_off_equator():
    lat = 45.0
    pc = MF.planetographic_to_planetocentric_deg(MF.MARS, lat)
    assert pc != pytest.approx(lat, abs=1e-6)
    # both zero at the equator
    assert MF.planetographic_to_planetocentric_deg(MF.MARS, 0.0) == pytest.approx(0.0)


# --- Report -------------------------------------------------------------------

def test_report_claims_nothing_physical():
    r = MF.mars_frame_report()
    assert r["phase_id"] == "P12"
    assert r["claim_class"] == ClaimClass.MATHEMATICAL_TRANSLATION.value
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["source_vector_geographic_semantics"] == (
        "SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED")
    assert "MARS" in r["bodies"] and "EARTH" in r["bodies"]
    assert r["verdict"]


def test_import_surface():
    from cwatlas import mars_frame  # noqa: F401
