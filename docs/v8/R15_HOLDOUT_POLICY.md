# R15 P20 — Holdout Dataset Authority Policy

**Phase:** P20 (Tranche T6, Statistical Firewall)
**Module:** `r15/holdouts.py`
**Tests:** `tests/v8/test_holdouts.py`
**Verdict:** `HOLDOUT_DATASET_AUTHORITY_SEALED`
**Claim class:** `SOFTWARE_IMPLEMENTED` — measured here: **nothing** — `PHYSICAL_VALIDATION_NOT_CLAIMED`

## Why the holdout authority exists

A holdout is only a holdout for as long as it stays unseen. The moment a
model is tuned against it, a partition is renamed to flatter a result, or
it is scored a second time after its response is known, it stops being a
test and becomes training data wearing the holdout's clothes. This phase
turns that discipline into machinery: it partitions the data, seals the
holdout **before** any modeling, freezes the model **before** the holdout
is scored, scores it **once** (or against a spent error budget), and logs
**every** access.

This phase reuses the R13 holdout authority directly rather than
duplicating it:

- the deterministic split, the SHA-256 commit/verify, holdout scoring
  against committed labels, and the planted-data power primitives are
  `r13.holdout` (`make_split`, `commit_holdout`, `verify_commitment`,
  `score_holdout`, `power_check`, `planted_label`, `planted_decoder`,
  `constant_decoder`);
- the model freeze is a `r13.serialize.content_hash`;
- the claim taxonomy and evidence ladder are `r15.claims`.

`refuse_holdout_in_training`, `refuse_decode_before_commit`, and
`refuse_overfit_as_generalization` are re-exported unchanged from
`r13.holdout`. No sibling R15 phase module is imported.

## The named partitions

`partition_dataset(item_ids, fractions=None, salt=...)` assigns each opaque
item id to exactly one partition by a hash of the id and the salt. The
assignment is a function of the ids, salt, and fractions alone, so it is
reproducible; the partitions are disjoint and cover every item.

| Partition | Role |
|-----------|------|
| `DEVELOPMENT` | build and tune the model |
| `CALIBRATION` | fix nuisance parameters |
| `CONTROL` | negative reference |
| `HOLDOUT` | **sealed**; scored once at the end |
| `FUTURE_MEASUREMENT` | reserved for data not yet acquired |

Default fractions are 0.50 / 0.15 / 0.10 / 0.20 / 0.05 and must sum to 1.0.
Because the split is a deterministic hash fixed before modeling, no
partition can be selected after a model has been tried.

**Development data cannot be relabelled holdout.**
`refuse_relabel_partition_as_holdout(current, proposed)` refuses renaming a
`DEVELOPMENT`, `CALIBRATION`, or `CONTROL` item to `HOLDOUT` — an item
already seen is no longer blind, and calling it holdout manufactures a
holdout out of training data.

## The sealed holdout manifest

`seal_holdout(holdout_labeled, epoch, source, salt)` returns a
`HoldoutManifest` carrying a SHA-256 commitment over the holdout ids and
their labels (reusing `r13.holdout.commit_holdout`), taken **before** any
modeling. The seal is tamper-evident: a substituted holdout, or the same
holdout with one label changed, fails `manifest.verify(...)` while the true
holdout passes. The `epoch` is passed in, never read from a clock, so the
manifest is reproducible.

`HoldoutSource` supports both `SYNTHETIC_PLANTED` labels (a deterministic
function of the ids — the power control) and `EXTERNAL_PHYSICAL` labels
supplied from outside. Neither is a physical measurement performed here: an
external label is opaque data to this authority.

## The no-peeking gate

The legitimate order is **partition → seal the holdout → freeze the model →
score**. `HoldoutAuthority.score(...)` passes these gates, in order:

1. **Committed** — the holdout must be sealed
   (`r13.holdout.refuse_decode_before_commit`).
2. **Frozen** — the model must be frozen with a content hash first
   (`refuse_score_before_model_frozen`); a model still free to change can
   be tuned until the holdout flatters it.
3. **Sealed labels** — scoring uses only the committed labels; a label set
   that fails the commitment is refused (`r13.holdout.score_holdout`).
4. **Policy** — see below.

## One-shot and sequential policies

- **`ONE_SHOT`** (default) — the holdout may be scored exactly once. A
  second score is refused (`refuse_multiple_holdout_scoring`): once the
  holdout's response is known, any later model choice is informed by it, so
  a second score is a training score in disguise.
- **`SEQUENTIAL`** — more than one look is allowed, but each spends part of
  a fixed `AlphaBudget`. When the budget is exhausted, further looks are
  refused. Looking at the holdout repeatedly inflates the false-positive
  rate unless each look reserves error in advance.

## Every access is logged; unauthorized access is refused

The authority records **every** access to the holdout — granted or refused
— as an `AccessRecord` (purpose, requester, epoch, granted flag). `SCORE`
and `AUDIT` are the only authorized purposes. Reading the sealed labels for
`TRAINING` or `MODEL_SELECTION` is refused (`refuse_unauthorized_access`)
and still logged — a model built or picked against the holdout labels has
been fitted to them, and its holdout score would certify nothing. This is
how the authority *prevents model selection against labels*.

## Power on planted data

`development_power_check(partition, decoder)` plants a deterministic label
on every `DEVELOPMENT` item and scores the decoder there. A rule-aware
decoder recovers them (detected); a null decoder stays near the
`1/num_classes` chance rate. A null on the sealed holdout is meaningful
**only because** the machinery is shown to detect a signal that is really
present — otherwise a null could just be blindness.

## Determinism

Everything is hash-based and clock-free: the partition and the commitment
are SHA-256 over the ids and labels, the model freeze is a canonical
content hash, and every epoch is passed in explicitly. `holdouts_report()`
is byte-stable across runs.

## Negative results and non-claims

- Nothing is measured. Every id is an opaque string and every label a small
  class index; no partition, holdout, or label here is real.
- A holdout is a statement about **what a model may see and when** — not
  about any physical outcome.
- The strongest class this module reaches is `SOFTWARE_IMPLEMENTED`. No
  physical validation is claimed, and there is no `PHRYLL_DETECTED` state.

## Reopening test

This phase reopens if any of the following becomes false:

- The partition assignment is a deterministic function of the ids, salt,
  and fractions (no cherry-picking).
- Development, calibration, or control data cannot be relabelled holdout.
- The holdout cannot be scored before the model is frozen.
- A `ONE_SHOT` holdout is scored at most once; a `SEQUENTIAL` holdout is
  scored only within its error budget.
- Scoring uses only labels that match the sealed commitment.
- Reading the holdout for training or model selection is refused, and every
  access is logged.
- Training performance is never presented as generalization.

## Acceptance checklist

- [x] `r15/holdouts.py` implements named partitions, sealed holdout
      manifests, a model freeze, one-shot and sequential policies, an access
      log with unauthorized-purpose refusal, and a planted-data power check.
- [x] Reuses R13 (`holdout`, `serialize`) and `r15.claims`; no sibling R15
      phase module imported.
- [x] Development data cannot be relabelled holdout; a score before the
      model is frozen is refused; a second one-shot score is refused;
      unauthorized access is detected and logged; sequential testing spends
      an error budget; overfit is not generalization.
- [x] Focused, negative, and determinism tests green
      (`tests/v8/test_holdouts.py`, 38 tests).
- [x] Receipt `docs/v8/receipts/P20.json` conforms to
      `phase_receipt.schema.json`; privacy scan clean (synthetic fixtures
      only).
