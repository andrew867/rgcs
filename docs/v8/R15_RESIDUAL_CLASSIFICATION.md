# R15 Residual Classification (P12)

**Phase:** P12 — Residual Classifier (Tranche T4, Evidence Engine)
**Module:** `r15/residuals.py`
**Tests:** `tests/v8/test_residuals.py`
**Depends on (concept only):** P10 (measurement ledger), P11 (ordinary-explanation engine)
**Status:** COMPLETE — software/simulation only, no physical measurement.

## What this is

The residual classifier types a residual — what is left after the model,
the calibration, and the known ordinary effects have been subtracted from an
observation — into **exactly one** `r15.claims.ClaimClass`, without
discovery inflation. Its whole purpose is to keep the ceiling for anything a
single laboratory's run can produce at `UNEXPLAINED_INSTRUMENT_RESIDUAL`:
never new physics, never a detection, and there is no `PHRYLL_DETECTED`
state.

The classifier operates no apparatus and acquires nothing. It types inputs
it is given. `measured_here = "nothing"` and
`PHYSICAL_VALIDATION_NOT_CLAIMED`.

## Inputs

The ordinary-explanation attack results are the **P11 concept passed in as
inputs** — this module does **not** import P11 (or any sibling phase
module); it reuses only `r15.claims`.

| Input | Type | Meaning |
| --- | --- | --- |
| `residual_id`, `observation_ids` | `str`, sequence | identity and the observations the residual is drawn from |
| `residual_magnitude` | `float ≥ 0` | the residual size, in the residual's units |
| `error_budget` | `ErrorBudget` | the decomposed uncertainty (below), plus `calibration_bound` and `model_adequate` flags |
| `attacks` | `tuple[OrdinaryAttackResult]` | each ordinary-explanation attack's `cause` and whether it `fired` |
| `replication` | `ReplicationEvidence` | independent-replication attempts, each a `ReplicationRecord(lab_id, independent, confirmed)` |

### Error budget

`ErrorBudget.combined()` is the **quadrature sum** of the standard
uncertainties, decomposed per `R15_ERROR_BUDGET_POLICY` into these canonical
components (any subset may be supplied; unknown names are refused):

`instrument_resolution`, `calibration`, `clock`, `environment`,
`fixture_repeatability`, `specimen_geometry`, `orientation`,
`numerical_method`, `dsp`, `operator_action`, `model_residual`.

## Decision order

The classifier is pure and deterministic — same inputs, same dossier — and
decides in this fixed order:

1. **Calibration gate.** An unbound / invalid calibration
   (`calibration_bound = False`) forces `CALIBRATION_ERROR` (invalid). No
   anomaly may be claimed on an uncalibrated number, however large the
   residual.
2. **Within budget.** A residual that does **not** exceed the combined
   uncertainty is a `KNOWN_ORDINARY_EFFECT` and is **not anomalous**. A
   residual below combined uncertainty is never anomalous.
3. **Ordinary explanation.** If any ordinary attack `fired` (an inadequate
   model, `model_adequate = False`, counts as a fired `MODEL_ERROR`), the
   residual is that fired attack's ordinary cause —
   `KNOWN_ORDINARY_EFFECT` / `MODEL_ERROR` / `CALIBRATION_ERROR` /
   `FIXTURE_EFFECT` — and is explained, not anomalous. When several fire, a
   fixed precedence (`CALIBRATION_ERROR` > `FIXTURE_EFFECT` > `MODEL_ERROR` >
   `KNOWN_ORDINARY_EFFECT`) makes the result reproducible.
4. **The ceiling.** A residual that survives **every** attack **and** exceeds
   the combined uncertainty **and** is unreplicated is an
   `UNEXPLAINED_INSTRUMENT_RESIDUAL`. This is the ceiling.
5. **Replicated anomaly.** Only genuine independent replication — at least
   `MIN_INDEPENDENT_LABS` = 2 **distinct** laboratories, each `independent`
   and `confirmed` — promotes the ceiling to `REPLICATED_ANOMALY`. One run,
   or one lab (however many times repeated), cannot.

```
                        ┌─────────────────────────────────────────┐
residual + budget ─────▶│ 1. calibration unbound? → CALIBRATION_ERROR (invalid)
+ attack results        │ 2. within combined uncertainty? → KNOWN_ORDINARY_EFFECT (not anomalous)
+ replication           │ 3. an ordinary attack fired? → its cause (by precedence)
                        │ 4. survives all + exceeds + unreplicated → UNEXPLAINED_INSTRUMENT_RESIDUAL  ◀── CEILING
                        │ 5. + independent replication (≥2 distinct labs) → REPLICATED_ANOMALY
                        └─────────────────────────────────────────┘
```

## Residual dossier

`ResidualClassifier.classify(...)` returns a `ResidualRecord` (a residual
dossier) that serializes to `r15/schemas/residual_record.schema.json`:
`residual_id`, `observation_ids`, `ordinary_explanation_attacks`,
`combined_uncertainty` (the full decomposed budget), `classification` (the
one claim class) and `reopening_test`. It also carries `classifier_version`
so a **classification change is versioned**, plus the standing honesty
fields.

### Reopening tests

Every classification is provisional and names the evidence that would reopen
it. The ceiling's reopening test is the strictest: it can be reopened **only**
via independent replication in at least 2 distinct laboratories — a single
lab or a single run cannot reopen it to a replicated anomaly, and it is never
new physics.

## Refusals

- `refuse_residual_as_new_physics()` — an `UNEXPLAINED_INSTRUMENT_RESIDUAL`
  is the ceiling for an unreplicated residual; it is not new physics, a new
  particle, or a new energy. Delegates to the governance core's canonical
  text.
- `refuse_unexplained_as_replicated_without_replication(...)` — the ceiling
  becomes a `REPLICATED_ANOMALY` only with independent replication in ≥2
  distinct labs. One run, or one lab, is refused.
- `refuse_phryll_detected()` — reused from `r15.claims`. There is no
  `PHRYLL_DETECTED` state anywhere in R15.

## What this does not say

It does not say any residual is a detection, a resonance, a new particle, a
new energy, or new physics. No apparatus was operated and nothing was
measured; the classifier types inputs it is given. The strongest label an
unreplicated residual can carry is `UNEXPLAINED_INSTRUMENT_RESIDUAL`.
`PHYSICAL_VALIDATION_NOT_CLAIMED`.

## Tests

`tests/v8/test_residuals.py` (26 tests): the within-budget path; each
ordinary cause and the multi-fire precedence; the missing-calibration and
inadequate-model gates; the ceiling; replicated anomaly reached only via two
independent labs; the negative paths (one lab / one run / non-independent
replication cannot reach a replicated anomaly; the ceiling is not promoted to
new physics or to a replicated anomaly without replication; phryll refused);
classification versioning; determinism; input validation; and schema
conformance.
