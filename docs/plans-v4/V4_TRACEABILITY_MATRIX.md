# V4 Traceability Matrix

**Status:** PLANNING. Every v4 requirement → spec → id(s) → test
category → benchmark → milestone. The executing run fills the concrete
test node ids; this pass fixes the mapping so no requirement is
unowned or untested (planning-QA rule).

## Requirement → spec → ids → tests → milestone

| Requirement | Spec | RSCS2 ids | Test categories | Benchmark | M |
|---|---|---|---|---|---|
| Import geometry + frames | GEOMETRY_AND_MESH | G.1 | unit, serialization, adversarial | — | M2 |
| Tet/surface mesh + quality + tags | GEOMETRY_AND_MESH | G.2/G.3/G.4/G.5/G.6 | unit, determinism, adversarial | V.8 mesh | M2 |
| Sparse generalized eigensolve | CPU_SOLVER | S.1/S.2/S.3/S.4 | golden, residual, orthogonality | V.1/V.5 | M3 |
| Boundary models | CPU_SOLVER | B.1–B.4 | unit, golden | V.2 | M3 |
| Analytic benchmarks | REFERENCE_SYSTEMS | V.1/V.2/V.3/V.5 | golden, convergence | V.1–V.5 | M3 |
| Isotropic elasticity (L1) | PIEZO_MULTIPHYSICS | E.1/E.2 | golden, energy-balance | V.5 | M3 |
| Anisotropic quartz (L2) | ANISOTROPIC_QUARTZ | E.3/E.4 | conservative-ext | **V.6** | M4 |
| Piezoelectric (L3) | PIEZO_MULTIPHYSICS | E.5 | golden, dimensional | V.7 | M4 |
| Coupled-mode reduction | CPU_SOLVER | S.6/E.12 | conservative-ext | **V.9** | M4 |
| Accelerator abstraction | ACCELERATOR_BACKEND | A.1/A.2 | contract, fallback | — | M5 |
| CUDA/OpenCL + parity | ACCELERATOR_BACKEND | A.3/A.4/A.5 | parity, memory, float-policy | — | M5 |
| Eye diagnostics family | EYE_DIAGNOSTICS | D.1–D.15 | unit, dimensional, guard, null-model | V.10 | M6 |
| Eye consensus + robustness | EYE_DIAGNOSTICS | D.0 | null-model, artifact-injection, persistence | V.10 | M6 |
| Optical/photoelastic (L5) | OPTICAL_MODELLING | E.8/E.9 | golden, conservative-ext | — | M6 |
| Coil/EM projection (L5) | COIL_AND_EM | E.10/E.11 | golden, energy-balance, leakage | — | M6 |
| Thermal/fixture (L4) | PIEZO_MULTIPHYSICS | E.6/E.7 | golden vs v3 band | — | M6 |
| Tuning fork | REFERENCE_SYSTEMS | V.4 | golden, convergence | **V.4** | M7 |
| Cantilever EB/Timoshenko | REFERENCE_SYSTEMS | V.2/V.3 | golden, MAC | V.2/V.3 | M7 |
| Datasets + provenance | DATA_AND_INVERSE | U.* datasets | licence-lint, leakage | — | M7 |
| Inverse fitting + UQ | DATA_AND_INVERSE | U.1–U.6 | recover-truth, null-model, MC-anchor | — | M7 |
| Visualization + report | VISUALIZATION_AND_REPORTING | — | visual-regression, freshness, mathtext-lint | — | M8 |
| Desktop/CLI + resumable | DESKTOP_AND_CLI | — | contract, recovery, migration | — | M8 |
| Manuscripts + QA + release | RELEASE_PLAN | — | doc-freshness, adversarial | all | M8 |

## Non-functional requirements → coverage

| NFR | Where enforced |
|---|---|
| CPU-only always usable | ACCEPTANCE global #3; dep policy DV4-005 |
| Determinism/reproducibility | SYSTEM_ARCHITECTURE §4; serialization tests |
| No new physics | MATHEMATICAL_MODEL_PLAN; provenance lint |
| Classification firewall | claim/provenance lint (every RSCS2-* object) |
| Safety envelope | OPTICAL/COIL specs; safety lint (RV4-15) |
| Frozen-path immutability | CI frozen-diff gate (RV4-14) |
| No unearned GPU claim | ACCELERATOR four-status ladder; claim lint |

## Planning-QA audit result

Every requirement in the brief maps to ≥1 spec, ≥1 RSCS2 id (or an
explicit "no new id" note), and ≥1 test category. Crystal is the primary
example; fork + cantilever are mandatory gates; CPU-only is preserved at
every milestone; no high-power/human-exposure content; the eye stays
non-EST; V.6/V.9 keep v4 a conservative extension of v3.
