# R13 Phase Receipt

```text
phase_id: 09
phase_title: Long-Wavelength Homogenization to Continuum Elasticity
status: COMPLETE
start_commit: 8ae9574
end_commit: v7.0.0 (branch v630-r13)
files_added: r13/homogenize.py, tests/v6/test_r13_homogenize.py
files_modified: none
tests_added: 12
focused_test_result: 12 passed
full_regression_result: 5638 passed, 8 skipped, 1 deselected, exit 0
source_hashes_used: build_meta source hash over SOURCE_ROOTS (incl. r13); references hashed by srcregistry
claim_classes_emitted: ANALYTIC_MODEL
private_files_read: false
```

## Work completed

Validated the q→0 bridge from atomistic phonons to continuum stiffness and
sound velocity. Verdict **`ATOMISTIC_TO_CONTINUUM_HOMOGENIZED_ANALYTIC`**. The
module carries three homogenizations from the atomistic to the continuum
picture — the acoustic limit, effective stiffness, and the elastic tensor with
the Christoffel acoustic velocities. `refuse_homogenized_as_measured` refuses
reading any modulus, sound speed or Christoffel velocity as a bench result.

## Evidence and equations implemented

- Acoustic limit: continuum sound speed `c = a√(K/m)` is the `k→0` slope of the
  chain dispersion `ω(k) = 2√(K/m)|sin(ka/2)|`; `long_wavelength_slope` (a
  Richardson step cancelling the leading `O(k²)` error) reads that slope off
  the branch and the two agree.
- Effective stiffness: two alternating springs homogenize to the harmonic
  (series) mean `2/(1/K1 + 1/K2)`, dominated by the softer spring.
- Elastic tensor: `ContinuumElastic` carries a 6×6 Voigt stiffness in the
  trigonal (class 32) symmetry pattern of alpha-quartz — which entries are
  zero, equal, opposite, and `C66 = (C11-C12)/2` — as exact crystal symmetry.
- Christoffel matrix `Γ_ik = C_ijkl n_j n_l / ρ` gives three non-negative
  eigenvalues whose square roots are a direction's acoustic velocities.

## Negative results

No crystal exists, no wave was launched or timed, and no modulus, sound speed
or Christoffel velocity was measured. The quartz stiffness magnitudes are
`CONVENTIONAL_LITERATURE` placeholders on an exact symmetry pattern — the
pattern is crystal symmetry, the magnitudes are quoted, not determined here. A
homogenized parameter is never a bench measurement.

## Deviations from prompt

None.

## Blocking inputs, when applicable

None — software/architecture phase. (Real stiffness magnitudes would come from
the same DFT/DFPT pipeline blocked in phase 08/31; the symmetry pattern here is
exact regardless.)

## Downstream impact

The continuum stiffness and Christoffel velocities feed the piezoelectric
continuum→BVD electrical bridge (10) and the baseline modal survey (25).

## Reopening test

Re-run `tests/v6/test_r13_homogenize.py`; reopen if the verdict string changes,
if the acoustic-limit slope, harmonic-mean stiffness, or `C66 = (C11-C12)/2`
symmetry identity fails, or if `refuse_homogenized_as_measured` stops raising.

## Acceptance checklist
- [x] focused tests pass
- [x] receipt written
- [x] claim classes recorded
- [x] no private files read
- [x] PHYSICAL_VALIDATION_NOT_CLAIMED
