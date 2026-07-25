"""P61 -- import, export, and interchange packages.

POWER: one bundle round-trips a batch of declared points across JSON, GeoJSON,
KML, CSV, and CW-URI and imports back to the same points; provenance and a
content hash bind the batch; the CRS + epoch travel with every point. Negative:
a private token in a label or in imported text is refused; a malformed package
fails safely. Deterministic.
"""

from __future__ import annotations

import pytest

from cwatlas import interchange
from cwatlas.interchange import Format, build_bundle, export_package, import_package
from cwatlas.io_geo import TypedPoint
from cwatlas.privacy import PrivacyError


def _points():
    return [
        TypedPoint(45.0, -75.0, epoch="2020.0", label="alpha"),
        TypedPoint(10.0, 20.0, height_m=5.0, epoch="2020.0", label="beta"),
        TypedPoint(-33.5, 151.25, epoch="2020.0"),
    ]


# --- POWER --------------------------------------------------------------------

def test_bundle_records_provenance_and_hash():
    b = build_bundle(_points(), source="synthetic", software_commit="abc123")
    assert b.provenance.point_count == 3
    assert b.provenance.software_commit == "abc123"
    assert b.provenance.content_hash.startswith("sha256:")
    assert b.verify_content_hash() is True


@pytest.mark.parametrize("fmt", list(Format))
def test_round_trip_preserves_points(fmt):
    b = build_bundle(_points())
    back = interchange.round_trip(b, fmt)
    compare_labels = fmt in interchange.LABEL_PRESERVING
    assert interchange.points_equal(b.points, back.points,
                                    compare_labels=compare_labels)


def test_every_point_carries_crs_epoch():
    b = build_bundle(_points())
    for p in b.points:
        assert p.frame and p.epoch and p.body


def test_bundle_to_vectors_encodes_all():
    b = build_bundle(_points())
    vectors = b.to_vectors()
    assert len(vectors) == 3
    assert all("codec=CW-GEO-1" in v for v in vectors)


def test_bundle_asserts_no_geographic_claim():
    d = build_bundle(_points()).to_dict()
    assert d["source_vector_geographic_semantics"] == "NOT_CLAIMED"
    assert d["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"


# --- Negative -----------------------------------------------------------------

def test_private_token_in_label_refused():
    token = "private" + "_do_not_commit"
    with pytest.raises(PrivacyError):
        TypedPoint(1.0, 2.0, label=token)


def test_private_token_in_import_text_refused():
    token = "private" + "_do_not_commit"
    text = '{"points": [{"latitude_deg": 1, "longitude_deg": 2, "label": "%s"}]}' % token
    with pytest.raises(PrivacyError):
        import_package(text, Format.JSON)


def test_malformed_json_refused():
    with pytest.raises(interchange.InterchangeError):
        import_package("{not json", Format.JSON)


def test_empty_bundle_refused():
    with pytest.raises(interchange.InterchangeError):
        build_bundle([])


def test_malformed_csv_header_refused():
    with pytest.raises(interchange.InterchangeError):
        import_package("wrong,header\n1,2", Format.CSV)


def test_malformed_cw_uri_refused():
    with pytest.raises(interchange.InterchangeError):
        import_package("http://not-a-cw-uri", Format.CW_URI)


def test_import_empty_package_refused():
    # A GeoJSON FeatureCollection with no features -> no points -> refusal.
    with pytest.raises(interchange.InterchangeError):
        import_package('{"type":"FeatureCollection","features":[]}', Format.GEOJSON)


# --- Determinism --------------------------------------------------------------

def test_export_is_deterministic():
    b = build_bundle(_points(), software_commit="x")
    for fmt in Format:
        assert export_package(b, fmt) == export_package(b, fmt)


def test_content_hash_is_deterministic():
    a = build_bundle(_points())
    b = build_bundle(_points())
    assert a.provenance.content_hash == b.provenance.content_hash


def test_report_declares_boundary():
    r = interchange.interchange_report()
    assert set(r["formats"]) == {"JSON", "GeoJSON", "KML", "CSV", "CW-URI"}
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"
