# Repository truth note (Cursor / integration)

Date: 2026-07-26  
Branch: `program/cursor-app-integration`  
Start commit: `eb7d7d4`

## What already exists

- `rgcs_coordinate` — stable public structural codec (F5|Q22|S3), CLI
  `rgcs-coordinate`, claim classes, golden fixtures, projection marked
  `UNDERDETERMINED` / YELLOW.
- `workbench/index.html` — approved zero-network structural decoder demo.
  Cursor reuses it; does not reimplement packet math in new JS.
- Broad multiphysics stack (`rscs2_core`, `cwatlas`, R6–R15) remains
  upstream of this public demonstrator hub.

## What Cursor is adding

- `rgcs_lab` — unified Recursive Infrastructure Lab: status/receipt schema,
  FastAPI local server (loopback default), nine-module static hub, CLI
  `rgcs-lab`, adapters that prefer domain packages when present.
- Reference adapters under `rgcs_lab/reference/` supply deterministic
  Golay / frame / lattice / metasurface / memory / dual-pole / prediction
  demos so the hub can ship before Codex domain packages land. Adapters
  import `rgcs_golay`, `rgcs_frames`, etc. when available and displace
  the reference path without UI changes.

## Physics honesty

- Physical Earth projection remains YELLOW.
- Spoof-SPP high-fidelity path remains YELLOW; reduced-order passive
  examples are IMPLEMENTED_SOFTWARE / CONVENTIONAL_PHYSICS.
- Prospective predictions freeze as YELLOW until measurement receipts exist.
- No antigravity, torsion-as-free-explanation, or vacuum-energy claims.

## Sibling worktrees

At claim time, `../rgcs-claude` and `../rgcs-codex` were not present.
Integration merges those branches when handoffs arrive; this branch does
not merge itself into `program/integration`.
