# R13 Phase Receipt

```text
phase_id: 21
phase_title: QCM, BVD, Ringdown, and Multi-Frequency Stack
status: COMPLETE (models on synthetic data); BLOCKED_MISSING_INPUT for real device numbers
start_commit: 8ae9574
end_commit: v7.0.0 (branch v630-r13)
files_added: r13/qcmstack.py, tests/v6/test_r13_qcmstack.py
files_modified: none (r13/__init__.py __all__ and packaging registered in Phase 01)
tests_added: 16
focused_test_result: 16 passed
full_regression_result: 5638 passed, 8 skipped, 1 deselected, exit 0
source_hashes_used: 52e50d49343e1e0b0fb65a13cf7c976d11ed9f2bfaa743ab0c28050b3409a834 (build_meta compute_source_hash over SOURCE_ROOTS incl. r13)
claim_classes_emitted: QCM_BVD_RINGDOWN_STACK_MODEL; NUMERICAL_SIMULATION; BLOCKED_MISSING_INPUT (real device R,L,C,C0,Q)
private_files_read: false
```

## Work completed

Delivered `r13/qcmstack.py` with focused tests in
`tests/v6/test_r13_qcmstack.py`. Verdict **`QCM_BVD_RINGDOWN_STACK_MODEL`**.
Completes the primary electrical and acoustic detector stack on synthetic data.

## Evidence and equations implemented

- Sauerbrey: `sauerbrey_delta_f(Δm, Cf) = −Cf·Δm` — linear, correct sign (mass
  up → frequency down), with an inverse pair.
- BVD fit: `fit_bvd(freqs, Z)` recovers `f_s, f_p, Q, R, L, C, C0` from a
  synthetic impedance sweep (conductance peak → f_s and R; half-power width →
  Q; off-resonance susceptance → C0), round-tripping planted `R,L,C,C0` to
  relative error < 1e-3.
- Ring-down: `ringdown_Q(signal, t)` recovers τ (envelope log-fit) and ω (FFT
  peak); `Q = ωτ/2`.
- `stack_agreement()` cross-checks the three routes on one synthetic
  `BVDResonator` (frequency spread ~2.6e-6, Q spread ~1.9e-6) — model
  self-consistency, not measurement agreement.

## Negative results

Every number is fit to synthetic data. Three methods agreeing on the same
synthetic resonator is code self-consistency, not a measured crystal.
`refuse_synthetic_fit_as_measured_crystal` and `refuse_model_Q_as_device_Q`
raise.

## Deviations from prompt

None.

## Blocking inputs, when applicable

Real device `R,L,C,C0,Q` are `BLOCKED_MISSING_INPUT`. All fits are to synthetic
impedance sweeps and synthetic ring-down signals; no physical crystal was
characterized. Real device numbers require operated hardware (out of scope).

## Downstream impact

The BVD/ringdown model feeds the synchronized DAQ energy ledger (phase 24) and
the QCM-based baseline modal survey (phase 25).

## Reopening test

Re-run `tests/v6/test_r13_qcmstack.py`; reopen if the verdict string
`QCM_BVD_RINGDOWN_STACK_MODEL` changes, or if
`refuse_synthetic_fit_as_measured_crystal` or `refuse_model_Q_as_device_Q`
stops raising.

## Acceptance checklist

- [x] focused tests pass (16 passed)
- [x] receipt written
- [x] claim classes recorded
- [x] no private files read
- [x] PHYSICAL_VALIDATION_NOT_CLAIMED
