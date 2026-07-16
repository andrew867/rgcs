# V4 Product Spec — RGCS v4 / RSCS 2.0

**Status:** PLANNING (no production code this pass). **Baseline:**
RGCS v3.0.1 public; frozen v2.0.0/v3.0.0 immutable. **Governing
decisions:** `V4_DECISION_LOG.md`.

## 1. Product statement

RGCS v4 turns the v3 framework into a **reproducible, GPU-optional,
multiphysics computational-physics platform** that meshes arbitrary
resonant bodies, solves elastic and coupled eigenmodes (with staged
piezoelectric/optical/thermal/EM fidelity), computes explicit field
diagnostics for candidate "eye" regions with robustness and
uncertainty, fits models to synthetic and public datasets, and
validates itself against conventional non-crystal systems — with a CPU
backend that is always the numerical authority.

It confirms **no new physics**. Every governing equation is standard
and cited (EST); every project computation is DER; the historical
"eye" is SRC; computed eye candidates are DER/HYP; all engineering is
ENG. No experimental confirmation, therapeutic effect, consciousness
causation, metric engineering, literal compact quartz dimension, ether
as established physics, "real vortex because the picture swirls", or
unique eye coordinate without robustness+uncertainty is claimed.

## 2. Users and use cases

| User | Use case | Backend needs |
|---|---|---|
| CPU-only researcher | mesh a body, solve modes, get field maps + report | numpy+scipy+scikit-fem only |
| Contributor with a GPU | accelerate large sweeps/MC; contribute parity evidence | + CuPy or PyOpenCL (optional) |
| Experimentalist (Agent 14 lane) | fit v4 models to bench data; compare eye candidates to measured nodes | data/inverse module |
| Reviewer / citer | reproduce every figure and number from a tagged state | deterministic manifests, CPU |
| Educator | run the tuning-fork / cantilever benchmarks against closed forms | CPU-only |

## 3. Capabilities (what v4 delivers) and the milestone that owns each

| Capability | First-usable milestone | Fidelity |
|---|---|---|
| Import geometry (SCAD via export, STL/OBJ, STEP where feasible, Gmsh) | M2 | — |
| Tetrahedral/surface meshing + quality diagnostics + tags | M2 | — |
| CPU sparse generalized eigensolve, isotropic elasticity | M3 | Level 1 |
| Analytic benchmarks (rod/beam/cube) passing | M3 | — |
| Anisotropic α-quartz elasticity + Christoffel validation | M4 | Level 2 |
| Piezoelectric coupled elastodynamics | M4 | Level 3 |
| Accelerator abstraction + CPU fallback + parity harness | M5 | — |
| Eye diagnostic family + Consensus Functional + robustness | M6 | — |
| Optical/photoelastic + coil/EM projections; thermal/fixture | M6 | Levels 4–5 |
| Tuning fork + cantilever validation; datasets; inverse fitting | M7 | — |
| Desktop/CLI, visualization, reports, adversarial QA, release | M8 | — |

**Staged fidelity is a feature:** Level 0 (analytic/reduced, reuses v3)
and Levels 1–2 are the first useful product; Levels 3–5 are additive.
No milestone requires all levels.

## 4. Non-goals (v4 will NOT)

- run physical experiments (external contributors, Agent 14 lane);
- rebuild a full Maxwell/FDTD solver (integration *contract* only);
- claim GPU speedups without compatible hardware benchmarks;
- ship a GPU-required product (CPU-only must always work);
- introduce new governing physics or redefine frozen ids;
- assert a unique eye point, or any physical eye structure.

## 5. Primary example (mandatory, most-detailed): faceted Vogel α-quartz

The faceted Vogel-style α-quartz resonator is the driving example
threaded through every spec: exact parametric geometry (reuses the v2
SCAD lineage + `rgcs_core.geometry`), crystallographic-axis
orientation, the anisotropic elastic tensor (frozen
`rgcs_core.anisotropy`), density and dimensional uncertainty,
termination angles + facets, free/fixture/hand-loading boundary
models, the full mode taxonomy (longitudinal/shear/torsional/flexural/
mixed), piezoelectric field coupling, coil excitation, optical paths +
photoelastic response, thermal drift, modal overlap, coupled-mode
reduction, and the candidate-eye diagnostics. Detailed in
`V4_ANISOTROPIC_QUARTZ_SPEC.md`,
`V4_PIEZOELECTRIC_MULTIPHYSICS_SPEC.md`, `V4_EYE_DIAGNOSTICS_SPEC.md`.

## 6. Mandatory external validation examples

- **Tuning fork (steel/aluminium):** analytic approximation + published
  values (where licensed) + mesh convergence. `V4_REFERENCE_SYSTEMS_SPEC.md`.
- **EB / Timoshenko cantilever (beam / MEMS resonator):** closed-form
  eigenfrequencies + mode shapes.
- **Optional 4th** (acoustic cavity / circular plate / optical ring):
  chosen to exercise a *different solver branch*.

These are **gates**, not extras: no crystal eye result is reported
until the two mandatory reference systems pass their acceptance
criteria (DV4-008).

## 7. Evidence the product must emit for every run

Field maps, candidate *regions* (not false-precision points), stability/
confidence scores, comparisons vs geometric centre / conventional
nodes+antinodes / the v3 RGCS node prior, an explicit NULL when no
stable candidate exists, uncertainty envelopes, mesh-convergence and
CPU/GPU-parity plots where applicable, and an auto-generated report with
a provenance graph and classification chip on every value.

## 8. Success definition (product level)

v4 is a success when a CPU-only user can, from a tagged repo state:
mesh the Vogel crystal, solve its anisotropic+piezo modes, obtain an
eye-diagnostic map with robustness/uncertainty and a NULL-capable
verdict, reproduce the tuning-fork and cantilever benchmarks against
closed forms, and regenerate every figure/number deterministically —
with no physical claim beyond DER diagnostics and pre-registered HYP.
