# R10.11 Runlog (2026-07-27)

Branch `program/r10-11-flat-face-codec` off R10.10 `f34bb52…`.

1. **Gate Zero** — clean at f34bb52; descends from R10.10; nothing
   tagged/pushed (`R10_11_GATE_ZERO.json`).
2. **Baseline** — tests/r1010 + tests/r109: 55 passed (T10 fixtures,
   46/0 and 32/0 searches, V1 no-fold, V2 folds, holdout firewalls).
3. **Authority migration** — 20:07 header/hierarchy wording, 20:36
   CYYT pair, geometry wording, 20:39/20:40 craft-program wording
   appended VERBATIM to the private provenance ledger (gitignored
   internal-docs; craft wording recorded as operator provenance only —
   no physics or engineering claim authorized).
4. **Census** — 44 unique vectors imported; cross-checked against
   r109 registry V2; one bridging record (168500683) present only via
   census notes; fit set unchanged (`R10_11_VECTOR_CENSUS_AUDIT.md`).
5. **Contradiction audit** — CYYT compact under old boundaries lands
   in the orange/Channel branch, 32.7° from St. John's; F5|Q22|S3
   DEMOTED to EXACT_OLD_STRUCTURAL_PROFILE
   (`R10_11_OLD_PARSER_CONTRADICTION.md`).
6. **Unified codec search** — families A–F, 183 candidates, ZERO
   survivors; E_SCATTER (all C(31,3) deletions) zero even per-pair —
   refined words are re-encodings, not supersets. Cross-phase: 261/0
   (`R10_11_CODEC_*` artifacts).
7. **Flat-face node-curvature map** — implemented per spec (flat
   chords, affine subdivision, spherical node lift, no RBF); fitted 24
   node-direction params (reg 0.002) to Stonehenge/Erie/Toronto with
   Wilkes root (1e-6°) and SAA phase vertex (0.0° move) locks; anchors
   exact to 4e-05°; convex; 0 folds at depth 6; 0 edge mismatches;
   inverse 60/60 (`R10_11_NODE_*`, `R10_11_FLAT_FACE_GEOMETRY_SPEC.json`,
   `R10_11_CONVEXITY_AND_EDGE_AUDIT.md`). One audit bug fixed during
   verification (orientation sign convention measured against per-root
   handedness — the uniform-handedness false positive is documented in
   the runlog history).
8. **Controls** — midpoint / param-Slerp / Möbius / Snyder-style
   approx vs V1/V2/new (`R10_11_MAP_COMPARISON.csv`); new model best
   by 5 orders of magnitude at 24 params; only V2 folds.
9. **Montréal** — direct record retained; excluded from fit; 45.93°
   residual documented — codec-layer tension, not curvature.
10. **UK cluster** — re-decoded post-freeze only; never fit
    (`R10_11_UK_CLUSTER_REEVALUATION.md`, `R10_11_UK_CLUSTER_NEWMAP.csv`).
11. **Holdout freeze** — state hash 7f72241e…; predictions under the
    NEW map (polygons + uncertainty ~0.03°) with V1 continuity values;
    `1687209343` BLOCKED; digest a1546809…
    (`R10_11_HOLDOUT_FREEZE_RECEIPT.json`, `R10_11_PREREVEAL_PREDICTIONS.json`).
12. **Tests** — tests/r1011 focused suite + full repository suite
    (`R10_11_TEST_RECEIPT.json`); r1011 registered in SOURCE_ROOTS.
13. Single commit; no tag/push/release/publication.
