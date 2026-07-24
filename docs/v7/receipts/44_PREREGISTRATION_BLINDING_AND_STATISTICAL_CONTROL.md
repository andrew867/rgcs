# R13 Phase Receipt

```text
phase_id: 44
phase_title: Preregistration, Blinding, and Statistical Control
status: COMPLETE
start_commit: 8ae9574
end_commit: v7.0.0 (branch v630-r13)
files_added: r13/preregister.py, tests/v6/test_r13_preregister.py
files_modified: (none)
tests_added: 22
focused_test_result: test_r13_preregister.py 22 passed
full_regression_result: 5638 passed, 8 skipped, 1 deselected, exit 0
source_hashes_used: build_meta source hash over SOURCE_ROOTS (incl. r13)
claim_classes_emitted: PROSPECTIVE_PREDICTION
private_files_read: false
```

## Work completed

Made prospective discovery claims resistant to look-elsewhere effects and
operator leakage in `r13/preregister.py`. Verdict emitted:
**`PREREGISTRATION_AND_BLINDING_SEALED`**; claim class `PROSPECTIVE_PREDICTION`.
All phase 25–30 experiments are sealed under this protocol before any
(hypothetical) data.

## Evidence and equations implemented

- `Preregistration` seals hypothesis, predicted signature, null model,
  decision rule, analysis plan, stopping rule, and an explicit committed
  epoch. `__post_init__` **refuses** an empty null model or decision rule
  (the R10.6 lesson).
- `seal()` is a SHA-256 over the canonical serialization: deterministic, and
  it changes if the hypothesis or analysis plan changes afterward — so a
  retrofitted analysis is detectable.
- `blind_labels` / `unblind` hide condition assignment behind one-way codes;
  unblinding succeeds only against the sealed commitment.
- `requires_power_on_planted_data` flags a plan that has not declared it can
  detect a planted effect; `validate()` returns the four-point checklist.
- Refusals: `refuse_hypothesis_change_after_seal` (HARKing),
  `refuse_result_without_prereg`, `refuse_optional_stopping`,
  `refuse_prediction_as_result`.

## Negative results

Sealing a hypothesis makes a future claim honest; **it is not itself a
result**. A sealed prediction is not a measured outcome, and a preregistration
without a null model or decision rule is refused as not being one.

## Deviations from prompt

None.

## Blocking inputs, when applicable

None — the seal is a prospective-prediction artifact; the confirmatory data it
would gate remains outside this repository.

## Downstream impact

The seal format (built on the phase-41 canonical serialization) is what makes
the phase 25–30 experiment plans confirmatory rather than exploratory, and
`refuse_prediction_as_result` is one of the refusals the phase-43 red team and
phase-46 manuscript rely on.

## Reopening test

Re-run `tests/v6/test_r13_preregister.py`; reopen if a preregistration with an
empty null model or decision rule stops being refused, if `seal()` stops
detecting a post-seal hypothesis change, or if any of the four retrofit
refusals stops raising.

## Acceptance checklist
- [x] focused tests pass
- [x] receipt written
- [x] claim classes recorded
- [x] no private files read
- [x] PHYSICAL_VALIDATION_NOT_CLAIMED
