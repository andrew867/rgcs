# V4X final completeness runlog (v4.2.1 closeout)

Date: 2026-07-16/17. Executor: closeout audit per the final
completeness prompt. Baseline immutable facts, verified before any
edit:

## Phase 0 — immutable baseline

| Fact | Verified value |
|---|---|
| Branch / HEAD | `v4-dev` at `d253c2f43206d5d00325f54cb1b62744dcd3e364` |
| Tag `v4.2.0` | exists at `d253c2f` (also `v4.2.0-rc1` at `325bb4f`, `v4.2.0-rc2` at `d253c2f`) |
| GitHub release page v4.2.0 | **does not exist** (`gh release view v4.2.0` → not found); publication was blocked before completion |
| Latest published release | v4.1.1 |
| Real test count at `d253c2f` | **682 passed, 1 deselected** (from `release/v4/rgcs-v4.2.0-test-report.txt`, built at `d253c2f` per PROVENANCE.json) |
| Release-notes claim at the tag | "expect: 681 passed" — **defect V4X-D-004 (test-count contradiction)**, carried into the tagged docs |
| Local assets | 9 files in `release/v4/`, producer commit `d253c2f` |
| Hosted CI at `d253c2f` | run 29543412678: 10/10 jobs success |
| `main` | `448037b` = v4.1.1; no unrelated work on it |
| Frozen history | `git diff --stat 715486b HEAD -- archive/v2.0.0` empty; tags v2.0.0/v3.0.x/v4.0.0*/v4.1.0*/v4.1.1* at their recorded commits |
| Dirty working tree at audit start | in-flight 681→682 reconciliation edits (README, CHANGELOG, RELEASE_NOTES_V4_2_0, docs/README.md index, closeout guard) — kept for v4.2.1; baseline-scanner JSONs restored |

Branch decision: `v4-dev` is itself at `d253c2f` and is the branch
every previous release was cut from, so the closeout continues on
`v4-dev` rather than a new branch.

v4.2.0 disposition (Phase 9 rule): the tag stays immutable. It is
recorded as a **CI-green tagged expansion candidate whose release
publication was blocked before completion**, superseded by v4.2.1.

## Defect register (this closeout)

- **V4X-D-004** (P1, docs) — tagged v4.2.0 docs say "expect: 681
  passed"; the actual report at the same commit says 682. Cause:
  hand-maintained count. Fix: reconcile to the test-report artifact +
  add a count-agreement guard (Phase 7). CLOSED.
- **V4X-D-005** (P1, scientific) — the cusp acceptance question. See
  the full finding below; the audit's premise was incorrect and the
  real defect was in the metric. CLOSED.
- **V4X-D-006** (P0, scientific) — C05 metrology was **registry-only
  work labelled as an implemented workstream**. The ledger pointed A-
  and G-lane metrology at `harmonic_family.specimen_registry()`, a
  table of declared values, with no metrology pipeline behind it.
  Fix: `rscs2_core/metrology.py` implemented + 9 tests. CLOSED.
- **V4X-D-007** (P0, scientific) — T-lane **status laundering**: 18
  C-entries claimed `REDUCED_ORDER_VALIDATED` while only 6 had models,
  all 52 pointing at one registry file. Fix: 5 models implemented, 7
  entries downgraded to `SOURCE_HYPOTHESIS` with the reason recorded,
  `model_symbol` now verified by test. CLOSED.
