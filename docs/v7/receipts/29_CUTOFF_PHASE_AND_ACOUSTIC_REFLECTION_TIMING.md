# R13 Phase Receipt

```text
phase_id: 29
phase_title: Cutoff Phase and Acoustic Reflection Timing
status: PREREGISTERED_NOT_RUN
start_commit: 8ae9574
end_commit: v7.0.0 (branch v630-r13)
files_added: r13/experiments.py, r13/preregister.py (shared across phases 25-30)
files_modified: none
tests_added: tests/v6/test_r13_experiments.py (shared prospective-registry suite, 17 tests)
focused_test_result: .venv/Scripts/python.exe -m pytest tests/v6/test_r13_experiments.py -q -> 17 passed
full_regression_result: 5638 passed, 8 skipped, 1 deselected, exit 0
source_hashes_used: build_meta source hash over SOURCE_ROOTS incl. r13
claim_classes_emitted: PROSPECTIVE_PREDICTION
private_files_read: false
```

## Work completed

Preregistered a test of whether interruption phase relative to acoustic
transit changes conventional modal energy distribution. Registered in
`r13/experiments.py`; timing analysis uses `r13/daq.py` (synchronized
sampling) and energy accounting uses `r13/boundaryenergy.py` (the closing
ledger). Sealed under `r13/preregister.py`. Status `PREREGISTERED_NOT_RUN`.

- **Hypothesis:** the phase of a drive interruption relative to the acoustic
  round-trip transit redistributes energy among conventional modes.
- **Predicted signature:** a phase-dependent modulation of the modal energy
  distribution, with the **total** energy ledger closing (work in = stored +
  dissipated + radiated).
- **Null model:** no phase dependence — modal energies independent of cutoff
  phase.
- **Decision rule:** confirm only if the modal redistribution is
  phase-dependent **and** the energy ledger closes within uncertainty; a
  non-closing ledger is a calibration failure, never new energy.

## Evidence and equations implemented

`r13/daq.py` supplies synchronized timing relative to acoustic transit;
`r13/boundaryenergy.py` closes the work-in = stored + dissipated + radiated
ledger. Power: a planted phase-dependent redistribution is detected; a
phase-independent control returns null.

## Negative results

No timing experiment was run. Any redistribution is conventional energy moving
between modes with a closed ledger; an unclosed residual would be a
calibration gap, not new energy. `PHYSICAL_VALIDATION_NOT_CLAIMED`.

## Deviations from prompt

None. Delivered as a sealed prospective experiment ahead of apparatus.

## Blocking inputs, when applicable

Execution is `BLOCKED_MISSING_INPUT` on a built bench: no synchronized-DAQ
apparatus exists to time cutoff against acoustic transit. The prediction is
sealed and awaits data.

## Downstream impact

Binds the synchronized-DAQ energy ledger (phase 24) and boundary-energy
accounting (phase 17) into a falsifiable timing test whose acceptance is
gated on a closing ledger, foreclosing any over-unity reading.

## Reopening test

Unseal the preregistration and run the sealed analysis on real bench data;
reopen when a bench exists.

## Acceptance checklist

- [x] Experiment registered and sealed; analysis in `r13/daq.py` and
  `r13/boundaryenergy.py`.
- [x] Confirmation requires phase dependence AND a closing ledger.
- [x] Planted phase-dependent redistribution detected; control nulls.
- [x] Focused suite passes (17 passed).
- [x] Claim class `PROSPECTIVE_PREDICTION`; no physical validation claimed.
