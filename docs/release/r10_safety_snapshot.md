# R10 Public Release Safety Snapshot

Captured: `2026-08-03T21:05:50.0848944-02:30`
Safety branch: `release-safety-snapshot-20260803-2105` at `dfab636c4bf5e165103d7ebc72a693ef828b9987`
No worktree was deleted, no push was performed, and no tag was created during this phase.

### `git branch --show-current`

```text
rcw-public-workbench
```

### `git status --short`

```text
?? audit-worktree/
?? codex-worktree/
```

### `git log -1 --oneline`

```text
dfab636 R10.74: add annular ring development kit scaffold
```

### `git branch -vv`

```text
  claude/hydrogenuine-nexus-workbench-8a8ac1 8077e04 R10.61A: framing profiles, no default winner, LS-002 lane, evidence layer
  claude/rgcs-integration-agent-4c2405       b98b490 v8.2.0: R10.8.2 Locked Two-Layer Earth Root + Source-Map Calibration (7803, exit 0)
+ claude/rgcs-r10-62-terminal-vertex-4aca40  710e594 (C:/Users/andrew/OneDrive - Green O365/Documents/GitHub/RGCS/.claude/worktrees/rgcs-r10-62-terminal-vertex-4aca40) R10.73: constrained recipe becomes a bench-drive spec and falsification test
  emergent-resonator                         0af811f V4X-D-015/016: the checksum file did not check
+ main                                       8077e04 (C:/Users/andrew/OneDrive - Green O365/Documents/GitHub/rgcs-integration) [origin/main: ahead 3] R10.61A: framing profiles, no default winner, LS-002 lane, evidence layer
+ program/claude-authority-docs              188caab (C:/Users/andrew/OneDrive - Green O365/Documents/GitHub/rgcs-claude) Program(claude): stamp end_commit a66ee05 in handoff receipts
+ program/codex-core-algorithms              71e7342 (C:/Users/andrew/OneDrive - Green O365/Documents/GitHub/RGCS/codex-worktree) Add RGCS lab core demonstrators
+ program/codex-numerical-audit              42fc284 (C:/Users/andrew/OneDrive - Green O365/Documents/GitHub/RGCS/audit-worktree) Add Codex numerical audit receipts
+ program/cursor-app-integration             d4baf0d (C:/Users/andrew/OneDrive - Green O365/Documents/GitHub/rgcs-cursor) Record Cursor WS09 handoff receipt for the lab integration branch.
  program/integration                        3af2496 docs(release): finalize consolidation handoff
  program/r10-10-face-orientation            f34bb52 R10.10: face-orientation algebra, dual-graph propagation, expanded T11 search (zero survivors), holdout freeze
  program/r10-11-flat-face-codec             138a09a R10.59B: N-vector polygon lane with a live builder
  program/r10-9-variable-depth               b422e36 R10.9: variable-depth octal codec integration (typed T10/T11, direct Montréal, Earth V1/V2, sealed holdouts)
  r1081-cwatlas                              de620bb v8.1.0: R10.8.1 CW Atlas — bidirectional geocoder, 64 phases (7392, exit 0)
  r1082-locked-root                          b98b490 v8.2.0: R10.8.2 Locked Two-Layer Earth Root + Source-Map Calibration (7803, exit 0)
  r1083-result-reconciliation                b98b490 v8.2.0: R10.8.2 Locked Two-Layer Earth Root + Source-Map Calibration (7803, exit 0)
  r1084-recursive-coordinate-recovery        3235f05 R10.8.5A: outer-in gravity-shell projection — YELLOW, authority held
* rcw-public-workbench                       dfab636 R10.74: add annular ring development kit scaffold
  release/rgcs-v1-map-workbench              9a88db8 [origin/release/rgcs-v1-map-workbench] R10.62D: reconcile the four current-practice docs with the five-lane view
  v4-dev                                     661d406 [origin/v4-dev] v4.8.1: workbook column-loss fix (52 columns across 10 sheets)
  v4.6-cspc                                  caa15c3 [origin/v4.6-cspc] v4.6.0 P07-P08 (A30-A36): workbook integration, findings, adversarial, release
  v4.7-pmwr                                  e339b88 [origin/v4.7-pmwr] v4.7.0 (A00-A83): phase memory, worldline channel recovery, Phryll guards
  v4.7x-r3                                   6b359c2 [origin/v4.7x-r3] v4.7.1 R3 (A00-A96): root-space resolver, lens, spin, HAL, atlas
  v4.8-r4                                    bb62b59 [origin/v4.8-r4] v4.8.0 R4 (A00-A63): tetrahedral spin-addressed codec, four-state qualification
  v49-r6                                     7847c2e [origin/v49-r6: gone] v4.9.0: R6 release artifacts, workbook 35 sheets, metadata refresh
  v50-r7                                     ea1cb0a [origin/v50-r7] v5.0.0: document the reproducible test count (2161, not 2166)
  v51-r8                                     a7f7730 [origin/main: behind 134] docs: refresh the docs/ index and fix a link broken in published assets
  v52-r10                                    cf7be22 [origin/v52-r10] v5.3.0: the count is 2709, because fixing the count changed the count
  v52-r9                                     f40f4a8 [origin/v52-r9: ahead 2] v5.2.0: release metadata, evidence workbook, and version bump
  v53-r10-1                                  3fb6874 [origin/v53-r10-1] v5.3.1: release metadata, workbook, and the count set to 2808
  v531-r10-2                                 41537be [origin/v531-r10-2] v5.4.0: release metadata, workbook, count 2837
  v540-r10-2b                                a76174b [origin/v540-r10-2b] v5.4.1: release metadata, workbook, count 2867
  v541-r10-3                                 f733763 [origin/v541-r10-3] v5.5.0: release metadata, workbook, count 2948
  v550-r10-6                                 95cd750 [origin/v550-r10-6] v5.6.0: release metadata, workbook, count 3014
  v560-r10-7                                 977e0b6 R10.7: keep the private investigation particulars out of the public docs
  v570-r10-8                                 3fca1e5 v5.8.0: version bump, release notes, changelog, metadata, workbook, count 3340
  v580-r10-10                                d2381c6 v5.9.0: version bump, release notes, changelog, metadata, workbook, count 3485
  v590-r11                                   06e5e69 v6.0.0: version bump, release notes, changelog, metadata, workbook, count 4062
  v600-r11-delta                             81eea7e v6.1.0: version bump, delta findings, release notes, changelog, count 4412
  v610-r11-1                                 a6f8c94 v6.2.0: R11.1 findings, release notes, changelog, count 4936
  v620-r12                                   103b7e1 v6.3.0: R12 findings, release notes, changelog, count 5175
  v630-r13                                   59667f9 v7.0.0: R13 complete 48-phase discovery and experiment architecture (5638, exit 0)
  v800-r15                                   2f49122 v8.0.0: R15 complete 36-phase experimental phase infrastructure (6533, exit 0)
```

