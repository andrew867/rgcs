# R13 Phase Receipt

```text
phase_id: 28
phase_title: Linear, Elliptical, and Circular Mode Test
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

Preregistered the six-angle polarization-class experiment in a conventional
bench domain. Registered in `r13/experiments.py`; analysis draws on
`r13/sixangle.py` (the ring) and `r13/chiral.py` (circular-polarization
angular momentum). Sealed under `r13/preregister.py`. Status
`PREREGISTERED_NOT_RUN`.

- **Hypothesis:** the driven mode has a classifiable polarization state
  (linear, elliptical, or circular), measurable as a characteristic pattern
  across the six-angle ring plus a handedness.
- **Predicted signature:** a linear mode shows a two-lobe azimuthal pattern;
  a circular mode shows planar uniformity **with** a non-zero handedness
  (per-mode angular momentum +/-hbar).
- **Null model:** an unpolarized / structureless response.
- **Decision rule:** classify circular only if planar uniformity **and** a
  resolved handedness are both present. Uniformity alone is insufficient.

## Evidence and equations implemented

`r13/sixangle.py` provides the azimuthal ring pattern and `r13/chiral.py` the
per-mode angular momentum. The six-angle governance carries over:
`refuse_planar_uniformity_as_isotropy` means a uniform ring reading is not
3-D isotropy. Power: planted linear vs circular states are distinguished, and
a planted handedness flips with drive helicity.

## Negative results

No polarization was measured. Planar uniformity is not 3-D isotropy, and a
computed phonon angular momentum is not a measured circular-dichroism signal.
`PHYSICAL_VALIDATION_NOT_CLAIMED`.

## Deviations from prompt

None. Delivered as a sealed prospective experiment ahead of apparatus.

## Blocking inputs, when applicable

Execution is `BLOCKED_MISSING_INPUT` on a built bench: no six-angle sensor
ring exists to acquire the polarization pattern. The prediction is sealed and
awaits data.

## Downstream impact

Ties the six-angle ring (phase 22) and chiral-phonon (phase 12) results into a
falsifiable polarization-classification test with a firm uniformity-vs-isotropy
guard.

## Reopening test

Unseal the preregistration and run the sealed analysis on real bench data;
reopen when a bench exists.

## Acceptance checklist

- [x] Experiment registered and sealed; analysis in `r13/sixangle.py` and
  `r13/chiral.py`.
- [x] Circular requires uniformity AND handedness; uniformity-as-isotropy
  refused.
- [x] Planted linear vs circular states distinguished under power check.
- [x] Focused suite passes (17 passed).
- [x] Claim class `PROSPECTIVE_PREDICTION`; no physical validation claimed.
