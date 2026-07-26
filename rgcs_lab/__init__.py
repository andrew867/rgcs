"""RGCS Recursive Infrastructure Lab — public demonstrator hub.

Integrates nine modules behind one local FastAPI server and one static
hub. Domain mathematics lives in adapters (preferring Codex packages when
installed). This package owns wiring, receipts, privacy defaults, and UI.
"""

from __future__ import annotations

__version__ = "0.1.0.dev0"
PRODUCT_NAME = "RGCS Recursive Infrastructure Lab"
PRODUCT_HEADLINE = (
    "Recursive infrastructure you can inspect, run, and falsify."
)

MODULES = (
    "coordinate",
    "golay",
    "frames",
    "memory",
    "dual_pole",
    "lattice",
    "metasurface",
    "predictions",
    "proofs",
)

__all__ = [
    "__version__",
    "PRODUCT_NAME",
    "PRODUCT_HEADLINE",
    "MODULES",
]
