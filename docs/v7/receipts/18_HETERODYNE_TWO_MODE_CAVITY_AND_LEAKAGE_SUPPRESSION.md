# R13 Phase Receipt

```text
phase_id: 18
phase_title: Heterodyne Two-Mode Cavity and Leakage Suppression
status: COMPLETE
start_commit: 8ae9574
end_commit: v7.0.0 (branch v630-r13)
files_added: r13/heterodyne.py, tests/v6/test_r13_heterodyne.py
files_modified: none (r13/__init__.py __all__ and packaging registered in Phase 01)
tests_added: 12
focused_test_result: 12 passed
full_regression_result: 5638 passed, 8 skipped, 1 deselected, exit 0
source_hashes_used: 52e50d49343e1e0b0fb65a13cf7c976d11ed9f2bfaa743ab0c28050b3409a834 (build_meta compute_source_hash over SOURCE_ROOTS incl. r13)
claim_classes_emitted: HETERODYNE_CAVITY_READOUT_MODEL; ANALYTIC_MODEL
private_files_read: false
```

## Work completed

Delivered `r13/heterodyne.py` with focused tests in
`tests/v6/test_r13_heterodyne.py`. Verdict **`HETERODYNE_CAVITY_READOUT_MODEL`**.
Applies two-mode overlap, tuning, and isolation methods to a conventional
detection and conversion architecture.

## Evidence and equations implemented

- `heterodyne_mix(signal, t, w_lo)` beats a signal against a local oscillator
  to the intermediate frequency, preserving amplitude and phase; both sidebands
  (signal and image) appear.
- Noise budget: `noise_floor` / `heterodyne_penalty_db` encode the 3 dB
  (factor-2) image-band penalty of heterodyne vs homodyne — a modelled noise
  budget, not a measured floor.
- `cavity_response(detuning, kappa)` is a Lorentzian: transmission FWHM equals
  κ and the phase rolls through π across resonance.
- `pdh_error_signal` / `pdh_slope_on_resonance` give an antisymmetric error
  signal with its zero crossing exactly on resonance and the correct slope sign.

## Negative results

No cavity was read out and no noise floor was measured. Leakage suppression and
the 3 dB penalty are model properties. A wrong-amplitude guard fails if the
recovery is broken. `refuse_model_readout_as_measured` raises: a computed
heterodyne spectrum is not a measured cavity readout.

## Deviations from prompt

None.

## Blocking inputs, when applicable

None for the model. A measured cavity readout and noise floor would require an
operated local oscillator and cavity (out of scope for this phase).

## Downstream impact

Supplies the cavity-readout model consumed by the synchronized DAQ (phase 24)
and the baseline modal survey (phase 25).

## Reopening test

Re-run `tests/v6/test_r13_heterodyne.py`; reopen if the verdict string
`HETERODYNE_CAVITY_READOUT_MODEL` changes, or if
`refuse_model_readout_as_measured` stops raising.

## Acceptance checklist

- [x] focused tests pass (12 passed)
- [x] receipt written
- [x] claim classes recorded
- [x] no private files read
- [x] PHYSICAL_VALIDATION_NOT_CLAIMED
