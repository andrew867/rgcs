# V4 System Architecture — RGCS v4 / RSCS 2.0

**Status:** PLANNING. Extends v3 additively; frozen packages untouched.

## 1. Layering

```
┌───────────────────────────────────────────────────────────────────┐
│ interfaces:  rgcs4_cli  ·  rgcs_desktop (v3 + v4 panels)           │
├───────────────────────────────────────────────────────────────────┤
│ reporting:   rscs2_core.report (figures, provenance graph, PDF/MD) │
├───────────────────────────────────────────────────────────────────┤
│ diagnostics: rscs2_core.diagnostics   (RSCS2-D.*  eye family)      │
│ inverse:     rscs2_core.inverse       (RSCS2-U.*  fit/UQ)          │
├───────────────────────────────────────────────────────────────────┤
│ physics:     rscs2_core.elastic · .piezo · .optical · .em · .thermal│
│              (RSCS2-E.* governing eqs, staged Levels 1–5)          │
├───────────────────────────────────────────────────────────────────┤
│ solve:       rscs2_core.solve (RSCS2-S.* eigensolve, harmonic,     │
│              modal reduction)  ── authority = CPU                  │
├───────────────────────────────────────────────────────────────────┤
│ assemble:    rscs2_core.fem (scikit-fem CPU reference assembly)   │
│ boundaries:  rscs2_core.boundary (RSCS2-B.* free/fixed/elastic/mass)│
├───────────────────────────────────────────────────────────────────┤
│ mesh/geom:   rscs2_core.mesh (RSCS2-G.* import, mesh, tags,        │
│              deterministic manifests)                              │
├───────────────────────────────────────────────────────────────────┤
│ accel:       rscs2_core.accel (RSCS2-A.* backend-neutral API;      │
│              CPU default · CuPy · PyOpenCL · capability detection) │
├───────────────────────────────────────────────────────────────────┤
│ REUSED FROZEN v3:  rgcs_core.anisotropy/coupled_modes/optics/       │
│   timing/uncertainty · rscs_core (typed coords/operators, firewall) │
├───────────────────────────────────────────────────────────────────┤
│ IMMUTABLE:  archive/v2.0.0/ · frozen RGCS-M.* · tags v2/v3          │
└───────────────────────────────────────────────────────────────────┘
```

New top-level package: **`rscs2_core`** (mirrors how `rscs_core` sat
beside `rgcs_core`). Nothing in `rgcs_core`/`rscs_core`/`archive` is
edited; v4 *composes* them (e.g. the elastic solver's anisotropic path
validates against `rgcs_core.anisotropy.wave_speeds`; the coupled-mode
reduction validates against `rgcs_core.coupled_modes`).

## 2. Data-flow (single run)

```
project manifest ─▶ geometry import ─▶ mesh + tags ─▶ mesh manifest (sha256)
      │                                                     │
      ▼                                                     ▼
  material card (RSCS2-E) ─▶ FEM assembly ─▶ boundary op ─▶ generalized
  (α-quartz C,e,ε,ρ+σ)         (K, M, [piezo blocks])        eigenproblem
                                                              │ (CPU authority;
                                                              │  accel optional,
                                                              │  parity-gated)
                                                              ▼
                                       modes (ω, u, [φ]) ─▶ diagnostics (RSCS2-D)
                                                              │
                          uncertainty samples ◀──────────────┤
                          mesh-refinement sweep ◀─────────────┤
                                                              ▼
                                 Eye Consensus map + regions + confidence
                                 + NULL-capable verdict + comparisons
                                                              │
                                                              ▼
                                        report (figures + provenance graph)
```

## 3. Backend-neutral compute seam (RSCS2-A.*)

One thin array-API seam (a numpy-subset) with a resolved backend per
run, recorded in provenance:

- **CPU (default, authority):** numpy/scipy — always present.
- **CUDA:** CuPy (drop-in numpy-like) — optional; parity-gated.
- **OpenCL:** PyOpenCL — optional; parity-gated.
- **capability detection:** device enumeration, memory budget, dtype
  support; **graceful fall-through to CPU** when absent or when a
  parity check has not been recorded for the operation.

Rule: an operation may run on an accelerator only if it has a passing
NUMERICALLY_PARITY_TESTED record; otherwise the seam routes it to CPU
and logs the downgrade. No silent GPU path.

## 4. Determinism and provenance spine

- Every artifact (mesh, matrices, modes, diagnostics, figures) records
  the git rev, input checksums, backend, dtype policy, and seeds — the
  same discipline as v3 reproducibility bundles, same verifier.
- Serialization: JSON (metadata) + `.npz` (arrays) always; HDF5/XDMF
  optional for large fields. Floating outputs are compared
  tolerance-aware cross-platform (the v3 D-V3-04 lesson is law here:
  no byte-equality assumption across toolchains).
- Typed I/O across module boundaries: quantities are RSCS coordinates
  or registered v4 types, never bare arrays (extends D3-009).

## 5. Failure & staging posture

- Every fidelity Level is independently shippable; a Level that cannot
  pass its benchmark does not gate the Levels below it.
- Every tranche has a partial-release option (`V4_RELEASE_PLAN.md`):
  e.g. ship "CPU elastic + benchmarks" (M3) as `v4.0.0-alpha` even if
  piezo/accel/eye are not yet done.
- Diagnostics can always return NULL ("no stable candidate"); that is a
  first-class result, never an error to be suppressed.
