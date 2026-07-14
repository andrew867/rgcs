"""Read-only access to docs/model_registry.yaml (model browser backend)."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "docs" / "model_registry.yaml"


@lru_cache(maxsize=1)
def load_registry() -> dict[str, Any]:
    return yaml.safe_load(REGISTRY_PATH.read_text())


def models() -> list[dict[str, Any]]:
    return list(load_registry().get("models", []))


def model_by_id(model_id: str) -> dict[str, Any] | None:
    for m in models():
        if m.get("id") == model_id:
            return m
    return None
