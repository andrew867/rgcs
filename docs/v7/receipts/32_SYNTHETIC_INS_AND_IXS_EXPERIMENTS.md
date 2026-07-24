# R13 Phase Receipt

```text
phase_id: 32
phase_title: Synthetic INS and IXS Experiments
status: COMPLETE
start_commit: 8ae9574
end_commit: v7.0.0 (branch v630-r13)
files_added: r13/scattering.py, tests/v6/test_r13_scattering.py
files_modified: none
tests_added: tests/v6/test_r13_scattering.py (12 tests)
focused_test_result: .venv/Scripts/python.exe -m pytest tests/v6/test_r13_scattering.py -q -> 12 passed
full_regression_result: 5638 passed, 8 skipped, 1 deselected, exit 0
source_hashes_used: build_meta source hash over SOURCE_ROOTS incl. r13
claim_classes_emitted: PROSPECTIVE_PREDICTION, BLOCKED_MISSING_INPUT
private_files_read: false
```

## Work completed

Predicted what neutron and X-ray instruments would observe for the candidate
modes and couplings. `r13/scattering.py` (tests
`tests/v6/test_r13_scattering.py`), verdict
**`SYNTHETIC_INS_IXS_PREDICTION_PROSPECTIVE`**.

## Evidence and equations implemented

- **Kinematics:** `scattering_kinematics` with neutron (`hbar^2 k^2 / 2m`) and
  X-ray (`hbar c k`) dispersions; `conserves()` checks energy and momentum
  against a named excitation, with wrong-excitation cases that must fail.
- **Bragg elastic:** `bragg_condition` peaks exactly on reciprocal-lattice
  points (off-point returns False); `braggs_law_holds` verifies
  `2 d sin(theta) = n lambda`.
- **One-phonon inelastic:** `one_phonon_sqw` from a Cartesian-polarization
  `PhononModel`, intensity proportional to `(Q.e)^2 / w * Bose`; the `(Q.e)`
  selection rule zeroes transverse-forbidden geometries, with a power check
  that rotating Q switches the mode back on.
- **Detailed balance:** `detailed_balance_ratio` matches `exp(hbar w / kT)`.
- `refuse_synthetic_sqw_as_beamtime_data` and `refuse_prediction_as_detection`
  raise.

## Negative results

A synthetic `S(Q,w)` is a prediction of what an instrument could observe, not
facility data and not a detection. No neutron or X-ray measurement was
performed. `PHYSICAL_VALIDATION_NOT_CLAIMED`.

## Deviations from prompt

None. The prompt calls for predicted instrument observables, delivered as a
labelled prospective `S(Q,w)` with the physics selection rules enforced.

## Blocking inputs, when applicable

Real beamtime data are `BLOCKED_MISSING_INPUT`: they require a neutron or
X-ray user facility (see phases 33, 34). The prediction is complete; the
detection is blocked. Responsible source class: a national neutron / X-ray
user facility.

## Downstream impact

Provides the feasibility `S(Q,w)` that phase 34's beam-time proposal draft
cites and that phase 35 ranks methods against, with the beamtime step held as
blocked so a synthetic spectrum cannot be read as a detection.

## Reopening test

Supply real facility `S(Q,w)` data and score it against the sealed
prediction; reopen when beamtime data exist (`refuse_prediction_as_detection`
no longer applies).

## Acceptance checklist

- [x] Neutron and X-ray kinematics with energy/momentum conservation checks.
- [x] Bragg condition on reciprocal-lattice points; Bragg's law verified.
- [x] One-phonon `S(Q,w)` with `(Q.e)` selection rule and rotate-Q power check.
- [x] Detailed balance matches `exp(hbar w / kT)`.
- [x] Synthetic-as-beamtime and prediction-as-detection refused.
- [x] Focused suite passes (12 passed).
- [x] Claim classes `PROSPECTIVE_PREDICTION` / `BLOCKED_MISSING_INPUT`; no
  physical validation claimed.
