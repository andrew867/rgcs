# R10.10 Montréal Tension Audit (Phase 7)

Question: did the R10.9 fold failure come from face ORIENTATION, from
FIELD PLACEMENT, or from a remaining incompatibility?

## Measured answer: the tension is orientation-INVARIANT

- Direct Montréal `165879243` and Stonehenge `165876523` share the
  first **6 of 11** quaternary path levels (LCP = 6). Both cells
  therefore sit inside the SAME level-6 triangle on mesh face 12 under
  ANY orientation.
- Computed under all six corner orders: the pre-warp separation is
  **0.2574° in every case** — identical to four decimal places.
  Reordering corners relabels the shared cell but cannot move the two
  leaves apart.
- Conclusion: face orientation is EXCLUDED as the source of the
  conflict. The recovered orientation machinery (even with its
  documented holonomy incompleteness) cannot reconcile a ~0.26°
  pre-warp separation with ~5,000 km of target separation.

## Remaining candidate explanations (all OPEN, none assumed)

1. Field placement / decode model: the Montréal wire may not be a
   plain T10 SPATIAL sibling of Stonehenge — e.g. shell/epoch or
   header context could alter the spatial reading. No admissible
   family found so far expresses this (78 candidates rejected).
2. The nonlinear, face-dependent, shell-dependent decoding the source
   described (2026-07-26 provenance) — still unspecified.
3. An anchor revision on the source side.

## Authority unchanged

`165879243` remains current DIRECT compact arithmetic authority
(R109-MTL-01); nothing here alters it. Earth V1 remains the smooth
calibrated candidate; V2 remains the folded diagnostic; **Earth V3 was
NOT built** — no recovered packet-geometry change justified new
calibration correspondences (Phase 8 condition not met), so
`R10_10_EARTH_V1_V2_V3_COMPARISON.csv` carries `NOT_BUILT` in the V3
column and no no-fold run for V3 exists (nothing to verify).
