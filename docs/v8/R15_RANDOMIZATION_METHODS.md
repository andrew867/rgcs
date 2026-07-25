# R15 P08 — Randomization Methods

**Module:** `r15/randomization.py`
**Tests:** `tests/v8/test_randomization.py`
**Receipt:** `docs/v8/receipts/P08.json`
**Verdict:** `RANDOMIZATION_PRECOMMITTED_REPRODUCIBLE_BALANCED`
**Claim class:** `SOFTWARE_IMPLEMENTED` — measured here: **nothing**; `PHYSICAL_VALIDATION_NOT_CLAIMED`.

## What this is

A randomization engine for experiment order and condition assignment. It
does three jobs, and each one closes an ordinary explanation that would
otherwise swallow any apparent result:

1. **Deterministic under a committed seed** — the schedule is reproducible,
   so an independent party can regenerate and check it.
2. **Balanced** — block and Latin-square designs keep conditions from being
   confounded with order, session, or position.
3. **Pre-committed before runs** — the schedule is sealed by a SHA-256
   commitment so the order cannot be cherry-picked after seeing the data.

Nothing here is measured. Conditions are opaque labels, seeds are integers,
and no order, block, or square is a reading of any physical quantity. The
strongest class the module reaches is `SOFTWARE_IMPLEMENTED`: it schedules;
it does not acquire.

## Why randomization is a defence, not a decoration

Two ordinary explanations sink most informal experiments:

- **Order effects.** If condition A is always run before condition B, any
  drift over time — warm-up, fatigue, settling — is confounded with the A/B
  difference. Randomized order and balanced designs break that link.
- **Operator leakage.** If the operator chooses (or can nudge) the order
  after glimpsing the data, the order stops being independent of the
  outcome. A seed committed *before* the run, with no post-hoc reordering
  allowed, removes that degree of freedom.

The engine is built so that both defences are *checkable* rather than
promised.

## Designs

| Design | Constructor | Balance property |
| --- | --- | --- |
| Complete random | `randomize(conditions, seed)` | a reproducible permutation |
| Randomized blocks | `random_blocks(conditions, n_blocks, seed)` | each condition exactly once per block |
| Latin square | `latin_square(symbols, seed)` | each symbol once in every row and every column |
| Counterbalanced plan | `randomization_plan(factors, seed)` | independent per-factor orders off one master seed |

Balance is asserted by `is_balanced_blocks` and `is_latin_square`, which
check the property directly instead of trusting the constructor. The Latin
square is built from a cyclic base square and then has its rows, columns,
and symbol labels permuted under the seed — every such permutation is still
a Latin square, so the row/column balance is preserved by construction and
re-verified by the check.

### Per-factor orders

`specimen_order`, `frequency_order`, `orientation_order`, and
`sensor_permutation` each draw from their **own** seed stream, derived from
the master seed by `derive_seed(seed, label)` (a SHA-256 of the seed and the
label). The streams are independent, yet the entire plan regenerates from
the single committed master seed — no clock, no external entropy.

## Reproducibility

Every draw uses `numpy.random.default_rng(seed)` and reads no wall clock.
Consequences:

- The same seed always yields the same schedule (`same_seed_same_order`).
- A different seed generally yields a different schedule
  (`different_seed_different_order`).

Reproducibility is what turns a schedule into evidence: anyone with the
committed seed can rebuild it and confirm it was not altered.

## Pre-commitment and tamper-evidence

A `RandomizationManifest` carries the design type, the seed, the produced
schedule, and a `design_hash` over the design spec (via the R13 canonical
serializer, `r13.serialize.content_hash` — no duplicate truth system).
Calling `seal()` takes a SHA-256 **commitment** over the seed, the design
hash, and the schedule.

The committed seed pins *the draw*; the design hash pins *what was drawn
over*. Together they make the assignment tamper-evident:

- `verify()` on the true schedule reproduces the commitment.
- `verify(swapped)` on any altered order fails.
- Re-sealing is refused — a second seal would let the schedule be swapped
  and committed again.

## No peeking, no post-hoc reordering

- **`refuse_read_before_seal`** — analysis or operator code that reads the
  assignment before the commitment exists is refused. An order seen early
  can still be nudged and then sealed as though it predated the data.
  `RandomizationManifest.reveal_schedule()` routes through this gate, so the
  schedule only unlocks after `seal()`.
- **`refuse_post_commit_reorder`** — any reorder after the commit is
  refused, even one that claims to be a correction. A genuine change
  requires a *new* manifest, separately committed, with the change recorded
  as a deviation.

## Blinding and confirmatory status

`refuse_confirmatory_after_unblind(unblinded)` collapses a run to
exploratory once the operator has seen the assignment: a confirmatory claim
rests on the blind holding through acquisition and reduction, and once it is
broken, order and leakage effects can no longer be excluded.
`analysis_status(manifest)` reports `NOT_YET_SEALED`, `CONFIRMATORY_ELIGIBLE`
(sealed and still blind), or `EXPLORATORY_ONLY` (unblinded).

## Balance failures, restarts, and deviations

Every departure from the pre-committed plan is recorded, never silently
dropped:

- `RandomizationManifest.record_deviation(kind, detail, epoch)` appends a
  typed `Deviation`. The `epoch` is passed in, never read from a clock, so
  the manifest stays deterministic.
- `restart(manifest, reason, epoch, restart_index)` produces a **new,
  unsealed** manifest under a deterministic restart seed
  (`restart_seed`), carrying the prior deviations plus a `RESTART` entry.
  The original sealed manifest is never edited — that would defeat the seal.

## What this does not say

It does not measure, acquire, or run anything. It assigns order and
conditions from a committed seed so the schedule is reproducible and, once
sealed, tamper-evident. Balance defends against order effects; the seal and
the no-peek / no-reorder refusals defend against operator leakage and
cherry-picking. Every condition and seed is synthetic; nothing here is a
physical measurement and no physical validation is claimed. This phase
advances no physical claim on the R15 evidence ladder.
