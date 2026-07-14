"""Experiment JSON-schema validation.

Reuses ``experiments/schemas/validate.py`` (loaded by file path — it is not a
package) so the desktop app validates with the *same* registry the QA gates
use. The custom ``rgcs://`` $id scheme does not URL-join, so schemas are also
registered under their bare relative names (validate.py handles this).
"""
from __future__ import annotations

import importlib.util
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = REPO_ROOT / "experiments" / "schemas"
VALIDATE_PY = SCHEMA_DIR / "validate.py"

#: Only this major version of the run-manifest schema set is understood.
SUPPORTED_SCHEMA_MAJOR = 1
CURRENT_SCHEMA_VERSION = "1.0.0"


@lru_cache(maxsize=1)
def _validate_module():
    spec = importlib.util.spec_from_file_location("rgcs_schema_validate",
                                                  VALIDATE_PY)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise ImportError(f"cannot load {VALIDATE_PY}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@lru_cache(maxsize=1)
def schema_registry():
    """The shared referencing.Registry built by validate.py."""
    return _validate_module().build_registry()


def _validator(schema_name: str):
    from jsonschema import Draft202012Validator
    schema = json.loads((SCHEMA_DIR / schema_name).read_text())
    return Draft202012Validator(schema, registry=schema_registry())


class SchemaVersionError(ValueError):
    """Raised when an instance carries an unknown major schema_version."""


def check_schema_version(version: str) -> None:
    """Refuse unknown *major* schema versions (binding UI gate).

    Minor/patch differences are accepted; a different major is refused.
    """
    try:
        major = int(str(version).split(".")[0])
    except (ValueError, AttributeError) as exc:
        raise SchemaVersionError(f"unparseable schema_version {version!r}") from exc
    if major != SUPPORTED_SCHEMA_MAJOR:
        raise SchemaVersionError(
            f"schema_version {version!r} has major {major}; this build "
            f"understands only major {SUPPORTED_SCHEMA_MAJOR}. Refusing to "
            f"load rather than misinterpret fields.")


def validate_instance(instance: dict[str, Any],
                      schema_name: str = "run_manifest.schema.json") -> list[str]:
    """Validate a dict against a schema; returns human-readable errors
    (empty list = valid). Enforces the major-version gate first for
    schemas that carry schema_version."""
    errors: list[str] = []
    if "schema_version" in instance:
        try:
            check_schema_version(instance["schema_version"])
        except SchemaVersionError as exc:
            return [str(exc)]
    for err in sorted(_validator(schema_name).iter_errors(instance),
                      key=lambda e: list(e.absolute_path)):
        loc = "/".join(str(p) for p in err.absolute_path) or "<root>"
        errors.append(f"at {loc}: {err.message}")
    return errors


def validate_manifest_file(path: str | Path) -> list[str]:
    """Validate a manifest JSON file; malformed/binary/empty files are
    reported as ordinary validation errors instead of leaking raw
    JSONDecodeError/UnicodeDecodeError (QA-D-07)."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return [f"file is not UTF-8 text (binary?): {path}"]
    try:
        instance = json.loads(text)
    except json.JSONDecodeError as exc:
        return [f"not valid JSON (line {exc.lineno}, column {exc.colno}): "
                f"{exc.msg}"]
    return validate_instance(instance)
