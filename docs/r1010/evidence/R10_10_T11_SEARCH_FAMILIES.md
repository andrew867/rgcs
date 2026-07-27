# R10.10 T11 Search Families (Phase 5)

`T11_SEARCH_V1_EXHAUSTED` (R10.9: 46 candidates — 24 contiguous field
orders + 11 octal insertions + 11 bit-group insertions — ZERO
survivors) is preserved untouched in `r109.t11_candidates` and was
re-run this phase with the identical result.

## Search V2 — 32 new candidates (documented before evaluation)

| Family | Count | Grammar |
|---|---|---|
| FAM_ORIENT | 8 | canonical `F5\|Q22\|C3\|S3` frame; wire quaternary symbols read through the topology-derived orientation state (Wilkes-rooted BFS assignment seed, geometrically derived child transitions); options: symbol map APPLY/UNAPPLY × seed forward/inverse × child raw/remapped |
| FAM_ORDER_ORIENT | 16 | same machinery over the two other admissible field orders `QFCS`, `QCSF` (Q-before-C-before-S preserved; `QCFS` excluded — F between child and shell breaks the locked closure ordering) |
| FAM_NODE | 8 | six-bit node state = `spin*20 + face` (explicit reversible split; states 60..63 REFUSED, never wrapped); 2-bit shell class; options: symbol map × seed × spin active/inert |

Constraints applied generically to BOTH training pairs (no location
names anywhere in the code — test-enforced): exact round trip, parent
face/path/shell equal to the frozen compact decode, one appended
child, topology-derived orientation only, no holdout data.

## Result

**32 candidates, ZERO survivors —
`NO_CANDIDATE_IN_EXPANDED_FAMILIES`.** Per the spec's interpretation
table: the expanded grammar family is falsified or incomplete. Not
reinterpreted as aliases. Notable recorded rejections:

- 8 candidates refuse outright because the refined word's top five
  bits read the literal reserved face **23** in their layout — the
  refusal lock holding exactly where the node-23 lore predicts
  confusion;
- the rest fail parent-path equality (and mostly face/shell too):
  orientation remapping permutes symbols within levels, but the
  refined words' bit content differs from the compact words far more
  deeply than any per-level corner permutation can bridge.

## Honest boundary

Combined with R10.9: 78 documented candidates across two phases, zero
survivors. The T11 interleave remains **UNRESOLVED**. The dual-graph
holonomy finding (see `R10_10_PATH_INDEPENDENCE_REPORT.md`) suggests
the missing ingredient may be a per-crossing phase rule that no
current family can express; obtaining that rule from the source (or
from further archived material) is the gated next step — not wider
guessing.
