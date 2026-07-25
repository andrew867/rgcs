"""P09 -- WGS84 geodetic <-> ECEF: focused, boundary, negative, round-trip."""

from __future__ import annotations

import math

import numpy as np
import pytest

from cwatlas import geodesy as G


# A synthetic sweep of declared coordinates (no private/real locations).
SWEEP = [
    (0.0, 0.0, 0.0),            # equator, prime meridian, on the ellipsoid
    (45.0, 90.0, 1000.0),       # mid-latitude, positive altitude
    (-33.5, 151.25, 58.0),      # southern hemisphere
    (10.0, -75.0, -120.0),      # negative (sub-ellipsoid) height
    (89.999, 179.999, 5000.0),  # near-pole, near-dateline
    (-60.0, -179.999, -400.0),  # southern near-dateline, negative height
]


def test_equator_prime_meridian_is_on_the_a_axis():
    x, y, z = G.geodetic_to_ecef(0.0, 0.0, 0.0)
    assert x == pytest.approx(G.WGS84_A, abs=1e-6)
    assert y == pytest.approx(0.0, abs=1e-6)
    assert z == pytest.approx(0.0, abs=1e-6)


def test_north_pole_z_is_semi_minor_axis():
    x, y, z = G.geodetic_to_ecef(90.0, 0.0, 0.0)
    assert math.hypot(x, y) == pytest.approx(0.0, abs=1e-6)
    assert z == pytest.approx(G.WGS84_B, abs=1e-6)


def test_pole_inverse_recovers_latitude_and_height():
    # A point straight up the +Z axis: latitude 90, height above pole.
    lat, lon, h = G.ecef_to_geodetic(0.0, 0.0, G.WGS84_B + 250.0)
    assert lat == pytest.approx(90.0, abs=1e-9)
    assert h == pytest.approx(250.0, abs=1e-6)


def test_dateline_plus_and_minus_180_are_the_same_point():
    p = G.geodetic_to_ecef(20.0, 180.0, 0.0)
    m = G.geodetic_to_ecef(20.0, -180.0, 0.0)
    assert np.allclose(p, m, atol=1e-6)
    # y is zero on the dateline, x is negative.
    assert p[1] == pytest.approx(0.0, abs=1e-6)
    assert p[0] < 0.0


def test_longitude_is_normalized_to_dateline_positive():
    lat, lon, h = G.ecef_to_geodetic(*G.geodetic_to_ecef(0.0, -180.0, 0.0))
    assert lon == pytest.approx(180.0, abs=1e-9)


@pytest.mark.parametrize("lat,lon,h", SWEEP)
def test_round_trip_geodetic_ecef_geodetic_under_1e_6_m(lat, lon, h):
    x, y, z = G.geodetic_to_ecef(lat, lon, h)
    lat2, lon2, h2 = G.ecef_to_geodetic(x, y, z)
    # Compare in ECEF metres to make the tolerance a true metric distance.
    x2, y2, z2 = G.geodetic_to_ecef(lat2, lon2, h2)
    dist = math.dist((x, y, z), (x2, y2, z2))
    assert dist < 1e-6
    assert h2 == pytest.approx(h, abs=1e-6)


@pytest.mark.parametrize("lat,lon,h", SWEEP)
def test_round_trip_ecef_geodetic_ecef_is_deterministic(lat, lon, h):
    e = G.geodetic_to_ecef(lat, lon, h)
    once = G.ecef_to_geodetic(*e)
    twice = G.ecef_to_geodetic(*e)
    assert once == twice  # deterministic, no wall-clock, no randomness


def test_dataclass_round_trip_preserves_crs():
    gp = G.GeodeticPoint(48.0, 11.0, 520.0)
    ep = G.geodetic_point_to_ecef(gp)
    back = G.ecef_point_to_geodetic(ep)
    assert back.crs == "WGS84"
    assert back.latitude_deg == pytest.approx(gp.latitude_deg, abs=1e-9)
    assert back.longitude_deg == pytest.approx(gp.longitude_deg, abs=1e-9)
    assert back.height_m == pytest.approx(gp.height_m, abs=1e-6)


# -- negative / failing-safe cases ------------------------------------------

def test_latitude_out_of_range_is_rejected():
    with pytest.raises(G.GeodesyError):
        G.geodetic_to_ecef(90.0001, 0.0, 0.0)
    with pytest.raises(G.GeodesyError):
        G.GeodeticPoint(-90.5, 0.0, 0.0)


def test_non_finite_inputs_are_rejected():
    with pytest.raises(G.GeodesyError):
        G.geodetic_to_ecef(float("nan"), 0.0, 0.0)
    with pytest.raises(G.GeodesyError):
        G.ecef_to_geodetic(float("inf"), 0.0, 0.0)


def test_geocentre_is_underdetermined_and_refused():
    with pytest.raises(G.GeodesyError):
        G.ecef_to_geodetic(0.0, 0.0, 0.0)


def test_report_claims_round_trip_and_nothing_physical():
    r = G.geodesy_report()
    assert r["claim_class"] == "CANONICAL_ROUND_TRIP"
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"
