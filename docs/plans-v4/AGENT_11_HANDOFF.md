# Agent 11 Handoff — Canonical 110 mm Proof Bundle

Status: COMPLETE. `proof_bundle_110mm/` (111 files, 1.8 MB) generated
by ONE deterministic command; SHA256 verification 110/110 OK.

**VERDICT: CONVENTIONAL_NODE_FOUND** (engine status
CONVENTIONAL_NODE_EXPLAINS_RESULT; scrambled-field null control
NO_STABLE_CANDIDATE; not forced — the same verdict reproduces at both
fast/coarse and full mesh resolutions).

## The one command

    python -m rscs2_core.proofbundle          # full resolution
    python -m rscs2_core.proofbundle OUT --fast   # smoke variant

Implemented in `rscs2_core/proofbundle.py` (`build_bundle`). Agent 12
wraps it as `rgcs-v4 proof-bundle canonical-110`.

## What the bundle contains (all from actual solver output)

- Top level: README, VERDICT.json, INPUT_MANIFEST, PROVENANCE,
  SOFTWARE_VERSIONS, DEVICE_CAPABILITY_REPORT (copied from agent07),
  SHA256SUMS.txt.
- geometry/: ideal + nominal records, 3-level meshes (VTU), msh, STL,
  OBJ, GLB (minimal binary glTF writer — no external deps),
  crystal.step.status.json (STEP declared NOT generated: built-in
  kernel geometry; OCC path documented/implemented/untested,
  DV4-013), quality CSV, deterministic hashes.
- material/: frozen quartz stiffness/piezo/dielectric/orientation +
  the ±1% uncertainty policy.
- benchmarks/: live recomputes (cantilever, static deflection, patch
  tests, Christoffel vs frozen axes, Lamé cube, cavity, mesh
  convergence) + tuning_fork.csv copied from agent10 (declared).
- modes/: eigenvalues (ideal AND nominal), residuals, orthogonality,
  mode VTUs 001–006 + selected 008/010.
- fields/: displacement/strain/kinetic/stress/overlap/vorticity CSVs,
  LIVE static piezo D5 solve (10 V electrode pair), optical probe
  paths + photoelastic projection, coil on-axis pair field, phase
  status record (D9/D10 degenerate for undamped real modes, declared).
- eye/: full consensus rerun (coarse+fine meshes, cradle boundary
  variant, 3 material draws), diagnostics.csv, candidates/consensus
  JSON, persistence/uncertainty/centre/conventional-node CSVs,
  scrambled-field no-candidate control.
- figures/: all 17 required figures, PNG + vector PDF, from real data.
- reports/: PROOF_BUNDLE_REPORT.md + .pdf, KNOWN_PHYSICS_COMPARISON,
  LIMITATIONS, REPRODUCTION.

## Notes for Agent 13 (QA/release)

- Verdict vocabulary mapping is documented in the module docstring.
- Copied artifacts (acceleration/, tuning_fork.csv) are declared in
  PROVENANCE.json — QA should check nothing else is copied.
- `rscs2_core` is not yet in pyproject packaging; Agent 12/13 adds it
  with the `rgcs-v4` entry point before release.
