"""P04 -- communications and correction ledger as typed provenance.

The private comms archive is a chronicle: messages, later corrections to
earlier messages, mundane controls (ordinary, non-extraordinary entries kept
as baseline), and source-reported timestamps. This module imports such a
ledger as *typed provenance events* and holds three contract invariants:

* **Raw strings are immutable** (System Contract invariant 1). Every event
  binds an immutable SHA-256 of the original string; the raw text is never
  rewritten in place, only hashed and preserved.
* **Corrections link, they do not overwrite.** A ``CORRECTION`` event points
  at the ``event_id`` it corrects and is appended; the corrected event stays
  in the ledger verbatim. History is preserved, never rewritten to make the
  newest statement look inevitable (invariant 4 / phase requirement).
* **The ledger is a hash chain.** Each event's ``chain_hash`` folds in the
  previous event's ``chain_hash``, so tampering with any past event -- its
  raw string, its kind, its link -- breaks verification from that point on.

Nothing here claims a source event identifies a real location or that any
reported prediction came true. An imported event is, at most, a
``SOURCE_CLAIM``. Public tests use synthetic events only; private corpora
load solely through the ignored local path in :mod:`cwatlas.privacy`.

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED

Epochs are decimal years and are always passed in -- never a wall-clock read.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Iterable, List, Optional

from cwatlas import claims

#: The chain root. The first event's ``prev_hash`` is this constant, so the
#: whole chain is anchored deterministically without any wall-clock seed.
GENESIS_HASH = "0" * 64

#: Emitted event class for the schema projection (see ``provenance_event``
#: schema). An imported comms/correction record is a reported source event.
SOURCE_CLASS = "SOURCE_CLAIM"


class LedgerError(ValueError):
    """Raised on a malformed event, a broken link, or a duplicate id."""


class EventKind(Enum):
    """The four typed kinds imported from the comms/correction chronicle."""

    MESSAGE = "message"
    CORRECTION = "correction"
    MUNDANE_CONTROL = "mundane_control"
    SOURCE_TIMESTAMP = "source_timestamp"


def _sha256(text: str) -> str:
    """SHA-256 hex of a string's UTF-8 bytes."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _content_digest(
    event_id: str,
    kind: EventKind,
    source_id: str,
    epoch: float,
    raw_hash: str,
    corrects: Optional[str],
    operator_note: Optional[str],
    software_commit: Optional[str],
) -> str:
    """Deterministic digest of an event's typed content (excludes chain)."""
    payload = {
        "event_id": event_id,
        "kind": kind.value,
        "source_id": source_id,
        "epoch": epoch,
        "raw_hash": raw_hash,
        "corrects": corrects,
        "operator_note": operator_note,
        "software_commit": software_commit,
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _chain_hash(prev_hash: str, content_digest: str) -> str:
    """Fold the previous chain hash into this event's content digest."""
    return hashlib.sha256((prev_hash + content_digest).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ProvenanceEvent:
    """A typed, immutable provenance event in the ledger hash chain.

    ``raw`` is the original string, preserved verbatim; ``raw_hash`` is its
    immutable SHA-256. A ``CORRECTION`` carries ``corrects`` -- the id of the
    event it amends -- and never overwrites it. ``prev_hash`` and
    ``chain_hash`` are assigned by the :class:`Ledger` when the event is
    appended; together they make the ledger tamper-evident.
    """

    event_id: str
    kind: EventKind
    source_id: str
    epoch: float
    raw: str
    raw_hash: str
    corrects: Optional[str]
    operator_note: Optional[str]
    software_commit: Optional[str]
    prev_hash: str
    chain_hash: str

    def __post_init__(self) -> None:
        if not self.event_id:
            raise LedgerError("event_id must be a non-empty string")
        if not isinstance(self.kind, EventKind):
            raise LedgerError(f"kind must be an EventKind, got {self.kind!r}")
        if not self.source_id:
            raise LedgerError("source_id must be a non-empty string")
        # Invariant 1: raw string and its hash must agree at construction.
        if self.raw_hash != _sha256(self.raw):
            raise LedgerError(
                "raw_hash does not match raw string: the immutable hash of "
                "the original string has been broken")
        if self.kind is EventKind.CORRECTION and not self.corrects:
            raise LedgerError(
                "a CORRECTION must link to the event_id it corrects; "
                "corrections link, they do not overwrite")
        if self.kind is not EventKind.CORRECTION and self.corrects is not None:
            raise LedgerError(
                f"only a CORRECTION may set 'corrects'; kind={self.kind.value}")

    def verify_raw(self) -> bool:
        """True iff the stored hash still matches the raw string."""
        return self.raw_hash == _sha256(self.raw)

    def to_event_dict(self) -> dict:
        """Project to a ``provenance_event`` schema-conforming mapping.

        The schema requires ``event_id``, ``timestamp``, ``source_class`` and
        ``raw_hash``; the typed ledger fields are carried alongside so later
        phases can rebuild the chain without a lossy round-trip.
        """
        return {
            "event_id": self.event_id,
            "timestamp": repr(self.epoch),
            "source_class": SOURCE_CLASS,
            "raw_hash": self.raw_hash,
            "operator_note": self.operator_note,
            "software_commit": self.software_commit,
            "kind": self.kind.value,
            "source_id": self.source_id,
            "epoch": self.epoch,
            "corrects": self.corrects,
            "prev_hash": self.prev_hash,
            "chain_hash": self.chain_hash,
        }


class Ledger:
    """An append-only, hash-chained ledger of typed provenance events."""

    def __init__(self) -> None:
        self._events: List[ProvenanceEvent] = []
        self._by_id: Dict[str, ProvenanceEvent] = {}

    def __len__(self) -> int:
        return len(self._events)

    @property
    def events(self) -> tuple:
        """The events in append order (an immutable snapshot)."""
        return tuple(self._events)

    def append(
        self,
        kind: EventKind,
        source_id: str,
        epoch: float,
        raw: str,
        *,
        corrects: Optional[str] = None,
        operator_note: Optional[str] = None,
        software_commit: Optional[str] = None,
        event_id: Optional[str] = None,
    ) -> ProvenanceEvent:
        """Append one typed event, extending the hash chain.

        ``epoch`` is a decimal year passed in by the caller. A ``CORRECTION``
        must name, via ``corrects``, an event already in the ledger; the
        corrected event is left untouched.
        """
        eid = event_id if event_id is not None else f"ev{len(self._events):04d}"
        if eid in self._by_id:
            raise LedgerError(f"duplicate event_id {eid!r}")
        if corrects is not None and corrects not in self._by_id:
            raise LedgerError(
                f"cannot correct unknown event_id {corrects!r}; a correction "
                f"must link to an event already in the ledger")
        raw_hash = _sha256(raw)
        prev = self._events[-1].chain_hash if self._events else GENESIS_HASH
        digest = _content_digest(
            eid, kind, source_id, epoch, raw_hash, corrects,
            operator_note, software_commit)
        chain = _chain_hash(prev, digest)
        event = ProvenanceEvent(
            event_id=eid,
            kind=kind,
            source_id=source_id,
            epoch=epoch,
            raw=raw,
            raw_hash=raw_hash,
            corrects=corrects,
            operator_note=operator_note,
            software_commit=software_commit,
            prev_hash=prev,
            chain_hash=chain,
        )
        self._events.append(event)
        self._by_id[eid] = event
        return event

    def get(self, event_id: str) -> ProvenanceEvent:
        """Return an event by id, or raise if it is not present."""
        if event_id not in self._by_id:
            raise LedgerError(f"no such event_id {event_id!r}")
        return self._by_id[event_id]

    def corrections_for(self, event_id: str) -> List[ProvenanceEvent]:
        """Every CORRECTION that links to ``event_id`` (history preserved)."""
        return [e for e in self._events if e.corrects == event_id]

    def verify_chain(self) -> bool:
        """Recompute the whole chain; ``True`` iff nothing has been tampered.

        Re-derives each event's raw hash, content digest and chain hash and
        checks the previous-hash linkage. Any change to a past event -- its
        raw string, kind, link, or epoch -- makes this return ``False``.
        """
        prev = GENESIS_HASH
        for event in self._events:
            if not event.verify_raw():
                return False
            digest = _content_digest(
                event.event_id, event.kind, event.source_id, event.epoch,
                event.raw_hash, event.corrects, event.operator_note,
                event.software_commit)
            expected = _chain_hash(prev, digest)
            if event.prev_hash != prev or event.chain_hash != expected:
                return False
            prev = event.chain_hash
        return True

    def head(self) -> str:
        """The tip chain hash (or the genesis hash for an empty ledger)."""
        return self._events[-1].chain_hash if self._events else GENESIS_HASH


def import_ledger(entries: Iterable[dict], ledger: Optional[Ledger] = None) -> Ledger:
    """Import an iterable of synthetic entry dicts into a :class:`Ledger`.

    Each entry maps to :meth:`Ledger.append`. Required keys: ``kind``
    (an :class:`EventKind` or its value), ``source_id``, ``epoch``, ``raw``.
    Optional: ``corrects``, ``operator_note``, ``software_commit``,
    ``event_id``. Order is preserved, so the resulting chain is deterministic.
    """
    ledger = ledger if ledger is not None else Ledger()
    for entry in entries:
        kind = entry["kind"]
        if not isinstance(kind, EventKind):
            kind = EventKind(kind)
        ledger.append(
            kind=kind,
            source_id=entry["source_id"],
            epoch=entry["epoch"],
            raw=entry["raw"],
            corrects=entry.get("corrects"),
            operator_note=entry.get("operator_note"),
            software_commit=entry.get("software_commit"),
            event_id=entry.get("event_id"),
        )
    return ledger


def provenance_ledger_report() -> dict:
    """What this module claims -- and, deliberately, what it does not."""
    return {
        "module": "cwatlas.provenance_ledger",
        "phase_id": "P04",
        "event_kinds": [k.value for k in EventKind],
        "genesis_hash": GENESIS_HASH,
        "invariants": [
            "raw strings immutable (bound by SHA-256)",
            "corrections link, they do not overwrite",
            "hash chain: tampering a past event breaks verification",
        ],
        "claim_class": claims.ClaimClass.SOURCE_CLAIM.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "COMMS_CORRECTION_LEDGER_TYPED_HASH_CHAINED",
        "what_this_does_not_say": (
            "An imported comms or correction event is a reported SOURCE_CLAIM. "
            "That the ledger is internally consistent says nothing about "
            "whether any reported location, prediction, or source vector is "
            "real. No geographic semantics are claimed."),
    }