- **V4X-D-008** (P1, scientific) — C01 lacked the strong-coupling
  criterion its own prompt makes mandatory ("do not report strong
  coupling without comparing splitting to losses"). Fix:
  `strong_coupling_criterion()` + verification against the complex
  eigenvalues. CLOSED.
- **V4X-D-009** (P1, completeness) — 47 required standalone documents
  missing; only 1 of 38 agents had its full deliverable set. Fix:
  Phase 6 document set. CLOSED.
- **V4X-D-010** (P1, completeness) — the P02 orphan sweep was never
  run, so the fixed 248 ledger was never checked against the corpus.
  Fix: `tools/v4x_orphan_sweep.py`; 20 orphans; coverage 248 → 268.
  CLOSED.

## V4X-D-005 in full — the cusp metric

The audit brief stated: *"the earlier cusp test expected greater than
5x concentration and was changed after observing approximately 1.44x"*
and asked whether the revised test merely matches the observed output.

**The premise is factually incorrect.** `git log -S"5 * sc.cusp_
response_metric"` returns exactly one commit — `bcd27b2`, where the
test was first written. The threshold has never been modified, and the
test asserts >5x today.

The real defect was in the **metric**, and it was worse:

| Measure | inner 10% radius |
|---|---|
| fraction of path **samples** | 69.5% |
| fraction of path **arc length** | 9.3% |

The unweighted metric summed over samples. A logarithmic spiral sampled
uniformly in theta crowds its samples near the centre, so the metric
reported that a **uniform** field had 69% of its energy concentrated at
the cusp. It was measuring the sampling grid.

| | concentrated | uniform | ratio |
|---|---|---|---|
| unweighted (buggy) | 0.9989 | 0.6945 | 1.438 |
| arc-length weighted | 0.9810 | 0.0928 | **10.576** |

The fix is justified by an **independent analytic control**, not by the
test passing: a uniform field's concentration must equal the arc-length
fraction (0.0928), and the weighted metric returns 0.0928.
`test_uniform_field_metric_equals_arclength_fraction` pins it.

Consequence: **ORPHAN-009** (cusp "singularity") is rejected on
evidence at 10.576x — a real, useful, and *finite* focusing effect. A
singularity would diverge under refinement; this does not. The earlier
1.44x figure is superseded and was itself an artifact.

Self-correction note: an earlier draft of this audit propagated the
1.44x figure into the orphan register and the spiral document before
the number was checked against the current code. It was wrong in both.
Both were corrected before commit.

## Phase 5 — the Eye, resolved

**Result: `NEAR_CONVENTIONAL_NODE_BUT_DISTINCT`, RESOLVED.**

| Level | spacing | centroid (mm) | d(v4.1) | d(station) | f₁ |
|---|---|---|---|---|---|
| cl3.0 | 3.423 | (0.237, −0.010, 100.986) | 1.375 | 5.138 | 13772.75 |
| cl2.0 | 2.362 | (−0.053, −0.038, 99.989) | 2.270 | 6.096 | 13772.38 |
| cl1.5 | 1.803 | (−0.048, −0.020, 99.783) | 2.476 | 6.298 | 13772.28 |

Halfwidth **1.803 mm** < separation **6.298 mm** → the comparison
carries information for the first time. The conventional model does not
explain the candidate.

**The v4.1 coordinate does not survive refinement.** d(v4.1) *grows*
monotonically: 1.375 → 2.270 → 2.476 mm. The candidate converges on
(−0.048, −0.020, 99.78), and at cl=1.5 there is no cluster at z=102.24.
The canonical record is preserved unchanged (G07); its interpretation
changes to resolution-limited.

Convergence: transverse agrees to 0.02 mm across the last two levels;
axial shift 1.039 → 0.207 mm; f₁ 13772.75 → 13772.38 → 13772.28 Hz.

**Honest stop.** cl=1.25 not attempted: measured **13.9 GB** at cl=1.5
on a 31.6 GB machine (4.5 GB free); calibrated projection ~45–71 GB.
Memory guard added (refuses a level leaving <6 GB free) and the ladder
now writes after every level so an infeasible level cannot destroy the
completed ones.

**Estimator correction.** The first resource estimate used the textbook
nnz(LU) ~ dof^1.5 rule and projected **0.29 GB** at cl=1.25. Reality at
cl=1.5 was 13.9 GB — the rule is 2-D; 3-D tet factors grow ~dof². The
model was recalibrated against the measurement (~150× error). Had the
original estimate been trusted, the run would have attempted cl=1.25
and thrashed a 31.6 GB machine.

## Phase log

- P0 complete: baseline above.
- P1 complete: crosswalk built; baseline 1/38 agents complete → 38/38.
- P2 complete: gates G42A–G42G; 268 rows; all pass.
- P3 complete: orphan sweep; 20 orphans; coverage 248 → 268.
- P4 complete: depth fixes (C01/C05/C06/C07/T-lane).
- P5 complete: Eye resolved (above).
- P6 complete: ~50 standalone documents.
- P7 complete: release metadata derived from a real pytest run.
- P8/P9: red team, release.
