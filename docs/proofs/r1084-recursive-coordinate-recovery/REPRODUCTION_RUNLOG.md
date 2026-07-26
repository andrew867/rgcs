# Reproduction runlog (R10.8.4)

All commands run from the repository root with the project venv
(`.venv/Scripts/python.exe`), branch `r1084-recursive-coordinate-recovery`.

## 1. Focused tests (parser, containment, geometry, gravity, vectors)

```
python -m pytest tests/cwatlas/r1084/ -q
# observed: 18 passed
```

## 2. Full trace suite + artifact generation

```
python tools/r1084_recursive_trace.py
# observed:
# SH sweep: 480 configs, in-face 24, contained 0, best min-dist 248.04 km
#   comp C0_none: best 248.04 km, contained False
#   comp C1_tangential_10_9: best 426.4 km, contained False
#   comp C2_radial_10_9: best 248.04 km, contained False
#   comp C3_metric_10_9: best 426.4 km, contained False
#   comp CTRL_tangential_9_8: best 491.1 km, contained False
#   comp CTRL_tangential_81_80: best 206.33 km, contained False
#   comp CTRL_tangential_55_54: best 191.19 km, contained False
```

Regenerates: FULL_VECTOR_TRACE.json, FACE_CODEBOOK_REPORT.md,
SHELL_AND_GRAVITY_GRADIENT_SPEC.md, ORANGE_SLICE_RECURSIVE_REPORT.md,
VARIABLE_LENGTH_REPORT.md, STONEHENGE_CONTAINMENT_REPORT.md,
COMPENSATION_REPORT.md, TEST_RECEIPT.json.

## 3. Regression (broad)

```
python -m pytest -q --deselect tests/regression/test_generator_determinism.py::test_generator_deterministic
# count recorded in the final R10.8.4 report
```

## Supersession notes

* The R10.8.3 reconciliation tool (`tools/r1083_cw_reconciliation.py`) was
  written but its execution was superseded by the R10.8.4 lock before any
  receipt was produced; its flattened-fraction pipeline is now a REJECTED
  model. No R10.8.3 receipt directory exists.
* `cwatlas/r1082/decoder_candidates.py` (typed candidate registry) remains
  valid: its parse-level facts are unchanged; its `local_triangle()`
  helper documents the *flattened* candidate, which the registry and
  LOCKED_INTERPRETATION.md now mark as rejected for the primary decode.
