# R15 P19 — Prospective Prediction Registry

**Phase:** P19 (Tranche T6, Statistical Firewall)
**Module:** `r15/predictions.py`
**Tests:** `tests/v8/test_predictions.py`
**Verdict:** `PROSPECTIVE_PREDICTION_REGISTRY_SEALED`
**Claim class:** `MODEL_PREDICTION` — measured here: **nothing** — `PHYSICAL_VALIDATION_NOT_CLAIMED`

## Why the registry exists

A confirmatory result means something only if the prediction it confirms
was fixed **before** the data existed. If the hypothesis, the predicted
quantities, the null model, the decision rule, or the analysis plan can be
chosen or "clarified" once the numbers are visible, a match is
manufactured: the analysis was fitted to the answer. This phase makes that
boundary mechanical. A prediction is **sealed** — hashed and committed at a
passed-in epoch — before any run, so it becomes a fixed object that a later
result cannot be retrofitted onto.

A sealed prediction is **prospective, never a result.** Sealing commits
what a run *would* show if the hypothesis holds; it does not run anything.
Every record carries claim class `PROSPECTIVE_PREDICTION` and sits at `E0`
on the evidence ladder — a hypothesis, nothing measured.

## Extends, does not duplicate

This phase reuses the R13 authorities rather than building new ones:

- **Seal machinery** — `r13.preregister` (`Preregistration`, `seal`,
  `is_sealed`, the null/decision refusals, `PROSPECTIVE_PREDICTION`). Every
  prediction maps onto a genuine R13 preregistration whose seal is folded
  into the R15 commitment.
- **Power discipline** — `r13.experiments.planted_signal_power_check`, wrapped
  as `power_on_planted_check`.
- **Canonical serialization + hash chain** — `r13.serialize` (`content_hash`,
  `new_chain`, `append_record`, `verify_chain`) for the commitment and the
  sealed bundles.
- **Claim taxonomy / evidence ladder** — `r15.claims`.

No sibling R15 phase module is imported.

## What a prediction registers

`RegisteredPrediction` carries the full prediction:

- `hypothesis`, `predicted_signature`
- `quantities` — a tuple of `PredictedQuantity`, each with a **name**,
  **unit**, **tolerance**, **mode**, **frequency**, **direction**
  (`INCREASE`/`DECREASE`/`NONZERO`/`UNCHANGED`), and a **null expectation**
- `null_model` — required
- `decision_rule`, `analysis_plan`
- `power_on_planted` — required declaration of proven power on planted data
- `fingerprint` — an `ArtifactFingerprint` over the **model, code, data, and
  parameters** the prediction was written against
- `stopping_rule`, `mode` (`EXPLORATORY`/`CONFIRMATORY`), `epoch_committed`

A predicted quantity with no null expectation is refused: a negative result
on it would be uninterpretable.

## The seal binds every input

`seal(prediction)` returns a SHA-256 commitment over the whole plan — the
R13 base seal of the core plan **plus** the predicted quantities and the
artifact fingerprint. It is deterministic (same prediction and epoch →
same hash) and tamper-evident: any change to the hypothesis, a predicted
quantity, the analysis plan, the decision rule, the null model, or the
model/code/data/parameter fingerprint changes the commitment. `is_sealed`
checks the ledger.

## Two structural requirements (the R10.6 lesson)

Every prediction must be able to fail **and** to succeed for the right
reason. Both are enforced at construction:

- `refuse_prediction_without_null` — a prediction with no null model
  confirms itself.
- `refuse_prediction_without_power` — a prediction that never proves it can
  recover a planted effect of the predicted size is empty: a null result
  from such a design proves nothing, and a positive one is suspect.

`power_on_planted_check(detect_func, planted_effect)` demonstrates the
discipline: a detector must flag the planted effect (POWER) and stay silent
on pure noise (SPECIFICITY).

## Exploratory vs confirmatory

`classify_analysis(commitment)` returns `CONFIRMATORY` only if a prior
sealed prediction backs the analysis; otherwise `EXPLORATORY`.
`refuse_result_without_prior_seal(commitment)` refuses a confirmatory claim
with no seal — an analysis with no prior seal is at most exploratory,
because nothing distinguishes it from an analysis assembled once the answer
was known.

## The three forbidden retrofits

1. **HARKing** — `refuse_edit_after_seal(sealed, proposed)`. Rewriting a
   load-bearing field (hypothesis, predicted signature, analysis plan,
   decision rule, null model, quantities, or fingerprint) after the seal and
   presenting it as prospective is refused; the sealed and proposed
   commitments differ. The edit is legal before the seal
   (`already_sealed=False`) and forbidden after.
2. **Result without seal** — `refuse_result_without_prior_seal` (above).
3. **Stale prediction** — `refuse_stale_prediction(prediction,
   current_fingerprint)`. A prediction sealed against a model/code/data/
   parameter set that has since changed is stale (`is_stale` returns True,
   `staleness_report` names the changed components). Running it would
   confirm a prediction the current model never made; re-seal against the
   current fingerprint as a fresh prediction instead.

And `refuse_prediction_as_result` refuses to read any sealed prediction as
a measured outcome.

## Sealed bundles

`seal_bundle(prediction, epoch, chain=None)` seals a prediction and appends
its commitment to an R13 tamper-evident hash chain, so a sequence of sealed
predictions forms a verifiable, ordered ledger. `verify_bundle(bundle)`
verifies the chain end to end; editing any past record breaks it.

## Determinism

Everything is hash-based and clock-free: the commitment is a canonical
content hash, the fingerprint is a hash over passed-in artifacts, and every
epoch is passed in explicitly. `predictions_report()` is byte-stable across
runs.

## Negative results and non-claims

- Nothing is measured. Every model, dataset, quantity, and parameter here is
  a synthetic fixture.
- Sealing a prediction is a statement about the **order** in which the plan
  and the data were fixed — the plan first, hashed against a known model; the
  data, if they ever exist, second.
- The strongest class this module reaches is `MODEL_PREDICTION`; every
  prediction is `PROSPECTIVE_PREDICTION`. No physical validation is claimed,
  and there is no `PHRYLL_DETECTED` state.

## Reopening test

This phase reopens if any of the following becomes false:

- The seal is deterministic for a fixed prediction and epoch, and any input
  change alters the commitment.
- A prediction with no null model or no proven power on planted data is
  refused.
- An edit to a load-bearing field after the seal is detected as HARKing.
- A confirmatory result with no prior sealed prediction is refused as
  exploratory.
- A prediction sealed against a changed model is detected as stale.
- A sealed prediction is never reported above `PROSPECTIVE_PREDICTION` or as
  a measured result, and a tampered sealed bundle fails verification.

## Acceptance checklist

- [x] `r15/predictions.py` implements sealed predictions, predicted
      quantities, artifact fingerprints, the registry, exploratory/
      confirmatory separation, staleness detection, and sealed bundles.
- [x] Extends R13 (`preregister`, `experiments`, `serialize`) and
      `r15.claims`; no sibling R15 phase module imported.
- [x] Any input change alters the hash; power-on-planted proven; no-null and
      no-power refused; edit after seal is HARKing; result without prior seal
      is exploratory; stale predictions detected.
- [x] Focused, negative, and determinism tests green
      (`tests/v8/test_predictions.py`, 26 tests).
- [x] Receipt `docs/v8/receipts/P19.json` conforms to
      `phase_receipt.schema.json`; privacy scan clean (synthetic fixtures
      only).