### `git worktree list`

```text
C:/Users/andrew/OneDrive - Green O365/Documents/GitHub/RGCS                                                       dfab636 [rcw-public-workbench]
C:/Users/andrew/OneDrive - Green O365/Documents/GitHub/RGCS/.claude/worktrees/hydrogenuine-nexus-workbench-8a8ac1 8077e04 (detached HEAD)
C:/Users/andrew/OneDrive - Green O365/Documents/GitHub/RGCS/.claude/worktrees/rgcs-integration-agent-4c2405       b98b490 (detached HEAD)
C:/Users/andrew/OneDrive - Green O365/Documents/GitHub/RGCS/.claude/worktrees/rgcs-r10-62-terminal-vertex-4aca40  710e594 [claude/rgcs-r10-62-terminal-vertex-4aca40]
C:/Users/andrew/OneDrive - Green O365/Documents/GitHub/RGCS/audit-worktree                                        42fc284 [program/codex-numerical-audit]
C:/Users/andrew/OneDrive - Green O365/Documents/GitHub/RGCS/codex-worktree                                        71e7342 [program/codex-core-algorithms]
C:/Users/andrew/OneDrive - Green O365/Documents/GitHub/rgcs-claude                                                188caab [program/claude-authority-docs]
C:/Users/andrew/OneDrive - Green O365/Documents/GitHub/rgcs-cursor                                                d4baf0d [program/cursor-app-integration]
C:/Users/andrew/OneDrive - Green O365/Documents/GitHub/rgcs-integration                                           8077e04 [main]
```

### `git tag --list`

```text
v1.0.0-rc1
v2.0.0
v3.0.0
v3.0.0-rc1
v3.0.1
v4.0.0
v4.0.0-alpha
v4.0.0-rc1
v4.1.0
v4.1.0-rc1
v4.1.1
v4.1.1-rc1
v4.2.0
v4.2.0-rc1
v4.2.0-rc2
v4.2.1
v4.2.1-rc1
v4.3.0
v4.3.0-rc1
v4.4.0
v4.4.0-rc1
v4.5.0
v4.5.0-rc1
v4.5.1
v4.5.1-rc1
v4.5.2
v4.5.2-rc1
v4.6.0
v4.6.0-rc1
v4.7.0
v4.7.0-rc1
v4.7.1
v4.7.1-rc1
v4.8.0
v4.8.0-rc1
v4.8.1
v4.8.1-rc1
v4.9.0
v5.0.0
v5.1.0
v5.2.0
v5.2.1
v5.3.0
v5.3.1
v5.4.0
v5.4.1
v5.5.0
v5.6.0
v5.7.0
v5.8.0
v5.9.0
v6.0.0
v6.1.0
v6.2.0
v6.3.0
v7.0.0
v8.0.0
v8.1.0
v8.2.0
```
