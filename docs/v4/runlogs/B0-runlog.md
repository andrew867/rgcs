# Run log — Agent B0 (repository baseline)

- Agent: B0. Scope: read-only recon + baseline artifacts. No physics.
- Base commit: `2fed8fd` (v4-dev). Execution mode: DV4C-004
  (sequential in-place, orchestrator-integrated).
- Owned paths: `tools/v4/baseline/`, `docs/v4/baseline/`,
  `docs/v4/runlogs/B0-*`, `tests/v4/test_v4c_baseline.py`.
- Shared paths touched: `docs/v4/V4C_DECISION_LOG.md` (orchestrator
  file — written BY the orchestrator, recording Phase-0 resolutions
  DV4C-001..006).

## Initial state (evidence)

- HEAD 2fed8fd, branch v4-dev, clean except untracked `release/v4/`
  (generated v4.0.0 release assets, deliberately untracked).
- Authority commits 9165594/7962817/3fcb0d7/715486b: all `commit`
  (reachable).
- Tags v2.0.0..v4.0.0 present; v4.0.0 published with 9 assets.
- New-wave source files: NOT present anywhere in the repo (full
  PDF/subtitle scan + pack-zip listing) → DV4C-003.

## Commands

- `python tools/v4/baseline/scan_baseline.py` → 4 JSON artifacts.
- `pytest tests/v4/test_v4c_baseline.py` → 5 passed.
- Full-suite baseline + hosted-CI check recorded in
  `V4_TEST_AND_CI_BASELINE.md`.

## Decisions proposed → resolved by orchestrator

DV4C-001 (path), DV4C-002 (v4.1.0 target), DV4C-003 (metadata-only
sources), DV4C-004 (topology), DV4C-005 (namespaces), DV4C-006 (v3
references frozen).

## Evidence artifacts

`docs/v4/baseline/*.json` + five baseline markdown documents.
