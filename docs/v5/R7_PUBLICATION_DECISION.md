# R7 Publication Decision Record

**Path chosen: `PRIVATE_RC`**

| Field | Value |
|---|---|
| Path | `PRIVATE_RC` |
| Decided by | Andrew Green (repository owner) |
| Decided on | 2026-07-18 |
| Programme | RGCS v5.0 R7 |
| Baseline | v4.9.0 (`7847c2e`) |
| Repository visibility at decision | private |

## Rationale

The decision between filing and publishing is unresolved, and no
registered patent agent has been consulted. `PRIVATE_RC` is the only
option that preserves both alternatives.

The three paths are not symmetric:

- `PRIVATE_RC` forecloses nothing.
- `FILE_THEN_PUBLISH` preserves the ability to publish later.
- `DEFENSIVE_PUBLICATION` preserves neither — it creates public prior
  art and destroys the author's own novelty in the same instant.

Choosing the reversible option while the decision is unresolved is
the only ordering that does not throw away optionality for free.

## What this decision means operationally

- The repository stays **private**.
- No new public release is created by R7.
- No enabling disclosure is published.
- All artifacts are preserved for a later decision.
- `r7.legacy.authorize_publication()` returns
  `authorized: False` with status `PRIVATE_RC_NOTHING_PUBLISHED`.
- The final token is the **private** one.

## What a git commit does and does not do

This distinction is enforced in `r7/legacy.py` because it is the one a
technically-minded person is most likely to get wrong.

A commit **does** provide:

- evidence of a date, if the history is preserved and trusted;
- a content hash showing the text has not changed since.

A commit **does not** provide:

- a patent filing or any priority date;
- a defensive publication in the legal sense;
- publication at all, while the repository is private;
- an enabling disclosure organised for a searcher to find;
- legal advice of any kind.

A private repository discloses nothing, so it neither establishes
prior art nor endangers novelty. **Making it public is the act that
does both at once** — it creates prior art against others and destroys
novelty for the author, in the same instant, and the two cannot be
separated afterwards.

## If the decision is revisited

Re-running the gate requires a new signed `DecisionRecord` with the
evidence its path demands:

- `FILE_THEN_PUBLISH` requires ten items including a registered patent
  agent, a prior-art search, a filing receipt, and publication dated
  after filing. The dataclass refuses to construct this path with
  `legal_advice_obtained=False`.
- `DEFENSIVE_PUBLICATION` requires eight items including a complete
  enabling disclosure, immutable timestamps and hashes, archival
  copies, an explicit open licence, and counsel review of the
  patent non-assertion policy.

## Disclaimer

Nothing in this record or in `r7/legacy.py` is legal advice. Grace
periods, jurisdictional rules, and what counts as an enabling
disclosure are questions for a registered patent agent. The module
enforces that a decision exists and is signed; it cannot and does not
say which decision is correct.
