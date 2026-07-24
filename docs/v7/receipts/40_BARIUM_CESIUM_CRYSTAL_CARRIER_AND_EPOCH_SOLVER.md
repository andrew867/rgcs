# R13 Phase Receipt

```text
phase_id: 40
phase_title: Barium, Cesium, Crystal Carrier, and Epoch Solver
status: COMPLETE
start_commit: 8ae9574
end_commit: v7.0.0 (branch v630-r13)
files_added: r13/epochsolve.py, tests/v6/test_r13_epochsolve.py
files_modified: (none)
tests_added: 15
focused_test_result: test_r13_epochsolve.py 15 passed
full_regression_result: 5638 passed, 8 skipped, 1 deselected, exit 0
source_hashes_used: build_meta source hash over SOURCE_ROOTS (incl. r13)
claim_classes_emitted: DERIVED_ARITHMETIC
private_files_read: false
```

## Work completed

Completed the typed multiscale epoch candidate and quantified its alias count
in `r13/epochsolve.py`. Solves `t ≡ r_i (mod P_i)` across periodic phase
constraints via exact-rational generalized CRT (non-coprime moduli supported;
inconsistent phase sets return `consistent=False` with an empty alias class).
Verdict emitted: **`EPOCH_SOLVER_ALIAS_LIMITED`**; claim class
`DERIVED_ARITHMETIC`.

## Evidence and equations implemented

- `solve_epoch` returns an `EpochSolution` residue **class** (base epoch +
  alias period), never a point.
- `epoch_alias_set(constraints, window)` walks the class and returns multiple
  epochs spaced by exactly `lcm(periods)` (periods 3,4 → alias period 12;
  members 7, 19, 31, …).
- `plant_and_recover` power control: a planted epoch is recovered modulo the
  alias period (`t=31 → 7 mod 12`).
- All epochs/phases/windows are passed in — **no wall-clock reads** — so
  results are deterministic.
- Refusals: `refuse_epoch_as_unique_time`,
  `refuse_phase_match_as_timestamp_authentication`.

## Negative results

An epoch solution is an **alias class** spaced by `lcm(periods)`, not a unique
decoded timestamp; a phase match is not authentication of a time source. The
candidate carriers (barium / cesium / crystal) are labels on periodic
constraints, not identified transmitters.

## Deviations from prompt

None.

## Blocking inputs, when applicable

None — derived-arithmetic phase.

## Downstream impact

The epoch residue class is serialized (with no wall-clock read) by phase 41
and is one of the alias-limited quantities the phase-42 protocol and the
phase-43 red team rely on remaining non-unique.

## Reopening test

Re-run `tests/v6/test_r13_epochsolve.py`; reopen if `epoch_alias_set` ever
returns a single member for a periodic constraint set, if the CRT spacing
stops equalling `lcm(periods)`, or if either refusal stops raising.

## Acceptance checklist
- [x] focused tests pass
- [x] receipt written
- [x] claim classes recorded
- [x] no private files read
- [x] PHYSICAL_VALIDATION_NOT_CLAIMED
