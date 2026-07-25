# R15 Circularity and Leakage Audit (P22)

**Phase:** P22 — Circularity and Leakage Audit (Tranche T6, Statistical Firewall)
**Module:** `r15/circularity.py`
**Tests:** `tests/v8/test_circularity.py`
**Receipt:** `docs/v8/receipts/P22.json`
**Reuses (no sibling phase imported):** `r13.holdout` (train/holdout disjointness authority), `r13.serialize` (deterministic content hash), `r15.claims` (claim taxonomy and forbidden promotions)
**Status:** COMPLETE — software/simulation only, no physical measurement.

## What this is

A number can look like a discovery and be nothing but the question asked
back to itself. This audit catches that. It examines an analysis **pipeline**
— an ordered list of steps that split data, engineer features, fit a model
and score it — and flags the steps whose result was already contained in
their own inputs. A pipeline that scores itself on data it was tuned on has
measured nothing new, and the audit says so **before** the score is ever
offered as evidence.

The audit operates no apparatus and measures nothing; it types the pipeline
it is given. `measured_here = "nothing"` and `PHYSICAL_VALIDATION_NOT_CLAIMED`.
The standing verdict is `CIRCULARITY_AUDIT_NO_CIRCULAR_RESULT_IS_CONFIRMATORY`.

## The five leak kinds (each a detector)

Each detector takes a list of `PipelineStep` records and returns a
`LeakFinding` whose `circular` flag says whether the pipeline is circular by
that mechanism.

| Kind (`LeakKind`) | Detector | Fires when |
| --- | --- | --- |
| `TRAIN_TEST_LEAKAGE` | `detect_train_test_leakage` | a TEST item id also appears in the TRAIN fold, or a training-side fitting step reads a feature `derived_from_labels`. The id-overlap check delegates to `r13.holdout.refuse_holdout_in_training`, so there is one truth system for "holdout leaked into training". |
| `DOUBLE_DIPPING` | `detect_double_dipping` | a `SELECT_FEATURES` step's `selected_on` fold is `FULL` or `TEST` — the selection peeked at the data it is later scored on. |
| `TARGET_LEAKAGE` | `detect_target_leakage` | a `FIT`/`PREDICT` step reads a predictor named in `target_features` (a proxy for the label), or a feature it declares `derived_from_labels`. |
| `PREPROCESSING_BEFORE_SPLIT` | `detect_preprocessing_before_split` | a `PREPROCESS`/`SELECT_FEATURES` step is fit on the `FULL` fold, or sits before the `SPLIT` step in pipeline order — test-fold statistics informed the transform. |
| `TEMPORAL_LEAKAGE` | `detect_temporal_leakage` | any training-item timestamp is at or after the earliest test-item timestamp — the past was informed by the future. |

## The pipeline model

A `PipelineStep` is opaque bookkeeping — nothing carries a physical quantity:

- `role` (`StepRole`): `SPLIT`, `PREPROCESS`, `SELECT_FEATURES`, `FIT`, `PREDICT`, `SCORE`.
- `fold` (`Fold`): `FULL` (the whole set, before any split — the anti-pattern for a fitting step), `TRAIN`, or `TEST`.
- `item_ids`, `features`: opaque string ids and feature names.
- `derived_from_labels`: features computed from the target.
- `selected_on`: which fold a selection peeked at.
- `timestamps`: `((item_id, int_time), ...)` for temporal ordering.

`audit_pipeline(steps, target_features=())` runs all five detectors and
returns a `PipelineAudit`: `circular` (any detector fired), the per-kind
`findings`, the union of `circular_steps`, the `leak_kinds` found, a
`reopening_test`, and a deterministic `content_hash` (via
`r13.serialize.content_hash`) so the same pipeline always audits to the same
digest.

## POWER and the negative control

- `clean_pipeline()` is the **negative control**: a split-before-fit pipeline
  with disjoint folds, the split before every fit, preprocessing/selection on
  the train fold only, no label proxy, and every train item before every test
  item in time. It passes all five detectors.
- `planted_leak_pipeline(kind)` is the **POWER control**: the minimal edit to
  the clean pipeline that trips exactly one detector. Each planted leak is
  caught by its own detector, flags the pipeline circular, and — verified by
  `test_only_the_planted_kind_fires` — trips no other detector.

## The refusal

`refuse_circular_result_as_confirmatory(audit, hypothesis="")` raises a
`CircularityError` whenever a circular audit is offered as confirmation of a
hypothesis. A result produced by a circular pipeline already contained its
own inputs — the holdout was trained on, the features were selected on the
test data, a predictor was the label in disguise, the transform saw the test
fold, or the past was told the future — and confirms nothing. A clean audit
passes silently.

The module also re-exports the governance-core refusals
`refuse_model_as_measurement` (a `MODEL_PREDICTION` is never a physical
measurement) and `refuse_phryll_detected` (there is no `PHRYLL_DETECTED`
state).

## What this does not say

A clean audit is a **necessary, not sufficient** condition for a result to
count as evidence. It does not assert that any non-circular result is true,
replicated, or physically measured — only that the result was not already
contained in its own inputs. The audit measures nothing. A circular result is
refused as confirmatory outright.
