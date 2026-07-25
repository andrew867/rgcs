"""P41 -- raw vector ingest: byte preservation, immutability, derived views."""

from __future__ import annotations

import pytest

from cwatlas import claims
from cwatlas.ingest import (
    IngestError,
    IngestForm,
    IngestedVector,
    ingest,
    ingest_report,
    refuse_mutated_original,
    _sha256_bytes,
)


# --- POWER: exact byte/string preservation and derived views ----------------

def test_ingest_preserves_exact_bytes_and_hash():
    iv = ingest("123 456 789", ingest_id="v1")
    assert iv.raw_bytes == b"123 456 789"
    assert iv.raw_text == "123 456 789"
    assert iv.content_hash == _sha256_bytes(b"123 456 789")
    assert iv.verify_integrity()


def test_normalized_view_strips_whitespace_only():
    iv = ingest("12 34\t56\n78", ingest_id="v1")
    # Whitespace removed; original bytes untouched.
    assert iv.normalized == "12345678"
    assert iv.raw_bytes == "12 34\t56\n78".encode("utf-8")


def test_digits_only_view_for_grouped_and_dashed_inputs():
    iv = ingest("12-34-56-78-9", ingest_id="v1")
    assert iv.digits_only() == "123456789"
    assert iv.form is IngestForm.DASHED


def test_stripped_of_removes_declared_separators_only():
    iv = ingest("00A|7B|CC", ingest_id="v1")
    assert iv.stripped_of(("|",)) == "00A7BCC"
    # Original preserved.
    assert iv.raw_text == "00A|7B|CC"


def test_binary_input_kept_as_opaque_bytes():
    iv = ingest(b"\xff\xfe\x00\x01", ingest_id="b1")
    assert iv.raw_text is None
    assert iv.encoding == "bytes"
    assert iv.normalized == ""
    assert iv.verify_integrity()


def test_leading_zeros_are_preserved_in_original():
    iv = ingest("007", ingest_id="v1")
    assert iv.raw_bytes == b"007"
    assert iv.digits_only() == "007"


# --- Negative: immutability and integrity refusals --------------------------

def test_content_hash_must_bind_raw_bytes():
    with pytest.raises(IngestError):
        IngestedVector(
            ingest_id="v1",
            raw_bytes=b"123",
            raw_text="123",
            encoding="utf-8",
            content_hash="sha256:deadbeef",  # does not bind the bytes
            normalized="123",
            form=IngestForm.RAW,
            claim_class=claims.ClaimClass.SOURCE_CLAIM,
        )


def test_ingested_vector_refuses_non_source_claim_class():
    with pytest.raises(claims.ClaimError):
        IngestedVector(
            ingest_id="v1",
            raw_bytes=b"123",
            raw_text="123",
            encoding="utf-8",
            content_hash=_sha256_bytes(b"123"),
            normalized="123",
            form=IngestForm.RAW,
            claim_class=claims.ClaimClass.CANONICAL_ROUND_TRIP,
        )


def test_raw_bytes_are_immutable_frozen_dataclass():
    iv = ingest("123", ingest_id="v1")
    with pytest.raises(Exception):
        iv.raw_bytes = b"999"  # frozen dataclass forbids reassignment


def test_empty_input_is_refused():
    with pytest.raises(IngestError):
        ingest("", ingest_id="v1")


def test_missing_ingest_id_is_refused():
    with pytest.raises(IngestError):
        ingest("123", ingest_id="")


def test_refuse_mutated_original_always_raises():
    with pytest.raises(IngestError):
        refuse_mutated_original()


def test_digits_only_refused_on_binary():
    iv = ingest(b"\xff\x00", ingest_id="b1")
    with pytest.raises(IngestError):
        iv.digits_only()


# --- Determinism -------------------------------------------------------------

def test_ingest_is_deterministic():
    a = ingest("12-34-56", ingest_id="v1")
    b = ingest("12-34-56", ingest_id="v1")
    assert a.content_hash == b.content_hash
    assert a.normalized == b.normalized
    assert a.digits_only() == b.digits_only()
    assert a.form == b.form


def test_report_declares_no_geographic_semantics():
    rep = ingest_report()
    assert rep["source_vector_geographic_semantics"] == "NOT_CLAIMED"
    assert rep["claim_class"] == "SOURCE_CLAIM"
    assert rep["phase_id"] == "P41"
