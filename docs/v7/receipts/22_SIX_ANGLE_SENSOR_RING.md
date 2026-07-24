# R13 Phase Receipt

```text
phase_id: 22
phase_title: Six-Angle Sensor Ring
status: COMPLETE
start_commit: 8ae9574
end_commit: v7.0.0 (branch v630-r13)
files_added: r13/sixangle.py, tests/v6/test_r13_sixangle.py
files_modified: none (r13/__init__.py __all__ and packaging registered in Phase 01)
tests_added: 8
focused_test_result: 8 passed
full_regression_result: 5638 passed, 8 skipped, 1 deselected, exit 0
source_hashes_used: 52e50d49343e1e0b0fb65a13cf7c976d11ed9f2bfaa743ab0c28050b3409a834 (build_meta compute_source_hash over SOURCE_ROOTS incl. r13)
claim_classes_emitted: SIX_ANGLE_RING_PLANAR_NOT_ISOTROPIC; ANALYTIC_MODEL
private_files_read: false
```

## Work completed

Delivered `r13/sixangle.py` with focused tests in
`tests/v6/test_r13_sixangle.py`. Verdict
**`SIX_ANGLE_RING_PLANAR_NOT_ISOTROPIC`**. Designs the calibrated home-lab
analog of the six-angle polarization test.

## Evidence and equations implemented

- `AngleRing(n=6)` samples a synthetic angular pattern at six coplanar azimuths
  (0/60/…/300°). `planar_uniformity(samples)` returns the coefficient of
  variation: a constant pattern reads uniform (CV≈0), a `cos θ` dipole reads
  non-uniform — proven both ways.
- Angular aliasing: `aliased_order(6) → 0`, so a `cos(6θ)` pattern is
  indistinguishable from uniform.

## Negative results

Planar uniformity is NOT three-dimensional isotropy: six coplanar detectors
never sample the out-of-plane (polar) directions, so uniform response around
one circle of angles is planar uniformity, not unrestricted 3-D isotropic
emission. Six samples resolve harmonics only up to order 3 and alias order 6 to
0 — a `cos(6θ)` pattern reads as uniform, which is why "looks uniform on the
ring" is weak evidence. No emission pattern was measured.
`refuse_planar_uniformity_as_isotropy` always raises, and
`refuse_ring_as_measured` raises.

## Deviations from prompt

None.

## Blocking inputs, when applicable

None for the model. A measured emission pattern would require operated hardware
(out of scope). Full 3-D isotropy is unreachable with any coplanar ring by
construction.

## Downstream impact

The aliasing and planar-uniformity limits tie directly to the few-angle imaging
degradation (phase 23) and constrain the six-angle reconstruction there.

## Reopening test

Re-run `tests/v6/test_r13_sixangle.py`; reopen if the verdict string
`SIX_ANGLE_RING_PLANAR_NOT_ISOTROPIC` changes, if `aliased_order(6)` stops
returning 0, or if `refuse_planar_uniformity_as_isotropy` or
`refuse_ring_as_measured` stops raising.

## Acceptance checklist

- [x] focused tests pass (8 passed)
- [x] receipt written
- [x] claim classes recorded
- [x] no private files read
- [x] PHYSICAL_VALIDATION_NOT_CLAIMED
