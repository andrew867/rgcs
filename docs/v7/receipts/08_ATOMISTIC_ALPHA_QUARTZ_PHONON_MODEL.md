# R13 Phase Receipt

```text
phase_id: 08
phase_title: Atomistic Alpha-Quartz Phonon Model
status: COMPLETE
start_commit: 8ae9574
end_commit: v7.0.0 (branch v630-r13)
files_added: r13/atomistic.py, tests/v6/test_r13_atomistic.py
files_modified: none
tests_added: 10
focused_test_result: 10 passed
full_regression_result: 5638 passed, 8 skipped, 1 deselected, exit 0
source_hashes_used: build_meta source hash over SOURCE_ROOTS (incl. r13); references hashed by srcregistry
claim_classes_emitted: ANALYTIC_MODEL
private_files_read: false
```

## Work completed

Built a mass-and-spring dynamical-matrix phonon model of a 1-D lattice.
Verdict **`ATOMISTIC_PHONON_MODEL_ANALYTIC`**. From a per-cell basis of masses
and nearest-neighbour springs it Fourier-transforms to a Hermitian dynamical
matrix `D(k)` — the wrap-around spring carrying the Bloch phase `exp(ikRa)` —
whose eigenvalues are the squared phonon frequencies; diagonalizing over the
zone gives the dispersion. `refuse_toy_model_as_real_spectrum` refuses reading
any frequency here as a real quartz phonon mode.

## Evidence and equations implemented

- Monatomic chain closed form `ω(k) = 2√(K/m)|sin(ka/2)|` with `ω(0)=0`.
- Diatomic chain acoustic and optical branches with zone-boundary edges
  `√(2K/m2)` and `√(2K/m1)`.
- Acoustic sum rule enforced, not assumed: `enforce_acoustic_sum_rule` sets
  each on-site term to minus its row sum and `acoustic_sum_rule_holds` checks
  it, so a rigid translation costs no energy.

## Negative results

These frequencies are not the phonon modes of real alpha-quartz: the springs
are chosen toy constants, not the interatomic force constants of real quartz.
A toy force-constant model is not a real phonon spectrum, and nothing is
measured. `refuse_toy_model_as_real_spectrum` enforces the distinction.

## Deviations from prompt

None.

## Blocking inputs, when applicable

Real alpha-quartz interatomic force constants require a DFT/DFPT calculation,
carried here as `BLOCKED_MISSING_INPUT` (`REAL_FORCE_CONSTANTS_STATUS`) and
handled by the Euphonic phase P31. The analytic model is complete; only the
real-material force constants are the missing physical input.

## Downstream impact

The dynamical-matrix dispersion feeds the long-wavelength homogenization to
continuum elasticity (09); the blocked real-force-constant status is
discharged by the Euphonic pipeline (31).

## Reopening test

Re-run `tests/v6/test_r13_atomistic.py`; reopen if the verdict string changes,
if the monatomic/diatomic closed-form agreement or the acoustic sum rule fails,
or if `refuse_toy_model_as_real_spectrum` stops raising.

## Acceptance checklist
- [x] focused tests pass
- [x] receipt written
- [x] claim classes recorded
- [x] no private files read
- [x] PHYSICAL_VALIDATION_NOT_CLAIMED
