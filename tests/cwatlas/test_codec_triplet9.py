"""P22 — CW-TRIPLET9-1 / CW-SHELL9-LEGACY: round-trip, legacy flag, schema."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cwatlas import codec_triplet9 as T
from cwatlas.claims import ClaimClass, ClaimError

SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "cwatlas" / "schemas" / "codec_result.schema.json"
)

TRIPLES = [(0, 0, 0), (1, 2, 3), (999, 999, 999), (12, 345, 678), (100, 0, 999)]


# --- CW-TRIPLET9-1 round-trips exactly ---------------------------------------

@pytest.mark.parametrize("value", TRIPLES)
def test_triplet9_round_trips_exactly(value):
    raw = T.TRIPLET9.encode(value)
    assert len(raw) == 9
    result = T.TRIPLET9.decode(raw)
    assert result.status == T.STATUS_OK_ALIAS_SET
    (candidate,) = result.candidates
    assert candidate["groups"] == list(value)
    assert candidate["round_trips"] is True
    assert candidate["claim_class"] == ClaimClass.MATHEMATICAL_TRANSLATION.value


def test_triplet9_known_vector():
    assert T.TRIPLET9.encode((12, 345, 678)) == "012345678"
    assert T.TRIPLET9.decode("012345678").candidates[0]["groups"] == [12, 345, 678]


def test_triplet9_malformed_is_refused():
    for bad in ("01234567", "0123456789", "abcdefghi", "", "12x456789"):
        assert T.TRIPLET9.decode(bad).status == T.STATUS_INVALID
    with pytest.raises(ClaimError):
        T.TRIPLET9.encode((1000, 0, 0))
    with pytest.raises(ClaimError):
        T.TRIPLET9.encode((1, 2))  # wrong arity


# --- CW-SHELL9-LEGACY: legacy, does NOT round-trip cleanly -------------------

def test_shell9_is_flagged_legacy_conditional():
    assert T.SHELL9.round_trips is False
    assert T.SHELL9.legacy_status == T.LEGACY_CONDITIONAL
    result = T.SHELL9.decode("012345678")
    assert result.status == T.STATUS_OK_ALIAS_SET
    assert any("does NOT round-trip" in w for w in result.warnings)
    assert result.candidates[0]["legacy_status"] == T.LEGACY_CONDITIONAL


def test_shell9_does_not_round_trip_for_shell_eight():
    # Encoding shell 8 then decoding collapses to 0 (lossy conditional closure).
    raw = T.SHELL9.encode((12, 345, 67, 8))
    assert raw == "012345678"
    candidate = T.SHELL9.decode(raw).candidates[0]
    assert candidate["shell_raw"] == 8
    assert candidate["shell_resolved"] == 0  # 8 -> 0, does not survive
    assert candidate["groups"][-1] == 0


def test_shell9_round_trips_for_non_eight_shells():
    for s in (0, 1, 7):
        raw = T.SHELL9.encode((12, 345, 67, s))
        cand = T.SHELL9.decode(raw).candidates[0]
        assert cand["shell_resolved"] == s


def test_shell9_malformed_and_bounds_refused():
    assert T.SHELL9.decode("12345").status == T.STATUS_INVALID
    with pytest.raises(ClaimError):
        T.SHELL9.encode((12, 345, 67, 9))  # shell out of [0, 8]
    with pytest.raises(ClaimError):
        T.SHELL9.encode((12, 345, 100, 0))  # pair out of [0, 99]


# --- Both emit MATHEMATICAL_TRANSLATION candidates ---------------------------

def test_both_emit_mathematical_translation_candidates():
    for codec in (T.TRIPLET9, T.SHELL9):
        cand = codec.decode("012345678").candidates[0]
        assert cand["claim_class"] == ClaimClass.MATHEMATICAL_TRANSLATION.value
        assert "score" in cand and "uncertainty" in cand
        assert cand["search_space_count"] > 0


# --- Determinism --------------------------------------------------------------

def test_decode_is_deterministic():
    assert T.TRIPLET9.decode("012345678").to_dict() == \
        T.TRIPLET9.decode("012345678").to_dict()
    assert T.SHELL9.decode("012345678").to_dict() == \
        T.SHELL9.decode("012345678").to_dict()


def test_report_is_deterministic_and_claims_nothing_physical():
    r = T.codec_triplet9_report()
    assert r == T.codec_triplet9_report()
    assert r["phase_id"] == "P22"
    assert r["claim_class"] == ClaimClass.MATHEMATICAL_TRANSLATION.value
    assert r["codecs"]["CW-SHELL9-LEGACY"]["round_trips"] is False
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"


# --- Schema -------------------------------------------------------------------

def test_codec_results_conform_to_schema():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    for codec in (T.TRIPLET9, T.SHELL9):
        jsonschema.validate(codec.decode("012345678").to_dict(), schema)
        jsonschema.validate(codec.decode("bad").to_dict(), schema)


def test_import_surface():
    from cwatlas import codec_triplet9  # noqa: F401
