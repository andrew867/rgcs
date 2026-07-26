"""RGCS Recursive Infrastructure Lab — shared program package.

The provisional public product name is ``RGCS Recursive Infrastructure
Lab`` (renameable only through a recorded architecture decision; see
``docs/program/ADR-001-product-name.md``).

Layout (three-agent protocol; see
``docs/program/coordination/CLAIMED_FILES_*.txt``):

* ``rgcs_lab.common``    — shared status/claim schema and receipt
  validation (Claude authority; Codex and Cursor consume, not redefine)
* ``rgcs_lab.authority`` — physics truth gate, hub registry, workstream
  specification modules (Claude)
* ``rgcs_lab.golay`` / ``frames`` / ``lattice`` / ``metasurface`` /
  ``memory`` engines — Codex core algorithms (not present until Codex
  lands them; nothing here stubs them)
* ``rgcs_lab.api`` / ``cli`` / ``web`` — Cursor integration surfaces

Program-wide wording rules come from the Physics Truth Gate and the
Project Authority Lock; the machine-readable versions live in
:mod:`rgcs_lab.authority.physics_truth_gate` and
:mod:`rgcs_lab.common.status_schema`.
"""

__version__ = "0.1.0.dev0"

PRODUCT_NAME = "RGCS Recursive Infrastructure Lab"
