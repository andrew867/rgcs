# V4 Data & Inverse Modelling Spec — `rscs2_core.inverse` (RSCS2-U.*)

**Status:** PLANNING. Fits registered model families to synthetic and
public datasets with uncertainty and held-out validation. **No dataset
leakage; no null-model omission; licences recorded.** Fitted parameters
are DER with uncertainty; a fit never upgrades a HYP.

## 1. Datasets

| Class | Source | Use | Governance |
|---|---|---|---|
| Synthetic | v4 forward solver (known ground truth) | recover-the-truth tests | generator seed + manifest |
| Public — beams/forks/plates | licensed open datasets (NIST-style, published FEM benchmarks) | validate the fitter | licence + provenance row per dataset |
| Public — quartz/piezoelectric resonators | open impedance/FRF datasets where legally usable | crystal fitting | licence recorded; **none embedded without a permissive licence** |
| Bench (future) | Agent-14 pipeline outputs | real fits | schema-valid manifests |

Every dataset gets a **provenance + licence record** (extends
`SOURCE_REGISTER`); a dataset without a clear usable licence is not
committed — only a fetch script + checksum.

## 2. Inverse operators (RSCS2-U.2..U.6)

- **Frequency-response fit (U.2):** fit |FRF| / impedance to the
  harmonic-response model (RSCS2-S.5) for parameters (E, ρ, C
  components, Q, coupling g).
- **Mode matching (U.3):** MAC-based correspondence between measured and
  computed modes; ambiguity flagged, not silently resolved.
- **Deterministic estimation (U.4):** regularized least squares with
  confidence intervals.
- **Bayesian estimation (U.5):** posteriors with **registered,
  classified priors** (a Source-claim prior stays SRC; an informative
  prior is logged, never smuggled); model comparison via the v3 SAP
  information criteria, not ad-hoc Bayes factors.
- **Held-out validation + null model (U.6):** train/validation split
  with **no leakage**; every fit reports its skill against a null model
  (e.g. constant / geometric-mean baseline). A fit that does not beat
  its null is reported as such.

## 3. Uncertainty (RSCS2-U.1)

Monte-Carlo propagation of material/dimension σ through the forward
model; converges to the linear `UncertainValue` propagation
(`rgcs_core.uncertainty`) in the small-σ limit — that limit is the
regression anchor. Posteriors/CIs on every estimated parameter.

## 4. Anti-overfit / honesty rules

- pre-registered model families only; a new family needs a ledger row
  first (governance);
- non-uniqueness of inverse solutions is **stated**, never hidden
  (report the posterior, not a point);
- no leakage between fit and validation sets (enforced by a split
  manifest + a leakage test);
- a fit result is DER; it can support or fail a HYP but never *become*
  one.

## 5. Tests

Synthetic recover-the-truth (known params within CI); leakage test
(deliberate overlap → detected); null-model comparison present on every
fit; small-σ MC-vs-linear agreement (U.1 anchor); MAC correctness on a
known permutation; prior-classification lint (a SRC prior stays SRC);
licence-presence lint on every committed dataset reference.
