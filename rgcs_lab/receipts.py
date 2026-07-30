"""Canonical JSON receipts for RGCS Lab demonstrators."""

from __future__ import annotations

import json
import subprocess
from typing import Any


def source_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True,
            stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "UNKNOWN"


def receipt(module: str, status: str, claim_class: list[str],
            inputs: dict[str, Any], models: list[dict[str, Any]],
            result: dict[str, Any], tests: list[str],
            warnings: list[str] | None = None,
            artifacts: list[str] | None = None) -> dict[str, Any]:
    body = {
        "module": module,
        "version": "rgcs-lab.receipt.v1",
        "source_commit": source_commit(),
        "status": status,
        "claim_class": claim_class,
        "inputs": inputs,
        "models": models,
        "result": result,
        "warnings": warnings or [],
        "tests": tests,
        "artifacts": artifacts or [],
    }
    # One receipt contract program-wide: every core receipt must pass
    # the canonical validator (Claude authority) before it is returned.
    from rgcs_lab.common.status_schema import validate_receipt

    validate_receipt(body)
    return body


def dumps(obj: Any) -> str:
    return json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n"

