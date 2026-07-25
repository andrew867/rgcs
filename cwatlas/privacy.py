"""P02 — private/public corpus boundary.

The private comms archive may contain personal narrative, source
attributions, predictions, locations, and raw vector strings. None of it may
enter public version control, builds, logs, telemetry, docs, or exports.

This module is the enforced boundary:

* **Public fixtures** are synthetic and live in the repository.
* **Private corpora** load only through an *ignored* local path (the
  ``CWATLAS_PRIVATE_DIR`` environment variable, or a ``.gitignore``-d
  directory). A private record is tagged ``PRIVATE`` on ingest.
* **Export is gated.** Any attempt to serialize a ``PRIVATE``-tagged object
  into a public artifact raises; a redaction pass strips private fields for
  a public receipt.

Nothing here reads a private path by default. Absent the env var, the
adapter yields nothing — public tests never touch private data.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class PrivacyError(RuntimeError):
    """Raised when private content would cross into a public artifact."""


class Sensitivity(Enum):
    PUBLIC_SYNTHETIC = "PUBLIC_SYNTHETIC"
    PRIVATE = "PRIVATE"


#: Fields that must never appear in a public export.
PRIVATE_FIELDS = frozenset({
    "narrative", "source_attribution", "prediction", "personal_location",
    "raw_vector_string", "operator_name", "contact", "timestamp_personal",
})

#: Forbidden literal tokens, fragment-built so this module never trips its
#: own scan.
_FORBIDDEN_TOKENS = (
    "private" + "_do_not_commit",
    "C:" + "\\Users",
    "one" + "drive - ",
)


@dataclass(frozen=True)
class Record:
    """A corpus record with an explicit sensitivity tag."""

    record_id: str
    payload: dict
    sensitivity: Sensitivity

    def is_private(self) -> bool:
        return self.sensitivity is Sensitivity.PRIVATE


def _private_dir() -> Path | None:
    """The operator's ignored private directory, or None if unset/missing."""
    env = os.environ.get("CWATLAS_PRIVATE_DIR")
    if not env:
        return None
    p = Path(env)
    return p if p.exists() else None


def load_private_records() -> list:
    """Load private records from the ignored local path.

    Returns an empty list when ``CWATLAS_PRIVATE_DIR`` is unset or missing,
    so public tests and builds never depend on private data. Each loaded
    record is tagged ``PRIVATE``.
    """
    import json
    base = _private_dir()
    if base is None:
        return []
    out = []
    for f in sorted(base.glob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        for i, item in enumerate(data if isinstance(data, list) else [data]):
            out.append(Record(f"{f.stem}:{i}", dict(item), Sensitivity.PRIVATE))
    return out


def public_fixture(record_id: str, payload: dict) -> Record:
    """Build a synthetic, public record (the only kind that ships)."""
    return Record(record_id, dict(payload), Sensitivity.PUBLIC_SYNTHETIC)


def scan_for_private(text: str) -> list:
    """Return any forbidden private path/identity tokens found in text."""
    low = text.lower()
    return [t for t in _FORBIDDEN_TOKENS if t.lower() in low]


def redact(payload: dict) -> dict:
    """Strip private fields, leaving a publishable projection."""
    return {k: v for k, v in payload.items() if k not in PRIVATE_FIELDS}


def assert_exportable(record: Record) -> dict:
    """Return the record's exportable payload, or refuse.

    A ``PRIVATE`` record can never be exported whole; a public record is
    still redacted defensively.
    """
    if record.is_private():
        raise PrivacyError(
            f"refused: record {record.record_id!r} is PRIVATE and may not be "
            f"exported to a public artifact. Redact it first, or export only "
            f"the synthetic public fixture.")
    payload = redact(record.payload)
    leftover = [k for k in payload if k in PRIVATE_FIELDS]
    if leftover:
        raise PrivacyError(
            f"refused: public export still carries private fields {leftover}")
    return payload


def refuse_private_in_public(text: str) -> None:
    """Refuse text that contains a private path/identity token."""
    hits = scan_for_private(text)
    if hits:
        raise PrivacyError(
            f"refused: text contains private tokens {hits}; public artifacts "
            f"carry no private paths or identities.")


def privacy_report() -> dict:
    return {
        "what_this_is": "the CW Atlas private/public corpus boundary",
        "private_dir_env": "CWATLAS_PRIVATE_DIR",
        "private_dir_active": _private_dir() is not None,
        "private_fields": sorted(PRIVATE_FIELDS),
        "claim_class": "SOURCE_CLAIM",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "verdict": "PRIVATE_PUBLIC_BOUNDARY_ENFORCED",
        "what_this_does_not_say": (
            "It ships no private data. Absent the ignored local path the "
            "adapter yields nothing; every public fixture is synthetic."),
    }
