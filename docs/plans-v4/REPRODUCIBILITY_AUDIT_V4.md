# Reproducibility Audit — RGCS v4 (Agent 13 Role B)

| item | method | result |
|---|---|---|
| One-command bundle (G25) | `python -m rscs2_core.proofbundle` from clean workspace (also step 8 of `tools/demo_v4.py`) | succeeds; exit 0 |
| Checksums (G26) | `rgcs-v4 verify-checksums` recomputes SHA256 of every bundle file | 110/110 OK |
| Bit determinism | TWO independent builds, SHA256 compare of every data artifact (CSV/JSON/MD/STL/OBJ/GLB/MSH) | bit-identical after V4-D-003 (ARPACK v0 + meshio OBJ timestamp — both registered, fixed, regression-tested) |
| Declared nondeterminism | figures (PNG/PDF) may embed renderer metadata; SOFTWARE_VERSIONS.json is environment-descriptive by design | scoped out explicitly in the audit, documented here |
| Mesh determinism | gmsh rebuild → identical node/tet SHA256 (Agent 05 + geometry_hashes.json) | green |
| Solver determinism | two identical solves bit-equal (regression test) | green |
| Copied artifacts | ONLY acceleration/* (hardware-dependent) and benchmarks/tuning_fork.csv; both listed in PROVENANCE.json | verified — nothing else copied |
| Environment record | SOFTWARE_VERSIONS.json: Python/numpy/scipy/skfem/meshio/gmsh/platform | present |
| Seeds | single SEED constant (20260716); no Date.now-style inputs | verified |
| Demo record | runtime, peak memory (real Win32 query), device, artifacts, hashes | demo_out/demo_run_record.json |
| Frozen history (G1) | git diff vs 715486b over archive/v2.0.0 empty; tags v2.0.0/v3.0.0/v3.0.1 present | green |

Residual caveat (declared): bit-identity is verified on THIS machine's
environment; across OS/BLAS versions, last-digit float drift is
expected — the same scoping as the v3 D-V3-04 decision. Cross-platform
CI verifies tolerance-level correctness, not byte equality.
