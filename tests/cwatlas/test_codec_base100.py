"""P21 — CW-BASE100-1: round-trip, malformed refusal, determinism, schema."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cwatlas import codec_base100 as B
from cwatlas.claims import ClaimClass, ClaimError

SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "cwatlas" / "schemas" / "codec_result.schema.json"
)

# Deterministic synthetic paths (variable depth, incl. empty and boundaries).
PATHS = [
    (),
    (0,),
    (99,),
    (0, 12, 99),
    (7, 7, 7, 7),
    (1, 2, 3, 4, 5, 6, 7, 8, 9, 10),
    (99, 0, 50, 25, 75),
]


# --- Round-trip ---------------------------------------------------------------

@pytest.mark.parametrize("path", PATHS)
def test_encode_decode_round_trips_exactly(path):
    raw = B.encode(path)
    assert len(raw) == 2 * len(path)
    assert B.decode_to_path(raw) == path


@pytest.mark.parametrize("path", PATHS)
def test_decode_result_carries_the_depth_n_path(path):
    raw = B.encode(path)
    result = B.decode(raw)
    assert result.status == B.STATUS_OK_POINT
    assert result.codec_id == B.CODEC_ID
    (candidate,) = result.candidates
    assert candidate["path"] == list(path)
    assert candidate["depth"] == len(path)
    assert candidate["claim_class"] == ClaimClass.CANONICAL_ROUND_TRIP.value


def test_known_vector_decodes_to_expected_tokens():
    assert B.decode_to_path("001299") == (0, 12, 99)
    assert B.encode((0, 12, 99)) == "001299"


def test_empty_string_is_the_depth_zero_path():
    assert B.decode_to_path("") == ()
    assert B.encode(()) == ""


# --- Negative: malformed token refused ---------------------------------------

def test_odd_length_token_string_is_refused():
    with pytest.raises(ClaimError):
        B.decode_to_path("123")  # odd length
    result = B.decode("123")
    assert result.status == B.STATUS_INVALID
    assert result.candidates == ()


def test_non_digit_token_is_refused():
    with pytest.raises(ClaimError):
        B.decode_to_path("0a")
    assert B.decode("0a").status == B.STATUS_INVALID
    # non-ASCII "digits" (superscript) are refused, not silently accepted
    with pytest.raises(ClaimError):
        B.decode_to_path("²²")


def test_non_str_raw_is_refused():
    with pytest.raises(ClaimError):
        B.decode_to_path(1299)  # type: ignore[arg-type]
    assert B.decode(1299).status == B.STATUS_INVALID  # type: ignore[arg-type]


def test_encode_refuses_out_of_range_and_bad_types():
    with pytest.raises(ClaimError):
        B.encode((100,))
    with pytest.raises(ClaimError):
        B.encode((-1,))
    with pytest.raises(ClaimError):
        B.encode((True,))  # bool is not an accepted token value
    with pytest.raises(ClaimError):
        B.encode("12")  # a string is not a path


# --- Determinism --------------------------------------------------------------

def test_decode_is_deterministic():
    a = B.decode("001299").to_dict()
    b = B.decode("001299").to_dict()
    assert a == b
    assert a["receipt_id"] == b["receipt_id"]


def test_report_is_deterministic_and_claims_nothing_physical():
    r = B.codec_base100_report()
    assert r == B.codec_base100_report()
    assert r["phase_id"] == "P21"
    assert r["claim_class"] == ClaimClass.CANONICAL_ROUND_TRIP.value
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"


# --- Schema -------------------------------------------------------------------

def test_codec_result_conforms_to_schema():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(instance=B.decode("001299").to_dict(), schema=schema)
    jsonschema.validate(instance=B.decode("123").to_dict(), schema=schema)


def test_import_surface():
    from cwatlas import codec_base100  # noqa: F401
