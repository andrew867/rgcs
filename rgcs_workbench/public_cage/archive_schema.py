"""MOD-007 source and provenance archive schema -- ledger, not proof.

Field and status validation for the public archive: every record has
a source type, every mirrored file has a hash, community submissions
start unverified and can be promoted only through the four intake
steps, and reposts never merge into originals.

The private archive DATA stays in the private repository. Only this
schema is public, which is exactly the release-filter boundary.

This module does provenance-ledger validation. It does not claim
source authentication. Public archive record import remains pending.
"""

from __future__ import annotations

STATUS = "PUBLIC_ARCHIVE_RECORD"

#: Required archive fields (spec pack, MOD-007).
REQUIRED_FIELDS = (
    "record_id", "source_type", "original_url", "access_datetime",
    "local_datetime", "title", "author_or_channel", "capture_method",
    "raw_file_hash", "rendered_file_hash", "transcript_hash",
    "operator_note_hash", "repost_status", "redirect_status",
    "copyright_status_note", "claim_boundary",
)

SOURCE_TYPES = (
    "PUBLIC_WEB",
    "MIRRORED_PUBLIC_WEB",
    "VIDEO_TRANSCRIPT",
    "PDF_SOURCE",
    "IMAGE_SOURCE",
    "OPERATOR_NOTE",
    "COMMUNITY_SUBMISSION_UNVERIFIED",
    "THIRD_PARTY_REPOST",
    "ESTATE_OR_DOMAIN_RISK",
    "SUPERSEDED_RECORD",
)

#: The four promotion steps for community submissions (spec pack).
PROMOTION_STEPS = (
    "original_source_recovery",
    "timestamp_capture",
    "duplicate_check",
    "technical_claim_extraction",
)

#: Fields that may legitimately be marked absent, but must say so
#: explicitly rather than being omitted (a dead link is a fact).
_EXPLICIT_ABSENT = ("NONE", "NOT_APPLICABLE", "DEAD_LINK", "NO_REDIRECT")


class PromotionRefused(RuntimeError):
    """Raised when a community submission skips an intake step."""


def validate_record(record: dict) -> list[str]:
    problems = [f"archive record missing field '{field}'"
                for field in REQUIRED_FIELDS
                if field not in record or record[field] in (None, "")]
    source_type = record.get("source_type")
    if source_type and source_type not in SOURCE_TYPES:
        problems.append(f"unknown source_type '{source_type}'")
    if source_type == "MIRRORED_PUBLIC_WEB":
        h = str(record.get("raw_file_hash", ""))
        if h.upper() in _EXPLICIT_ABSENT or len(h) < 32:
            problems.append("a mirrored file must carry a real raw file "
                            "hash")
    if record.get("source_type") == "THIRD_PARTY_REPOST":
        if not record.get("repost_of_record_id"):
            problems.append("a repost must reference the original record "
                            "id; reposts are never merged into originals")
    return problems


def community_intake(record: dict) -> dict:
    """Anything from group chat starts unverified, whatever it says."""
    entry = dict(record)
    entry["source_type"] = "COMMUNITY_SUBMISSION_UNVERIFIED"
    entry["verified"] = False
    entry["promotion_steps_completed"] = []
    return entry


def promote_community_submission(record: dict, steps_completed) -> dict:
    """Promotion requires all four steps, each named, in the record."""
    done = set(steps_completed)
    missing = [s for s in PROMOTION_STEPS if s not in done]
    if missing:
        raise PromotionRefused(
            f"community submission cannot be promoted; missing intake "
            f"steps: {missing}")
    promoted = dict(record)
    promoted["source_type"] = "PUBLIC_WEB"
    promoted["verified"] = True
    promoted["promotion_steps_completed"] = list(PROMOTION_STEPS)
    return promoted


def load_public_records() -> list[dict]:
    """Load the imported public-safe seed records; each must validate."""
    import json
    import pathlib
    data = json.loads(
        (pathlib.Path(__file__).resolve().parent
         / "archive_records.json").read_text(encoding="utf-8"))
    records = data["records"]
    for record in records:
        problems = validate_record(record)
        if problems:
            raise ValueError(f"invalid imported archive record "
                             f"{record.get('record_id')}: {problems}")
    return records


__all__ = ["STATUS", "REQUIRED_FIELDS", "SOURCE_TYPES",
           "PROMOTION_STEPS", "PromotionRefused", "validate_record",
           "community_intake", "promote_community_submission",
           "load_public_records"]
