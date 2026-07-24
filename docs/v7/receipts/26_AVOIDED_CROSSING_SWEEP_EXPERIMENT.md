# R13 Phase Receipt

```text
phase_id: 26
phase_title: Avoided-Crossing Sweep Experiment
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

Preregistered a prospective search for coupled-mode hybridization under a
declared tuning parameter. Registered in `r13/experiments.py`; the analysis
math is `r13/avoided.py` (verdict `AVOIDED_CROSSING_MODEL_ANALYTIC`). Sealed
under `r13/preregister.py`. Status `PREREGISTERED_NOT_RUN`.

- **Hypothesis:** as a declared tuning parameter sweeps two modes through
  degeneracy, a real coupling opens a gap of `2|g| > 0` (they repel rather
  than cross), with eigenvector character exchanged across the crossing.
- **Predicted signature:** a minimum gap equal to `2|g|` and a
  diabatic <-> adiabatic character swap.
- **Null model:** the modes cross freely (gap consistent with zero) — mere
  numeric proximity, not hybridization.
- **Decision rule:** confirm hybridization only if the fitted minimum gap is
  significantly non-zero **and** the character swap is observed; a close
  approach alone is refuted as numeric proximity.

## Evidence and equations implemented

`r13/avoided.py` fits the two-level anticrossing minimum gap `2|g|` and
tracks eigenvector character across the sweep. Power: the fit provably
resolves a planted gap and returns null when `g = 0`.

## Negative results

No sweep was performed. Numeric proximity of two modelled frequencies is not
hybridization, and a computed anticrossing is not an observed mode repulsion.
`PHYSICAL_VALIDATION_NOT_CLAIMED`.

## Deviations from prompt

None. Delivered as a sealed prospective experiment ahead of apparatus.

## Blocking inputs, when applicable

Execution is `BLOCKED_MISSING_INPUT` on a built bench: no tunable apparatus
exists to sweep. The prediction is sealed and awaits data.

## Downstream impact

Feeds the transfer-of-modal-character line (phase 11) with a prospective,
falsifiable hybridization test that later runs can be scored against without
post-hoc tuning.

## Reopening test

Unseal the preregistration and run the sealed analysis on real bench data;
reopen when a bench exists.

## Acceptance checklist

- [x] Experiment registered and sealed; analysis in `r13/avoided.py`.
- [x] Hypothesis, null model, decision rule, and power stated.
- [x] Gap-vs-crossing discrimination has a planted-signal power check.
- [x] Focused suite passes (17 passed).
- [x] Claim class `PROSPECTIVE_PREDICTION`; no physical validation claimed.
