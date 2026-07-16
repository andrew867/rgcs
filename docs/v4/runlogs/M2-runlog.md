# Run log — Agent M2 (capability firewall + coupled-state core)

- Base commit: `db96882`. Mode: DV4C-004.
- Owned paths: `rscs2_core/multiphysics/`, `schemas/v4/
  material_capabilities.schema.json`, `tests/v4/test_v4c_capability.py`,
  `docs/v4/V4_MULTIPHYSICS_MODEL.md`,
  `docs/v4/V4_MATERIAL_CAPABILITY_MATRIX.md` (generated),
  `docs/v4/runlogs/M2-*`.
- Shared file touched: `rscs2_core/cli.py` (new `capabilities`
  command) — orchestrator-integrated in this same commit.

## Delivered

MaterialCapabilities (24 typed capability records/material, schema-
backed), 16 registered materials/references (quartz + 15), the
applicability service (UNKNOWN ≠ permission), the 13-block coupling
graph with pre-numeric edge rejection and a graph-level
source_hypothesis quarantine, the rgcs.v4.result.1 envelope with
ceiling-checked classification and no-fake-zero enforcement, generated
public capability matrix + per-material what-is-not-supported, CLI
integration.

## Tests

`pytest tests/v4/test_v4c_capability.py` → **13 passed**; CLI
regression 22 passed combined. Gates C1 (schema+records validate),
C2/E5 (quartz negatives with reasons), C3 (null value + reason code),
C4 (edge rejection incl. LiNiPO4-positive/quartz-negative pair and
source_hypothesis quarantine), C5 (matrix complete) — all PASS.

## Notes for downstream agents

Every module in M3–M14 must (a) resolve its material via
`get_material`, (b) call `applicability` (or build a CouplingGraph)
before computing, (c) emit results via `make_result` /
`not_applicable_result`. Q1 attacks these paths directly.
