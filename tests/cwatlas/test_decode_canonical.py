"""P42 -- deterministic canonical decode: one point or explicit invalid."""

from __future__ import annotations

import pytest

from cwatlas import claims
from cwatlas.canonical import CanonicalCoordinate
from cwatlas.decode_canonical import (
    CanonicalDecodeError,
    DecodeStatus,
    GeographicPoint,
    decode_canonical,
    decode_canonical_report,
    encode_canonical,
    refuse_alias_for_canonical,
)


def _vector(lat=45.0, lon=-75.0, h=100.0):
    coord = CanonicalCoordinate(
        body_id="EARTH", frame_id="ITRF2014", epoch="2020.0",
        latitude_deg=lat, longitude_deg=lon, height_m=h)
    return encode_canonical(coord), coord


# --- POWER: a canonical vector decodes to exactly one point -----------------

def test_canonical_vector_decodes_to_exactly_one_point():
    vector, coord = _vector()
    result = decode_canonical(vector)
    assert result.status is DecodeStatus.OK_POINT
    assert result.is_point()
    point = result.require_point()
    assert isinstance(point, GeographicPoint)
    assert point.latitude_deg == pytest.approx(coord.latitude_deg, abs=1e-6)
    assert point.longitude_deg == pytest.approx(coord.longitude_deg, abs=1e-6)
    assert point.crs == "ITRF2014"
    assert point.epoch == "2020.0"
    assert result.claim_class == claims.ClaimClass.CANONICAL_ROUND_TRIP.value


def test_point_carries_crs_and_epoch():
    vector, _ = _vector()
    point = decode_canonical(vector).require_point()
    assert point.crs
    assert point.epoch
    assert point.uncertainty_m >= 0.0


def test_round_trip_multiple_coordinates():
    for lat, lon in ((0.0, 0.0), (-33.9, 18.4), (60.0, 179.9)):
        vector, coord = _vector(lat=lat, lon=lon)
        point = decode_canonical(vector).require_point()
        assert point.latitude_deg == pytest.approx(lat, abs=1e-6)
        assert point.longitude_deg == pytest.approx(lon, abs=1e-6)


# --- Negative: bad checksum / malformed -> explicit invalid, never a guess --

def test_bad_checksum_is_explicit_invalid():
    vector, _ = _vector()
    tampered = vector[:-1] + ("0" if vector[-1] != "0" else "1")
    result = decode_canonical(tampered)
    assert result.status is DecodeStatus.INVALID
    assert result.point is None
    assert result.claim_class == claims.ClaimClass.REFUSAL.value


def test_malformed_vector_is_invalid():
    result = decode_canonical("not-a-canonical-vector")
    assert result.status is DecodeStatus.INVALID
    assert result.point is None


def test_legacy_digit_string_is_invalid_never_alias_set():
    # A nine-digit legacy string is not a canonical vector: INVALID, no aliases.
    result = decode_canonical("123456789")
    assert result.status is DecodeStatus.INVALID
    assert not hasattr(result, "candidates")


def test_require_point_raises_on_invalid():
    result = decode_canonical("garbage")
    with pytest.raises(CanonicalDecodeError):
        result.require_point()


def test_refuse_alias_for_canonical_always_raises():
    with pytest.raises(claims.ClaimError):
        refuse_alias_for_canonical()


def test_result_rejects_inconsistent_point_status():
    with pytest.raises(CanonicalDecodeError):
        from cwatlas.decode_canonical import CanonicalDecodeResult
        CanonicalDecodeResult(
            status=DecodeStatus.OK_POINT, codec_id="CW-GEO-1",
            point=None, reason="x", claim_class="X", receipt_id="r")


def test_geographic_point_requires_crs_and_epoch():
    with pytest.raises(claims.ClaimError):
        GeographicPoint(
            body_id="EARTH", crs="", epoch="", latitude_deg=0.0,
            longitude_deg=0.0, height_m=0.0, shell_state=None,
            codec_id="CW-GEO-1", codec_version="1.0.0", uncertainty_m=0.1)


# --- Determinism -------------------------------------------------------------

def test_decode_is_deterministic_including_receipt():
    vector, _ = _vector()
    a = decode_canonical(vector)
    b = decode_canonical(vector)
    assert a.to_dict() == b.to_dict()
    assert a.receipt_id == b.receipt_id


def test_report_declares_no_geographic_semantics():
    rep = decode_canonical_report()
    assert rep["source_vector_geographic_semantics"] == "NOT_CLAIMED"
    assert rep["claim_class"] == "CANONICAL_ROUND_TRIP"
    assert rep["phase_id"] == "P42"
