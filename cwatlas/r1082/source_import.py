"""P03 -- private provenance and source-registry import.

Import the communications-derived source-vector registry and its anchor
records as **typed provenance**, without ever exposing private narrative.

The privacy boundary (System Contract "Privacy"):

* private records load **only** through the ignored local path in
  :mod:`cwatlas.privacy` (the ``CWATLAS_PRIVATE_DIR`` env var). Absent that
  path the adapter yields nothing, so public tests and builds never touch
  private data;
* every public record is **synthetic** and is referred to by an **opaque
  fixture id** (for example ``SRC_SYN_0001``). The user-reported Stonehenge
  training anchor is referenced by the opaque id ``STONEHENGE_PRIVATE_001`` --
  never by its raw vector or narrative in a public artifact;
* a record's ``narrative`` (and any other private field) is **never exported**.
  :meth:`SourceVectorRecord.public_projection` strips private fields through
  :func:`cwatlas.privacy.redact`; :meth:`assert_exportable` refuses if any
  private field survives.

Provenance is typed onto the existing
:mod:`cwatlas.provenance_ledger` hash chain: each imported record contributes a
``MESSAGE`` (or ``SOURCE_TIMESTAMP`` / ``CORRECTION``) event bound to the
immutable SHA-256 of its raw string. All vectors register with body status
``UNKNOWN`` unless a body is explicitly assigned (Locked Decisions: unlabeled
vectors are not silently guessed).

Nothing here asserts a vector is a real location or that its source origin is
validated. An imported record is, at most, a ``SOURCE`` / ``SOURCE_CLAIM``.

    SOURCE_ORIGIN_NOT_VALIDATED
    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from cwatlas import privacy
from cwatlas import provenance_ledger as pl
from cwatlas.r1082 import claims

#: The opaque public id for the Stonehenge training anchor. Public tests and
#: artifacts reference the anchor by this id only -- never the raw vector or
#: any narrative.
STONEHENGE_FIXTURE_ID = "STONEHENGE_PRIVATE_001"

#: Fields carried on a record that must never reach a public export. These are
#: the private-narrative fields; :mod:`cwatlas.privacy` owns the master list.
NARRATIVE_FIELDS = frozenset({"narrative", "notes", "label", "prediction"})


class ImportError_(RuntimeError):
    """Raised on a malformed record or a private-narrative export attempt."""


class BodyStatus(Enum):
    """Whether a vector's body is unknown or explicitly assigned."""

    UNKNOWN = "unknown"
    ASSIGNED = "assigned"


class RecordUse(Enum):
    """How a record is used relative to calibration."""

    TRAINING_ANCHOR = "training_anchor"
    HOLDOUT = "holdout"
    UNCLASSIFIED = "unclassified"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class SourceVectorRecord:
    """A typed, imported source-vector record with an enforced privacy split.

    ``fixture_id`` is an opaque public id. ``raw`` is the exact source string
    and ``raw_hash`` its immutable SHA-256. ``tokens`` is the five-token
    base-100 route core. ``body_status`` defaults to ``UNKNOWN`` and only
    becomes ``ASSIGNED`` when ``body`` is set explicitly. ``sensitivity``
    tags the record public-synthetic or private. ``_private`` holds narrative
    fields that never leave this object.
    """

    fixture_id: str
    raw: str
    tokens: Tuple[int, ...]
    raw_hash: str
    body_status: BodyStatus = BodyStatus.UNKNOWN
    body: Optional[str] = None
    use: RecordUse = RecordUse.UNCLASSIFIED
    sensitivity: privacy.Sensitivity = privacy.Sensitivity.PUBLIC_SYNTHETIC
    _private: Dict = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        if not self.fixture_id:
            raise ImportError_("fixture_id must be a non-empty opaque id")
        if self.raw_hash != _sha256(self.raw):
            raise ImportError_(
                "raw_hash does not match raw string: the original source "
                "string is immutable")
        if self.body is not None and self.body_status is not BodyStatus.ASSIGNED:
            raise ImportError_(
                "a record with an explicit body must be BodyStatus.ASSIGNED")
        if self.body is None and self.body_status is BodyStatus.ASSIGNED:
            raise ImportError_(
                "BodyStatus.ASSIGNED requires an explicit body")

    def is_private(self) -> bool:
        return self.sensitivity is privacy.Sensitivity.PRIVATE

    def public_projection(self) -> dict:
        """The publishable projection: opaque id, hash, tokens -- no narrative.

        Private narrative fields are stripped through
        :func:`cwatlas.privacy.redact`; the raw string and any narrative never
        appear. The result is safe for a public receipt or log line.
        """
        projection = {
            "fixture_id": self.fixture_id,
            "raw_hash": self.raw_hash,
            "tokens": list(self.tokens),
            "body_status": self.body_status.value,
            "body": self.body,
            "use": self.use.value,
            "claim_class": claims.EvidenceClass.SOURCE.value,
        }
        # Defensive: never emit narrative or the raw source string.
        redacted = privacy.redact({**projection, **self._private})
        return {k: v for k, v in redacted.items()
                if k in projection and k not in NARRATIVE_FIELDS}

    def assert_exportable(self) -> dict:
        """Return the public projection, or refuse if it carries private data.

        Refuses a private-tagged record outright, and refuses if any narrative
        field would leak. This is the export firewall for the source registry.
        """
        if self.is_private():
            raise privacy.PrivacyError(
                f"refused: source record {self.fixture_id!r} is PRIVATE and may "
                f"not be exported to a public artifact; export the synthetic "
                f"public fixture instead")
        projection = self.public_projection()
        leaked = [k for k in projection if k in NARRATIVE_FIELDS]
        leaked += [k for k in projection if k in privacy.PRIVATE_FIELDS]
        if leaked:
            raise privacy.PrivacyError(
                f"refused: public export of {self.fixture_id!r} still carries "
                f"private fields {sorted(set(leaked))}")
        # A raw source string never belongs in an export.
        if "raw" in projection:
            raise privacy.PrivacyError(
                "refused: the raw source string is never exported")
        return projection


