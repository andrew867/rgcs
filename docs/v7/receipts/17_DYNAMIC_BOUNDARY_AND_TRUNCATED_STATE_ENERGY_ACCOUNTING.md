# R13 Phase Receipt

```text
phase_id: 17
phase_title: Dynamic Boundary and Truncated-State Energy Accounting
status: COMPLETE
start_commit: 8ae9574
end_commit: v7.0.0 (branch v630-r13)
files_added: r13/boundaryenergy.py, tests/v6/test_r13_boundaryenergy.py
files_modified: none (r13/__init__.py __all__ and packaging registered in Phase 01)
tests_added: 18
focused_test_result: 18 passed
full_regression_result: 5638 passed, 8 skipped, 1 deselected, exit 0
source_hashes_used: 52e50d49343e1e0b0fb65a13cf7c976d11ed9f2bfaa743ab0c28050b3409a834 (build_meta compute_source_hash over SOURCE_ROOTS incl. r13)
claim_classes_emitted: DYNAMIC_BOUNDARY_ENERGY_LEDGER_CLOSES_NO_NEW_ENERGY; ANALYTIC_MODEL; BLOCKED_MISSING_INPUT (real per-term energies)
private_files_read: false
```

## Work completed

Delivered `r13/boundaryenergy.py` with focused tests in
`tests/v6/test_r13_boundaryenergy.py`. Verdict
**`DYNAMIC_BOUNDARY_ENERGY_LEDGER_CLOSES_NO_NEW_ENERGY`**. Models abrupt and
finite-time changes of mechanical, electrical, and optical boundaries without
inventing missing energy.

## Evidence and equations implemented

- Three boundary domains (MECHANICAL, ELECTRICAL, OPTICAL), each with an
  `abrupt_change(...)` (sudden) and a `finite_time_change(..., tau)` (ramp).
  The finite-time change adds a radiated term that grows as τ shrinks.
- Unified ledger `E_after = E_before + W_boundary − E_dissipated − E_radiated`,
  with per-term sigmas propagated in quadrature and `E_unclosed` returned as an
  interval.
- A synthetic ledger with known dyadic terms closes at `E_unclosed = 0`
  exactly; omitting the boundary-work term leaves a residual whose magnitude
  equals that work exactly.
- The default `blocked_ledger()` marks every real term `BLOCKED_MISSING_INPUT`
  with an interval that includes zero.

## Negative results

No energy was measured, and no anomaly is claimed. A non-zero residual whose
confidence interval includes zero is a calibration gap, never new energy. Four
refusals raise: `refuse_unclosed_as_new_energy` (an interval spanning zero is
an uncalibrated ledger, not a new channel), `refuse_ignored_boundary_work`,
`refuse_transferred_energy_as_loss` (energy moved to another mode is not loss),
and `refuse_infinite_free_energy` (the instantaneous-switch divergence is an
unphysical idealization).

## Deviations from prompt

None.

## Blocking inputs, when applicable

The real per-term energies (`E_before`, `W_boundary`, `E_dissipated`,
`E_radiated`) are `BLOCKED_MISSING_INPUT`. `blocked_ledger()` marks each with
an interval that includes zero until measured hardware values exist. The ledger
closes only on synthetic dyadic terms.

## Downstream impact

The ledger structure and refusals are reused by the synchronized DAQ energy
ledger (phase 24) and inform the cutoff/reflection timing experiment (phase 29).

## Reopening test

Re-run `tests/v6/test_r13_boundaryenergy.py`; reopen if the verdict string
`DYNAMIC_BOUNDARY_ENERGY_LEDGER_CLOSES_NO_NEW_ENERGY` changes, or if any of the
four refusals (`refuse_unclosed_as_new_energy`, `refuse_ignored_boundary_work`,
`refuse_transferred_energy_as_loss`, `refuse_infinite_free_energy`) stops
raising.

## Acceptance checklist

- [x] focused tests pass (18 passed)
- [x] receipt written
- [x] claim classes recorded
- [x] no private files read
- [x] PHYSICAL_VALIDATION_NOT_CLAIMED
