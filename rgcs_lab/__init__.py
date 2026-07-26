"""RGCS Recursive Infrastructure Lab — shared program package.

The provisional public product name is ``RGCS Recursive Infrastructure
Lab`` (renameable only through a recorded architecture decision; see
``docs/program/ADR-001-product-name.md``).

Layout (three-agent protocol; see
``docs/program/coordination/CLAIMED_FILES_*.txt`` and
``docs/program/integration/CONFLICT_RESOLUTION.md``):

* ``rgcs_lab.common``    — shared status/claim schema and receipt
  validation (Claude authority; Codex and Cursor consume, not redefine)
* ``rgcs_lab.authority`` — physics truth gate, hub registry, workstream
  specification modules (Claude)
* ``rgcs_lab.golay`` / ``frames`` / ``lattice`` / ``metasurface`` /
  ``memory`` / ``dual_pole`` — Codex core algorithms (the executed
  cores behind every GREEN receipt)
* ``rgcs_lab.adapters`` / ``api`` / ``cli`` / ``reference`` — Cursor
  integration surfaces; adapters execute Codex cores and only fall
  back to labelled reference demos (never GREEN) if a core is missing

Program-wide wording rules come from the Physics Truth Gate and the
Project Authority Lock; the machine-readable versions live in
:mod:`rgcs_lab.authority.physics_truth_gate` and
:mod:`rgcs_lab.common.status_schema`.
"""

from __future__ import annotations

__version__ = "0.1.0.dev0"

PRODUCT_NAME = "RGCS Recursive Infrastructure Lab"
PRODUCT_HEADLINE = (
    "Recursive infrastructure you can inspect, run, and falsify."
)

# Imported AFTER the constants above: rgcs_lab.common.receipts reads
# rgcs_lab.__version__ during package import, so the constants must
# already exist on this partially-initialised module.
from rgcs_lab.common.status_schema import MODULES  # noqa: E402

__all__ = [
    "__version__",
    "PRODUCT_NAME",
    "PRODUCT_HEADLINE",
    "MODULES",
]
