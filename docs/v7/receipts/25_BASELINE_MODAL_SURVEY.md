# R13 Phase Receipt

```text
phase_id: 25
phase_title: Baseline Modal Survey
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

Preregistered the first bench sequence that characterizes the apparatus
before any transfer experiment. The experiment is registered in
`r13/experiments.py` (verdict `PROSPECTIVE_EXPERIMENT_REGISTRY_PREREGISTERED`)
and sealed under the protocol in `r13/preregister.py`. Modal-survey analysis
reuses `r13/qcmstack.py` (the BVD / ring-down multi-frequency stack from
phase 21). Status `PREREGISTERED_NOT_RUN`.

- **Hypothesis:** the apparatus has a characterizable set of mechanical /
  electrical modes with stable frequencies and quality factors.
- **Predicted signature:** a discrete modal spectrum (peaks in the BVD /
  ring-down stack) reproducible across runs.
- **Null model:** no reproducible modal structure above measurement noise.
- **Decision rule:** confirm only if the same modes appear across independent
  runs with overlapping uncertainty; otherwise refute.

## Evidence and equations implemented

`Experiment.__post_init__` refuses a `RUN` status or a measurement claim
class, so the registry cannot silently promote a prediction to a result.
Power on planted data: the analysis provably detects a planted modal peak and
returns null on pure noise (`planted_signal_power_check`).

## Negative results

No bench exists and no survey was run. A preregistered predicted signature is
not a measured spectrum. `PHYSICAL_VALIDATION_NOT_CLAIMED`.

## Deviations from prompt

None. The prompt calls for preregistration ahead of any apparatus, which is
what was delivered.

## Blocking inputs, when applicable

Execution is `BLOCKED_MISSING_INPUT` on a built bench: no apparatus exists to
run the sealed survey against. The prediction is sealed and awaits data.

## Downstream impact

Establishes the modal baseline that later transfer experiments (phases 26-30)
reference. The seal prevents post-hoc promotion of any later run to a
measurement without unsealing.

## Reopening test

Unseal the preregistration and run the sealed analysis on real bench data;
reopen when a bench exists.

## Acceptance checklist

- [x] Experiment registered in `r13/experiments.py` and sealed by
  `r13/preregister.py`.
- [x] Hypothesis, null model, decision rule, and power-on-planted-data stated.
- [x] Registry refuses RUN status / measurement claim class.
- [x] Focused suite passes (17 passed).
- [x] Claim class `PROSPECTIVE_PREDICTION`; no physical validation claimed.
