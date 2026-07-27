# R10.10 Final Report — Face-Orientation and T11 Recovery (2026-07-27)

**Verdict:
`RGCS_R10_10_YELLOW_FACE_ORIENTATION_IMPLEMENTED_T11_EXPANDED_FAMILIES_EXHAUSTED_ZERO_SURVIVORS`**

## What was recovered

- A complete, exact **triangle-orientation algebra** (S3: three
  cyclic, three reflected; composition, inverse, parity, application,
  serialization, stable hashing — all test-enforced).
- **Dual-graph orientation propagation** over the frozen Wilkes-rooted
  mesh: all 20 faces, 30 adjacencies, 60 directed edge-induced
  permutations (all reflections, all exactly inverting), deterministic
  BFS face assignments.
- A geometrically derived **child-orientation table** with the centre
  child's two independent flags (cyclic permutation parity +1;
  point-inversion TRUE) tested explicitly.

## The two load-bearing negative results (both spec-anticipated)

1. **Path independence fails**: every dual 5-cycle carries holonomy
   parity −1 (odd reflections). A single per-face orientation label is
   globally inconsistent under edge-reflection transport; the
   transition/phase model is INCOMPLETE. Corroborated empirically: the
   BFS assignment for mesh face 12 (`012`) is exactly one reflection
   from the recovered exact V1 convention (`102`). The missing
   per-crossing phase rule is UNRESOLVED — to be recovered, not
   invented.
2. **T11 expanded families exhausted**: 32 documented
   orientation-aware candidates (canonical + admissible reorders +
   reversible six-bit node-state participation) — ZERO survive both
   training pairs. Combined with R10.9: **78 candidates, 0
   survivors.** Zero is reported as falsification/incompleteness of
   the grammar families, never reinterpreted as aliases.

## Montréal and Earth

The direct-Montréal fold tension is **orientation-invariant**
(0.2574° pre-warp separation under all six corner orders; LCP 6/11
with Stonehenge). Orientation is excluded as the cause; field
placement / decode-model explanations remain open. Direct arithmetic
authority unchanged. Earth V1 remains the smooth candidate (0
reversals); V2 remains the folded diagnostic (361), never promoted;
**V3 not built** — no packet-geometry change justified it (documented
omission).

## Holdouts

R10.9 intake and receipts preserved; nothing sealed was used for any
selection or fit (test-enforced). Post-freeze full-field pre-reveal
predictions exist for all four decodable sealed vectors under both
operators, with cell polygons and uncertainty radii;
`1687209343` remains BLOCKED. Freeze and prediction receipts are
hashed. **Per protocol the operator may now ask the source whether
each decoded result is correct and request labels** — replies to be
recorded verbatim; no retuning after reveal.

## Standing unresolved

T11 interleave; per-crossing orientation phase rule; header-table
semantics; face-19 convention; epoch closure; Montréal decode model;
everything physical. Publication remains HOLD. No source-origin or
physical-coordinate validation is claimed.
