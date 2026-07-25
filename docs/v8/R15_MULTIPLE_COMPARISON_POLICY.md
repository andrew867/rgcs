# R15 Multiple-Comparison and Sequential-Analysis Policy (P23)

**Module:** `r15/multiple_testing.py`
**Tests:** `tests/v8/test_multiple_testing.py`
**Receipt:** `docs/v8/receipts/P23.json`
**Claim cap:** `SOFTWARE_IMPLEMENTED` (synthetic fixtures are `SYNTHETIC_OBSERVATION`).
**Measured here:** nothing. `PHYSICAL_VALIDATION_NOT_CLAIMED`.

An R15 experiment sweeps frequencies, angles, transforms, specimens,
sensors and retries. That is not one test but many, and this phase is the
firewall that keeps "many tests" from being laundered into "one
significant result." It supplies the corrections and the preregistered
stopping discipline, and it refuses the two moves that manufacture false
positives: reporting an uncorrected smallest p-value, and stopping on
significance with no preregistered rule.

Nothing in this phase is measured. Every p-value, z-score and family is a
synthetic fixture or a passed-in input; the module operates no apparatus.

## 1. The look-elsewhere effect

With `m` independent tests each at nominal level `alpha`, the probability
that *at least one* crosses is

    P(any cross) = 1 - (1 - alpha)^m        # look_elsewhere_probability(m, alpha)

which climbs toward 1 as `m` grows (at `alpha = 0.05`, twenty tests give
~0.64, a hundred give >0.99). Reporting the single smallest of `m`
uncorrected p-values therefore runs at the look-elsewhere rate, not at
`alpha`. `uncorrected_min_p_fpr` demonstrates this by Monte-Carlo under the
global null; `corrected_family_fpr` shows the inflation removed once a
correction is applied.

### Hidden retries count

The honest number of comparisons is **reported tests plus hidden retries**
— re-mounts, re-runs, dropped sensors, swept-then-discarded transforms.
`TestFamily.total_trials()` carries this, and every correction is applied
against it. A sweep reported as one test but re-run five times is six
comparisons, and the correction uses six. `effective_trials` exposes the
arithmetic; the negative test `test_hidden_retries_change_the_correction`
shows a p-value that passes against the reported count and fails against
the disclosed one.

## 2. Corrections

| Method | Controls | Rule |
|---|---|---|
| `BONFERRONI` | FWER | adjusted `p = min(m·p, 1)` |
| `HOLM` | FWER | step-down; k-th smallest ×`(m−k+1)`, monotone, clip at 1 |
| `BENJAMINI_HOCHBERG` | FDR | step-up; k-th smallest ×`m/k`, running min from the top, clip at 1 |

- **FWER** (family-wise error rate): the probability of *any* false
  rejection. Bonferroni and Holm bound it at `alpha`; Holm is uniformly at
  least as powerful.
- **FDR** (false-discovery rate): the expected *fraction* of rejections
  that are false. Benjamini-Hochberg bounds it at `alpha`.

**The power point.** FDR control is not merely conservative. With a few
true effects among many nulls it *recovers the true effects* while holding
the false-discovery fraction at `alpha`, where FWER control can be too
strict to detect anything. `power_and_error` measures both power (planted
effects recovered) and error (nulls wrongly rejected) against a
`synthetic_planted_family` whose ground truth is known:

- `test_bh_recovers_all_planted_effects` — BH recovers every planted
  effect with FDR ≤ `alpha`.
- `test_holm_recovers_effects_and_controls_fwer` — Holm recovers strong
  effects with zero false discoveries.
- `test_bh_is_more_powerful_than_bonferroni_with_many_effects` — with many
  moderate effects, BH rejects at least as many as Bonferroni.

**Sensitivity to method is a result.** `correction_sensitivity` reports
which hypotheses each method rejects. If the conclusion flips between
methods, the finding is fragile and the method must be preregistered, not
chosen after seeing which one "works."

## 3. Sequential analysis and alpha spending

