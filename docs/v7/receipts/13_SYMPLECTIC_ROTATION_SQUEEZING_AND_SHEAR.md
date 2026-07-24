# R13 Phase Receipt

```text
phase_id: 13
phase_title: Symplectic Rotation, Squeezing, and Shear
status: COMPLETE
start_commit: 8ae9574
end_commit: v7.0.0 (branch v630-r13)
files_added: r13/symplectic.py, tests/v6/test_r13_symplectic.py
files_modified: none (r13/__init__.py __all__ and packaging registered in Phase 01)
tests_added: 13
focused_test_result: 13 passed
full_regression_result: 5638 passed, 8 skipped, 1 deselected, exit 0
source_hashes_used: 52e50d49343e1e0b0fb65a13cf7c976d11ed9f2bfaa743ab0c28050b3409a834 (build_meta compute_source_hash over SOURCE_ROOTS incl. r13)
claim_classes_emitted: SYMPLECTIC_TRANSFORMS_ROTATION_SQUEEZE_SHEAR; ANALYTIC_MODEL
private_files_read: false
```

## Work completed

Delivered `r13/symplectic.py` with focused tests in
`tests/v6/test_r13_symplectic.py`. Verdict
**`SYMPLECTIC_TRANSFORMS_ROTATION_SQUEEZE_SHEAR`**. The module is the unifying
transform layer that classifies the two-channel apparatus as passive rotation,
active squeezing, shear, or a mixed symplectic transformation. Rotation,
squeeze and shear all live in the 2×2 real symplectic group `Sp(2,R)`. The
load-bearing distinction is rotation versus squeeze, carrying the
`r11.modemix.rotation_versus_squeeze` distinction into covariance language.

## Evidence and equations implemented

- `is_symplectic`: `M` is symplectic iff `M^T J M = J`; every such `M` has
  `det = 1` and preserves phase-space area.
- Rotation `[[cos,−sin],[sin,cos]]` is orthogonal as well as symplectic: a
  passive phase shift that conserves `x²+p²` and preserves `trace(cov)` (the
  variance sum).
- Squeeze `diag(e^r, e^-r)` is symplectic but not orthogonal: multiplies one
  quadrature variance by `e^(2r)` and the other by `e^(-2r)`, preserving only
  `det(cov)` (the uncertainty product) — active parametric gain that demands a
  pump.
- Shear `[[1,s],[0,1]]` is symplectic, not orthogonal, and preserves only the
  area.
- `preserves_trace` / `preserves_det` and the typed `TRANSFORM_FACTS`
  catalogue pin what each transform conserves.

## Negative results

It does not say any state was rotated, squeezed or sheared, that any quadrature
variance was measured, or that squeezing was observed below any shot-noise
reference. It does not say algebraic membership in `Sp(2,R)` makes two physical
systems the same mechanism. No field mode, cavity, parametric amplifier or
homodyne detector was operated. `refuse_squeeze_as_rotation` refuses reading
parametric quadrature gain as a passive phase shift;
`refuse_symplectic_model_as_measurement` refuses reading the arithmetic as a
bench result.

## Deviations from prompt

None.

## Blocking inputs, when applicable

None. Every matrix is a declared 2×2 and every variance is arithmetic on a
declared covariance.

## Downstream impact

Supplies the transform vocabulary consumed by the quadrature/transducer model
(phase 14), the Floquet/parametric model (phase 16), and the
rotation-versus-squeezing experiment (phase 27).

## Reopening test

Re-run `tests/v6/test_r13_symplectic.py`; reopen if the verdict string
`SYMPLECTIC_TRANSFORMS_ROTATION_SQUEEZE_SHEAR` changes, or if
`refuse_squeeze_as_rotation` or `refuse_symplectic_model_as_measurement` stops
raising.

## Acceptance checklist

- [x] focused tests pass (13 passed)
- [x] receipt written
- [x] claim classes recorded
- [x] no private files read
- [x] PHYSICAL_VALIDATION_NOT_CLAIMED
