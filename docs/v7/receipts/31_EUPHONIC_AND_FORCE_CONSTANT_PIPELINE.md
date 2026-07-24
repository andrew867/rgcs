# R13 Phase Receipt

```text
phase_id: 31
phase_title: Euphonic and Force-Constant Pipeline
status: COMPLETE
start_commit: 8ae9574
end_commit: v7.0.0 (branch v630-r13)
files_added: r13/euphonic.py, tests/v6/test_r13_euphonic.py
files_modified: none
tests_added: tests/v6/test_r13_euphonic.py (13 tests)
focused_test_result: .venv/Scripts/python.exe -m pytest tests/v6/test_r13_euphonic.py -q -> 13 passed
full_regression_result: 5638 passed, 8 skipped, 1 deselected, exit 0
source_hashes_used: build_meta source hash over SOURCE_ROOTS incl. r13
claim_classes_emitted: ANALYTIC_MODEL, BLOCKED_MISSING_INPUT
private_files_read: false
```

## Work completed

Delivered a reproducible force-constant -> phonon interface for quartz.
`r13/euphonic.py` (tests `tests/v6/test_r13_euphonic.py`), verdict
**`FORCE_CONSTANT_INTERFACE_BLOCKED_ON_DFT`**. The interface is modelled in
the Euphonic style ourselves (the real `euphonic` package is not imported, so
its absence cannot break the build). Force constants are stored as real-space
blocks indexed by cell offset (`Phi_R[i,j]`), the way Euphonic actually stores
them.

## Evidence and equations implemented

- `phonon_dispersion(fc, qpath)` matches the analytic `2*sqrt(K/m)*|sin(qa/2)|`
  to 1e-9 and the diatomic two-branch closed form; the acoustic branch -> 0 at
  Gamma (sum rule enforced, with a broken-sum-rule negative control that does
  **not** reach zero).
- `density_of_states` integrates to the mode count with a van-Hove pile-up.
- `dynamic_structure_factor` is a clearly-labelled synthetic stub.
- `refuse_synthetic_fc_as_dft` and `refuse_model_dispersion_as_measured_INS`
  raise.

## Negative results

Synthetic force constants are not a DFT calculation, and a computed dispersion
is not an inelastic-neutron-scattering measurement. The real quartz phonon
spectrum remains blocked. `PHYSICAL_VALIDATION_NOT_CLAIMED`.

## Deviations from prompt

The prompt asks to "complete a reproducible atomistic pipeline". The interface
is complete and reproducible, but the real force-constant input is not
available in this environment, so the pipeline terminates at
`from_dft` with a blocked receipt rather than a computed real spectrum.

## Blocking inputs, when applicable

Real quartz force constants are `BLOCKED_MISSING_INPUT`: they require a
DFT/DFPT calculation not available here. `ForceConstants.from_dft(path)`
**raises** `EuphonicError` with a `BLOCKED_MISSING_INPUT` receipt — no
DFT/DFPT output exists in this environment. Responsible source class: an
external DFT/DFPT computation (e.g. a lattice-dynamics code run on a real
compute allocation).

## Downstream impact

Supplies the analytic phonon dispersion / DOS that phase 32 (synthetic
INS/IXS) and phase 34 (beam-time proposal feasibility) build on, while pinning
the real-spectrum step as blocked so nothing downstream can treat the model as
measured.

## Reopening test

Provide real DFT/DFPT force constants and call `ForceConstants.from_dft(path)`
successfully (no `EuphonicError`); reopen when a real force-constant file
exists and the dispersion is computed from it.

## Acceptance checklist

- [x] Force-constant -> phonon interface implemented; `euphonic` not imported.
- [x] Analytic monatomic and diatomic dispersions matched; acoustic sum rule
  enforced with a broken-sum-rule negative control.
- [x] DOS integrates to mode count; `S(Q,w)` labelled synthetic.
- [x] `from_dft` raises `BLOCKED_MISSING_INPUT`; synthetic-as-DFT and
  model-as-INS refused.
- [x] Focused suite passes (13 passed).
- [x] Claim classes `ANALYTIC_MODEL` / `BLOCKED_MISSING_INPUT`; no physical
  validation claimed.
