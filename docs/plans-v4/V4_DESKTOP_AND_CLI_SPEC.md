# V4 Desktop & CLI Spec

**Status:** PLANNING. CLI is first-class (CI + remote/HPC); desktop
extends the v3 workbench with v4 panels as **thin views over tested
headless services** (the T2 discipline). No scientific capability lives
only in the GUI.

## 1. CLI (`rgcs4`) — headless, scriptable, resumable

| Command | Does |
|---|---|
| `rgcs4 mesh <geom> --tags … -o mesh.manifest` | import + mesh + tag + manifest |
| `rgcs4 solve <mesh.manifest> --level L2 --modes N --backend cpu` | assemble + eigensolve |
| `rgcs4 eye <modes> --diagnostics all --uq 200 --refine 0,1,2` | eye battery + robustness + verdict |
| `rgcs4 bench <name>` | run a reference benchmark vs its truth |
| `rgcs4 fit <dataset> --model frf --holdout 0.3` | inverse fit + null comparison |
| `rgcs4 report <run>` | generate the figures + report |
| `rgcs4 backends` | list devices + per-op parity status |

- **Deterministic & resumable:** every command reads/writes a workspace
  manifest; long jobs checkpoint (mesh, matrices, modes, MC samples) and
  resume; a killed job resumes from the last checkpoint (failure-safe
  persistence, extends v3).
- **Backend/device selection** explicit (`--backend cpu|cuda|opencl`);
  default cpu; a requested backend without a parity record for an op
  falls back to cpu with a logged downgrade.
- Suitable for HPC: no GUI import, offscreen rendering, JSON/`.npz`
  everywhere, exit codes + JUnit for CI.

## 2. Desktop (extends `rgcs_desktop`)

New panels, each a thin view over a headless service (tested without
Qt):
- **model builder wizard** (geometry params → mesh → tags);
- **solver configuration** (level, modes, boundary, backend/device);
- **run monitor** (progress, checkpoints, cancel/resume);
- **result comparison** (spectra, fields, eye verdicts side-by-side);
- **eye-diagnostic viewer** (field + regions + confidence + the four
  comparisons + NULL panel);
- **provenance graph** (extends v3 service to RSCS2-* ids);
- **screenshot/export automation**.

## 3. Workspace / project manifests

A v4 workspace manifest references geometry, mesh manifests, solver
configs, runs, datasets, and reports — each by id + checksum; the
provenance spine (§V4_SYSTEM_ARCHITECTURE) threads through it. Extends
the v3 workspace schema; migration hook for older workspaces (fail-loud
on unknown schema, per v3 crystal_db pattern).

## 4. Tests

CLI command contract tests (headless); resumability test (kill →
resume → identical result within tolerance); backend-fallback test
(request GPU without parity → cpu + logged downgrade); workspace-manifest
round-trip + migration; desktop-service tests without Qt; offscreen
screenshot harness; malformed-workspace adversarial (loud failure);
exit-code/JUnit correctness for CI.
