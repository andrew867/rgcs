# R13 Phase Receipt

```text
phase_id: 27
phase_title: Rotation Versus Squeezing Experiment
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

Preregistered a prospective test discriminating whether the driven response
is passive rotation, active squeeze, shear, or a mixture. Registered in
`r13/experiments.py`; the discrimination math is `r13/symplectic.py` (verdict
`SYMPLECTIC_TRANSFORMS_ROTATION_SQUEEZE_SHEAR`). Sealed under
`r13/preregister.py`. Status `PREREGISTERED_NOT_RUN`.

- **Hypothesis:** the two-channel driven response is one of a passive
  rotation, an active (parametric) squeeze, a shear, or a mixed symplectic
  map — distinguishable by their action on the quadrature covariance.
- **Predicted signature:** a rotation preserves `trace(cov)` (variance sum);
  a squeeze preserves `det(cov)` but splits the individual variances (one up,
  one down); every symplectic map preserves `det(cov)`.
- **Null model:** the response is an identity / passive phase shift with no
  active gain.
- **Decision rule:** classify as squeeze only if one quadrature variance
  rises and the other falls with the product preserved; classify as rotation
  only if the variance sum is preserved.

## Evidence and equations implemented

`r13/symplectic.py` computes the discriminating invariants on the quadrature
covariance; `refuse_squeeze_as_rotation` blocks calling parametric gain a
passive rotation. Power: planted rotation / squeeze covariances are correctly
classified.

## Negative results

No driven response was measured. Parametric gain is not a passive rotation,
and the classification here is of a modelled covariance.
`PHYSICAL_VALIDATION_NOT_CLAIMED`.

## Deviations from prompt

None. Delivered as a sealed prospective experiment ahead of apparatus.

## Blocking inputs, when applicable

Execution is `BLOCKED_MISSING_INPUT` on a built bench: no driven two-channel
apparatus exists to measure the covariance. The prediction is sealed and
awaits data.

## Downstream impact

Supplies the symplectic classification rule (phase 13) with a falsifiable,
preregistered discriminator so a future run cannot relabel gain as rotation.

## Reopening test

Unseal the preregistration and run the sealed analysis on real bench data;
reopen when a bench exists.

## Acceptance checklist

- [x] Experiment registered and sealed; analysis in `r13/symplectic.py`.
- [x] Discriminating invariants (`trace`, `det`) and refusals stated.
- [x] Planted rotation / squeeze covariances correctly classified.
- [x] Focused suite passes (17 passed).
- [x] Claim class `PROSPECTIVE_PREDICTION`; no physical validation claimed.
