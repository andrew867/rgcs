"""P01 — timestamped session ingest, append-only, with the source and
operator records kept rigorously separate.

A session record has two jobs that must never blur into one another:
preserve what a Tier-A *source* said, and preserve what the *operator*
(AG) noted. Merging the two -- letting an operator paraphrase become a
source statement, or an interpretive note become a raw record -- is the
single most common way a faithful archive turns into a fabricated one.
This module makes that merge structurally impossible.

Three commitments:

**Append-only.** A record is frozen at creation and carries a content
hash. A correction is a *new* appended record that references the one it
corrects; the original is never edited or deleted. History is the point.

**Source is not operator.** ``SRC_JH`` and ``SRC_LS`` are Tier-A private
sources; AG notes are a different provenance class entirely. A record is
one or the other, never both, and the constructor refuses a source
record that carries an operator-note type (and vice versa).

**Raw stays private.** ``raw_text_private`` is exactly that. The public
view redacts it and every timestamp precise enough to identify, emitting
only structure, evidence status, and publication class. A record whose
publication class is ``PRIVATE_ONLY`` yields nothing quotable in public.

Nothing here is evidence. A Tier-A source record is faithful
attribution, not empirical support, and its evidence status is tracked
independently and never auto-promoted.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum


class SessionError(RuntimeError):
    """Raised on a malformed or provenance-violating session record."""


class Provenance(Enum):
    """Who a record is attributed to. Source and operator never merge."""

    SRC_JH = "SRC_JH"                     # Tier-A private source
    SRC_LS = "SRC_LS"                     # Tier-A private source
    AG = "AG"                             # the operator


class AGNoteType(Enum):
    """The distinct kinds of operator note (only valid when AG)."""

    DIRECT_NOTE = "AG_DIRECT_NOTE"
    PARAPHRASE = "AG_PARAPHRASE"
    INTERPRETIVE_NOTE = "AG_INTERPRETIVE_NOTE"
    PRIOR_MEDIA_RECALL = "AG_PRIOR_MEDIA_RECALL"
    NO_LOOKAHEAD_SELF_REPORT = "AG_NO_LOOKAHEAD_SELF_REPORT"
    OPERATOR_STATE = "AG_OPERATOR_STATE"


#: Evidence statuses a record may hold (independent of provenance). None
#: of them is created by attribution: Tier-A is not empirical evidence.
EVIDENCE_STATUSES = (
    "RAW_SOURCE_RECORD", "SOURCE_CLAIM", "OPERATOR_NOTE",
    "PRIOR_MEDIA_RECALL", "NO_LOOKAHEAD_SELF_REPORT",
    "MATHEMATICAL_TRANSLATION", "CONVENTIONAL_ENGINEERING_ANALOGUE",
    "SOFTWARE_VERIFIED", "PHYSICAL_HYPOTHESIS", "PROSPECTIVE_PREDICTION",
    "MEASURED", "REPLICATED", "UNSUPPORTED", "CONTRADICTED", "UNRESOLVED",
)

_SOURCE = {Provenance.SRC_JH, Provenance.SRC_LS}


@dataclass(frozen=True)
class SessionEvent:
    """One append-only session record.

    ``ag_note_type`` is set iff ``provenance is AG``. ``raw_text_private``
    is never emitted publicly. ``corrects`` names an earlier event_id when
    this record is an appended correction.
    """

    event_id: str
    session_id: str
    provenance: Provenance
    normalized_text: str
    evidence_status: str
    local_time: str
    timezone: str
    utc_time: str
    raw_text_private: str = ""
    ag_note_type: AGNoteType | None = None
    clock_checked_after_onset: bool = False
    minute_rollover: bool = False
    prior_media_exposure: tuple[str, ...] = ()
    no_lookahead_self_report: bool = False
    correction: bool = False
    corrects: str | None = None
    publication_class: str = "PRIVATE_ONLY"

    def __post_init__(self) -> None:
        if self.evidence_status not in EVIDENCE_STATUSES:
            raise SessionError(
                f"evidence_status {self.evidence_status!r} is not one of "
                f"the allowed statuses")
        is_source = self.provenance in _SOURCE
        if is_source and self.ag_note_type is not None:
            raise SessionError(
                "a Tier-A source record may not carry an AG note type; "
                "source and operator provenance never merge")
        if (not is_source) and self.ag_note_type is None:
            raise SessionError(
                "an AG record must declare an AGNoteType")
        if is_source and self.evidence_status == "OPERATOR_NOTE":
            raise SessionError(
                "a source record cannot have evidence_status OPERATOR_NOTE")
        if self.correction and not self.corrects:
            raise SessionError(
                "a correction must reference the event_id it corrects")
        if not self.event_id or not self.session_id:
            raise SessionError("event_id and session_id are required")

    @property
    def is_source(self) -> bool:
        return self.provenance in _SOURCE

    @property
    def content_hash(self) -> str:
        """Stable content hash over the frozen fields (integrity)."""
        parts = (self.event_id, self.session_id, self.provenance.value,
                 self.normalized_text, self.evidence_status,
                 self.local_time, self.timezone, self.utc_time,
                 self.raw_text_private,
                 self.ag_note_type.value if self.ag_note_type else "",
                 str(self.corrects))
        return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()

    def public_view(self) -> dict:
        """A privacy-safe projection. Never emits raw_text_private, and
        for PRIVATE_ONLY records never emits normalized_text either."""
        emit_text = self.publication_class != "PRIVATE_ONLY"
        return {
            "event_id": self.event_id,
            "session_id": self.session_id,
            "provenance": self.provenance.value,
            "ag_note_type": self.ag_note_type.value if self.ag_note_type else None,
            "evidence_status": self.evidence_status,
            "publication_class": self.publication_class,
            "normalized_text": self.normalized_text if emit_text else "WITHHELD_PRIVATE",
            "raw_text_present": bool(self.raw_text_private),
            "hash": self.content_hash,
            "endorsed": False,
        }


class SessionLog:
    """An append-only ordered log of session events."""

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self._events: list[SessionEvent] = []
        self._ids: set[str] = set()

    def append(self, event: SessionEvent) -> None:
        if event.session_id != self.session_id:
            raise SessionError("event belongs to a different session")
        if event.event_id in self._ids:
            raise SessionError(
                f"event_id {event.event_id!r} already present; the log is "
                f"append-only and does not overwrite")
        if event.corrects is not None and event.corrects not in self._ids:
            raise SessionError(
                f"correction references unknown event {event.corrects!r}")
        self._events.append(event)
        self._ids.add(event.event_id)

    def refuse_overwrite(self, event_id: str) -> None:
        raise SessionError(
            f"cannot overwrite {event_id!r}: the session log is "
            f"append-only. Record a correction as a new event that "
            f"references it instead.")

    @property
    def events(self) -> tuple[SessionEvent, ...]:
        return tuple(self._events)

    def source_events(self) -> tuple[SessionEvent, ...]:
        return tuple(e for e in self._events if e.is_source)

    def operator_events(self) -> tuple[SessionEvent, ...]:
        return tuple(e for e in self._events if not e.is_source)

    def public_view(self) -> list[dict]:
        return [e.public_view() for e in self._events]


def refuse_merge_source_into_ag(a: SessionEvent, b: SessionEvent) -> None:
    """Refuse to fold a source record and an AG note into one record."""
    if a.is_source != b.is_source:
        raise SessionError(
            "refused: a Tier-A source record and an operator (AG) note "
            "are separate provenance classes and may not be merged into a "
            "single record. Attribution integrity depends on the "
            "separation.")


def session_report() -> dict:
    return {
        "what_this_is": (
            "an append-only session archive that keeps Tier-A source "
            "records and operator (AG) notes rigorously separate and "
            "never emits private text publicly"),
        "provenance_classes": [p.value for p in Provenance],
        "ag_note_types": [t.value for t in AGNoteType],
        "evidence_statuses": list(EVIDENCE_STATUSES),
        "evidence_class": "RAW_SOURCE_RECORD and OPERATOR_NOTE, kept distinct",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "verdict": "SESSION_ARCHIVE_SOFTWARE_ONLY",
        "what_this_does_not_say": (
            "It does not endorse any recorded claim, does not treat "
            "Tier-A attribution as evidence, and does not expose private "
            "text. It records who said what, when, and refuses to merge "
            "source with operator or to overwrite history."),
    }
