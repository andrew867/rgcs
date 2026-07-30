"""Canonical receipt builder for lab modules."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from rgcs_lab.common.gitmeta import source_commit
from rgcs_lab import __version__


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True)


def receipt_sha256(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


def build_receipt(
    *,
    module: str,
    status: str,
    claim_class: list[str],
    inputs: dict[str, Any],
    models: list[Any],
    result: dict[str, Any],
    tests: list[str] | None = None,
    warnings: list[str] | None = None,
    artifacts: list[Any] | None = None,
    version: str | None = None,
) -> dict[str, Any]:
    """Build a receipt matching schemas/lab/receipt.schema.json."""
    body = {
        "module": module,
        "version": version or __version__,
        "source_commit": source_commit(),
        "status": status,
        "claim_class": list(claim_class),
        "inputs": inputs,
        "models": models,
        "result": result,
        "warnings": warnings or [],
        "tests": tests or [],
        "artifacts": artifacts or [],
    }
    # One receipt contract program-wide: a receipt that violates the
    # canonical schema must never be written silently (AA-01).
    from rgcs_lab.common.status_schema import validate_receipt

    validate_receipt(body)
    body["receipt_sha256"] = receipt_sha256(
        {k: v for k, v in body.items() if k != "receipt_sha256"}
    )
    return body
