# R13 Phase Receipt

```text
phase_id: 16
phase_title: Floquet and Parametric Conversion
status: COMPLETE
start_commit: 8ae9574
end_commit: v7.0.0 (branch v630-r13)
files_added: r13/floquet.py, tests/v6/test_r13_floquet.py
files_modified: none (r13/__init__.py __all__ and packaging registered in Phase 01)
tests_added: 11
focused_test_result: 11 passed
full_regression_result: 5638 passed, 8 skipped, 1 deselected, exit 0
source_hashes_used: 52e50d49343e1e0b0fb65a13cf7c976d11ed9f2bfaa743ab0c28050b3409a834 (build_meta compute_source_hash over SOURCE_ROOTS incl. r13)
claim_classes_emitted: FLOQUET_PARAMETRIC_MODEL_ANALYTIC; ANALYTIC_MODEL
private_files_read: false
```

## Work completed

Delivered `r13/floquet.py` with focused tests in
`tests/v6/test_r13_floquet.py`. Verdict **`FLOQUET_PARAMETRIC_MODEL_ANALYTIC`**.
Models periodic time dependence, sidebands, instability thresholds, and
parametric gain as analytic properties of the model equation.

## Evidence and equations implemented

- `floquet_monodromy(delta, epsilon)` integrates the parametric oscillator
  `ẍ + (δ + ε cos 2t) x = 0` over one period; the monodromy is symplectic,
  `det(M) = 1` (defect ~1e-15).
- `principal_tongue_contrast`: inside the principal instability tongue (δ≈1,
  ε>0) the spectral radius exceeds 1 (|μ|>1, growing); outside it |μ|=1
  (bounded) — proven both ways, with an ε=0 stable negative control.
- `quasi_energies(monodromy, T)` from `μ = e^{-i ε_F T}`: real and in ± pairs
  for the stable case, complex for the unstable one.
- `parametric_gain(pump, detuning)`: above threshold one quadrature is
  amplified by `e`, the other deamplified by `1/e` (product 1,
  phase-sensitive); below threshold, bounded.

## Negative results

No parametric instability or gain was measured. The tongues and gain are
analytic properties of the model equation.
`refuse_model_instability_as_measured` raises: a computed resonance tongue is
not an observed instability in hardware.

## Deviations from prompt

None.

## Blocking inputs, when applicable

None. Every result is an analytic property of a declared model equation.

## Downstream impact

Supplies the parametric-gain and instability model consumed by the
rotation-versus-squeezing experiment (phase 27) and the boundary-energy ledger
(phase 17).

## Reopening test

Re-run `tests/v6/test_r13_floquet.py`; reopen if the verdict string
`FLOQUET_PARAMETRIC_MODEL_ANALYTIC` changes, or if
`refuse_model_instability_as_measured` stops raising.

## Acceptance checklist

- [x] focused tests pass (11 passed)
- [x] receipt written
- [x] claim classes recorded
- [x] no private files read
- [x] PHYSICAL_VALIDATION_NOT_CLAIMED