@dataclass(frozen=True)
class AnchorRecord:
    """A calibration anchor referenced by an opaque fixture id.

    The Stonehenge training anchor is imported as an :class:`AnchorRecord` with
    ``fixture_id = STONEHENGE_FIXTURE_ID`` and ``use = TRAINING_ANCHOR``. Its
    narrative label ("Stonehenge") is a private field and is not stored on the
    public record; only the opaque id is public.
    """

    fixture_id: str
    use: RecordUse
    sensitivity: privacy.Sensitivity = privacy.Sensitivity.PUBLIC_SYNTHETIC

    def public_projection(self) -> dict:
        return {"fixture_id": self.fixture_id, "use": self.use.value}


class SourceImport:
    """A registry of imported source-vector and anchor records.

    Public construction uses synthetic vectors referenced by opaque ids;
    :meth:`from_private` loads private records through
    :func:`cwatlas.privacy.load_private_records` (empty absent the ignored
    path). Importing also extends a :class:`cwatlas.provenance_ledger.Ledger`,
    binding every record's raw string to an immutable hash-chained event.
    """

    def __init__(self, ledger: Optional[pl.Ledger] = None) -> None:
        self._vectors: Dict[str, SourceVectorRecord] = {}
        self._anchors: Dict[str, AnchorRecord] = {}
        self.ledger = ledger if ledger is not None else pl.Ledger()

    def __len__(self) -> int:
        return len(self._vectors)

    @property
    def vectors(self) -> Tuple[SourceVectorRecord, ...]:
        return tuple(self._vectors[k] for k in self._vectors)

    @property
    def anchors(self) -> Tuple[AnchorRecord, ...]:
        return tuple(self._anchors[k] for k in self._anchors)

    def register_vector(
        self,
        fixture_id: str,
        raw: str,
        tokens,
        *,
        epoch: float,
        body: Optional[str] = None,
        use: RecordUse = RecordUse.UNCLASSIFIED,
        sensitivity: privacy.Sensitivity = privacy.Sensitivity.PUBLIC_SYNTHETIC,
        narrative: Optional[dict] = None,
    ) -> SourceVectorRecord:
        """Register one source vector and append its provenance event.

        Body status is ``UNKNOWN`` unless ``body`` is explicitly given, in
        which case it becomes ``ASSIGNED``. ``narrative`` (private) is held
        internally and never exported. ``epoch`` is a decimal year passed in
        by the caller -- never a wall-clock read.
        """
        if fixture_id in self._vectors:
            raise ImportError_(f"duplicate fixture_id {fixture_id!r}")
        status = BodyStatus.ASSIGNED if body is not None else BodyStatus.UNKNOWN
        record = SourceVectorRecord(
            fixture_id=fixture_id,
            raw=raw,
            tokens=tuple(int(t) for t in tokens),
            raw_hash=_sha256(raw),
            body_status=status,
            body=body,
            use=use,
            sensitivity=sensitivity,
            _private=dict(narrative or {}),
        )
        self._vectors[fixture_id] = record
        # Typed provenance: bind the raw string to the hash chain. The event
        # carries the opaque id and hash, never the narrative.
        self.ledger.append(
            kind=pl.EventKind.MESSAGE,
            source_id=fixture_id,
            epoch=epoch,
            raw=raw,
        )
        return record

    def register_anchor(
        self,
        fixture_id: str,
        use: RecordUse = RecordUse.TRAINING_ANCHOR,
        sensitivity: privacy.Sensitivity = privacy.Sensitivity.PUBLIC_SYNTHETIC,
    ) -> AnchorRecord:
        """Register a calibration anchor by opaque id."""
        anchor = AnchorRecord(fixture_id, use, sensitivity)
        self._anchors[fixture_id] = anchor
        return anchor

    def register_stonehenge_anchor(self) -> AnchorRecord:
        """Register the Stonehenge training anchor by its opaque fixture id.

        The anchor is public *as an opaque id*: the raw vector and the label
        "Stonehenge" stay private. It is a training anchor, so it is never
        scored as a holdout prediction.
        """
        return self.register_anchor(
            STONEHENGE_FIXTURE_ID, use=RecordUse.TRAINING_ANCHOR)

    @classmethod
    def from_private(cls, epoch: float) -> "SourceImport":
        """Import the private registry, or an empty one absent the local path.

        Reads only through :func:`cwatlas.privacy.load_private_records`, which
        returns nothing unless ``CWATLAS_PRIVATE_DIR`` points at an existing
        (ignored) directory. Every loaded record is tagged ``PRIVATE`` and its
        narrative fields are held internally, never exported.
        """
        imp = cls()
        for rec in privacy.load_private_records():
            payload = rec.payload
            raw = str(payload.get("raw", ""))
            if not raw:
                continue
            tokens = payload.get("tokens", [])
            narrative = {k: payload[k] for k in NARRATIVE_FIELDS if k in payload}
            body = payload.get("body")
            imp.register_vector(
                rec.record_id,
                raw,
                tokens,
                epoch=epoch,
                body=body,
                sensitivity=privacy.Sensitivity.PRIVATE,
                narrative=narrative,
            )
        return imp

    def export_public(self) -> dict:
        """A public projection of the whole import, narrative-free.

        Raises through the export firewall if any registered record is private
        or would leak a narrative field. Public builds call this to emit a safe
        receipt of what was imported.
        """
        return {
            "vector_count": len(self._vectors),
            "anchor_count": len(self._anchors),
            "vectors": [v.assert_exportable() for v in self.vectors],
            "anchors": [a.public_projection() for a in self.anchors],
            "ledger_head": self.ledger.head(),
        }


