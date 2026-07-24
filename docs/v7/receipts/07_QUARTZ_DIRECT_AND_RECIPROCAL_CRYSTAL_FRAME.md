# R13 Phase Receipt

```text
phase_id: 07
phase_title: Quartz Direct and Reciprocal Crystal Frame
status: COMPLETE
start_commit: 8ae9574
end_commit: v7.0.0 (branch v630-r13)
files_added: r13/crystalframe.py, tests/v6/test_r13_crystalframe.py
files_modified: none
tests_added: 15
focused_test_result: 15 passed
full_regression_result: 5638 passed, 8 skipped, 1 deselected, exit 0
source_hashes_used: build_meta source hash over SOURCE_ROOTS (incl. r13); references hashed by srcregistry
claim_classes_emitted: SOURCE_ESTABLISHED_PHYSICS
private_files_read: false
```

## Work completed

Provided an exact mapping among specimen geometry, crystallographic axes,
reciprocal lattice, Brillouin zone, and lab coordinates. Verdict
**`DIRECT_AND_RECIPROCAL_FRAME_CONSISTENT`**. `LatticeFrame` writes down the
trigonal (space groups `P3_121` / `P3_221`) frame of alpha-quartz from the
`CONVENTIONAL_LITERATURE` lattice constants `a = 4.913 Å`, `c = 5.405 Å`
(quoted, never measured here). `refuse_frame_as_measurement` refuses reading
any lattice parameter, volume or `d(hkl)` as a measured or diffraction result.

## Evidence and equations implemented

- Reciprocal basis `b_i = 2π(a_j × a_k)/V` satisfying the load-bearing identity
  `a_i · b_j = 2π δ_ij` exactly.
- Cell volume agreeing with the analytic `(√3/2)a²c`.
- Plane spacings `d(hkl)` agreeing with the analytic hexagonal `1/d²` form.
- Fractional↔Cartesian maps that round-trip.
- The six proper rotations of point group 32 (`D₃`), each orthogonal with
  determinant +1 and the 3-fold cubed equal to the identity.

## Negative results

No real quartz crystal was mounted, irradiated or measured; the lattice
constants are quoted literature values, not determined here; no `d(hkl)` is a
recorded diffraction result. A geometry model is not a diffraction measurement.
The frame is textbook crystallography geometry, computed exactly, not observed.

## Deviations from prompt

None.

## Blocking inputs, when applicable

None — software/architecture phase.

## Downstream impact

The direct/reciprocal frame supplies the crystal geometry for the atomistic
phonon model (08), the homogenization to continuum (09) and its trigonal
symmetry pattern, the chiral-phonon zone corners (12) and the scattering
geometry (32).

## Reopening test

Re-run `tests/v6/test_r13_crystalframe.py`; reopen if the verdict string
changes, if the `a_i · b_j = 2π δ_ij` identity or the analytic volume/`d(hkl)`
agreement fails, or if `refuse_frame_as_measurement` stops raising.

## Acceptance checklist
- [x] focused tests pass
- [x] receipt written
- [x] claim classes recorded
- [x] no private files read
- [x] PHYSICAL_VALIDATION_NOT_CLAIMED
