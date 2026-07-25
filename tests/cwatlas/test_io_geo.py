"""P38 -- GeoJSON/KML/CSV import-export: round-trip, malformed refused, privacy."""

from __future__ import annotations

import json

import pytest

from cwatlas import io_geo
from cwatlas.claims import ClaimClass
from cwatlas.privacy import PrivacyError

POINTS = [
    io_geo.TypedPoint(51.178882, -1.826215, label="synthetic-a"),
    io_geo.TypedPoint(29.979235, 31.134202, height_m=60.0),
    io_geo.TypedPoint(0.0, 0.0),
    io_geo.TypedPoint(10.0, -179.99999),
]


# --- GeoJSON round-trip -----------------------------------------------------

def test_geojson_round_trip_points():
    gj = io_geo.to_geojson(POINTS, as_text=True)
    back = io_geo.parse_geojson(gj)
    assert len(back) == len(POINTS)
    for a, b in zip(POINTS, back):
        assert b.latitude_deg == pytest.approx(a.latitude_deg)
        assert b.longitude_deg == pytest.approx(a.longitude_deg)
        assert b.height_m == pytest.approx(a.height_m)


def test_geojson_carries_crs_and_epoch():
    fc = io_geo.to_geojson(POINTS)
    props = fc["features"][0]["properties"]
    assert props["frame"] == io_geo.DEFAULT_FRAME
    assert props["body"] == io_geo.DEFAULT_BODY
    assert "epoch" in props


def test_geojson_axis_order_is_lon_lat():
    fc = io_geo.to_geojson([io_geo.TypedPoint(12.0, 34.0)])
    coords = fc["features"][0]["geometry"]["coordinates"]
    assert coords[0] == pytest.approx(34.0)  # lon first
    assert coords[1] == pytest.approx(12.0)  # lat second


# --- KML round-trip ---------------------------------------------------------

def test_kml_round_trip_points():
    kml = io_geo.to_kml(POINTS)
    back = io_geo.parse_kml(kml)
    assert len(back) == len(POINTS)
    for a, b in zip(POINTS, back):
        assert b.latitude_deg == pytest.approx(a.latitude_deg)
        assert b.longitude_deg == pytest.approx(a.longitude_deg)


def test_kml_parses_without_namespace():
    kml = ("<kml><Document><Placemark><Point>"
           "<coordinates>10.5,20.25,3.0</coordinates>"
           "</Point></Placemark></Document></kml>")
    pts = io_geo.parse_kml(kml)
    assert len(pts) == 1
    assert pts[0].longitude_deg == pytest.approx(10.5)
    assert pts[0].latitude_deg == pytest.approx(20.25)
    assert pts[0].height_m == pytest.approx(3.0)


# --- CSV --------------------------------------------------------------------

def test_csv_header_and_rows():
    csv_text = io_geo.to_csv(POINTS)
    lines = csv_text.splitlines()
    assert lines[0] == ",".join(io_geo.CSV_HEADER)
    assert len(lines) == 1 + len(POINTS)


# --- CW vector encoding -----------------------------------------------------

def test_points_to_vectors_preserves_order_and_count():
    vectors = io_geo.points_to_vectors(POINTS)
    assert len(vectors) == len(POINTS)
    assert all(isinstance(v, str) and "CW-GEO-1" in v for v in vectors)


def test_determinism_same_output_twice():
    assert io_geo.to_geojson(POINTS, as_text=True) == \
        io_geo.to_geojson(POINTS, as_text=True)
    assert io_geo.points_to_vectors(POINTS) == io_geo.points_to_vectors(POINTS)


# --- negative: malformed refused --------------------------------------------

def test_malformed_json_refused():
    with pytest.raises(io_geo.GeoIoError):
        io_geo.parse_geojson("{not valid json")


def test_non_feature_collection_refused():
    with pytest.raises(io_geo.GeoIoError):
        io_geo.parse_geojson(json.dumps({"type": "Point", "coordinates": [0, 0]}))


def test_non_point_geometry_refused():
    fc = {"type": "FeatureCollection", "features": [{
        "type": "Feature",
        "geometry": {"type": "LineString", "coordinates": [[0, 0], [1, 1]]},
        "properties": {}}]}
    with pytest.raises(io_geo.GeoIoError):
        io_geo.parse_geojson(json.dumps(fc))


def test_missing_coordinates_refused():
    fc = {"type": "FeatureCollection", "features": [{
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [0]},
        "properties": {}}]}
    with pytest.raises(io_geo.GeoIoError):
        io_geo.parse_geojson(json.dumps(fc))


def test_out_of_range_latitude_refused():
    with pytest.raises(io_geo.GeoIoError):
        io_geo.TypedPoint(120.0, 0.0)


def test_non_finite_coordinate_refused():
    with pytest.raises(io_geo.GeoIoError):
        io_geo.TypedPoint(float("nan"), 0.0)


def test_malformed_kml_refused():
    with pytest.raises(io_geo.GeoIoError):
        io_geo.parse_kml("<kml><Document><Placemark></Placemark>")


def test_kml_placemark_without_point_refused():
    kml = "<kml><Document><Placemark><name>x</name></Placemark></Document></kml>"
    with pytest.raises(io_geo.GeoIoError):
        io_geo.parse_kml(kml)


# --- privacy ----------------------------------------------------------------

def test_private_token_in_label_refused():
    with pytest.raises(PrivacyError):
        io_geo.TypedPoint(0.0, 0.0, label="see C:\\Users\\someone")


# --- governance report ------------------------------------------------------

def test_report_shape():
    r = io_geo.io_geo_report()
    assert r["claim_class"] == ClaimClass.MATHEMATICAL_TRANSLATION.value
    assert r["measured_here"] == "nothing"
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"
    assert r["crs_epoch_carried"] is True
