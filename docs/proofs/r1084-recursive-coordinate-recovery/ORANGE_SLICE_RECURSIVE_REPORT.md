# Orange-slice recursive report (R10.8.4 SS9.2)

Recursive paths (exact, parser-locked):

```json
{
 "165892743": [
  [
   1,
   6,
   5
  ],
  [
   8,
   9,
   2
  ],
  [
   7,
   4,
   3
  ]
 ],
 "165892763": [
  [
   1,
   6,
   5
  ],
  [
   8,
   9,
   2
  ],
  [
   7,
   6,
   3
  ]
 ],
 "165892783": [
  [
   1,
   6,
   5
  ],
  [
   8,
   9,
   2
  ],
  [
   7,
   8,
   3
  ]
 ]
}
```

* first two refinement levels identical: L1 (1,6,5), L2 (8,9,2) — VERIFIED
* level-3 X instruction identical (7), Z instruction identical (3) —
  VERIFIED
* only level-3 Y changes: 4 -> 6 -> 8 — VERIFIED
* radial intervals identical at the differing level (same Z path) —
  VERIFIED (test_orange_slice_level3_cells_share_prefix_cell)
* all three level-3 cells are DOWN (folded) children: 7+4, 7+6, 7+8 >= 10

Geometry in the report frame: cell representatives are collinear on one
great circle to 0.0000 deg with spacing 15.67 km then
15.65 km (equal steps of two lattice units).

Classification: **one child-axis line** — the level-3 Y-instruction axis
inside the shared level-2 cell (lattice column i = 2 constant, j stepping
by 2). It is NOT a face cevian (does not pass through a face vertex), NOT
a dual-graph path (all three cells share one face), and constant-radius
by construction (identical Z path), so it is simultaneously a
constant-radius line. Meridionality depends on the frame context and is a
reporting property, not a parse property.
