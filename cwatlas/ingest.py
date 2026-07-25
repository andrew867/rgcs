"""P41 -- raw vector ingest with exact byte and string preservation.

The inverse decoder starts here: a vector arrives *pasted*, *scanned*,
*grouped*, *dashed*, or *tokenized*, and the first duty is to keep it exactly
as it arrived. System Contract invariant 1 -- the original string (its bytes)
is immutable -- is enforced at this boundary before any decode is attempted.

An :class:`IngestedVector` holds three things that never contradict each other:

* ``raw_bytes`` -- the **exact original bytes**, immutable. This is
  authoritative; nothing downstream may mutate it.
* ``content_hash`` -- a SHA-256 that *binds* the raw bytes. A record whose hash
  does not match its bytes is refused at construction, so a silently altered
  original cannot masquerade as the source.
* ``normalized`` -- a **separate, derived view** (whitespace removed) offered
  for convenience. It never replaces the original; helpers such as
  :meth:`IngestedVector.digits_only` and :meth:`IngestedVector.stripped_of`
  produce further views on demand, again without touching the bytes.

Ingest asserts nothing geographic. A raw vector is a ``SOURCE_CLAIM`` -- what a
source wrote -- and nothing more.

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED

All derivation is deterministic and depends only on the bytes passed in.
"""

from __future__ import annotations

import hashlib
import unicodedata
from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Optional, Union

from cwatlas import claims

#: The only claim class an ingested raw vector may carry: it records what a
#: source wrote, never a geographic meaning.
ALLOWED_CLASS = claims.ClaimClass.SOURCE_CLAIM

#: Separators stripped when a caller asks for a grouping-free view. These are
#: the characters that appear in grouped / dashed / tokenized numeric inputs.
GROUPING_SEPARATORS = (
    " ", "\t", "\n", "\r", " ",  # whitespace incl. non-breaking space
    "-", "‐", "‑", "‒", "–", "—",  # hyphens / dashes
    "_", "|", ",", "/", ".",  # common grouping punctuation
)

#: ASCII + unicode whitespace stripped for the always-available normalized view.
_WHITESPACE = (" ", "\t", "\n", "\r", "\f", "\v", " ")


class IngestError(ValueError):
    """Raised on a malformed ingest or a byte/hash integrity violation."""


class IngestForm(Enum):
    """The shape an input arrived in. Recorded, never used to mutate bytes."""

    PASTED = "PASTED"
    SCANNED = "SCANNED"
    GROUPED = "GROUPED"
    DASHED = "DASHED"
    TOKENIZED = "TOKENIZED"
    RAW = "RAW"


def _sha256_bytes(data: bytes) -> str:
    """The immutable content hash of the raw bytes (invariant 1)."""
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _normalize_view(text: str) -> str:
    """A derived view: NFC-normalized text with all whitespace removed.

    Safe for every input -- it removes only whitespace, so it never corrupts a
    canonical vector's ``=``/``;`` structure or a signed field. It is a *view*;
    the original bytes are untouched.
    """
    nfc = unicodedata.normalize("NFC", text)
    return "".join(ch for ch in nfc if ch not in _WHITESPACE)


def detect_form(text: str) -> IngestForm:
    """A deterministic heuristic for how an input was grouped.

    Advisory only: the form is metadata, never a licence to rewrite the bytes.
    """
    if any(d in text for d in ("-", "–", "—", "‐", "‑", "‒")):
        return IngestForm.DASHED
    if any(w in text for w in (" ", "\t", " ")):
        return IngestForm.TOKENIZED
    if any(sep in text for sep in ("_", "|", ",", "/")):
        return IngestForm.GROUPED
    return IngestForm.RAW


