# R10.9 T11 Finite Recovery — Alias Report (Phase 4)

**Result: `NO_CANDIDATE_IN_BOUNDED_SPACE` — the T11 interleave remains
UNRESOLVED. Zero of 46 declared candidates satisfy both training
pairs. No candidate was promoted; nothing was invented.**

## Declared bounded space (46 candidates)

1. `T11_CANDIDATE_ORDER_*` (24): all contiguous orderings of
   F5(5) + Q22(22) + C3(3) + S3(3) in the 33-bit frame of the 11-octal
   word (the four fields sum to exactly 33 bits).
2. `T11_CANDIDATE_OCTAL_DELETE_k` (11): refined octal11 = compact
   octal10 with the child digit inserted at octal position k.
3. `T11_CANDIDATE_BITSHIFT_GROUP_k` (11): refined bits = compact bits
   with one 3-bit child group inserted at bit offset 3k.

Constraints applied identically to BOTH pairs — refined Stonehenge
`1643789253` / compact `165876523`, and refined Toronto `1672875493` /
compact `168930443` — with **no location-named special case** (the
checker takes arbitrary pairs; a test asserts no location name appears
in the module source):

- structural decodability (valid face);
- exact encode/decode reversibility;
- same source face as the compact parent;
- same shell class;
- containment (refined parent path equals the compact path — one
  appended 8-way child refines the parent cell).

## Outcome

Per-candidate results: `R10_9_T11_CANDIDATES.csv` and
`R10_9_PARENT_CHILD_CONTAINMENT.json`. No candidate passes all
constraints on both pairs; therefore:

- the source statement "T11 uses a different interleave — similar but
  not identical" is CONSISTENT with this outcome (a trivially similar
  layout would have appeared in the bounded space);
- the exact T11 interleave remains **UNRESOLVED** (authority
  R109-PKT-05);
- refined values remain typed `T11` wires that are never truncated
  into the compact parser; the parent-child location identity
  (R109-PKT-07) remains a SOURCE_REPORTED constraint awaiting the true
  interleave;
- the finite ambiguity report is the honest deliverable — extending
  the space (bit permutations beyond contiguous fields, mixed-radix
  digit maps) is future bounded work, not license to guess.
