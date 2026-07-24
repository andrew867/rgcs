# R13 Phase Receipt

```text
phase_id: 39
phase_title: Eight-Shell Mapping and Surface-Locked Trajectory
status: COMPLETE
start_commit: 8ae9574
end_commit: v7.0.0 (branch v630-r13)
files_added: r13/shellmap.py, tests/v6/test_r13_shellmap.py
files_modified: (none)
tests_added: 18
focused_test_result: test_r13_shellmap.py 18 passed
full_regression_result: 5638 passed, 8 skipped, 1 deselected, exit 0
source_hashes_used: build_meta source hash over SOURCE_ROOTS (incl. r13)
claim_classes_emitted: ANALYTIC_MODEL
private_files_read: false
```

## Work completed

Determined whether the S3 field maps to a physically coherent radial model in
`r13/shellmap.py`, reusing `r12.shells8`. `EightShell` holds nine monotonic
boundary radii; `assign_shell(r)` maps a radius to a shell index 0..7. Verdict
emitted: **`EIGHT_SHELL_MAPPING_MODEL`**; claim class `ANALYTIC_MODEL`.

## Evidence and equations implemented

- `assign_shell(r)`: monotonicity, correctness at each boundary (inclusive
  outer edge → shell 7), and an out-of-range raise.
- `shell_transfer(z1, z2)`: Fresnel energy fractions in exact `Fraction`
  arithmetic, so `R + T = 1` holds exactly; a matched boundary gives
  `T = 1, R = 0`.
- `mode_spacing` / `radial_modes`: radial eigenmodes scale with shell
  thickness.
- Refusals: `refuse_shell_as_decoded_layer`, `refuse_model_shell_as_measured`.

## Negative results

A shell index is a **coarse bin** — many radii map to one shell — not a
decoded physical layer identity, and nothing here is measured. The eight-shell
mapping is a coherent radial *model* with exactly conserved transfer, and no
more.

## Deviations from prompt

None.

## Blocking inputs, when applicable

None — analytic-model phase.

## Downstream impact

The shell-projection convention is one of the five R12 conventions whose
product forms the phase-37 alias set; the coarse-bin property documented here
contributes to the alias multiplicity.

## Reopening test

Re-run `tests/v6/test_r13_shellmap.py`; reopen if `R + T = 1` stops holding
exactly, if `assign_shell` boundary/monotonicity behaviour changes, or if
either refusal stops raising.

## Acceptance checklist
- [x] focused tests pass
- [x] receipt written
- [x] claim classes recorded
- [x] no private files read
- [x] PHYSICAL_VALIDATION_NOT_CLAIMED
