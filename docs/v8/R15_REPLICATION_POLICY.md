# R15 Independent Replication Policy (P24)

**Phase:** P24 — Independent Replication Receipts (Tranche T6, Statistical Firewall)
**Module:** `r15/replication.py`
**Tests:** `tests/v8/test_replication.py`
**Depends on (reuse only):** `r15.claims` (governance core), `r13.serialize` (hash chain)
**Depends on (concept only):** P12 (residual classifier), P19–P23
**Status:** COMPLETE — software/simulation only, no physical measurement.

## What this is

Independent-replication receipts are the **only** path off the single-lab
ceiling. The residual classifier (P12) caps anything one laboratory can
produce at `UNEXPLAINED_INSTRUMENT_RESIDUAL`: a residual that survived the
ordinary-explanation firewall and exceeded its own error budget, but which one
apparatus, in one room, run by one operator, cannot promote any further. This
module types exactly what independent replication requires and decides, from a
hash-chained bundle of receipts, whether that residual may rise to a
`REPLICATED_ANOMALY` (evidence level E7).

Nothing here is measured. Every receipt in this repository is a synthetic
fixture; the module types passed-in receipts and operates no apparatus.
`measured_here = "nothing"` and `PHYSICAL_VALIDATION_NOT_CLAIMED`. Even a
`REPLICATED_ANOMALY` is only a replicated **unexplained** effect warranting
further study — never new physics, and there is no `PHRYLL_DETECTED` state.

## The independence ladder

Rerun, independent implementation, independent operator, and independent
laboratory are represented as **distinct** levels. Only the top level counts
as genuine independence.

| Level | Distinct apparatus | Distinct operator | Distinct site | Counts? |
| --- | --- | --- | --- | --- |
| `RERUN` | no | no | no | no — a same-setup re-run or a reanalysis of the same data |
| `INDEPENDENT_IMPLEMENTATION` | yes | — | — | no |
| `INDEPENDENT_OPERATOR` | yes | yes | no | no |
| `INDEPENDENT_LABORATORY` | yes | yes | yes | **yes** |

Independence is judged both against the **origin** and, for promotion,
**mutually** between confirming replications: two confirmations that share an
operator, apparatus, or site are not independent of each other, so only one of
them counts.

## The replication receipt

A `ReplicationReceipt` records one independent attempt:

| Field | Meaning |
| --- | --- |
| `origin`, `replica` | `LabIdentity(operator_id, apparatus_id, site_id, specimen_id)` — the who/what/where of each lab |
| `protocol_hash` | the **frozen** protocol hash the replica followed |
| `mode` | `REAL` / `REPLAY` / `SYNTHETIC` / `FAULT_INJECTION`, kept distinct; only `REAL` is physical |
| `residual_magnitude`, `combined_uncertainty` | the replica's **own** residual and error budget |
| `ran_ordinary_explanation_firewall`, `survived_ordinary_explanations` | whether the replica actually ran the firewall and whether the residual survived it |
| `outcome` | `CONFIRMS` / `FAILS_TO_CONFIRM` / `CONTRADICTS` |
| `blinded`, `independent_calibration`, `independent_analysis` | replication-bundle properties recorded where claimed |
| `has_raw_artifact` | required (with `REAL` mode) before an attempt could ever be a *physical* replication — none exists here |

A receipt is a **valid confirmation** only if `outcome == CONFIRMS`, the
residual **exceeds its own budget**, and it **survived the firewall it
actually ran**. A `CONFIRMS` that skipped the ordinary-explanation attacks, or
whose residual fell within its uncertainty, is not a confirmation — accepting
it would be confirmation bias.

## The blinded replication bundle

A `ReplicationBundle` is an append-only, **hash-chained** ledger (built on
`r13.serialize`) for one originating residual under one frozen protocol. Its
genesis record is the single-lab residual at the ceiling; every appended
receipt — confirming, **failed, or contradicting** — is chained on top and
never discarded. Epochs are passed in; the bundle never reads a clock.
Mutating any past record breaks `verify()` from that point onward, so a
promotion can always be re-derived and a retraction always drops it.

## The promotion rule

```
REPLICATED_ANOMALY  ⇔  ≥ MIN_INDEPENDENT_REPLICATIONS (= 2) mutually
                        independent confirming replications, each:
                          • following the frozen protocol hash,
                          • independent of the origin (distinct operator
                            AND apparatus AND site),
                          • mutually independent of each other,
                          • residual exceeding its own error budget,
                          • surviving the full ordinary-explanation firewall.
otherwise           →  UNEXPLAINED_INSTRUMENT_RESIDUAL  (the ceiling holds)
```

Selection of the mutually independent confirming set is greedy over
`receipt_id`, so the count is deterministic and order-independent.

## Negative results and refusals

- **Reanalysis is not replication** (`refuse_reanalysis_as_replication`): re-running the same code on the same data is a `RERUN`; it reproduces an analysis, not the phenomenon.
- **A same-lab re-run is not independent** (`refuse_same_lab_as_independent`): genuine independence requires a distinct operator AND apparatus AND site.
- **A single lab stays at the ceiling** (`refuse_promotion_without_replication`): fewer than two mutually independent confirmations leaves the residual at `UNEXPLAINED_INSTRUMENT_RESIDUAL`.
- **A skipped-firewall confirmation does not count** (`refuse_confirmation_bias`): a replication that skipped the ordinary-explanation attacks (or did not survive them, or did not exceed its own budget) is not a confirmation.
- **Synthetic replication differs from physical replication**: `is_physical_replication()` requires a `REAL` acquisition with a raw artifact — no such artifact exists here, so every receipt is a `SYNTHETIC_OBSERVATION`.
- **A replicated anomaly is still not new physics** (`refuse_residual_as_new_physics`, `refuse_phryll_detected`, reused from the governance core).

## Reopening test

Reopen a `REPLICATED_ANOMALY` if any contributing replication is retracted,
found non-independent (a shared operator, apparatus, or site), or found to have
skipped the firewall, dropping the mutually independent confirming count below
two. Reopen a residual toward promotion **only** via at least two mutually
independent replications — distinct operator AND apparatus AND site, distinct
from the origin and from each other — each following the frozen protocol,
exceeding its own budget, and surviving the full firewall. A same-lab re-run or
a reanalysis of the same data cannot reopen it, and it is never new physics.

## What this does not say

It does not say any residual was physically replicated. The strongest a
software layer types here is the **shape** of a replication; every receipt is
synthetic. A `REPLICATED_ANOMALY` is a replicated unexplained effect warranting
further study, never a detection, a resonance, a new particle, a new energy, or
new physics. `PHYSICAL_VALIDATION_NOT_CLAIMED`.
