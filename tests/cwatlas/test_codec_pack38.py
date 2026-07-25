"""P20 — CW-PACK38-1: round-trip, overflow refusal, determinism, schema."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cwatlas import claims
from cwatlas import codec_pack38 as C

SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "cwatlas" / "schemas" / "codec_result.schema.json"
)


def _sample_cases():
    """A deterministic spread of (header, (f0, f1, f2)) cases."""
    headers = [0, 1, 2, 3]
    field_vals = [0, 1, 2047, 2048, 4094, C.FIELD_MAX]
    cases = []
    for h in headers:
        for i, a in enumerate(field_vals):
            b = field_vals[(i + 2) % len(field_vals)]
            c = field_vals[(i + 4) % len(field_vals)]
            cases.append((h, (a, b, c)))
    return cases


def test_bit_layout_constants():
    assert C.HEADER_BITS == 2
    assert C.FIELD_BITS == 12
    assert C.NUM_FIELDS == 3
    assert C.TOTAL_BITS == 38
    assert C.HEADER_MAX == 3
    assert C.FIELD_MAX == 4095


@pytest.mark.parametrize("header,fields", _sample_cases())
def test_power_round_trip(header, fields):
    word = C.encode(header, fields)
    back = C.decode(word.packed)
    assert back.header == header
    assert back.fields == tuple(fields)
    assert back.packed == word.packed


def test_packed_word_composition():
    word = C.encode(3, (C.FIELD_MAX, C.FIELD_MAX, C.FIELD_MAX))
    expected = (3 << 36) | (4095 << 24) | (4095 << 12) | 4095
    assert word.packed == expected
    assert word.packed == C.PACKED_MAX


def test_fields_are_ordered_most_significant_first():
    word = C.encode(0, (1, 2, 3))
    assert word.packed == (1 << 24) | (2 << 12) | 3
    assert C.decode(word.packed).fields == (1, 2, 3)


def test_header_overflow_refused_not_truncated():
    with pytest.raises(ValueError):
        C.encode(C.HEADER_MAX + 1, (0, 0, 0))


def test_field_overflow_refused_not_truncated():
    with pytest.raises(ValueError):
        C.encode(0, (C.FIELD_MAX + 1, 0, 0))
    with pytest.raises(ValueError):
        C.encode(0, (0, C.FIELD_MAX + 1, 0))
    with pytest.raises(ValueError):
        C.encode(0, (0, 0, C.FIELD_MAX + 1))


def test_wrong_field_count_refused():
    with pytest.raises(ValueError):
        C.encode(0, (1, 2))
    with pytest.raises(ValueError):
        C.encode(0, (1, 2, 3, 4))


def test_negative_values_refused():
    with pytest.raises(ValueError):
        C.encode(-1, (0, 0, 0))
    with pytest.raises(ValueError):
        C.encode(0, (-1, 0, 0))


def test_bool_and_nonint_refused():
    with pytest.raises(ValueError):
        C.encode(True, (0, 0, 0))
    with pytest.raises(ValueError):
        C.encode(0, (1.5, 0, 0))


def test_decode_out_of_range_refused():
    with pytest.raises(ValueError):
        C.decode(C.PACKED_MAX + 1)
    with pytest.raises(ValueError):
        C.decode(-1)


def test_determinism():
    a = C.encode(2, (11, 22, 33))
    b = C.encode(2, (11, 22, 33))
    assert a == b
    assert C.to_codec_result(a) == C.to_codec_result(b)


def test_not_a_geographic_decode_is_refused():
    with pytest.raises(claims.ClaimError):
        C.refuse_as_geographic()


def test_codec_result_validates_against_schema():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    for header, fields in _sample_cases():
        result = C.to_codec_result(C.encode(header, fields))
        jsonschema.validate(instance=result, schema=schema)
        assert result["status"] == "NO_UNIQUE_GEOGRAPHIC_DECODE"
        assert result["codec_id"] == "CW-PACK38-1"


def test_codec_result_never_forces_a_pin():
    result = C.to_codec_result(C.encode(1, (100, 200, 300)))
    assert result["status"] != "OK_POINT"
    for cand in result["candidates"]:
        assert cand["claim_class"] == "MATHEMATICAL_TRANSLATION"


def test_report_claims_nothing_geographic():
    r = C.codec_pack38_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"
    assert r["claim_class"] == "MATHEMATICAL_TRANSLATION"
    assert r["reversible"] is True
    assert r["overflow_policy"] == "REFUSED_NOT_TRUNCATED"
