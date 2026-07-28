# R10.11 Unified Codec Grammar Families (Phase 5)

Declared BEFORE evaluation; 183 finite candidates; no old boundary
assumed; no location names in any decision path.

| Family | Candidates | Description |
|---|---|---|
| A | 42 | whole-number natural-width words: contiguous 3-bit deletion at every offset (31) + single octal-digit deletion at every position (11) |
| B | 90 | decimal header clip k∈{1,2,3} as typed field + payload bit-deletion at every offset; header agreement recorded per pair |
| C | 1 | typed star\|Sol\|body digits ("1","6","5\|7") as nested fields |
| E | 48 + 1 | Morton/XYZ level structures: pad {natural, 30/33} × axis perms (6) × level reversal (2) × Gray (2); plus E_SCATTER_DEL3 — ALL C(31,3)=4,495 three-bit deletion subsets per pair, intersected |
| F | 1 | finite reversible transducers: bounded to identity (non-trivial machine spaces are unbounded — searching them would silently widen the grammar; recorded, not done) |

## Result: ZERO survivors (`TESTED_GRAMMAR_INCOMPLETE_ZERO_SURVIVORS`)

Decisive sub-results:

1. **E_SCATTER_DEL3: zero hits even per-pair.** No refined word equals
   its compact plus 3 inserted bits ANYWHERE (contiguous or not). The
   refined→compact relation is a re-encoding, not digit-appending —
   this falsifies the entire "insert one child symbol" reading at the
   whole-word level.
2. Family C structural: typed third digits are 5→4 (pair 1), 8→7
   (pair 2), 5→5 (pair 3) across compact→refined. The −1/−1/0 pattern
   is RECORDED as data; no interpretation is invented.
3. Family B: no clip depth makes headers agree across all pairs while
   payloads align.

Cross-phase total: R10.9 (46) + R10.10 (32) + R10.11 (183) = **261
documented candidates, 0 survivors.** The unified codec remains
UNRESOLVED; the honest next step is the source's explicit offer of
purpose-built vectors (choose digit counts / faces), not wider
guessing.
