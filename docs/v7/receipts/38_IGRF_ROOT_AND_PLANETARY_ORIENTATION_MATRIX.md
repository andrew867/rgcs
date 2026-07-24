# R13 Phase Receipt

```text
phase_id: 38
phase_title: IGRF Root and Planetary Orientation Matrix
status: COMPLETE
start_commit: 8ae9574
end_commit: v7.0.0 (branch v630-r13)
files_added: r13/magroot.py, tests/v6/test_r13_magroot.py
files_modified: (none)
tests_added: 13
focused_test_result: test_r13_magroot.py 13 passed
full_regression_result: 5638 passed, 8 skipped, 1 deselected, exit 0
source_hashes_used: build_meta source hash over SOURCE_ROOTS (incl. r13)
claim_classes_emitted: ANALYTIC_MODEL
private_files_read: false
```

## Work completed

Operationalized the supplied magnetic-anomaly root and clockwise-zero
orientation rule in `r13/magroot.py`, reusing `r12.igrf14root` and
`r11.earthface.dipole_axis` for the epoch-drifting field. Verdict emitted:
**`IGRF_ROOT_AND_ORIENTATION_ALIAS_LIMITED`**. The IGRF coefficients are
`CONVENTIONAL_LITERATURE` values, so the claim class is `ANALYTIC_MODEL`.

## Evidence and equations implemented

- `orientation_from_field(reference, measured)` recovers attitude via the
  shortest-arc rotation. A power test plants an attitude and recovers the
  field direction.
- `root_alias_set(target)` returns the locus (two hemispheres × many
  longitudes) sharing one axial-dipole intensity — size > 1 — every member
  reproducing the target.
- `drift_between` verifies the field changes with epoch.
- Refusals: `refuse_full_attitude_from_single_vector`,
  `refuse_root_as_unique_location`, `refuse_field_match_as_source`.

## Negative results

A single field vector fixes attitude only up to rotation about the field axis
— one rotational degree of freedom is genuinely undetermined (any such
rotation reproduces the identical single-vector measurement). The "root" is a
**locus** of locations sharing one axial-dipole intensity, not a unique place.
Matching a field value is a `RETROSPECTIVE_NUMERIC_MATCH`, not authentication
of a transmitter location.

## Deviations from prompt

None.

## Blocking inputs, when applicable

None — analytic-model phase.

## Downstream impact

The magnetic-root convention is one of the five R12 conventions whose product
forms the 32-member alias set finalized in phase 37; the undetermined
rotational DOF documented here is why that set does not collapse.

## Reopening test

Re-run `tests/v6/test_r13_magroot.py`; reopen if `root_alias_set` ever returns
size 1 for a generic target, if the single-vector rotational freedom stops
being reproduced, or if any of the three refusals stops raising.

## Acceptance checklist
- [x] focused tests pass
- [x] receipt written
- [x] claim classes recorded
- [x] no private files read
- [x] PHYSICAL_VALIDATION_NOT_CLAIMED
