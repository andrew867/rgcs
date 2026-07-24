# R13 Phase Receipt

```text
phase_id: 04
phase_title: Typed State Variables, Units, and Claim Semantics
status: COMPLETE
start_commit: 8ae9574
end_commit: v7.0.0 (branch v630-r13)
files_added: r13/claimtypes.py, tests/v6/test_r13_claimtypes.py
files_modified: none
tests_added: 15
focused_test_result: 15 passed
full_regression_result: 5638 passed, 8 skipped, 1 deselected, exit 0
source_hashes_used: build_meta source hash over SOURCE_ROOTS (incl. r13); references hashed by srcregistry
claim_classes_emitted: EXACT_IDENTITY
private_files_read: false
```

## Work completed

Built the governance core the rest of R13 is built on, typing every result and
forbidding the seven promotions. Verdict **`CLAIM_SEMANTICS_TYPED_NO_PROMOTION`**.
`ClaimClass` is a strict ladder from `EXACT_IDENTITY` up through
`ANALYTIC_MODEL`, `NUMERICAL_SIMULATION`, `REPOSITORY_COMPUTATIONAL_RESULT`,
`ENGINEERING_CANDIDATE` and the measurement classes `BENCH_MEASUREMENT` /
`INDEPENDENTLY_REPLICATED`, with `MAX_SOFTWARE_CLASS` fixed at
`REPOSITORY_COMPUTATIONAL_RESULT`. `StateVariable` binds name, unit and domain
so a hertz can never be compared with a microsecond.

## Evidence and equations implemented

`refuse_unit_mismatch` enforces unit/domain compatibility. `refuse_promotion`
blocks raising a claim without new evidence of the target class, and any move
into a measurement class is refused outright because this environment has no
measurement. The seven forbidden promotions are each a named refusal in
`FORBIDDEN_PROMOTIONS`: algebraic similarity → physical equivalence, simulation
→ measurement, numeric match → authentication, unclosed energy ledger → new
energy, planar uniformity → 3-D isotropy, coordinate alias → decoded
destination, and exotic-particle paper → carrier evidence. The suite pins that
there are exactly seven.

## Negative results

No result is certified as measured. The strongest class any R13 module reaches
from software is `REPOSITORY_COMPUTATIONAL_RESULT`; the measurement classes
exist only so the ladder stays honest about what is missing. No weak claim
becomes a strong one by assertion — every one of the seven promotions is
refused by name.

## Deviations from prompt

None.

## Downstream impact

Every downstream module imports `ClaimClass`, `StateVariable` and the refusals
from here to type its own verdict and cap its own claim; the bridge phases (06,
10) rely on `MAX_SOFTWARE_CLASS` and the measurement-class refusal to cap
certificate chains at `ENGINEERING_CANDIDATE`.

## Blocking inputs, when applicable

None — software/architecture phase.

## Reopening test

Re-run `tests/v6/test_r13_claimtypes.py`; reopen if the verdict string changes,
if `FORBIDDEN_PROMOTIONS` no longer holds exactly seven, if `MAX_SOFTWARE_CLASS`
moves above `REPOSITORY_COMPUTATIONAL_RESULT`, or if any promotion/unit-mismatch
refusal stops raising.

## Acceptance checklist
- [x] focused tests pass
- [x] receipt written
- [x] claim classes recorded
- [x] no private files read
- [x] PHYSICAL_VALIDATION_NOT_CLAIMED
