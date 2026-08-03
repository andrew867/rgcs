"""Canonical receipt encoding and hashing."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


def canonical_receipt_bytes(receipt: Mapping[str, Any]) -> bytes:
    return (json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def receipt_digest(receipt: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_receipt_bytes(receipt)).hexdigest()


def data_file_digest(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
