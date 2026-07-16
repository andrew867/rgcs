# V4 Implementation Plan — 8 tranches, 32 phases

**Status:** PLANNING. Each phase is independently reviewable with
measurable exit criteria, stop conditions, and a partial-release option.
Every phase follows the **Hydrogenuine iteration format**: PRODUCT
impact · SPEC changes · TEST changes · IMPLEMENTATION changes · RISKS ·
ACCEPTANCE · EVIDENCE ARTIFACTS · ROLLBACK. Below, each phase gives its
scope + exit criteria; the executing run expands each into the full
Hydrogenuine block (template in `V4_HANDOFF.md` §Iteration-template).

## Tranche A — Foundations (P1–P4) → milestone M1

| P | Scope | Exit criteria |
|---|---|---|
| P1 | Baseline-freeze audit; confirm v2/v3 immutability; create `rscs2_core` skeleton + registry namespaces | frozen-path diff empty; `RSCS2-*` registry file exists (schema, 0 entries); v3 suite still green |
| P2 | Requirements → id registration; author machine-registry rows for the RSCS2-* objects this tranche needs | every planned id has a stub row (id/sig/units/class/prov/excl/module/tests/doc) |
| P3 | Dependency proof-of-concepts + **licence audit** (scikit-fem, meshio, Gmsh-as-tool, CuPy/PyOpenCL import-only) | PoC scripts run on CPU; licence table committed; GPL isolation (Gmsh subprocess) demonstrated |
| P4 | **Backend selection decision** (confirm/adjust DV4-005/007) with evidence | decision-log row; CPU stack pinned; GPU backends chosen + status ladder wired |

**Partial release:** none (foundations). **Stop condition:** if scikit-fem
cannot meet the CPU-authority need → escalate (candidate: PETSc/SLEPc
optional, or custom assembly) before P5.

## Tranche B — Geometry & Mesh (P5–P8) → M2

| P | Scope | Exit |
|---|---|---|
| P5 | Geometry import (SCAD-export, STL/OBJ; STEP/Gmsh where feasible) + coordinate-frame provenance | import round-trip; frame recorded |
| P6 | Tetra/surface meshing via Gmsh subprocess + meshio; P1/P2 elements | deterministic element counts from a manifest |
| P7 | Region/boundary/electrode/coil/optical/fixture tags + coverage validation | tag-coverage test green; malformed-input loud |
| P8 | Deterministic mesh manifest + quality diagnostics | manifest verifier; quality-floor enforcement |

**Partial release:** `v4.0.0-alpha0` (meshing toolkit). **Stop:** STEP
import may be dropped to "documented-unsupported" without blocking.

## Tranche C — CPU Elastic Solver (P9–P12) → M3 (first usable product)

| P | Scope | Exit |
|---|---|---|
| P9 | scikit-fem assembly (K,M) + sparse generalized eigensolve; isotropic L1 | V.1 (rod), V.5 (cube) within tol |
| P10 | Analytic benchmarks: EB beam, Timoshenko, mesh convergence | **V.2, V.3, V.8 green** (mandatory gates) |
| P11 | Rigid-body handling, normalization, orthogonality/residual, boundaries B.1–B.4 | orthogonality + residual + rigid-mode tests |
| P12 | Harmonic response + convergence estimator + deterministic serialization | FRF sweep; serialization round-trip |

**Partial release:** `v4.0.0-alpha (CPU elastic + benchmarks)` — a
genuinely useful modal solver even if nothing above ships. **Stop:** a
benchmark that will not converge halts the tranche for solver review.

## Tranche D — Anisotropy & Piezo (P13–P16) → M4

| P | Scope | Exit |
|---|---|---|
| P13 | Anisotropic α-quartz elasticity (L2) + Bond rotation | **V.6 Christoffel anchor green** (conservative ext.) |
| P14 | Full crystal modes + taxonomy + free/loaded boundaries | taxonomy stable across refine; loaded-shift vs v3 band |
| P15 | Piezoelectric coupling (L3) + single-element validation | **V.7 green**; coupled eigenproblem |
| P16 | Coupled-mode reduction reproducing frozen 2-mode picture | **V.9 splitting anchor green** |

**Partial release:** `v4.0.0-beta (crystal multiphysics L1–L3)`.

## Tranche E — Acceleration (P17–P20) → M5

| P | Scope | Exit |
|---|---|---|
| P17 | Backend-neutral seam (RSCS2-A.1) + capability detection + CPU fallback | seam contract tests; fallback logged |
| P18 | CuPy backend + interface tests + parity harness | INTERFACE_TESTED; parity on a GPU runner if available |
| P19 | PyOpenCL backend + interface + memory budgeting | INTERFACE_TESTED; tiling correctness |
| P20 | Precision policy + parity-evidence harness + status ladder wiring | f32 error-bound recording; ladder statuses recorded |

**Partial release:** acceleration ships **experimental**; CPU remains
authority. **Stop / honest status:** without hardware, ceiling is
NUMERICALLY_PARITY_TESTED (only if a runner exists) else INTERFACE_TESTED.

## Tranche F — Eye Diagnostics & Projections (P21–P24) → M6

| P | Scope | Exit |
|---|---|---|
| P21 | Diagnostic family RSCS2-D.1..15 (each unit+dimensional+guard tested) | all 15 tested; guards on D.9/D.10/D.11 |
| P22 | Optical/photoelastic (L5) + coil/EM drive projection | Snell/OPL/photoelastic vs frozen; leakage control |
| P23 | Thermal + fixture perturbations (L4) | thermal-drift sign/mag vs v3; fixture band |
| P24 | Eye Consensus Functional + robustness battery + NULL verdict | **V.10 green**; NULL-model test; taxonomy labels |

**Partial release:** `v4.0.0-beta (eye diagnostics)`; eye candidates are
DER/HYP with robustness, or NULL.

## Tranche G — Reference Systems & Inverse (P25–P28) → M7

| P | Scope | Exit |
|---|---|---|
| P25 | Tuning fork (Example 2) full validation | **V.4 green** + convergence |
| P26 | Cantilever EB/Timoshenko (Example 3) + optional 4th | MAC ≥ 0.99; Timoshenko case |
| P27 | Datasets (synthetic + public, licence-recorded) | provenance/licence rows; leakage test |
| P28 | Inverse fitting + UQ + Bayesian/deterministic + held-out + null | recover-the-truth; null comparison; MC-vs-linear anchor |

**Partial release:** `v4.0.0-rc (validated + inverse)`.

## Tranche H — Interfaces & Release (P29–P32) → M8

| P | Scope | Exit |
|---|---|---|
| P29 | Visualization + auto report + provenance graph | visual-regression + report-freshness green |
| P30 | Desktop/CLI + workspace manifests + resumable jobs | CLI contract; resumability; migration |
| P31 | Manuscripts (generated numbers) + **adversarial QA pass** | 0 undefined/overfull; QA defect register |
| P32 | Integration + release build + **tag v4.0.0** (only if gates green) | full gate table GREEN; artifacts + checksums; Zenodo |

**Partial release:** `v4.0.0`. **Stop:** any red conservative-extension
anchor (V.6/V.9) or mandatory benchmark (V.2/V.3/V.4) blocks the tag.

## Cross-tranche rules

- CPU-only usable at **every** milestone from M3.
- Each tranche has a partial-release option (above) so value ships even
  if later tranches slip.
- Every phase updates the traceability matrix and (where claims/risks
  change) the living registers.
