# Modelling Roadmap — the next software generation (Agent 15) — ENG

Where the modelling stack goes after v3 **without changing v3**: the
v3.0.0 mathematics is the frozen scientific baseline; everything below
is additive, enters through the registry governance path where it
defines anything new, and must satisfy the invariants of §0 before it
merges. Target frame: a v4 programme, run with the same
freeze-and-conservatively-extend discipline v3 applied to v2.

## 0. Invariants every proposed module must preserve

1. **Reference-oracle rule:** every accelerated/approximate path ships
   with a CPU reference implementation and a tolerance-aware
   equivalence test (GPU vs CPU is CI-gated exactly like RSCS vs RGCS).
2. **Reproducibility:** seeds explicit, SOURCE_DATE_EPOCH-stable
   outputs, printed-precision portability (the D-V3-04 lesson is law).
3. **Typed I/O:** new quantities are RSCS coordinates or registered
   application types — no bare arrays across module boundaries.
4. **Classification:** solver outputs are DER from their declared
   inputs; fitted parameters carry uncertainty; nothing a solver emits
   upgrades a HYP.
5. **Determinism before speed:** a module that cannot be regression-
   tested deterministically (or tolerance-deterministically) does not
   merge, whatever its benchmark numbers.

## 1. Compute foundation

| Module | Content | Depends on |
|---|---|---|
| **Array-backend abstraction** | single seam (numpy API subset) with CPU default; CUDA (CuPy-class) and OpenCL backends behind it; per-run backend recorded in provenance | — |
| **CPU fallback guarantee** | every feature functions with zero GPU present; CI runs the full suite CPU-only forever | backend |
| **GPU eigenmode solver** | batched dense/banded eigensolves for Christoffel sweeps (thousands of directions), coupled-mode H matrices, and FEM-reduced modal problems; CPU-oracle-tested per §0.1 | backend |

## 2. Field and geometry modelling

| Module | Content | Notes |
|---|---|---|
| **FEM import/export** | complete the T3 contract: mesh import (CalculiX/Elmer/Gmsh), material card from `fea_export`, modal results back into typed mode records | feeds H-01a/H-03 adjudication directly |
| **Anisotropic wave propagation** | beyond plane-wave Christoffel: slowness surfaces, group-velocity/beam-walkoff fields, ray tracing through oriented crystals | EST elastodynamics only |
| **Optical ray tracing** | multi-surface refraction/reflection with birefringent splitting and Jones chains along rays; extends `rgcs_core.optics` straight-ray model | EST optics; closed-form-tested |
| **Field visualization** | mode-shape fields, phase fields, node surfaces on meshes; export to glTF/VTK for external viewers | presentation only, generated |
| **Tensor visualization** | stiffness/slowness surface glyphs, photoelastic response surfaces | ditto |
| **Modal animations** | time-evolution renders of measured/computed mode shapes, driven by the same generators as manuscript figures | generated-artifact rules apply |

## 3. Inference and data confrontation (the scientifically loaded tier)

| Module | Content | Guard rails |
|---|---|---|
| **Uncertainty Monte Carlo** | propagate the CALIBRATION_GUIDE budget through any model chain by sampling; converges to the linear `UncertainValue` propagation in the small-σ limit (that's the regression test) | seeded; sample counts recorded |
| **Measured-dataset fitting** | fit registered models to pipeline outputs (ladders, splittings, decay forms) with uncertainty-aware likelihoods | fits ONLY pre-registered model families; new families need a ledger row first |
| **Bayesian parameter estimation** | posteriors for (v_L, κ_χ, g, τ_c, …) with explicit priors; model comparison via the SAP's information criteria, not ad-hoc Bayes factors | priors are registered and classified (a Source-claim prior stays SRC) |
| **Inverse modelling** | geometry+orientation from a target/measured ladder (extends the v2 density-inverse solver with the anisotropic model); reports posterior, never a point answer | non-uniqueness stated, not hidden |

## 4. Sequencing (proposed v4 tranches)

```
V4-T1 backend + CPU-fallback CI + GPU eigensolver (oracle-gated)
V4-T2 FEM import/export + benchmark golden problems
V4-T3 propagation/ray-tracing + visualization tier
V4-T4 Monte Carlo + fitting + Bayesian/inverse tier
        (only after bench data exists to confront — the inference tier
         without data is decoration)
```

Gate to start v4: tag the v3 lineage as the frozen baseline (already
true), open a v4 notation-ledger section by governance, and port the
CEP battery pattern: **every v4 solver must reproduce the v3 numbers on
the v3 domain.** Same trick, one generation up.
