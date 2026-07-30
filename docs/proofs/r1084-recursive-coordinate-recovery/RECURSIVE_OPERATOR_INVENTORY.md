# Recursive operator inventory (R10.8.4 §4)

Audit of every candidate recursive operator already in the repository,
performed BEFORE any new operator was written.

| operator ID | path | definition | children | digit domain | face rule | radial rule | invertible | prefix containment | production wiring | tests |
|---|---|---|---|---|---|---|---|---|---|---|
| HCM_OCTAL_LOCALIZE | `cwatlas/localize.py` | one-to-eight refinement, octal path per depth; cell diameter halves per depth | 8 | 0–7 | face id + octal path | none (surface only) | yes (`forward`/`inverse`) | yes | R10.8.1 atlas geocoder | `tests/cwatlas/` |
| BASE100_FOLD_MOD20 | `cwatlas/r1082/spatialization.py` | 5 base-100 tokens folded to n; face = n % 20; path = base-8 of n//20, depth 10 | 8 | tokens 0–99 | n % 20 (defective: last-token-only) | packed shell field | yes | yes (via octal path) | v8.2.0 locked production | `tests/cwatlas/r1082/` |
| VARDEPTH_SQUARE_TO_TRIANGLE | `internal-docs/plans-v5/.../CW_VARDEPTH_V1_SPEC.md` §5 | extension digit pairs r1, r2; s = sqrt(r1), lambda = (1-s, s(1-r2), s r2) | continuous | base-100 pairs | inherits core | none | yes (spec) | claimed in spec | **spec only — never implemented** | none |
| R1082_LOCAL_BARYCENTRIC | `cwatlas/r1082/local_coord.py` | route -> point -> local barycentric in face | n/a | n/a | family route | none | partial | n/a | T04 diagnostics | `tests/cwatlas/r1082/` |
| DODECA_DUAL_ROUTE | `cwatlas/r1082/route_graph.py` | dual-graph traversal face<->vertex bridge | 3-adjacent | n/a | dual bridge | none | yes | n/a | T03 | `tests/cwatlas/r1082/` |

## Finding

**No existing repository operator has a decimal (0–9) per-axis digit
domain.** The only recursive surface operator is octal (HCM_OCTAL_LOCALIZE);
bridging decimal triplets into it would require flattening the digit stream
into an integer first — exactly the rejected move. The locked recursive
semantics therefore need a decimal-native operator.

## §4.1 family decisions (structural, not Stonehenge-fitted)

* **Family A** (digit-indexed child table): subsumed by Family C — the
  lattice IS a declared 100-entry child table; no independent table exists
  in the repo to audit. MERGED_INTO_C.
* **Family B** (decimal interval refinement transported through child
  transforms): equivalent to Family C on UP children but has no canonical
  folding rule for orientation-reversing children; C's lattice supplies
  exactly that rule. SUBSUMED.
* **Family C** (simplex lattice, ten parts per axis, deterministic
  folding): **SELECTED** — the unique operator that is (a) decimal-native,
  (b) bijective over the 100 digit pairs (55 UP + 45 DOWN children),
  (c) exactly invertible, (d) containment-exact, (e) genuinely recursive
  (DOWN children flip orientation, so the stream cannot be flattened into
  positional fractions — regression-tested). Implementation:
  `cwatlas/r1084/cw_surface_refinement.py`.
* **Family D** (hedron path + local residual): requires a declared split of
  digit roles that neither the source lane nor the repository supplies —
  BLOCKED_BY_MISSING_INPUT, recorded not guessed.
* **Family E** (existing octal/dyadic bridge): REJECTED — decimal-to-octal
  conversion flattens the stream (forbidden by the lock).

Selection basis: locked structural constraints and repository authority
only. Stonehenge proximity was **not** consulted (the selected operator was
implemented and tested before the containment sweep ran).

Radial rule: no repository radial subdivision exists; decimal tenth-nesting
is declared (`cw_radial_refinement.py`) with the root interval carried as a
finite set of DECLARED profiles, since the source lane never states the
radial datum.