Peeking at accumulating data and stopping the moment a threshold is crossed
is the look-elsewhere effect on a clock: enough looks and noise crosses any
fixed line. The legitimate alternative fixes a total error budget in
advance and merely *allocates* it across the looks.

`alpha_spending(alpha, information_fractions, spending)` returns a
`SpendingSchedule` with, per look, the cumulative alpha spent and a
per-look nominal boundary chosen so that

    prod_k (1 - a_k) = 1 - F(t_K) = 1 - alpha

i.e. the overall false-positive rate under independent looks is exactly
`alpha`. Spending functions:

- `LINEAR` — `F(t) = alpha·t`.
- `POCOCK` — `F(t) = alpha·ln(1 + (e−1)·t)` (spends earlier).
- `OBRIEN_FLEMING` — conservative early, most of the budget at the end.

`evaluate_sequential` walks the looks and stops the first time
`p_k ≤ a_k`. The control property is demonstrated:

- `naive_peeking_fpr` — using the full `alpha` at every look inflates the
  rate to the look-elsewhere value.
- `spent_peeking_fpr` — testing each look against its spent-down boundary
  holds the rate at `alpha`.

`test_spending_boundary_controls_sequential_fpr` shows `naive > 0.10` while
`spent ≈ alpha`. **Peeking spends alpha**: the cumulative spend rises
monotonically to exactly `alpha` at the final look.

## 4. The refusals

- **`refuse_uncorrected_multiple_comparisons(family)`** — a family of more
  than one test (counting hidden retries) with no correction is refused;
  the smallest raw p-value is small by construction. A single test is
  allowed through; a corrected family is allowed through.
- **`refuse_optional_stopping(prereg)`** — delegates to the R13 authority
  (`r13.preregister`) so there is one truth for optional stopping across
  the platform. Stopping on significance with no preregistered stopping
  rule / alpha-spending boundary is refused.
- **`refuse_exploratory_as_confirmatory(sealed_commitment)`** — ranking a
  family and reporting the top hit is exploration: the contrast was chosen
  after seeing the data, so its p-value is not confirmatory. Confirmation
  requires a contrast sealed in advance (delegates the seal check to
  `r13.preregister.refuse_result_without_prereg`).

Exploratory ranking and confirmatory testing are kept separate: an
exploratory scan can *generate* a hypothesis; only a sealed, preregistered
contrast tested on data it has not seen can *confirm* one.

## 5. Diagnostics

`diagnose(z_scores, null_variance)` flags an implausibly large `|z|`
(default `> 6`) and a collapsed null variance (`< 1e-6`). A vanishing null
variance makes every deviation look enormous and inflates `z` without
bound; these are prompts to stop and check the null model, never
detections.

## 6. Determinism

Every simulation takes `numpy.random.default_rng(seed)`; the same seed
reproduces the family and the Monte-Carlo estimate exactly.
`family_digest` hashes a family through the R13 canonical serializer
(`r13.serialize.content_hash`), so identical families hash identically and
any change to a p-value, label or retry count changes the digest. Results
carry `ANALYSIS_VERSION` so an analysis is reproducible.

## 7. What this phase does not say

Correcting p-values and spending alpha are bookkeeping about how many
things were tried and in what order. They remove the look-elsewhere and
optional-stopping inflations; they confirm nothing. A survived correction
is not a measurement and is not, by itself, new physics. A confirmatory
claim still needs a preregistered contrast and, above all, physical data —
none of which exists here.

**Reopening test.** Reopen this phase if: a family of more than one test
(including hidden retries) ever reports an uncorrected smallest p as
significant; a stop on significance is ever accepted with no preregistered
stopping rule; an exploratory top hit is ever read as a confirmatory
p-value; an alpha-spending schedule's cumulative spend ever exceeds the
target `alpha` or fails to be monotonic; a Benjamini-Hochberg or Holm
correction fails to recover planted true effects while controlling error on
the synthetic fixture; or any result here is emitted above
`SOFTWARE_IMPLEMENTED` / `SYNTHETIC_OBSERVATION`.
