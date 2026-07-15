"""Crystal database persistence (RGCS v3, Agent 08; schema from crystal
application section 9).

A JSON-file crystal database: each record carries the specimen geometry,
measured crystallographic orientation (feeds the anisotropic model),
density, environmental/fixture descriptors, and per-field uncertainty.
Explicit `schema_version` with a forward migration hook so later agents can
evolve the record shape without silent breakage. JSON is null-not-NaN.

Classification: pure engineering persistence; embedded VALUES keep their
own classes (a Source-claim dimension stays flagged in its provenance
note, exactly as in the v2 specimen schema).
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Callable

from .provenance import classified

__all__ = ["CRYSTAL_DB_SCHEMA_VERSION", "new_record", "save_db", "load_db",
           "add_record", "get_record", "migrate"]

CRYSTAL_DB_SCHEMA_VERSION = 1

#: Forward-migration hooks: version -> function(old_db_dict) -> new_db_dict.
#: Registered by future agents; version N hook migrates N-1 -> N.
_MIGRATIONS: dict[int, Callable[[dict[str, Any]], dict[str, Any]]] = {}


def _require_finite_positive(name: str, v: Any) -> float:
    if not (isinstance(v, (int, float)) and math.isfinite(v) and v > 0):
        raise ValueError(f"{name} must be positive and finite")
    return float(v)


@classified("Derived", sources=("RGCS_CRYSTAL_APPLICATION.md section 9",),
            note="uncertainty-aware crystal record: geometry + orientation "
                 "+ environment descriptors, each value with optional sigma")
def new_record(specimen_id: str, length_mm: float, diameter_wide_mm: float,
               diameter_narrow_mm: float, facet_count: int,
               density_kg_m3: float = 2648.0,
               orientation_euler_zxz_deg: dict[str, float] | None = None,
               uncertainties: dict[str, float] | None = None,
               environment: dict[str, Any] | None = None,
               provenance_note: str = "") -> dict[str, Any]:
    """Build one validated crystal-database record."""
    if not specimen_id or not isinstance(specimen_id, str):
        raise ValueError("specimen_id must be a non-empty string")
    rec: dict[str, Any] = {
        "specimen_id": specimen_id,
        "length_mm": _require_finite_positive("length_mm", length_mm),
        "diameter_wide_mm": _require_finite_positive(
            "diameter_wide_mm", diameter_wide_mm),
        "diameter_narrow_mm": _require_finite_positive(
            "diameter_narrow_mm", diameter_narrow_mm),
        "facet_count": int(facet_count),
        "density_kg_m3": _require_finite_positive(
            "density_kg_m3", density_kg_m3),
        "orientation_euler_zxz_deg": orientation_euler_zxz_deg,
        "orientation_known": orientation_euler_zxz_deg is not None,
        "uncertainties": {},
        "environment": dict(environment or {}),
        "provenance_note": provenance_note,
    }
    if rec["facet_count"] < 3:
        raise ValueError("facet_count must be >= 3")
    for key, sigma in (uncertainties or {}).items():
        if key not in rec:
            raise ValueError(f"uncertainty for unknown field {key!r}")
        if not (isinstance(sigma, (int, float)) and math.isfinite(sigma)
                and sigma >= 0):
            raise ValueError(f"uncertainty for {key!r} must be >= 0")
        rec["uncertainties"][key] = float(sigma)
    return rec


@classified("Derived", sources=(),
            note="JSON persistence with explicit schema_version; "
                 "null-not-NaN (v2 rule)")
def save_db(records: list[dict[str, Any]], path: str | Path) -> Path:
    """Write the database file (schema-versioned, sorted, canonical)."""
    seen: set[str] = set()
    for r in records:
        sid = r.get("specimen_id")
        if not sid:
            raise ValueError("every record needs a specimen_id")
        if sid in seen:
            raise ValueError(f"duplicate specimen_id {sid!r}")
        seen.add(sid)
    doc = {"schema_version": CRYSTAL_DB_SCHEMA_VERSION,
           "records": sorted(records, key=lambda r: r["specimen_id"])}
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(doc, indent=2, sort_keys=True, allow_nan=False)
    p.write_text(text, encoding="utf-8")
    return p


@classified("Derived", sources=(),
            note="loads any known schema version and migrates forward to "
                 "the current one via registered hooks; unknown versions "
                 "fail loudly")
def load_db(path: str | Path) -> list[dict[str, Any]]:
    """Load a database file, migrating older schema versions forward."""
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    doc = migrate(doc)
    return list(doc["records"])


@classified("Derived", sources=(),
            note="stepwise forward migration; missing hook = loud failure "
                 "(no silent reinterpretation of old records)")
def migrate(doc: dict[str, Any]) -> dict[str, Any]:
    """Migrate a loaded database dict to CRYSTAL_DB_SCHEMA_VERSION."""
    version = doc.get("schema_version")
    if not isinstance(version, int) or version < 1:
        raise ValueError("database missing a valid integer schema_version")
    if version > CRYSTAL_DB_SCHEMA_VERSION:
        raise ValueError(
            f"database schema {version} is newer than this software "
            f"({CRYSTAL_DB_SCHEMA_VERSION}); upgrade instead of guessing")
    while version < CRYSTAL_DB_SCHEMA_VERSION:
        hook = _MIGRATIONS.get(version + 1)
        if hook is None:
            raise ValueError(f"no migration registered for schema "
                             f"{version} -> {version + 1}")
        doc = hook(doc)
        version = doc["schema_version"]
    return doc


@classified("Derived", sources=(),
            note="pure append with duplicate-id rejection")
def add_record(records: list[dict[str, Any]],
               record: dict[str, Any]) -> list[dict[str, Any]]:
    """Return records + record, rejecting duplicate specimen ids."""
    if any(r["specimen_id"] == record["specimen_id"] for r in records):
        raise ValueError(f"duplicate specimen_id {record['specimen_id']!r}")
    return [*records, record]


@classified("Derived", sources=(),
            note="exact-id lookup; loud KeyError when absent")
def get_record(records: list[dict[str, Any]],
               specimen_id: str) -> dict[str, Any]:
    """Exact-id lookup; loud KeyError when absent."""
    for r in records:
        if r["specimen_id"] == specimen_id:
            return r
    raise KeyError(f"no record with specimen_id {specimen_id!r}")
