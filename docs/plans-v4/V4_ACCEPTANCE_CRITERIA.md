# V4 Acceptance Criteria

**Status:** PLANNING. What "done and correct" means, per level. All are
machine-checkable; none is satisfied by prose.

## Global (every milestone)

1. Frozen-path diff (`archive/v2.0.0`, tags v2/v3) empty.
2. v3 suite still green; v4 additions do not regress it.
3. CPU-only install works with numpy+scipy+scikit-fem+meshio; the full
   scientific path runs with no GPU and no heavy optional deps.
4. Every reported quantity carries units + an `UncertainValue` where a
   value has uncertainty; every claim-bearing object carries a
   classification.
5. Cross-platform (ubuntu/windows/macos) green, tolerance-aware.
6. No forbidden vocabulary; SRC/HYP firewall holds; no eye→EST upgrade.

## M3 (CPU elastic solver — MVP)

- V.1 (rod), V.2 (EB beam), V.3 (Timoshenko), V.5 (cube) within recorded
  tolerances; V.8 convergence order matches element theory.
- Orthogonality, residual, rigid-body, energy-balance tests green.
- Deterministic serialization round-trips.

## M4 (crystal multiphysics) — conservative extension

- **V.6:** α-quartz axis speeds reproduce frozen `rgcs_core.anisotropy`
  within rtol tied to mesh resolution.
- **V.9:** degenerate two-mode splitting reproduces frozen
  `RSCS-O.4`/`RGCS-M.24`.
- V.7 piezo single-element round-trip; taxonomy stable across refine;
  loaded-shift within the v3 loading band.

## M5 (acceleration)

- Seam contract tests green on CPU; capability detection + CPU fallback
  logged; a non-parity-tested op refuses GPU and falls back.
- GPU status recorded per the four-status ladder; **no HARDWARE_BENCHMARKED
  claim without a recorded device**. f32 error bounds recorded.

## M6 (eye + projections)

- All 15 diagnostics unit+dimensional+guard tested; V.10 (asymmetric
  geometry) shifts predictably.
- Consensus functional emits regions+confidence+four comparisons+NULL;
  the NULL-model test passes (a featureless mode returns NULL); artifact
  injections are labelled artifact, not candidate.
- A candidate is only "robust cross-physics" if it survives mesh +
  uncertainty + cross-channel + boundary-perturbation persistence.

## M7 (validation + inverse)

- **Mandatory gates green:** V.2, V.3 (cantilever), V.4 (fork), MAC ≥
  0.99 on the first ≥4 beam modes.
- Inverse recover-the-truth within CI; leakage test passes; every fit
  reports skill vs a null model; MC-vs-linear small-σ anchor holds.

## M8 (release)

- Full gate table GREEN (all mandatory benchmarks + both
  conservative-extension anchors + all lints + cross-platform).
- Manuscripts: 0 undefined refs / 0 overfull; all numbers generated.
- Adversarial QA pass with defects documented before fixes.
- Release artifacts + SHA256SUMS + PROVENANCE + report; Zenodo path
  ready; **tag v4.0.0 only if every above gate is GREEN**.

## Definition of "not accepted"

Any red conservative-extension anchor, any red mandatory benchmark, any
eye result reported without its robustness+uncertainty battery, any GPU
speed claim without hardware, or any frozen-path modification →
**not accepted**, regardless of other progress.
