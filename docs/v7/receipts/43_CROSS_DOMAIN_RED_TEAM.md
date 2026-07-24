# R13 Phase Receipt

```text
phase_id: 43
phase_title: Cross-Domain Red Team
status: COMPLETE
start_commit: 8ae9574
end_commit: v7.0.0 (branch v630-r13)
files_added: tests/v6/test_r13_redteam.py
files_modified: (none)
tests_added: 16
focused_test_result: test_r13_redteam.py 16 passed
full_regression_result: 5638 passed, 8 skipped, 1 deselected, exit 0
source_hashes_used: build_meta source hash over SOURCE_ROOTS (incl. r13)
claim_classes_emitted: REPOSITORY_COMPUTATIONAL_RESULT
private_files_read: false
```

## Work completed

Attacked the permissive bridge architecture hard enough to prevent domain
collapse. `tests/v6/test_r13_redteam.py` is an adversarial suite (**16 tests,
all passing**) whose job is to *make the framework over-claim* and prove every
attempt is refused. Verdict emitted: **`RED_TEAM_ALL_ATTACKS_REFUSED`**; claim
class `REPOSITORY_COMPUTATIONAL_RESULT`.

## Evidence and equations implemented

Attacks mounted, each of which must raise / be blocked:

- **The seven forbidden promotions**, one test each, plus a check that there
  are exactly seven and every one raises `ClaimError`.
- **Ladder promotion:** promoting a `NUMERICAL_SIMULATION` claim to any
  measurement class is refused.
- **Package-wide sweep:** every r13 module with a `*_report()` (≥20 checked)
  must report `measured_here == "nothing"`,
  `physical_validation == PHYSICAL_VALIDATION_NOT_CLAIMED`, and a
  non-measurement claim class.
- **Bridge graph:** an end-to-end certificated path never reaches a
  measurement class; `refuse_path_as_measured` and
  `refuse_automatic_composition` raise.
- **Coordinate codec:** the alias set cannot be collapsed to a destination; a
  numeric match is not authentication.
- **Energy ledger:** an unclosed boundary residual is not new energy; the
  instantaneous-switch divergence is refused.
- **Six-angle ring:** planar uniformity is not isotropy.
- **External validation:** a synthetic `S(Q,ω)` is not beamtime data; a
  synthetic force-constant set is not a DFT calculation (`from_dft` raises).

## Negative results

All 16 over-claim attacks are **refused**. No path through the permissive
bridge architecture reaches a measurement or a decoded destination from
software alone.

## Deviations from prompt

None.

## Blocking inputs, when applicable

None — verification phase.

## Downstream impact

The red team is the enforcement backstop for the code↔manuscript agreement
asserted in phase 46 (the seven forbidden promotions here are the same seven
in `r13/claimtypes.py`) and is part of the phase-47 proof bundle.

## Reopening test

Re-run `tests/v6/test_r13_redteam.py`; reopen if any of the 16 attacks stops
being refused, if the forbidden-promotion count diverges from seven, or if the
package-wide sweep finds a module reporting a measurement class.

## Acceptance checklist
- [x] focused tests pass
- [x] receipt written
- [x] claim classes recorded
- [x] no private files read
- [x] PHYSICAL_VALIDATION_NOT_CLAIMED
