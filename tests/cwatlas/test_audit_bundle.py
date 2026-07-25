"""P56 — evidence receipts and audit bundles.

POWER: a bundle of decode/search-space/holdout/challenge receipts assembles,
verifies, and each receipt projects to a provenance_event.schema.json event.
Negative: tampering with any receipt content, chain hash, or order breaks
verification; a private token in a receipt is refused at seal time. The bundle
asserts no geographic/physical claim. Deterministic.
"""

from __future__ import annotations

import copy

import pytest

from cwatlas import audit_bundle as A
from cwatlas.audit_bundle import AuditReceipt, ReceiptType


def _receipts():
    return [
        AuditReceipt("rec-decode", ReceiptType.DECODE_RECEIPT, 2026.01,
                     {"codec": "CW-GEO-1", "candidates": 3}),
        AuditReceipt("rec-space", ReceiptType.SEARCH_SPACE_ACCOUNTING, 2026.02,
                     {"searched": 1024, "admissible": 3}),
        AuditReceipt("rec-holdout", ReceiptType.HOLDOUT_SEAL, 2026.03,
                     {"holdout": 2, "sealed": True}),
        AuditReceipt("rec-challenge", ReceiptType.CHALLENGE_RESULT, 2026.04,
                     {"passed": True, "residual_m": 12.3}),
    ]


# --- POWER --------------------------------------------------------------------

def test_bundle_assembles_and_verifies():
    bundle = A.build_audit_bundle(_receipts(), software_commit="deadbeef")
    assert bundle.receipt_count if hasattr(bundle, "receipt_count") else True
    assert len(bundle.receipts) == 4
    assert bundle.verify() is True
    assert A.verify_bundle(bundle.to_dict()) is True


def test_each_receipt_projects_to_schema_event():
    bundle = A.build_audit_bundle(_receipts())
    assert len(bundle.events) == 4
    for ev in bundle.events:
        A.validate_event_schema(ev)  # does not raise
        assert ev["source_class"] == "SOURCE_CLAIM"
        assert len(ev["raw_hash"]) == 64


def test_bundle_asserts_no_geographic_claim():
    bundle = A.build_audit_bundle(_receipts())
    d = bundle.to_dict()
    assert d["source_vector_geographic_semantics"] == "NOT_CLAIMED"
    assert d["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert bundle.assert_no_geographic_claim()["measured_here"] == "nothing"


# --- Negative: tamper detection ----------------------------------------------

def test_tampered_content_breaks_verification():
    bundle = A.build_audit_bundle(_receipts()).to_dict()
    bundle["receipts"][0]["content"]["candidates"] = 99  # alter a receipt
    assert A.verify_bundle(bundle) is False


def test_tampered_chain_hash_breaks_verification():
    bundle = A.build_audit_bundle(_receipts()).to_dict()
    bundle["events"][2]["chain_hash"] = "0" * 64
    assert A.verify_bundle(bundle) is False


def test_reordered_receipts_break_verification():
    bundle = A.build_audit_bundle(_receipts()).to_dict()
    bundle["receipts"][0], bundle["receipts"][1] = (
        bundle["receipts"][1], bundle["receipts"][0])
    assert A.verify_bundle(bundle) is False


def test_tampered_head_breaks_verification():
    bundle = A.build_audit_bundle(_receipts()).to_dict()
    bundle["chain_head"] = "f" * 64
    assert A.verify_bundle(bundle) is False


# --- Negative: privacy + malformed -------------------------------------------

def test_private_token_in_receipt_refused():
    token = "private" + "_do_not_commit"
    bad = [AuditReceipt("r", ReceiptType.DECODE_RECEIPT, 2026.0,
                        {"path": token})]
    with pytest.raises(Exception):
        A.build_audit_bundle(bad)


def test_bad_receipt_type_refused():
    with pytest.raises(A.AuditError):
        AuditReceipt("r", "decode_receipt", 2026.0, {})  # not a ReceiptType


def test_empty_receipt_id_refused():
    with pytest.raises(A.AuditError):
        AuditReceipt("", ReceiptType.DECODE_RECEIPT, 2026.0, {})


def test_off_shape_event_refused():
    with pytest.raises(A.AuditError):
        A.validate_event_schema({"event_id": "x"})  # missing required keys


# --- Determinism --------------------------------------------------------------

def test_bundle_head_is_deterministic():
    a = A.build_audit_bundle(_receipts())
    b = A.build_audit_bundle(_receipts())
    assert a.chain_head == b.chain_head


def test_report_declares_boundary():
    r = A.audit_bundle_report()
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"
    assert r["tamper_evident"] is True
