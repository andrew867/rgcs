# V4 Test Plan — RGCS v4 / RSCS 2.0

**Status:** PLANNING. Extends the v3 suite (378 tests, 3-OS CI) without
weakening it. Every v4 requirement maps to ≥1 test category (audited in
`V4_TRACEABILITY_MATRIX.md`). CPU tests are mandatory everywhere; GPU
tests are skip-green on CPU-only runners.

## 1. Test categories and what each guards

| Category | Guards | Example |
|---|---|---|
| unit | per-function correctness | boundary-op assembly |
| dimensional | units on every quantity | eigenfrequency in Hz, energy in J |
| property (hypothesis) | invariants over input space | orthogonality for random SPD K,M |
| golden / analytic-reference | closed-form truth | V.1/V.2/V.3/V.5 eigenfrequencies |
| mesh-convergence | discretization order | V.8 order estimate per benchmark |
| solver-residual | ‖Ku−ω²Mu‖ per mode | RSCS2-S.4 |
| orthogonality | uᵢᵀMuⱼ=δ | RSCS2-S.3/S.4 |
| energy-balance | Σ modal energy vs input | drive projection |
| conservative-extension | reproduces frozen v3 | V.6 (Christoffel), V.9 (splitting) |
| CPU/GPU parity | backend equivalence | RSCS2-A.5 ladder |
| float policy | f64 authority; f32 bounded | precision-policy test |
| cross-platform | ubuntu/windows/macos | tolerance-aware (D-V3-04 law) |
| adversarial / malformed | loud failure | non-manifold mesh, singular M, NaN |
| memory-pressure | budgeted tiling | large SpMV within budget |
| cancellation / recovery | resumable jobs | kill→resume identical |
| serialization round-trip | manifests, matrices, modes | mesh/solve/report |
| visual regression | figures stable | perceptual hash + mathtext lint |
| documentation freshness | generated tables/numbers current | report regen byte-stable |
| benchmark reproducibility | V.* stable across runs | seeded, tolerance-aware |
| null-model | fits beat a baseline; eye can return NULL | U.6, D.0 NULL |
| claim/provenance lint | classification present; no forbidden vocab; SRC/HYP firewall | every RSCS2-* object |

## 2. Standing rules

- **f64 is authority.** f32/GPU results are "equivalent within tolerance",
  never byte-equal (the golden-CSV D-V3-04 lesson generalizes: no
  byte-equality across toolchains/backends).
- **Fail loud.** Every malformed input raises; NaN never propagates;
  unknown schema/version is an error; a mode failing its residual is
  flagged, not reported.
- **NULL is a pass, not a failure.** An eye run that correctly returns
  NULL, or a fit that correctly reports "does not beat null", is a
  green test.
- **No GPU claim without a device.** GPU parity tests are `@requires_backend`
  and skip-green on CPU CI; a HARDWARE_BENCHMARKED assertion without a
  recorded device fails the claim lint.

## 3. CI matrix (extends v3)

- **Portable (always):** ubuntu/windows/macos × Python 3.11/3.13 — full
  CPU suite incl. all analytic benchmarks, conservative-extension anchors,
  adversarial, serialization, visual regression, lints.
- **Reference:** ubuntu pinned scientific stack — full suite + report
  regeneration + release-builder smoke.
- **GPU (optional / contributed):** self-hosted or contributor runner —
  the `@requires_backend` parity set; uploads parity-evidence artifacts.
  Its absence never reds the required checks.

## 4. Coverage audit (planning QA)

Before implementation of each phase, its exit criteria enumerate the
exact tests that must be green. The traceability matrix maps every
RSCS2-* id and every V4 requirement to a test; an unmapped requirement
blocks the phase (no "implemented but untested" merges).
