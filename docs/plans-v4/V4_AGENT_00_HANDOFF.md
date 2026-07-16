# Agent 00 Handoff — Baseline, Dependencies, and the M3 Solver Blocker

**Date:** 2026-07-16. **Branch:** `v4-dev` (checkpoint from `d858a17`;
frozen v2/v3 untouched, tags never rewritten). **Honest status:
foundation GREEN; CPU solver validation RED (M3 gate not passed).**

## 1. User decisions recorded (this session)

1. **GPU:** OpenCL / integrated-GPU targeted for parity; **CUDA
   interface-only** until compatible hardware is available. (Updates
   DV4-007: primary parity target = OpenCL/iGPU; CUDA ceiling =
   INTERFACE_TESTED for now.)
2. **Datasets:** only open-source-licensed data usable in an MIT project.
3. **Optional 4th reference system:** acoustic **cavity** (Helmholtz
   branch).
4. **STEP import:** implement, document, ship **untested** (no way to
   verify now); support "eventually if it works".

## 2. Dependency proof (REAL — installed and run on this machine)

CPU FEM stack installs and runs:
- **scikit-fem 12.0.2** (BSD-3, pure-Python) — assembly + eigensolve;
- **meshio 5.3.5** (MIT) — mesh I/O;
- **gmsh 4.15.2** (Python wheel; used as an external mesher, GPL isolated
  per DV4-006).
Baseline present: numpy 2.5.1, scipy 1.18.0, matplotlib 3.11.0.
GPU: none (no NVIDIA driver; iGPU/OpenCL not yet probed) → GPU work stays
INTERFACE-level, honestly.

**Proof-of-concept verified:** scikit-fem assembles a **symmetric SPD**
stiffness (library `linear_elasticity` model; symmetry error ~1e-16) and
a consistent mass matrix, and `scipy.sparse.linalg.eigsh` solves the
generalized eigenproblem returning physically-typed eigenmodes.

## 3. The M3 blocker (documented before any fix — QA discipline)

**Defect V4-D-001 (P1, OPEN):** the CPU elasticity eigensolver does not
yet reproduce the analytic cantilever eigenfrequency (RSCS2-V.2). On the
steel cantilever (E=210 GPa, ρ=7850, 0.1×0.01×0.01 m; analytic f₁ =
835.5 Hz), the computed first flexural mode is a factor ~4–22 too low
**and decreases with mesh refinement**, across both `ElementHex1` and
`ElementVector(ElementTetP2())` on `init_tensor` meshes. Verified NOT
caused by: BC application (75 face DoFs correctly condensed), matrix
symmetry (machine-precision after switching to the library model),
mesh geometry (bbox exactly [0,0,0]–[0.1,0.01,0.01]), or material (c=5172
m/s correct). A dense `scipy.linalg.eigh` cross-check confirms the sparse
eigenvalues are the true smallest of the assembled (K,M) — so the
(K,M) pair itself is mesh-dependently wrong.

**Hypothesis (for the next session):** an element-quality / node-ordering
issue in `MeshTet/MeshHex.init_tensor` interacting with the vector basis,
or a quadrature/`condense` convention. **Fix path:** methodical patch
tests (single-element eigenmodes vs closed form; a gmsh-generated
well-shaped tet beam instead of `init_tensor`; verify per-element
Jacobian signs; static tip-deflection δ=FL³/3EI patch test). This is
real Agent-03 numerical engineering.

**Consequence (honest):** no solver result is exposed as validated; the
M3 acceptance gate is **not** met; **no v4 release candidate is
possible** until V4-D-001 is closed with V.1/V.2/V.3/V.8 green.

## 4. What IS shipped and verified in this foundation

- `rscs2_core/reference.py` — analytic benchmark formulas (RSCS2-V.1/V.2/
  V.3), correct and unit-tested independently of the solver (7/7 green:
  cantilever = 835.5 Hz, scaling laws, Timoshenko→EB limit, Lamé
  identity).
- `rscs2_core/registry/` — RSCS2 registry + classification/provenance
  **lint** (namespace, collision, class, units, provenance, tests, SRC
  firewall), tested incl. violation detection.
- `tests/v4/` — 7 passing tests; v3 suite unaffected (frozen paths
  untouched).

## 5. Next-session start point

Close V4-D-001 (get RSCS2-V.2 green via a validated solver), then proceed
P9→P12 (Agent 03) → the M3 MVP tag `v4.0.0-alpha`. Do **not** advance to
anisotropy/piezo/eye until the CPU authority reproduces the analytic
benchmarks — every later result depends on a trustworthy solver.
