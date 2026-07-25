"""P43 -- legacy candidate search: multi-candidate alias set, no forced pin."""

from __future__ import annotations

import pytest

from cwatlas import claims
from cwatlas.decode_legacy import (
    LegacySearchError,
    SearchStatus,
    decode_legacy_report,
    refuse_source_as_location,
    search_legacy,
    search_legacy_ingested,
)
from cwatlas.ingest import ingest


# --- POWER: a legacy vector yields a multi-candidate alias set ---------------

def test_nine_digit_vector_yields_multiple_candidates():
    result = search_legacy("123456789")
    assert result.status is SearchStatus.OK_ALIAS_SET
    assert result.candidate_count() >= 2
    ids = {c.codec_id for c in result.alias_set.candidates}
    assert "CW-TRIPLET9-1" in ids
    assert "CW-SHELL9-LEGACY" in ids
    assert result.claim_class == claims.ClaimClass.LEGACY_ALIAS_CANDIDATE.value


def test_each_candidate_carries_score_uncertainty_and_search_space():
    result = search_legacy("123456789")
    for c in result.alias_set.candidates:
        assert 0.0 <= c.score <= 1.0
        assert 0.0 <= c.uncertainty <= 1.0
        assert c.search_space_count > 0
    assert result.search_space_total > 0


def test_search_over_ingested_grouped_vector_uses_digits():
    iv = ingest("12-34-56-78-9", ingest_id="v1")
    result = search_legacy_ingested(iv, use_digits=True)
    assert result.status is SearchStatus.OK_ALIAS_SET
    assert result.candidate_count() >= 2


# --- Negative: never a forced pin, never a location --------------------------

def test_multi_candidate_set_refuses_unique_pin():
    result = search_legacy("123456789")
    assert result.candidate_count() >= 2
    with pytest.raises(claims.ClaimError):
        result.require_unique_pin()


def test_source_vector_refused_as_location():
    result = search_legacy("123456789")
    with pytest.raises(claims.ClaimError):
        result.refuse_as_location()
    with pytest.raises(claims.ClaimError):
        refuse_source_as_location()


def test_unadmitted_vector_is_a_refusal_not_a_guess():
    # A non-nine-digit string no legacy codec admits -> refusal, empty set.
    result = search_legacy("hello")
    assert result.status is SearchStatus.REFUSAL
    assert result.is_empty()
    assert result.claim_class == claims.ClaimClass.REFUSAL.value
    with pytest.raises(claims.ClaimError):
        result.require_unique_pin()


def test_non_string_input_refused():
    with pytest.raises(LegacySearchError):
        search_legacy(123456789)  # type: ignore[arg-type]


# --- Determinism -------------------------------------------------------------

def test_candidate_order_is_deterministic():
    a = search_legacy("123456789")
    b = search_legacy("123456789")
    assert [c.codec_id for c in a.alias_set.candidates] == \
           [c.codec_id for c in b.alias_set.candidates]
    assert a.to_dict() == b.to_dict()


def test_report_declares_no_geographic_semantics():
    rep = decode_legacy_report()
    assert rep["source_vector_geographic_semantics"] == "NOT_CLAIMED"
    assert rep["claim_class"] == "LEGACY_ALIAS_CANDIDATE"
    assert rep["phase_id"] == "P43"
