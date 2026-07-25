"""P19 — CW-PACK40-1: round-trip, overflow refusal, determinism, schema."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cwatlas import claims
from cwatlas import codec_pack40 as C

SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "cwatlas" / "schemas" / "codec_result.schema.json"
)


def _sample_pairs():
    """A deterministic spread of (header, path) pairs across the space."""
    headers = [0, 1, 7, 8, 15]
    paths = [
        0,
        1,
        7,  # single octal digit
        8,  # rolls into the second octal digit
        12345,
        C.PATH_MAX // 2,
        C.PATH_MAX - 1,
        C.PATH_MAX,
    ]
    return [(h, p) for h in headers for p in paths]


def test_bit_layout_constants():
    assert C.HEADER_BITS == 4
    assert C.PATH_BITS == 36
    assert C.TOTAL_BITS == 40
    assert C.PATH_OCTAL_DIGITS == 12
    assert C.HEADER_MAX == 15
    assert C.PATH_MAX == (1 << 36) - 1


@pytest.mark.parametrize("header,path", _sample_pairs())
def test_power_round_trip(header, path):
    word = C.encode(header, path)
    back = C.decode(word.packed)
    assert back.header == header
    assert back.path == path
    assert back.packed == word.packed
    assert back.path_octal == word.path_octal


def test_octal_path_is_twelve_digits_and_reverses():
    for _, path in _sample_pairs():
        s = C.path_to_octal(path)
        assert len(s) == 12
        assert all(ch in "01234567" for ch in s)
        assert C.octal_to_path(s) == path


def test_packed_word_composition():
    word = C.encode(15, C.PATH_MAX)
    assert word.packed == (15 << 36) | C.PATH_MAX
    assert word.packed == C.PACKED_MAX


def test_decode_octal_round_trip():
    word = C.encode(9, 0o765432107654)
    rebuilt = C.decode_octal(word.header, word.path_octal)
    assert rebuilt.packed == word.packed
    assert rebuilt.path == word.path


def test_header_overflow_refused_not_truncated():
    with pytest.raises(ValueError):
        C.encode(C.HEADER_MAX + 1, 0)


def test_path_overflow_refused_not_truncated():
    with pytest.raises(ValueError):
        C.encode(0, C.PATH_MAX + 1)


def test_negative_fields_refused():
    with pytest.raises(ValueError):
        C.encode(-1, 0)
    with pytest.raises(ValueError):
        C.encode(0, -1)


def test_bool_and_nonint_refused():
    with pytest.raises(ValueError):
        C.encode(True, 0)
    with pytest.raises(ValueError):
        C.encode(0, 1.5)


def test_decode_out_of_range_refused():
    with pytest.raises(ValueError):
        C.decode(C.PACKED_MAX + 1)
    with pytest.raises(ValueError):
        C.decode(-1)


def test_octal_malformed_refused():
    with pytest.raises(ValueError):
        C.octal_to_path("777")  # too short
    with pytest.raises(ValueError):
        C.octal_to_path("0000000000009")  # 13 digits
    with pytest.raises(ValueError):
        C.octal_to_path("00000000000A")  # non-octal digit
    with pytest.raises(ValueError):
        C.octal_to_path("00000000008" + "8")  # digit 8 not octal


def test_determinism():
    a = C.encode(5, 424242)
    b = C.encode(5, 424242)
    assert a == b
    assert C.to_codec_result(a) == C.to_codec_result(b)


def test_not_a_geographic_decode_is_refused():
    with pytest.raises(claims.ClaimError):
        C.refuse_as_geographic()


def test_codec_result_validates_against_schema():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    for header, path in _sample_pairs():
        result = C.to_codec_result(C.encode(header, path))
        jsonschema.validate(instance=result, schema=schema)
        assert result["status"] == "NO_UNIQUE_GEOGRAPHIC_DECODE"
        assert result["codec_id"] == "CW-PACK40-1"


def test_codec_result_never_forces_a_pin():
    result = C.to_codec_result(C.encode(3, 999))
    # A legacy candidate codec must not emit a geographic point.
    assert result["status"] != "OK_POINT"
    for cand in result["candidates"]:
        assert cand["claim_class"] == "MATHEMATICAL_TRANSLATION"


def test_report_claims_nothing_geographic():
    r = C.codec_pack40_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"
    assert r["claim_class"] == "MATHEMATICAL_TRANSLATION"
    assert r["reversible"] is True
    assert r["overflow_policy"] == "REFUSED_NOT_TRUNCATED"
