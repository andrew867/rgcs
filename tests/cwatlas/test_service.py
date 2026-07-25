"""P57 -- framework-agnostic service layer.

POWER: a declared point encodes to a canonical vector and decodes back to the
same point (CW-GEO-1 and CW-HCM-ICO); a raw string yields a legacy alias set; a
batch exports to a verifiable audit bundle. Every result carries CRS + epoch +
claim class. Negative: an unsupported codec, a missing uncertainty, and a
malformed vector all fail safely (a typed refusal, never a crash); a private
token in an export is refused. Deterministic. No web framework is imported.
"""

from __future__ import annotations

import sys

import pytest

from cwatlas import service
from cwatlas.claims import ClaimClass


# --- POWER --------------------------------------------------------------------

def test_encode_carries_crs_epoch_claim_class():
    r = service.encode_point(
        body_id="EARTH", frame_id="CRS84", epoch="2020.0",
        latitude_deg=45.0, longitude_deg=-75.0, uncertainty_m=1.0)
    assert r["codec_id"] == "CW-GEO-1"
    assert r["crs"] == "CRS84"
    assert r["epoch"] == "2020.0"
    assert r["claim_class"] == ClaimClass.CANONICAL_ROUND_TRIP.value
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"
    assert r["vector"]


def test_encode_decode_round_trips_geo1():
    enc = service.encode_point(
        body_id="EARTH", frame_id="CRS84", epoch="2020.0",
        latitude_deg=45.0, longitude_deg=-75.0, uncertainty_m=1.0)
    dec = service.decode_vector(enc["vector"])
    assert dec["status"] == "OK_POINT"
    assert dec["crs"] == "CRS84"
    assert dec["epoch"] == "2020.0"
    assert dec["point"]["latitude_deg"] == pytest.approx(45.0, abs=1e-6)
    assert dec["point"]["longitude_deg"] == pytest.approx(-75.0, abs=1e-6)


def test_encode_decode_round_trips_ico():
    enc = service.encode_point(
        body_id="EARTH", frame_id="CRS84", epoch="2021.5",
        latitude_deg=12.3456, longitude_deg=-98.7654, uncertainty_m=2.0,
        codec="CW-HCM-ICO")
    assert enc["codec_id"] == "CW-HCM-ICO"
    dec = service.decode_vector(enc["vector"])
    assert dec["status"] == "OK_POINT"
    assert dec["codec_id"] == "CW-HCM-ICO"
    assert dec["point"]["latitude_deg"] == pytest.approx(12.3456, abs=1e-6)
    assert dec["point"]["longitude_deg"] == pytest.approx(-98.7654, abs=1e-6)


def test_round_trip_closes():
    r = service.round_trip(
        body_id="EARTH", frame_id="CRS84", epoch="2020.0",
        latitude_deg=-33.87, longitude_deg=151.21, uncertainty_m=1.0)
    assert r["closed"] is True
    assert r["residual_deg"] <= r["tolerance_deg"]
    assert r["claim_class"] == ClaimClass.CANONICAL_ROUND_TRIP.value


def test_legacy_search_returns_alias_set():
    r = service.legacy_search("123456789")
    assert r["status"] == "OK_ALIAS_SET"
    assert r["count"] >= 1
    assert r["claim_class"] == ClaimClass.LEGACY_ALIAS_CANDIDATE.value
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"


def test_export_bundle_is_verifiable():
    from cwatlas import audit_bundle
    points = [
        {"body_id": "EARTH", "frame_id": "CRS84", "epoch": "2020.0",
         "latitude_deg": 1.0, "longitude_deg": 2.0, "uncertainty_m": 1.0},
        {"body_id": "EARTH", "frame_id": "CRS84", "epoch": "2020.0",
         "latitude_deg": 3.0, "longitude_deg": 4.0, "uncertainty_m": 1.0},
    ]
    bundle = service.export_bundle(points)
    assert bundle["receipt_count"] == 2
    assert audit_bundle.verify_bundle(bundle) is True
    assert bundle["source_vector_geographic_semantics"] == "NOT_CLAIMED"


def test_verify_vector_valid_and_invalid():
    enc = service.encode_point(
        body_id="EARTH", frame_id="CRS84", epoch="2020.0",
        latitude_deg=0.0, longitude_deg=0.0, uncertainty_m=1.0)
    good = service.verify_vector(enc["vector"])
    assert good["checksum_ok"] is True and good["valid"] is True
    bad = service.verify_vector("not-a-vector")
    assert bad["checksum_ok"] is False and bad["valid"] is False


# --- Negative -----------------------------------------------------------------

def test_unsupported_codec_refused():
    with pytest.raises(service.ServiceError):
        service.encode_point(
            body_id="EARTH", frame_id="CRS84", epoch="2020.0",
            latitude_deg=0.0, longitude_deg=0.0, uncertainty_m=1.0,
            codec="NOPE")


def test_missing_uncertainty_refused():
    with pytest.raises(service.ServiceError):
        service.encode_point(
            body_id="EARTH", frame_id="CRS84", epoch="2020.0",
            latitude_deg=0.0, longitude_deg=0.0)


def test_missing_epoch_refused():
    with pytest.raises(service.ServiceError):
        service.encode_point(
            body_id="EARTH", frame_id="CRS84", epoch="",
            latitude_deg=0.0, longitude_deg=0.0, uncertainty_m=1.0)


def test_malformed_vector_is_typed_refusal_not_crash():
    for bad in ["", "garbage", "v=1;lat=1", 12345, None,
                "v=1.0.0;codec=UNKNOWN;x=1*cwck1:0000000000000000"]:
        d = service.decode_vector(bad)
        assert d["status"] == "REFUSED"
        assert d["claim_class"] == ClaimClass.REFUSAL.value
        assert d["point"] is None


def test_legacy_search_non_string_is_refusal():
    r = service.legacy_search(999)
    assert r["status"] == "REFUSAL"
    assert r["claim_class"] == ClaimClass.REFUSAL.value


def test_export_refuses_empty_batch():
    with pytest.raises(service.ServiceError):
        service.export_bundle([])


def test_export_refuses_private_token():
    token = "private" + "_do_not_commit"
    # A private token in an epoch field flows into the sealed receipt content.
    points = [{"body_id": "EARTH", "frame_id": "CRS84", "epoch": token,
               "latitude_deg": 1.0, "longitude_deg": 2.0, "uncertainty_m": 1.0}]
    with pytest.raises(service.ServiceError):
        service.export_bundle(points)


# --- Determinism + hygiene ----------------------------------------------------

def test_encode_is_deterministic():
    kw = dict(body_id="EARTH", frame_id="CRS84", epoch="2020.0",
              latitude_deg=45.0, longitude_deg=-75.0, uncertainty_m=1.0)
    assert service.encode_point(**kw) == service.encode_point(**kw)


def test_no_web_framework_imported():
    # The service layer must be framework-agnostic: importing it must not drag
    # in FastAPI/Flask/Starlette.
    for mod in ("fastapi", "flask", "starlette"):
        assert mod not in sys.modules


def test_report_declares_boundary():
    r = service.service_report()
    assert r["framework_agnostic"] is True
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"
    assert set(r["every_result_carries"]) == {"crs", "epoch", "claim_class"}
