# Route rendering

A wide-envelope record yields two refinement chains. Rendering them as a route is
a **hypothesis about chain semantics**, and one such hypothesis has already been
refuted.

## Views

1. **Abstract rooted tree** - depth vs step index. Works with **no Earth
   projector**, and is the only view that is safe by default.
2. Shell-depth vs step index.
3. Toroidal / poloidal / radial state trajectory.
4. Optional hedron mesh route, only when a **frozen** projector profile is
   supplied.

## Rules

- The left chain moves from source-local depth toward the pivot; the right chain
  from the pivot toward destination-local depth.
- Both normal and reversed transmission order are tested for each side; both
  representations are carried in every split as `chain_left_reversed` and
  `chain_right_reversed`.
- Parent labels are never invented from child digits.
- Steps whose transition law is unknown are marked **symbolic edges**.
- Illegal loops, impossible depth changes and state discontinuities are detected
  and reported.
- Route smoothness is a **diagnostic only**. It never selects a split.

## What has been refuted

Chain digits read as 45-degree compass bearings: **0 hits at p < 0.05 across 48
permutation tests, against 2.4 expected by chance.** None survived Bonferroni.

Recorded in
[`negative_results/R1063_WIDE_ENVELOPE_NULLS.md`](../negative_results/R1063_WIDE_ENVELOPE_NULLS.md),
including the test-design defect that made the first pass look positive.

## Selection

No split is selected. Ever - unless an independently frozen rule selects it, and
never because a rendering looks like a route.