def source_import_report() -> dict:
    """What this module claims -- and, deliberately, what it does not."""
    return {
        "module": "cwatlas.r1082.source_import",
        "phase_id": "P03",
        "private_dir_env": "CWATLAS_PRIVATE_DIR",
        "private_dir_active": privacy.privacy_report()["private_dir_active"],
        "stonehenge_fixture_id": STONEHENGE_FIXTURE_ID,
        "body_status_default": BodyStatus.UNKNOWN.value,
        "narrative_fields_never_exported": sorted(NARRATIVE_FIELDS),
        "guarantees": [
            "private records load only via the ignored CWATLAS_PRIVATE_DIR",
            "public records are synthetic, referenced by opaque fixture ids",
            "a record's narrative field is never exported",
            "unlabeled vectors keep body status UNKNOWN (never guessed)",
            "the Stonehenge anchor is referenced by an opaque id only",
        ],
        "claim_class": claims.EvidenceClass.SOURCE.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "physical_effects": "PHYSICAL_EFFECTS_NOT_CLAIMED",
        "source_origin": "SOURCE_ORIGIN_NOT_VALIDATED",
        "verdict": "PRIVATE_PROVENANCE_IMPORTED_NO_NARRATIVE_EXPOSED",
        "what_this_does_not_say": (
            "An imported source record is a reported SOURCE claim. Importing it "
            "as typed provenance validates neither its origin nor any "
            "geographic meaning, and never publishes its private narrative."),
    }
