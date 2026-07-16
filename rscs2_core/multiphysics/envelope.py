"""Public result envelope (Agent M2; shared contract section 4).

Every v4-completion public result serializes through make_result:
classification is checked against the M1 source ceilings (laundering
blocked at the envelope), NOT_APPLICABLE results carry null values and
a reason code — never a fake numeric zero."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from ..provenance_v4 import check_classification, load_sources

SCHEMA_VERSION = "rgcs.v4.result.1"
_ALLOWED_CLASS = ("CORE_VALIDATED", "REDUCED_ORDER_VALIDATED",
                  "INTERFACE_ONLY", "SOURCE_HYPOTHESIS",
                  "NOT_APPLICABLE")
_ALLOWED_TAGS = ("EST", "DER", "HYP", "SRC", "ENG")
_REPO = Path(__file__).resolve().parents[2]
_SOURCES = None


def _commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"],
                              capture_output=True, text=True,
                              cwd=_REPO, check=True).stdout.strip()
    except Exception:
        return "UNKNOWN"


def make_result(module_id: str, material_id: str, classification: str,
                evidence_tags: list[str], value, units: dict,
                source_ids: list[str] | None = None,
                equation_ids: list[str] | None = None,
                uncertainty: dict | None = None,
                assumptions: list[str] | None = None,
                applicability: str = "APPLICABLE",
                warnings: list[str] | None = None,
                generated_at_utc: str = "1970-01-01T00:00:00Z"
                ) -> dict:
    """Build a schema-conformant result envelope. Deterministic by
    default (fixed epoch timestamp unless the caller supplies one)."""
    global _SOURCES
    if classification not in _ALLOWED_CLASS:
        raise ValueError(f"bad classification {classification}")
    bad = set(evidence_tags) - set(_ALLOWED_TAGS)
    if bad:
        raise ValueError(f"bad evidence tags {bad}")
    if classification == "NOT_APPLICABLE" and value is not None:
        raise ValueError("NOT_APPLICABLE results must carry a null "
                         "value, never a numeric stand-in")
    # anti-laundering at the envelope: classification respects every
    # cited source's ceiling
    if _SOURCES is None:
        _SOURCES = load_sources()
    for sid in (source_ids or []):
        if classification != "NOT_APPLICABLE":
            check_classification(sid, classification, _SOURCES)
    env = {
        "schema_version": SCHEMA_VERSION,
        "module_id": module_id,
        "material_id": material_id,
        "classification": classification,
        "evidence_tags": sorted(evidence_tags),
        "applicability": applicability,
        "value": value,
        "units": units,
        "uncertainty": uncertainty or {},
        "assumptions": assumptions or [],
        "source_ids": sorted(source_ids or []),
        "equation_ids": sorted(equation_ids or []),
        "implementation_commit": _commit(),
        "generated_at_utc": generated_at_utc,
        "warnings": warnings or [],
    }
    payload = json.dumps(
        {k: env[k] for k in ("module_id", "material_id", "value",
                             "units", "classification")},
        sort_keys=True, default=str)
    env["result_id"] = hashlib.sha256(
        payload.encode()).hexdigest()[:24]
    return env


def not_applicable_result(module_id: str, material_id: str,
                          reason_code: str, reason: str) -> dict:
    env = make_result(module_id, material_id, "NOT_APPLICABLE",
                      ["ENG"], None, {},
                      applicability="NOT_APPLICABLE")
    env["reason_code"] = reason_code
    env["reason"] = reason
    return env


def dumps(env: dict) -> str:
    """Deterministic serialization."""
    return json.dumps(env, sort_keys=True, indent=2, default=str)
