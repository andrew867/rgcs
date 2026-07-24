# R13 Phase Receipt

```text
phase_id: 14
phase_title: Two-Channel Quadrature Field and Transducer Model
status: COMPLETE
start_commit: 8ae9574
end_commit: v7.0.0 (branch v630-r13)
files_added: r13/quadfield.py, tests/v6/test_r13_quadfield.py
files_modified: none (r13/__init__.py __all__ and packaging registered in Phase 01)
tests_added: 10
focused_test_result: 10 passed
full_regression_result: 5638 passed, 8 skipped, 1 deselected, exit 0
source_hashes_used: 52e50d49343e1e0b0fb65a13cf7c976d11ed9f2bfaa743ab0c28050b3409a834 (build_meta compute_source_hash over SOURCE_ROOTS incl. r13)
claim_classes_emitted: TWO_CHANNEL_QUADRATURE_TRANSDUCTION_MODEL; NUMERICAL_SIMULATION
private_files_read: false
```

## Work completed

Delivered `r13/quadfield.py` with focused tests in
`tests/v6/test_r13_quadfield.py`. Verdict
**`TWO_CHANNEL_QUADRATURE_TRANSDUCTION_MODEL`**. Models the rotating drive,
channel errors, spatial field, and electromechanical coupling of the
two-channel apparatus from synthetic signals.

## Evidence and equations implemented

- `iq_demodulate(signal, t, w_ref)` mixes against cos/sin references and
  low-passes to recover `I = A cos φ / 2`, `Q = A sin φ / 2`; a power test
  plants a tone and recovers its amplitude and phase.
- Complex amplitude `a = I + iQ` with magnitude/phase; `squeezing_readout`
  reports the two quadrature variances as a model indicator only.
- `Transducer(gain, noise_psd, certified)` maps a mechanical quadrature to an
  electrical one: output variance is `gain²·v + noise_psd`, and the SNR
  degradation referred to input is exactly `noise_psd/gain²`.

## Negative results

No quadrature was measured on an apparatus, and no squeezed state was observed.
A modelled sub-reference variance is a calculation, not a physical squeezing
measurement. A wrong-amplitude guard must fail if the recovery is broken.
`refuse_model_squeezing_as_observed` (a modelled variance below the symmetric
reference is not an observed squeezed state) and
`refuse_transduction_without_certificate` (a mechanical→electrical transducer
is a bridge and needs the R12/R13 coupling certificate) both raise.

## Deviations from prompt

None.

## Blocking inputs, when applicable

None for the model. A real quadrature measurement and a certified transducer
would require operated hardware (out of scope for this phase).

## Downstream impact

Feeds the heterodyne cavity readout (phase 18), the QCM/BVD/ringdown stack
(phase 21), and the synchronized DAQ energy ledger (phase 24).

## Reopening test

Re-run `tests/v6/test_r13_quadfield.py`; reopen if the verdict string
`TWO_CHANNEL_QUADRATURE_TRANSDUCTION_MODEL` changes, or if
`refuse_model_squeezing_as_observed` or
`refuse_transduction_without_certificate` stops raising.

## Acceptance checklist

- [x] focused tests pass (10 passed)
- [x] receipt written
- [x] claim classes recorded
- [x] no private files read
- [x] PHYSICAL_VALIDATION_NOT_CLAIMED
