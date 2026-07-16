# Agent 12 Handoff — CLI, Demo, and User Guide

Status: COMPLETE. 9 CLI tests (incl. mandatory offscreen render +
checksum round trip); scripted demo passes all 10 steps end-to-end.

## Delivered

- `rscs2_core/cli.py` — `rgcs-v4` / `python -m rscs2_core.cli` with 14
  commands: devices, geometry, mesh, material, modes, sweep, piezo,
  optical, coil, diagnostics, refsystems, proof-bundle, report,
  verify-checksums. Spec target
  `rgcs-v4 proof-bundle canonical-110 --backend auto --refinement all`
  works (the flags are recorded; the bundle always runs all levels).
- `pyproject.toml`: `rscs2_core*` added to packaging, `rgcs-v4` entry
  point, `tests/v4` added to default testpaths, registry YAML shipped
  as package data.
- `tools/demo_v4.py` — clean-workspace scripted demo: detect devices →
  generate both crystals → mesh → validated modes (asserts 6 rigid) →
  static piezo field → eye diagnostics → offscreen screenshots →
  proof bundle → checksum verify → exit 0. Records runtime, peak
  memory (Win32 K32GetProcessMemoryInfo with explicit argtypes —
  ctypes without argtypes silently fails on x64), device, artifact
  paths, hashes into `demo_out/demo_run_record.json`.
  Last run: 19.6 s (--fast), peak 437.9 MB, verdict
  CONVENTIONAL_NODE_FOUND, checksums 110/110.
- `docs/USER_GUIDE_V4.md` — install, CLI table, bundle, demo, API
  one-pager, honesty rails.
- `tests/v4/test_rscs2_cli.py` — parser coverage, JSON/CSV outputs,
  sweep backend policy, checksum tamper detection, offscreen PNG
  render, gmsh-skippable mesh manifest.

## Desktop staging (declared)

v4-specific GUI views are STAGED past v4.0.0 (the spec's staging
clause permits this when CLI + offscreen rendering cover every
function — they do, tested). The v3 desktop app is untouched.

## For Agent 13

- `demo_out/` and `cli_work/` are gitignored (generated).
- CI should run `pytest` (testpaths now include tests/v4) and
  `python tools/demo_v4.py --fast` on hosted runners; gmsh-dependent
  tests self-skip where gmsh is absent.
- Version in pyproject is still 3.0.1 — bump to 4.0.0 at release.
