"""P18 -- CW-GEO-1 reversible baseline: round-trip (POWER), negative, determinism."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cwatlas import checksums
from cwatlas.canonical import CanonicalCoordinate, CodecStatus
from cwatlas.codec_geo1 import (
    HEIGHT_QUANT_M,
    LAT_QUANT_DEG,
    LON_QUANT_DEG,
    CWGeo1Codec,
    Geo1Error,
)

FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "docs" / "cwatlas" / "fixtures" / "synthetic_round_trip_cases.json"
)


def _fixture_cases():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _coord_from_case(case):
    return CanonicalCoordinate(
        body_id=case["body"], frame_id="ITRF2020", epoch="2020.0",
        latitude_deg=case["lat"], longitude_deg=case["lon"], height_m=0.0)


# -- POWER: round-trip every fixture case within declared quantization -------

@pytest.mark.parametrize("case", _fixture_cases(), ids=lambda c: c["name"])
def test_round_trip_within_declared_quantization(case):
    codec = CWGeo1Codec()
    coord = _coord_from_case(case)
    vector = codec.encode(coord)
    back = codec.decode(vector)
    assert back.latitude_deg == pytest.approx(coord.latitude_deg, abs=LAT_QUANT_DEG)
    assert back.longitude_deg == pytest.approx(coord.longitude_deg, abs=LON_QUANT_DEG)
    assert back.height_m == pytest.approx(coord.height_m, abs=HEIGHT_QUANT_M)


@pytest.mark.parametrize("case", _fixture_cases(), ids=lambda c: c["name"])
def test_encode_is_idempotent_on_decoded_coordinate(case):
    codec = CWGeo1Codec()
    coord = _coord_from_case(case)
    vector = codec.encode(coord)
    # encode(decode(vector)) == vector byte-for-byte (exact within quantization).
    assert codec.encode(codec.decode(vector)) == vector


def test_vector_is_versioned_and_checksummed():
    codec = CWGeo1Codec()
    vector = codec.encode(_coord_from_case(_fixture_cases()[0]))
    assert checksums.verify_vector(vector)
    codec_id, version = checksums.parse_codec_version(vector)
    assert codec_id == "CW-GEO-1"
    assert version == "1.0.0"


def test_height_and_shell_round_trip():
    codec = CWGeo1Codec()
    coord = CanonicalCoordinate(
        body_id="EARTH", frame_id="ITRF2020", epoch="2020.0",
        latitude_deg=29.979235, longitude_deg=31.134202, height_m=138.5,
        shell_state=4)
    back = codec.decode(codec.encode(coord))
    assert back.height_m == pytest.approx(138.5, abs=HEIGHT_QUANT_M)
    assert back.shell_state == 4


def test_encode_address_carries_checksum_and_residual():
    codec = CWGeo1Codec()
    coord = _coord_from_case(_fixture_cases()[0])
    addr = codec.encode_address(coord)
    assert addr.verify_checksum()
    assert addr.codec_id == "CW-GEO-1"
    assert addr.local_residual is not None
    # Residual is sub-quantization.
    assert abs(addr.local_residual[0]) <= LAT_QUANT_DEG
    assert addr.frame_id == "ITRF2020" and addr.epoch == "2020.0"


# -- typed result -----------------------------------------------------------

def test_decode_result_ok_point():
    codec = CWGeo1Codec()
    vector = codec.encode(_coord_from_case(_fixture_cases()[0]))
    result = codec.decode_result(vector, receipt_id="rcpt-geo1-0001")
    assert result.status is CodecStatus.OK_POINT
    assert len(result.candidates) == 1


# -- negative: fail safely --------------------------------------------------

def test_corrupted_vector_is_refused():
    codec = CWGeo1Codec()
    vector = codec.encode(_coord_from_case(_fixture_cases()[0]))
    corrupted = vector.replace("lat=", "lat=9", 1)
    with pytest.raises(Geo1Error):
        codec.decode(corrupted)
    # And the typed path returns INVALID rather than raising.
    result = codec.decode_result(corrupted, receipt_id="rcpt-bad")
    assert result.status is CodecStatus.INVALID


def test_version_mismatch_is_refused():
    codec = CWGeo1Codec()
    coord = _coord_from_case(_fixture_cases()[0])
    payload, _tokens = codec._payload(coord)
    stale_payload = payload.replace("v=1.0.0", "v=2.0.0", 1)
    stale_vector = checksums.append_checksum(stale_payload)
    with pytest.raises(Geo1Error):
        codec.decode(stale_vector)


def test_encode_rejects_non_coordinate():
    codec = CWGeo1Codec()
    with pytest.raises(Geo1Error):
        codec.encode("not a coordinate")


def test_decode_rejects_empty():
    codec = CWGeo1Codec()
    with pytest.raises(Geo1Error):
        codec.decode("")


# -- determinism + report ---------------------------------------------------

def test_encode_is_deterministic():
    codec = CWGeo1Codec()
    coord = _coord_from_case(_fixture_cases()[0])
    assert codec.encode(coord) == codec.encode(coord)


def test_report_claims_round_trip_and_nothing_physical():
    r = CWGeo1Codec and __import__(
        "cwatlas.codec_geo1", fromlist=["codec_geo1_report"]).codec_geo1_report()
    assert r["claim_class"] == "CANONICAL_ROUND_TRIP"
    assert r["independent_of_source_vectors"] is True
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"
