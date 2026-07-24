# R13 Phase Receipt

```text
phase_id: 24
phase_title: Synchronized DAQ, Calibration, and Energy Ledger
status: COMPLETE (models); BLOCKED_MISSING_INPUT for real acquired data
start_commit: 8ae9574
end_commit: v7.0.0 (branch v630-r13)
files_added: r13/daq.py, tests/v6/test_r13_daq.py
files_modified: none (r13/__init__.py __all__ and packaging registered in Phase 01)
tests_added: 14
focused_test_result: 14 passed
full_regression_result: 5638 passed, 8 skipped, 1 deselected, exit 0
source_hashes_used: 52e50d49343e1e0b0fb65a13cf7c976d11ed9f2bfaa743ab0c28050b3409a834 (build_meta compute_source_hash over SOURCE_ROOTS incl. r13)
claim_classes_emitted: SYNCHRONIZED_DAQ_ENERGY_LEDGER_MODEL; NUMERICAL_SIMULATION; BLOCKED_MISSING_INPUT (real acquired channel data)
private_files_read: false
```

## Work completed

Delivered `r13/daq.py` with focused tests in `tests/v6/test_r13_daq.py`.
Verdict **`SYNCHRONIZED_DAQ_ENERGY_LEDGER_MODEL`**. Unifies drive, field,
electrical, acoustic, optical, thermal, and timing channels as a numerical
model.

## Evidence and equations implemented

- Sampling / Nyquist: `sample(...)` recovers a below-Nyquist tone and a tone
  above Nyquist aliases to the predicted `alias_frequency` — the load-bearing
  correctness check.
- Synchronization: `estimate_skews` / `synchronize` detect and correct a known
  per-channel skew by cross-correlation to within one sample.
- Jitter: `sample_with_jitter` / `jitter_snr` show more clock jitter
  monotonically worsens a tone's SNR.
- Energy ledger: `synthetic_ledger` closes exactly on known terms and dropping
  a loss term leaves a residual equal to that term; `blocked_ledger` marks real
  values `BLOCKED_MISSING_INPUT`.

## Negative results

No instrument acquired data and no energy was measured. Synthetic sampled data
is not acquired data, and an unclosed synthetic residual is not new energy. A
guard fails if the aliased frequency equals the original.
`refuse_unclosed_as_new_energy` raises for an interval-spanning-zero residual
called new energy, and `refuse_synthetic_daq_as_acquired` raises.

## Deviations from prompt

None.

## Blocking inputs, when applicable

Real acquired channel data are `BLOCKED_MISSING_INPUT`. `blocked_ledger` marks
every real energy value blocked until acquired; all sampling, synchronization,
jitter, and ledger results here are computed from synthetic signals on a
modelled clock. Real acquisition requires operated hardware (out of scope).

## Downstream impact

The synchronized DAQ and energy ledger integrate the quadrature (phase 14),
heterodyne (phase 18), QCM stack (phase 21), imaging (phase 23), and
boundary-energy (phase 17) channels for the baseline modal survey (phase 25)
and cross-domain transfer benchmark (phase 30).

## Reopening test

Re-run `tests/v6/test_r13_daq.py`; reopen if the verdict string
`SYNCHRONIZED_DAQ_ENERGY_LEDGER_MODEL` changes, or if
`refuse_unclosed_as_new_energy` or `refuse_synthetic_daq_as_acquired` stops
raising.

## Acceptance checklist

- [x] focused tests pass (14 passed)
- [x] receipt written
- [x] claim classes recorded
- [x] no private files read
- [x] PHYSICAL_VALIDATION_NOT_CLAIMED
