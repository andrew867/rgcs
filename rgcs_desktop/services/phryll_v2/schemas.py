"""Phryll v2 schema validation.

These schemas use schema major 2 and live as packaged data — kept
deliberately outside the experiments/schemas registry, whose UI gate
pins major 1 for the run-manifest family.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

SCHEMA_FILES = {
    "crystal_profile": "phryll_v2_crystal_profile.schema.json",
    "cone_design": "phryll_v2_cone_design.schema.json",
    "coil_sleeve": "phryll_v2_coil_sleeve.schema.json",
    "reference_asset": "phryll_v2_reference_asset.schema.json",
}


@lru_cache(maxsize=None)
def _validator(kind: str):
    from jsonschema import Draft202012Validator
    schema = json.loads((DATA_DIR / SCHEMA_FILES[kind])
                        .read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


def validate(kind: str, instance: dict[str, Any]) -> list[str]:
    """Human-readable schema errors (empty list = valid)."""
    if kind not in SCHEMA_FILES:
        raise KeyError(f"unknown phryll v2 schema kind {kind!r}")
    errors = []
    for err in sorted(_validator(kind).iter_errors(instance),
                      key=lambda e: list(e.absolute_path)):
        loc = "/".join(str(p) for p in err.absolute_path) or "<root>"
        errors.append(f"at {loc}: {err.message}")
    return errors