@dataclass(frozen=True)
class IngestedVector:
    """A raw source vector held with its exact bytes preserved.

    ``raw_bytes`` is authoritative and immutable. ``raw_text`` is the decoded
    string when the bytes are valid text under ``encoding`` (else ``None`` and
    ``encoding == "bytes"``). ``content_hash`` binds the bytes; a mismatch is a
    typed refusal. ``normalized`` is a derived whitespace-free view.
    """

    ingest_id: str
    raw_bytes: bytes
    raw_text: Optional[str]
    encoding: str
    content_hash: str
    normalized: str
    form: IngestForm
    claim_class: claims.ClaimClass

    def __post_init__(self) -> None:
        if not self.ingest_id:
            raise IngestError("ingest_id must be a non-empty string")
        if not isinstance(self.raw_bytes, bytes):
            raise IngestError("raw_bytes must be immutable bytes")
        # Invariant 1: the content hash must bind the immutable raw bytes.
        if self.content_hash != _sha256_bytes(self.raw_bytes):
            raise IngestError(
                "content_hash does not bind raw_bytes: the original vector is "
                "immutable and must not be altered after ingest (invariant 1)")
        if self.claim_class is not ALLOWED_CLASS:
            raise claims.ClaimError(
                f"refused: an ingested raw vector is a {ALLOWED_CLASS.value}; "
                f"{self.claim_class.value} is not permitted -- ingest asserts "
                f"nothing geographic (SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_"
                f"CLAIMED)")

    def verify_integrity(self) -> bool:
        """``True`` iff the stored hash still binds the immutable raw bytes."""
        return self.content_hash == _sha256_bytes(self.raw_bytes)

    def is_text(self) -> bool:
        return self.raw_text is not None

    def stripped_of(self, separators: Iterable[str] = GROUPING_SEPARATORS) -> str:
        """A derived view with the given separators removed (bytes untouched).

        Refused on a non-text (binary) vector: there is no string to strip.
        """
        if self.raw_text is None:
            raise IngestError(
                "cannot produce a stripped view of a non-text (binary) vector")
        drop = frozenset(separators)
        return "".join(ch for ch in self.raw_text if ch not in drop)

    def digits_only(self) -> str:
        """A derived view keeping only ASCII digits (grouped/dashed numbers).

        This is the input the nine-digit legacy codec search consumes when a
        numeric vector arrived grouped or dashed. It never mutates the original.
        """
        if self.raw_text is None:
            raise IngestError(
                "cannot extract digits from a non-text (binary) vector")
        return "".join(ch for ch in self.raw_text if ch.isascii() and ch.isdigit())

    def to_dict(self) -> dict:
        """A JSON-safe projection. ``raw_bytes`` is rendered as a hex string."""
        return {
            "ingest_id": self.ingest_id,
            "raw_hex": self.raw_bytes.hex(),
            "raw_text": self.raw_text,
            "encoding": self.encoding,
            "content_hash": self.content_hash,
            "normalized": self.normalized,
            "form": self.form.value,
            "claim_class": self.claim_class.value,
        }


def ingest(
    data: Union[str, bytes],
    *,
    ingest_id: str,
    form: Optional[IngestForm] = None,
    encoding: str = "utf-8",
) -> IngestedVector:
    """Ingest a raw vector, preserving its exact bytes (invariant 1).

    ``data`` may be text (encoded to bytes under ``encoding``) or raw bytes
    (decoded to text when possible, else kept as opaque bytes with
    ``encoding == "bytes"``). ``form`` defaults to a deterministic heuristic on
    the text; on binary input it defaults to :attr:`IngestForm.RAW`. Nothing is
    cleaned, coerced, or interpreted -- the normalized view is derived beside
    the original, never in place of it.
    """
    if not ingest_id:
        raise IngestError("ingest_id must be a non-empty string")
    if isinstance(data, bytes):
        raw_bytes = data
        try:
            raw_text: Optional[str] = data.decode(encoding)
            enc = encoding
        except (UnicodeDecodeError, LookupError):
            raw_text = None
            enc = "bytes"
    elif isinstance(data, str):
        raw_text = data
        try:
            raw_bytes = data.encode(encoding)
        except (UnicodeEncodeError, LookupError) as exc:
            raise IngestError(f"cannot encode input under {encoding!r}: {exc}") from exc
        enc = encoding
    else:
        raise IngestError(
            f"ingest expects str or bytes, got {type(data).__name__}")
    if raw_bytes == b"":
        raise IngestError("empty vector; refusing to ingest nothing")
    normalized = _normalize_view(raw_text) if raw_text is not None else ""
    if form is None:
        form = detect_form(raw_text) if raw_text is not None else IngestForm.RAW
    return IngestedVector(
        ingest_id=ingest_id,
        raw_bytes=raw_bytes,
        raw_text=raw_text,
        encoding=enc,
        content_hash=_sha256_bytes(raw_bytes),
        normalized=normalized,
        form=form,
        claim_class=ALLOWED_CLASS,
    )


def refuse_mutated_original(*_a, **_k) -> None:
    """The original bytes are immutable; a rewrite of them is refused."""
    raise IngestError(
        "refused: the ingested original is immutable (invariant 1). Derive a "
        "normalized view instead of altering the raw bytes.")


def ingest_report() -> dict:
    """What this module claims -- and, deliberately, what it does not."""
    return {
        "module": "cwatlas.ingest",
        "phase_id": "P41",
        "tranche": "T06",
        "forms": [f.value for f in IngestForm],
        "guarantees": [
            "exact original bytes preserved and immutable (invariant 1)",
            "content hash binds the raw bytes; a mismatch is refused",
            "normalized and stripped views are derived beside, never in place of, the original",
            "no unit, coordinate, or geographic meaning assigned",
        ],
        "claim_class": ALLOWED_CLASS.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "RAW_VECTOR_INGEST_BYTE_PRESERVING_IMMUTABLE_ORIGINAL",
        "what_this_does_not_say": (
            "Ingest records the exact bytes a source wrote. It assigns no unit "
            "and no location; the vector stays a SOURCE_CLAIM until a codec, a "
            "calibration, and prospective evidence say otherwise."),
    }
