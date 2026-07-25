"""P56 — Evidence receipts and audit bundles.

An audit bundle is a hash-chained, tamper-evident collection of evidence
receipts: decode receipts, search-space accounting, holdout seals, and
challenge results. Each receipt is projected as a
``provenance_event.schema.json`` :class:`~cwatlas.provenance_ledger.ProvenanceEvent`
and appended to a :class:`~cwatlas.provenance_ledger.Ledger`, so the whole
bundle inherits the ledger's guarantees:

* the raw content of every receipt is bound by an immutable SHA-256;
* each event folds in the previous event's chain hash, so altering any past
  receipt — its content, type, or order — breaks verification from that point;
* the tip chain hash is the bundle's signature.

The bundle carries no geographic or physical claim. Receipt content is scanned
against the private/public boundary (:mod:`cwatlas.privacy`) before it is
sealed, so no private token enters the signed record. Public tests use
synthetic receipts only.

Deterministic; epochs are decimal years passed in — never a wall-clock read.

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from cwatlas import claims, privacy
from cwatlas import provenance_ledger as pl
from cwatlas.provenance_ledger import EventKind, Ledger

#: The provenance-event schema each receipt is validated against.
_SCHEMA_PATH = Path(__file__).with_name("schemas") / "provenance_event.schema.json"


class AuditError(ValueError):
    """Raised on a malformed receipt or a failed schema/chain check."""


class ReceiptType(Enum):
    """The evidence receipt kinds an audit bundle assembles."""

    DECODE_RECEIPT = "decode_receipt"
    SEARCH_SPACE_ACCOUNTING = "search_space_accounting"
    HOLDOUT_SEAL = "holdout_seal"
    CHALLENGE_RESULT = "challenge_result"


def _load_schema() -> dict:
    return json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


_SCHEMA = _load_schema()
_SCHEMA_TYPES = {
    "string": str,
    "object": dict,
    "number": (int, float),
    "array": list,
    "boolean": bool,
}


def validate_event_schema(event: dict) -> None:
    """Minimal check that ``event`` conforms to ``provenance_event.schema.json``.

    Verifies required keys are present and that declared property types match
    (``null`` allowed where the schema unions it). Avoids a hard dependency on
    a JSON-schema engine while still refusing an off-shape event.
    """
    for key in _SCHEMA.get("required", []):
        if key not in event:
            raise AuditError(f"event missing required key {key!r}.")
    for key, spec in _SCHEMA.get("properties", {}).items():
        if key not in event:
            continue
        declared = spec.get("type")
        types = declared if isinstance(declared, list) else [declared]
        ok = False
        for t in types:
            if t == "null":
                ok = ok or event[key] is None
            elif t in _SCHEMA_TYPES:
                ok = ok or isinstance(event[key], _SCHEMA_TYPES[t])
        if not ok:
            raise AuditError(
                f"event key {key!r} has wrong type for schema {declared!r}.")


@dataclass(frozen=True)
class AuditReceipt:
    """One evidence receipt: a typed, JSON-able content payload."""

    receipt_id: str
    receipt_type: ReceiptType
    epoch: float
    content: dict

    def __post_init__(self) -> None:
        if not self.receipt_id:
            raise AuditError("receipt_id must be a non-empty string.")
        if not isinstance(self.receipt_type, ReceiptType):
            raise AuditError(
                f"receipt_type must be a ReceiptType, got {self.receipt_type!r}.")
        if not isinstance(self.content, dict):
            raise AuditError("content must be a dict.")

    def canonical(self) -> str:
        """Deterministic JSON of the receipt (the immutably hashed raw string)."""
        return json.dumps(
            {
                "receipt_id": self.receipt_id,
                "receipt_type": self.receipt_type.value,
                "epoch": self.epoch,
                "content": self.content,
            },
            sort_keys=True,
            separators=(",", ":"),
        )


def _build_ledger(receipts: Iterable[AuditReceipt],
                  software_commit: Optional[str]) -> Tuple[Ledger, List[AuditReceipt]]:
    receipts = list(receipts)
    ledger = Ledger()
    for r in receipts:
        raw = r.canonical()
        privacy.refuse_private_in_public(raw)  # no private token enters the seal
        ledger.append(
            kind=EventKind.SOURCE_TIMESTAMP,
            source_id=r.receipt_type.value,
            epoch=r.epoch,
            raw=raw,
            operator_note=r.receipt_type.value,
            software_commit=software_commit,
            event_id=r.receipt_id,
        )
    return ledger, receipts


@dataclass(frozen=True)
class AuditBundle:
    """A signed (hash-chained) audit bundle of evidence receipts."""

    receipts: Tuple[AuditReceipt, ...]
    events: Tuple[dict, ...]
    chain_head: str
    software_commit: Optional[str]

    def verify(self) -> bool:
        """Rebuild the chain from the receipts; ``True`` iff nothing tampered."""
        return verify_bundle(self.to_dict())

    def assert_no_geographic_claim(self) -> dict:
        """The standing refusal the bundle carries with it."""
        return {
            "source_vector_geographic_semantics": "NOT_CLAIMED",
            "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
            "measured_here": "nothing",
        }

    def to_dict(self) -> dict:
        return {
            "what_this_is": "a hash-chained audit bundle of evidence receipts",
            "receipt_count": len(self.receipts),
            "receipts": [
                {
                    "receipt_id": r.receipt_id,
                    "receipt_type": r.receipt_type.value,
                    "epoch": r.epoch,
                    "content": r.content,
                }
                for r in self.receipts
            ],
            "events": list(self.events),
            "chain_head": self.chain_head,
            "software_commit": self.software_commit,
            "claim_class": claims.ClaimClass.SOURCE_CLAIM.value,
            "measured_here": "nothing",
            "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
            "source_vector_geographic_semantics": "NOT_CLAIMED",
            "verdict": "AUDIT_BUNDLE_HASH_CHAINED_NO_GEOGRAPHIC_CLAIM",
        }


def build_audit_bundle(receipts: Iterable[AuditReceipt], *,
                       software_commit: Optional[str] = None) -> AuditBundle:
    """Assemble and sign a hash-chained audit bundle of evidence receipts."""
    ledger, receipts = _build_ledger(receipts, software_commit)
    events = tuple(ev.to_event_dict() for ev in ledger.events)
    for ev in events:
        validate_event_schema(ev)
    return AuditBundle(
        receipts=tuple(receipts),
        events=events,
        chain_head=ledger.head(),
        software_commit=software_commit,
    )


def verify_bundle(bundle: dict) -> bool:
    """Verify a serialized bundle: recompute the chain and compare.

    Any tampering with a receipt's content, type, epoch, order, or the recorded
    chain hashes makes this return ``False``.
    """
    try:
        receipts = [
            AuditReceipt(
                receipt_id=r["receipt_id"],
                receipt_type=ReceiptType(r["receipt_type"]),
                epoch=r["epoch"],
                content=r["content"],
            )
            for r in bundle.get("receipts", [])
        ]
        ledger, _ = _build_ledger(receipts, bundle.get("software_commit"))
    except (AuditError, pl.LedgerError, privacy.PrivacyError, KeyError, ValueError):
        return False

    rebuilt = [ev.to_event_dict() for ev in ledger.events]
    recorded = bundle.get("events", [])
    if len(rebuilt) != len(recorded):
        return False
    for got, want in zip(rebuilt, recorded):
        if got.get("chain_hash") != want.get("chain_hash"):
            return False
        if got.get("raw_hash") != want.get("raw_hash"):
            return False
    if ledger.head() != bundle.get("chain_head"):
        return False
    return ledger.verify_chain()


def audit_bundle_report() -> dict:
    """P56 declaration receipt."""
    return {
        "phase_id": "P56",
        "what_this_is": (
            "evidence receipts and audit bundles: a hash-chained collection of "
            "decode receipts, search-space accounting, holdout seals, and "
            "challenge results, each a provenance_event.schema.json event; "
            "tampering breaks verification."),
        "receipt_types": [t.value for t in ReceiptType],
        "schema": "provenance_event.schema.json",
        "tamper_evident": True,
        "claim_class": claims.ClaimClass.SOURCE_CLAIM.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "EVIDENCE_RECEIPTS_AUDIT_BUNDLE_HASH_CHAINED",
        "what_this_does_not_say": (
            "A verifiable, internally consistent audit bundle proves only that "
            "its receipts have not been altered since sealing. It makes no "
            "geographic or physical claim about any decode, search space, "
            "holdout, or challenge it records."),
    }
