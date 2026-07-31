"""R10.61A -- the Hydrogenuine evidence layer.

Every candidate carries its whole provenance chain, and superseded
results stay queryable. There is no mutable status laundering: a record
is never edited to change its verdict. A correction appends a new entry
to ``correction_history`` and the prior state remains readable.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import subprocess

REQUIRED_FIELDS = (
    "source_artifact", "source_hash", "representation_recipe",
    "framing_profile", "decoder_profile", "null_family",
    "hypothesis_count", "result_class", "correction_history",
    "software_commit",
)

RESULT_CLASSES = (
    "NO_PARSE", "STRUCTURAL_PARSE_ONLY", "CONVENTIONAL_TEXT_CANDIDATE",
    "ERROR_CONTROL_CANDIDATE", "RGCS_ENVELOPE_CANDIDATE",
    "RGCS_ROUTE_CANDIDATE", "ARCHIVE_ARTIFACT", "INSTRUMENT_ARTIFACT",
    "NULL_COMPATIBLE", "REPLICATION_REQUIRED",
)

#: Human-readable byte scales. IEC, because archives are quoted in GiB.
_SCALES = ((1024 ** 4, "TiB"), (1024 ** 3, "GiB"),
           (1024 ** 2, "MiB"), (1024, "KiB"), (1, "B"))


class EvidenceError(ValueError):
    """A candidate is missing required provenance."""


def human_bytes(n: int, places: int = 3) -> str:
    """Format bytes with a DECIMAL POINT, never a thousands separator.

    R10.61 printed ``4,912 GiB`` for an archive of ``4.912 GiB`` -- a
    thousand-fold overstatement produced purely by formatting. This
    function is the fix and is pinned by regression test.
    """
    n = int(n)
    for scale, unit in _SCALES:
        if abs(n) >= scale or scale == 1:
            v = n / scale
            return f"{v:.{places}f} {unit}" if unit != "B" else f"{n} B"
    return f"{n} B"


def software_commit() -> str:
    try:
        return subprocess.run(("git", "rev-parse", "HEAD"),
                              capture_output=True, text=True,
                              timeout=30).stdout.strip() or "unknown"
    except Exception:                                   # noqa: BLE001
        return "unknown"


def candidate(source_artifact: str, source_hash: str,
              representation_recipe: str, framing_profile: str,
              decoder_profile: str, null_family: str,
              hypothesis_count: int, result_class: str,
              correction_history=None, **extra) -> dict:
    """Build a fully-provenanced candidate record."""
    if result_class not in RESULT_CLASSES:
        raise EvidenceError(
            f"{result_class!r} is not a permitted result class")
    rec = {
        "schema": "rgcs.r1061a.evidence-candidate.v1",
        "source_artifact": source_artifact,
        "source_hash": source_hash,
        "representation_recipe": representation_recipe,
        "framing_profile": framing_profile,
        "decoder_profile": decoder_profile,
        "null_family": null_family,
        "hypothesis_count": int(hypothesis_count),
        "result_class": result_class,
        "correction_history": list(correction_history or []),
        "software_commit": software_commit(),
        "recorded_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(
            timespec="seconds"),
        **extra,
    }
    missing = [f for f in REQUIRED_FIELDS if f not in rec]
    if missing:
        raise EvidenceError(f"candidate missing {missing}")
    rec["candidate_id"] = hashlib.sha256(
        json.dumps({k: rec[k] for k in REQUIRED_FIELDS if k
                    != "correction_history"},
                   sort_keys=True, default=str).encode()).hexdigest()[:16]
    return rec


def supersede(rec: dict, reason: str, replaced_by: str | None = None) -> dict:
    """Mark a candidate superseded WITHOUT destroying it.

    Returns a new record. The original stays byte-identical and
    queryable; the correction is appended, never applied in place.
    """
    out = json.loads(json.dumps(rec, default=str))
    out["correction_history"] = list(rec.get("correction_history", [])) + [{
        "at_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(
            timespec="seconds"),
        "action": "SUPERSEDED",
        "reason": reason,
        "replaced_by": replaced_by,
        "prior_result_class": rec.get("result_class"),
        "prior_candidate_id": rec.get("candidate_id"),
    }]
    out["superseded"] = True
    out["queryable"] = True
    return out


def ledger_summary(candidates) -> dict:
    """Counts by result class and by framing profile. Superseded included."""
    rows = list(candidates)
    by_class, by_profile = {}, {}
    for c in rows:
        by_class[c["result_class"]] = by_class.get(c["result_class"], 0) + 1
        p = c.get("framing_profile", "?")
        by_profile[p] = by_profile.get(p, 0) + 1
    return {
        "schema": "rgcs.r1061a.evidence-ledger.v1",
        "candidates": len(rows),
        "superseded": sum(1 for c in rows if c.get("superseded")),
        "by_result_class": dict(sorted(by_class.items())),
        "by_framing_profile": dict(sorted(by_profile.items())),
        "all_carry_full_provenance": all(
            all(f in c for f in REQUIRED_FIELDS) for c in rows),
        "no_status_laundering": "superseded records retain their prior "
                                "result class in correction_history and "
                                "remain queryable",
    }
