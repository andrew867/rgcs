"""Resolve the source commit for receipts without requiring a dirty tree."""

from __future__ import annotations

import os
import subprocess
from functools import lru_cache


@lru_cache(maxsize=1)
def source_commit() -> str:
    env = os.environ.get("RGCS_SOURCE_COMMIT") or os.environ.get("GITHUB_SHA")
    if env:
        return env[:40]
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=5,
        )
        return out.strip()[:40]
    except (OSError, subprocess.SubprocessError):
        return "unknown"
