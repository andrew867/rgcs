"""P24 — Codec registry and alias-set API: discovery, alias set, invariant 4."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cwatlas import codec_registry as R
from cwatlas.claims import ClaimClass, ClaimError

SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "cwatlas" / "schemas" / "codec_result.schema.json"
)


# --- Discovery / registration -------------------------------------------------

def test_default_registry_discovers_available_codecs():
    reg = R.build_default_registry()
    ids = reg.codec_ids()
    # base100 (canonical) + triplet9 module's two legacy codecs are present.
    assert "CW-BASE100-1" in ids
    assert "CW-TRIPLET9-1" in ids
    assert "CW-SHELL9-LEGACY" in ids


def test_absent_module_is_skipped_not_required():
    # codec_pack40 / codec_pack38 do not exist yet; discovery must not raise.
    reg = R.build_default_registry()
    assert "CW-PACK40-1" not in reg.codec_ids()


def test_register_refuses_non_conforming_object():
    reg = R.CodecRegistry()
    with pytest.raises(ClaimError):
        reg.register(object())

    class NoDecode:
        codec_id = "X"
        version = "1"

        def encode(self, v):
            return ""

    with pytest.raises(ClaimError):
        reg.register(NoDecode())


def test_register_refuses_duplicate_id():
    reg = R.build_default_registry()
    with pytest.raises(ClaimError):
        reg.register(reg.get("CW-TRIPLET9-1"))


def test_legacy_codecs_excludes_the_canonical_codec():
    reg = R.build_default_registry()
    legacy = {getattr(c, "codec_id") for c in reg.legacy_codecs()}
    assert "CW-BASE100-1" not in legacy  # canonical, not a legacy candidate
    assert {"CW-TRIPLET9-1", "CW-SHELL9-LEGACY"} <= legacy


# --- decode_all -> AliasSet ---------------------------------------------------

def test_decode_all_returns_multi_candidate_alias_set():
    reg = R.build_default_registry()
    alias_set = reg.decode_all("012345678")
    assert len(alias_set) >= 2  # triplet9 + shell9 both admit 9 digits
    assert not alias_set.is_empty()
    for cand in alias_set.candidates:
        assert cand.claim_class == ClaimClass.LEGACY_ALIAS_CANDIDATE.value
        assert cand.search_space_count > 0
        assert 0.0 <= cand.uncertainty <= 1.0


def test_empty_alias_set_is_allowed():
    reg = R.build_default_registry()
    alias_set = reg.decode_all("not-nine-digits")
    assert alias_set.is_empty()
    assert len(alias_set) == 0
    assert alias_set.to_dict()["candidates"] == []


# --- Invariant 4: never force one pin -----------------------------------------

def test_require_unique_pin_refuses_multi_candidate_set():
    reg = R.build_default_registry()
    alias_set = reg.decode_all("012345678")
    assert len(alias_set) >= 2
    with pytest.raises(ClaimError):
        alias_set.require_unique_pin()
    with pytest.raises(ClaimError):
        reg.refuse_alias_as_unique(alias_set)


def test_require_unique_pin_refuses_empty_set():
    reg = R.build_default_registry()
    with pytest.raises(ClaimError):
        reg.decode_all("xxx").require_unique_pin()


def test_require_unique_pin_returns_the_sole_candidate():
    # A registry with a single legacy codec yields exactly one candidate.
    reg = R.CodecRegistry()
    from cwatlas import codec_triplet9 as T
    reg.register(T.TRIPLET9)
    alias_set = reg.decode_all("012345678")
    assert len(alias_set) == 1
    pin = alias_set.require_unique_pin()
    assert pin.codec_id == "CW-TRIPLET9-1"


# --- Determinism --------------------------------------------------------------

def test_decode_all_is_deterministic():
    reg = R.build_default_registry()
    a = reg.decode_all("012345678").to_dict()
    b = reg.decode_all("012345678").to_dict()
    assert a == b


def test_report_is_deterministic_and_claims_nothing_physical():
    r = R.codec_registry_report()
    assert r == R.codec_registry_report()
    assert r["phase_id"] == "P24"
    assert r["claim_class"] == ClaimClass.LEGACY_ALIAS_CANDIDATE.value
    assert "CW-TRIPLET9-1" in r["legacy_codec_ids"]
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"


# --- Schema (results reached through the registry) ----------------------------

def test_registry_reached_results_conform_to_schema():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    reg = R.build_default_registry()
    for codec in reg.legacy_codecs():
        jsonschema.validate(codec.decode("012345678").to_dict(), schema)


def test_import_surface():
    from cwatlas import codec_base100, codec_triplet9, codec_registry  # noqa: F401
