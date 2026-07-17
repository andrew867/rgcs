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

- V4X-D-004 — tagged v4.2.0 docs say "expect: 681 passed"; the actual
  report at the same commit says 682. Cause: hand-maintained count.
  Fix: reconcile to the test-report artifact + add a count-agreement
  guard (Phase 7).
- (register grows below as phases run)

## Phase log

- P0 complete: baseline above.
