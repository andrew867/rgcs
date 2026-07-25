"""P33 -- map/globe click to geospatial address: focused, negative, schema."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cwatlas import claims
from cwatlas.map_to_address import (
    GeospatialAddress,
    MapClickError,
    Viewport,
    map_click_to_address,
    map_to_address_report,
    pixel_click_to_address,
)

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "cwatlas" / "schemas"


def _validator():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(
        (SCHEMA_DIR / "geospatial_address.schema.json").read_text("utf-8"))
    return jsonschema.Draft202012Validator(schema)


def _addr(**over):
    base = dict(
        body_id="EARTH", frame_id="ITRF2020", epoch="2020.0",
        latitude_deg=45.0, longitude_deg=-73.5, uncertainty_m=1.0)
    base.update(over)
    return map_click_to_address(**base)


# -- focused ----------------------------------------------------------------

def test_direct_click_builds_address_with_crs_and_epoch():
    a = _addr()
    assert a.body_id == "EARTH"
    assert a.frame_id == "ITRF2020"
    assert a.epoch == "2020.0"
    assert a.coordinate_convention == "ITRF2020"  # explicit echo, not hidden


def test_longitude_normalized_to_dateline_positive():
    a = _addr(longitude_deg=-180.0)
    assert a.longitude_deg == pytest.approx(180.0)


def test_pixel_click_round_trips_through_viewport():
    vp = Viewport(width_px=3600, height_px=1800,
                  lon_min_deg=-180.0, lon_max_deg=180.0,
                  lat_min_deg=-90.0, lat_max_deg=90.0)
    lat, lon = vp.pixel_to_lonlat(1234.0, 567.0)
    px, py = vp.lonlat_to_pixel(lat, lon)
    assert px == pytest.approx(1234.0)
    assert py == pytest.approx(567.0)


def test_pixel_click_centre_is_origin_on_full_globe_viewport():
    vp = Viewport(width_px=1000, height_px=500,
                  lon_min_deg=-180.0, lon_max_deg=180.0,
                  lat_min_deg=-90.0, lat_max_deg=90.0)
    a = pixel_click_to_address(vp, 500, 250, body_id="EARTH",
                               frame_id="WGS84", epoch="2020.0")
    assert a.latitude_deg == pytest.approx(0.0)
    assert a.longitude_deg == pytest.approx(0.0)
    # Uncertainty is computed from the pixel footprint, not a hidden default.
    assert a.uncertainty_m > 0.0


def test_mars_click_is_accepted():
    a = _addr(body_id="MARS", frame_id="IAU_MARS_BODY_FIXED")
    assert a.body_id == "MARS"


# -- negative ---------------------------------------------------------------

def test_missing_crs_is_refused():
    with pytest.raises(claims.ClaimError):
        _addr(frame_id="")


def test_missing_epoch_is_refused():
    with pytest.raises(claims.ClaimError):
        _addr(epoch="")


def test_unknown_body_is_refused():
    with pytest.raises(MapClickError):
        _addr(body_id="PLUTO")


def test_out_of_range_latitude_is_refused():
    with pytest.raises(MapClickError):
        _addr(latitude_deg=91.0)


def test_negative_uncertainty_is_refused():
    with pytest.raises(MapClickError):
        _addr(uncertainty_m=-1.0)


def test_out_of_range_shell_is_refused():
    with pytest.raises(MapClickError):
        _addr(shell_state=9)


def test_pixel_outside_viewport_is_refused():
    vp = Viewport(width_px=100, height_px=100,
                  lon_min_deg=-10.0, lon_max_deg=10.0,
                  lat_min_deg=-10.0, lat_max_deg=10.0)
    with pytest.raises(MapClickError):
        vp.pixel_to_lonlat(101.0, 50.0)


def test_degenerate_viewport_is_refused():
    with pytest.raises(MapClickError):
        Viewport(width_px=100, height_px=100,
                 lon_min_deg=10.0, lon_max_deg=-10.0,
                 lat_min_deg=-10.0, lat_max_deg=10.0)


# -- determinism ------------------------------------------------------------

def test_same_click_gives_identical_address():
    assert _addr().to_dict() == _addr().to_dict()


# -- schema conformance -----------------------------------------------------

def test_address_conforms_to_geospatial_schema():
    validator = _validator()
    validator.validate(_addr().to_dict())
    validator.validate(_addr(body_id="MARS", frame_id="IAU_MARS_BODY_FIXED",
                             height_m=100.0, shell_state=3).to_dict())


# -- report -----------------------------------------------------------------

def test_report_declares_no_geographic_claim():
    r = map_to_address_report()
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"
    assert r["measured_here"] == "nothing"
    assert r["crs_and_epoch_required"] is True
