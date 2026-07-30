"""Domain adapters — execute the Codex cores; reference is fallback only.

The Codex cores ship inside this package (``rgcs_lab.golay``,
``rgcs_lab.frames``, ``rgcs_lab.memory``, ``rgcs_lab.dual_pole``,
``rgcs_lab.lattice``, ``rgcs_lab.metasurface``), so in a normal
install every adapter runs the real core. The labelled reference
demos under ``rgcs_lab.reference`` remain as an explicit fallback
mode ONLY: when a fallback runs, the result status is capped at
YELLOW and a fallback warning is attached — a fallback can never
produce a GREEN executed-core receipt
(docs/program/integration/CONFLICT_RESOLUTION.md, IR-03).
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

CODEX_BACKEND = "codex"
REFERENCE_BACKEND = "reference"

FALLBACK_WARNING = (
    "REFERENCE FALLBACK IN USE — Codex core unavailable; this run is "
    "not an executed-core receipt and cannot be GREEN"
)


def resolve_core(core: str, fallback: str) -> tuple[Any, str]:
    """Import the Codex core module, else the labelled reference demo.

    Returns ``(module, backend)`` where backend is ``"codex"`` or
    ``"reference"``.
    """
    try:
        return import_module(core), CODEX_BACKEND
    except ImportError:
        return import_module(fallback), REFERENCE_BACKEND


def guard_fallback(status: Any, backend: str,
                   warnings: list[str]) -> Any:
    """Cap the status at YELLOW and warn when a fallback executed."""
    from rgcs_lab.common.status import Status

    if backend == CODEX_BACKEND:
        return status
    warnings.append(FALLBACK_WARNING)
    if Status(status) == Status.GREEN:
        return Status.YELLOW
    return status
