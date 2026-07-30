# R10.10 Runlog (2026-07-27)

Branch `program/r10-10-face-orientation` off R10.9
`b422e36ae4a289c0d392f946bf1b604a3b3c5065`. Venv
`%LOCALAPPDATA%/rgcs-int-venv`, Python 3.13.2.

1. **Gate Zero** — clean tree at b422e36; HEAD descends from the R10.9
   commit; no tags added; nothing pushed (`R10_10_GATE_ZERO.json`).
2. **R10.9 reproduction** — T10 fixtures byte-equal; 46-candidate
   search re-run: 0 survivors; V1 Stonehenge exact to 1e-9; V2 fold
   counts (102 L5 / 361 L6) and V1's 0 reproduced from the frozen
   receipts; direct Montréal decode unchanged; sealed-intake hash
   matches (`R10_10_R109_REPRODUCTION.json`).
3. **Orientation algebra** — six-element S3 group with exact
   composition/inverse/parity, vertex application, serialization,
   stable hashes; full Cayley closure receipt
   (`R10_10_ORIENTATION_GROUP.json`).
4. **Dual-graph propagation** — 20 faces / 30 adjacencies from the
   frozen V1 mesh; 60 directed edge transitions, all reflections, all
   inverting exactly; Wilkes-rooted BFS assignment; **path
   independence FAILS: all 12 dual 5-cycles have holonomy parity −1**
   — transition/phase model incomplete, recorded not patched
   (`R10_10_PATH_INDEPENDENCE_REPORT.md`).
5. **Child orientation** — table derived geometrically from
   barycentric structure: corner children identity, centre child
   `201` (cyclic parity +1, winding preserved, point-inversion TRUE —
   both flags tracked independently); traces through all four compact
   anchors (`R10_10_CHILD_ORIENTATION_TABLE.json`,
   `R10_10_ORIENTATION_TRACE_FIXTURES.json`).
6. **T11 search V2** — 32 documented orientation-aware candidates
   (FAM_ORIENT 8, FAM_ORDER_ORIENT 16, FAM_NODE 8 with reversible
   six-bit `spin*20+face` split, 60..63 refused); evaluated on both
   pairs generically: **ZERO survivors**; every rejection recorded
   (`R10_10_T11_*.csv/json`). Search V1 preserved as
   `T11_SEARCH_V1_EXHAUSTED`.
7. **Montréal tension audit** — separation 0.2574° under ALL six
   orientations; LCP 6/11; orientation excluded as the cause
   (`R10_10_MONTREAL_TENSION_AUDIT.md`).
8. **Earth V3** — NOT built; Phase 8 condition unmet; reason
   documented (`R10_10_NO_FOLD_REPORT.md`,
   `R10_10_EARTH_V1_V2_V3_COMPARISON.csv`).
9. **Holdout freeze** — implementation-state hash over r1010+r109
   sources; full-field pre-reveal predictions for the four decodable
   sealed vectors under V1 (current) and V2 (labelled FOLDED
   diagnostic): cell polygons, uncertainty radii, orientation states,
   shell/epoch firewall status; `1687209343` BLOCKED (T11 unresolved);
   receipts hashed (`R10_10_HOLDOUT_FREEZE_RECEIPT.json`,
   `R10_10_PREREVEAL_PREDICTIONS.json`). **The operator may now ask
   the source whether each result is correct and request labels;
   replies must be recorded verbatim; no retuning after reveal.**
10. **Tests** — tests/r1010 (16) + tests/r109 (39) = 55 passed;
    `r1010` registered in SOURCE_ROOTS (freshness guard); full
    repository suite result in `R10_10_TEST_RECEIPT.json`.
11. Single commit; no tag, push, release, publication, or public-main
    merge.
