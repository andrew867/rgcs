# R13 Phase Receipt

```text
phase_id: 15
phase_title: Dynamic Quasi-Phase Matching
status: COMPLETE
start_commit: 8ae9574
end_commit: v7.0.0 (branch v630-r13)
files_added: r13/qpm.py, tests/v6/test_r13_qpm.py
files_modified: none (r13/__init__.py __all__ and packaging registered in Phase 01)
tests_added: 11
focused_test_result: 11 passed
full_regression_result: 5638 passed, 8 skipped, 1 deselected, exit 0
source_hashes_used: 52e50d49343e1e0b0fb65a13cf7c976d11ed9f2bfaa743ab0c28050b3409a834 (build_meta compute_source_hash over SOURCE_ROOTS incl. r13)
claim_classes_emitted: DYNAMIC_QUASI_PHASE_MATCHING_MODEL; NUMERICAL_SIMULATION
private_files_read: false
```

## Work completed

Delivered `r13/qpm.py` with focused tests in `tests/v6/test_r13_qpm.py`.
Verdict **`DYNAMIC_QUASI_PHASE_MATCHING_MODEL`**. Adapts programmable phase
matching to electromechanical and optical candidate bridges with explicit
mechanisms, via coupled-mode calculation.

## Evidence and equations implemented

- `conversion_efficiency(dk, L)` ∝ `(κL)²·sinc²(Δk·L/2)`: maximal at Δk=0
  (grows as L²), with zeros exactly at `Δk·L/2 = nπ` — proven both ways.
- `qpm_effective_coupling(dk, period, L)` accumulates amplitude under a
  sign-flipping ±1 grating: the matched period `Λ = 2π/Δk` drives secular
  growth with L (matched reaches ~127) while uniform coupling stays bounded by
  `2κ/|Δk|` (~4.0) — the load-bearing contrast.
- `dynamic_qpm(dk_of_z)` integrates the coupled-amplitude ODE through a
  z-dependent mismatch; a chirped grating broadens the acceptance bandwidth
  (FWHM ~5.9 vs ~0.5 fixed).
- `coupled_mode_solve` (RK4) conserves photon number (Manley–Rowe defect
  ~1e-15) in undepleted and depleted regimes.

## Negative results

No conversion was measured, and no programmable phase-matched device was
operated. Quasi-phase-matching here is a coupled-mode calculation.
`refuse_model_conversion_as_measured` raises: a computed conversion efficiency
is not a measured second-harmonic or parametric output.

## Deviations from prompt

None.

## Blocking inputs, when applicable

None for the model. A measured conversion efficiency would require operated
hardware (out of scope for this phase).

## Downstream impact

Supplies the conversion machinery reused by the Floquet/parametric model
(phase 16) and the cross-domain transfer benchmark (phase 30).

## Reopening test

Re-run `tests/v6/test_r13_qpm.py`; reopen if the verdict string
`DYNAMIC_QUASI_PHASE_MATCHING_MODEL` changes, or if
`refuse_model_conversion_as_measured` stops raising.

## Acceptance checklist

- [x] focused tests pass (11 passed)
- [x] receipt written
- [x] claim classes recorded
- [x] no private files read
- [x] PHYSICAL_VALIDATION_NOT_CLAIMED
