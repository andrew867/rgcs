# R10 Public Release Branch and Worktree Inventory

Generated: `2026-08-03T21:12:26.330283-02:30`
Baseline: `main` at `8077e04395b04464ad57d99a4b6b49e6b72a2e60`

Classification is applied to each branch delta relative to `main`, not as a declaration that every historical file at that tip is publishable. File-level release still requires the exclusion-first manifest. An unmatched or mixed lane is never auto-promoted.

## Branches

| Branch | HEAD | Main relation | Delta | Worktree state | Proof/test dirs | Class | Reason |
|---|---|---|---:|---|---|---|---|
| claude/hydrogenuine-nexus-workbench-8a8ac1 | `8077e04395b0` | same-as-main; +0/-0 | 0 | clean/not linked | 19 | **review-needed** | integration tree contains mixed historical lanes; publish only through the exclusion-first manifest |
| claude/rgcs-integration-agent-4c2405 | `b98b490a742d` | ancestor-of-main; +0/-74 | 0 | clean/not linked | 8 | **review-needed** | already contained in main; no delta to merge and no automatic publication decision |
| claude/rgcs-r10-62-terminal-vertex-4aca40 | `710e5947c80e` | descendant-of-main; +37/-0 | 415 | clean/not linked | 19 | **quarantine** | mixed 37-commit line contains public engineering commits and private decode/privacy commits; whole-branch merge prohibited |
| emergent-resonator | `0af811f77975` | ancestor-of-main; +0/-195 | 0 | clean/not linked | 4 | **review-needed** | historical resonator lane requires file-level public review |
| main | `8077e04395b0` | same-as-main; +0/-0 | 0 | changed=0, untracked=1 | 19 | **review-needed** | integration tree contains mixed historical lanes; publish only through the exclusion-first manifest |
| program/claude-authority-docs | `188caabea0ea` | ancestor-of-main; +0/-67 | 0 | clean/not linked | 10 | **safe-public** | bounded public work or receipt lane; merge only its delta after filter audit |
| program/codex-core-algorithms | `71e73423031f` | ancestor-of-main; +0/-68 | 0 | clean/not linked | 9 | **safe-public** | bounded public work or receipt lane; merge only its delta after filter audit |
| program/codex-numerical-audit | `42fc284b1ecb` | ancestor-of-main; +0/-56 | 0 | clean/not linked | 13 | **safe-public** | bounded public work or receipt lane; merge only its delta after filter audit |
| program/cursor-app-integration | `d4baf0d575f0` | ancestor-of-main; +0/-66 | 0 | clean/not linked | 12 | **safe-public** | bounded public work or receipt lane; merge only its delta after filter audit |
| program/integration | `3af2496969a1` | ancestor-of-main; +0/-49 | 0 | clean/not linked | 13 | **safe-public** | bounded public work or receipt lane; merge only its delta after filter audit |
| program/r10-10-face-orientation | `f34bb521c32e` | ancestor-of-main; +0/-47 | 0 | clean/not linked | 15 | **private** | private glyph/message research lane; no release merge |
| program/r10-11-flat-face-codec | `138a09a8eb88` | ancestor-of-main; +0/-8 | 0 | clean/not linked | 19 | **private** | private glyph/message research lane; no release merge |
| program/r10-9-variable-depth | `b422e36ae4a2` | ancestor-of-main; +0/-48 | 0 | clean/not linked | 14 | **private** | private glyph/message research lane; no release merge |
| r1081-cwatlas | `de620bb2585f` | ancestor-of-main; +0/-75 | 0 | clean/not linked | 7 | **safe-public** | bounded public work or receipt lane; merge only its delta after filter audit |
| r1082-locked-root | `b98b490a742d` | ancestor-of-main; +0/-74 | 0 | clean/not linked | 8 | **safe-public** | bounded public work or receipt lane; merge only its delta after filter audit |
| r1083-result-reconciliation | `b98b490a742d` | ancestor-of-main; +0/-74 | 0 | clean/not linked | 8 | **safe-public** | bounded public work or receipt lane; merge only its delta after filter audit |
| r1084-recursive-coordinate-recovery | `3235f05c3064` | ancestor-of-main; +0/-71 | 0 | clean/not linked | 9 | **review-needed** | authority is held and the branch title carries an ambiguous physical interpretation |
| rcw-public-workbench | `dfab636c4bf5` | diverged-from-main; +1/-69 | 74 | changed=0, untracked=2 | 11 | **safe-public** | bounded public work or receipt lane; merge only its delta after filter audit |
| release-safety-snapshot-20260803-2105 | `dfab636c4bf5` | diverged-from-main; +1/-69 | 74 | clean/not linked | 11 | **safe-public** | immutable local safety pointer; retain but do not merge |
| release/rgcs-v1-map-workbench | `9a88db8a045f` | ancestor-of-main; +0/-4 | 0 | clean/not linked | 19 | **safe-public** | bounded public work or receipt lane; merge only its delta after filter audit |
| v4-dev | `661d406e2bb6` | ancestor-of-main; +0/-169 | 0 | clean/not linked | 4 | **review-needed** | historical release tip is already contained in main but is not an automatic public-RC input |
| v4.6-cspc | `caa15c35dcbf` | ancestor-of-main; +0/-180 | 0 | clean/not linked | 4 | **review-needed** | historical release tip is already contained in main but is not an automatic public-RC input |
| v4.7-pmwr | `e339b887b938` | ancestor-of-main; +0/-176 | 0 | clean/not linked | 4 | **review-needed** | historical release tip is already contained in main but is not an automatic public-RC input |
| v4.7x-r3 | `6b359c2d23ad` | ancestor-of-main; +0/-174 | 0 | clean/not linked | 4 | **review-needed** | historical release tip is already contained in main but is not an automatic public-RC input |
| v4.8-r4 | `bb62b5918a63` | ancestor-of-main; +0/-172 | 0 | clean/not linked | 4 | **review-needed** | historical release tip is already contained in main but is not an automatic public-RC input |
| v49-r6 | `7847c2e34e18` | ancestor-of-main; +0/-161 | 0 | clean/not linked | 4 | **review-needed** | historical release tip is already contained in main but is not an automatic public-RC input |
| v50-r7 | `ea1cb0a37458` | ancestor-of-main; +0/-153 | 0 | clean/not linked | 4 | **review-needed** | historical release tip is already contained in main but is not an automatic public-RC input |
| v51-r8 | `a7f77308a21f` | ancestor-of-main; +0/-137 | 0 | clean/not linked | 4 | **review-needed** | historical release tip is already contained in main but is not an automatic public-RC input |
| v52-r10 | `cf7be2246d06` | ancestor-of-main; +0/-117 | 0 | clean/not linked | 4 | **review-needed** | historical release tip is already contained in main but is not an automatic public-RC input |
| v52-r9 | `f40f4a8e840a` | ancestor-of-main; +0/-128 | 0 | clean/not linked | 4 | **review-needed** | historical release tip is already contained in main but is not an automatic public-RC input |
| v53-r10-1 | `3fb687475197` | ancestor-of-main; +0/-110 | 0 | clean/not linked | 4 | **review-needed** | historical release tip is already contained in main but is not an automatic public-RC input |
| v531-r10-2 | `41537be8b438` | ancestor-of-main; +0/-106 | 0 | clean/not linked | 4 | **review-needed** | historical release tip is already contained in main but is not an automatic public-RC input |
| v540-r10-2b | `a76174b2e5c4` | ancestor-of-main; +0/-103 | 0 | clean/not linked | 4 | **review-needed** | historical release tip is already contained in main but is not an automatic public-RC input |
| v541-r10-3 | `f73376331bd1` | ancestor-of-main; +0/-100 | 0 | clean/not linked | 4 | **review-needed** | historical release tip is already contained in main but is not an automatic public-RC input |
| v550-r10-6 | `95cd7504ea73` | ancestor-of-main; +0/-96 | 0 | clean/not linked | 4 | **review-needed** | historical release tip is already contained in main but is not an automatic public-RC input |
| v560-r10-7 | `977e0b6a6e3c` | ancestor-of-main; +0/-93 | 0 | clean/not linked | 4 | **review-needed** | historical release tip is already contained in main but is not an automatic public-RC input |
| v570-r10-8 | `3fca1e54ed7d` | ancestor-of-main; +0/-90 | 0 | clean/not linked | 4 | **review-needed** | historical release tip is already contained in main but is not an automatic public-RC input |
| v580-r10-10 | `d2381c6ff994` | ancestor-of-main; +0/-88 | 0 | clean/not linked | 4 | **review-needed** | historical release tip is already contained in main but is not an automatic public-RC input |
| v590-r11 | `06e5e69b71ae` | ancestor-of-main; +0/-86 | 0 | clean/not linked | 4 | **review-needed** | historical release tip is already contained in main but is not an automatic public-RC input |
| v600-r11-delta | `81eea7e86c55` | ancestor-of-main; +0/-84 | 0 | clean/not linked | 4 | **review-needed** | historical release tip is already contained in main but is not an automatic public-RC input |
| v610-r11-1 | `a6f8c94371db` | ancestor-of-main; +0/-82 | 0 | clean/not linked | 4 | **review-needed** | historical release tip is already contained in main but is not an automatic public-RC input |
| v620-r12 | `103b7e186a55` | ancestor-of-main; +0/-79 | 0 | clean/not linked | 4 | **review-needed** | historical release tip is already contained in main but is not an automatic public-RC input |
| v630-r13 | `59667f9f5998` | ancestor-of-main; +0/-77 | 0 | clean/not linked | 5 | **review-needed** | historical release tip is already contained in main but is not an automatic public-RC input |
| v800-r15 | `2f49122a771a` | ancestor-of-main; +0/-76 | 0 | clean/not linked | 6 | **review-needed** | historical release tip is already contained in main but is not an automatic public-RC input |

## Worktrees

| Path | Branch | HEAD | Changed | Untracked | Proof/test dirs | Class |
|---|---|---|---:|---:|---:|---|
| `C:/Users/andrew/OneDrive - Green O365/Documents/GitHub/RGCS` | rcw-public-workbench | `dfab636c4bf5` | 0 | 2 | 11 | **safe-public** |
| `C:/Users/andrew/OneDrive - Green O365/Documents/GitHub/RGCS/.claude/worktrees/hydrogenuine-nexus-workbench-8a8ac1` | (detached) | `8077e04395b0` | 0 | 0 | 19 | **review-needed** |
| `C:/Users/andrew/OneDrive - Green O365/Documents/GitHub/RGCS/.claude/worktrees/rgcs-integration-agent-4c2405` | (detached) | `b98b490a742d` | 0 | 0 | 8 | **review-needed** |
| `C:/Users/andrew/OneDrive - Green O365/Documents/GitHub/RGCS/.claude/worktrees/rgcs-r10-62-terminal-vertex-4aca40` | claude/rgcs-r10-62-terminal-vertex-4aca40 | `710e5947c80e` | 0 | 0 | 19 | **quarantine** |
| `C:/Users/andrew/OneDrive - Green O365/Documents/GitHub/RGCS/audit-worktree` | program/codex-numerical-audit | `42fc284b1ecb` | 0 | 0 | 13 | **safe-public** |
| `C:/Users/andrew/OneDrive - Green O365/Documents/GitHub/RGCS/codex-worktree` | program/codex-core-algorithms | `71e73423031f` | 0 | 0 | 9 | **safe-public** |
| `C:/Users/andrew/OneDrive - Green O365/Documents/GitHub/rgcs-claude` | program/claude-authority-docs | `188caabea0ea` | 0 | 0 | 10 | **safe-public** |
| `C:/Users/andrew/OneDrive - Green O365/Documents/GitHub/rgcs-cursor` | program/cursor-app-integration | `d4baf0d575f0` | 0 | 0 | 12 | **safe-public** |
| `C:/Users/andrew/OneDrive - Green O365/Documents/GitHub/rgcs-integration` | main | `8077e04395b0` | 0 | 1 | 19 | **review-needed** |

## Detailed Delta Evidence

### `claude/rgcs-r10-62-terminal-vertex-4aca40`

- Changed relative to `main`: `.gitignore`; `CHANGELOG.md`; `docs/proofs/PROJECT_STATUS.md`; `docs/proofs/r1057-oa/R10_57_RESULT.md`; `docs/proofs/r1057-oa/SAFE_TEST_ARTICLE_SPEC.md`; `docs/proofs/r1062tv-terminal-vertex/REPOSITORY_AUTHORITY_INVENTORY.md`; `docs/proofs/r1062tv-terminal-vertex/VERDICT.md`; `docs/proofs/r1062tv-terminal-vertex/authority_inventory.json`; +407 more
- Untracked in linked worktree: none
- Proof/test directories: `docs/cwatlas/r1082/receipts`; `docs/cwatlas/receipts`; `docs/program/receipts`; `docs/proofs`; `docs/r1010/evidence`; `docs/r1011/evidence`; `docs/r1013/receipts`; `docs/r109/evidence`; `docs/v4/proof`; `docs/v7/receipts`; `docs/v8/receipts`; `evidence`; +7 more

### `main`

- Changed relative to `main`: none
- Untracked in linked worktree: `tools/r10_public_release.py`
- Proof/test directories: `docs/cwatlas/r1082/receipts`; `docs/cwatlas/receipts`; `docs/program/receipts`; `docs/proofs`; `docs/r1010/evidence`; `docs/r1011/evidence`; `docs/r1013/receipts`; `docs/r109/evidence`; `docs/v4/proof`; `docs/v7/receipts`; `docs/v8/receipts`; `evidence`; +7 more

### `rcw-public-workbench`

- Changed relative to `main`: `docs/proofs/r1074-annular-devkit/firmware_reference_report.md`; `docs/proofs/r1074-annular-devkit/manufacturing_readiness_report.md`; `docs/proofs/r1074-annular-devkit/parametric_geometry_report.md`; `docs/proofs/r1074-annular-devkit/pcb_design_spec.md`; `docs/proofs/r1074-annular-devkit/r1074_summary_for_ag.md`; `docs/proofs/r1074-annular-devkit/safety_and_claim_firewall.md`; `docs/proofs/r1074-annular-devkit/sensor_feedback_report.md`; `pyproject.toml`; +66 more
- Untracked in linked worktree: `audit-worktree/`; `codex-worktree/`
- Proof/test directories: `docs/cwatlas/r1082/receipts`; `docs/cwatlas/receipts`; `docs/proofs`; `docs/v4/proof`; `docs/v7/receipts`; `docs/v8/receipts`; `evidence`; `proof_bundle_110mm/reports`; `rgcs_ardk/reports`; `rgcs_ardk/tests`; `tests`

### `release-safety-snapshot-20260803-2105`

- Changed relative to `main`: `docs/proofs/r1074-annular-devkit/firmware_reference_report.md`; `docs/proofs/r1074-annular-devkit/manufacturing_readiness_report.md`; `docs/proofs/r1074-annular-devkit/parametric_geometry_report.md`; `docs/proofs/r1074-annular-devkit/pcb_design_spec.md`; `docs/proofs/r1074-annular-devkit/r1074_summary_for_ag.md`; `docs/proofs/r1074-annular-devkit/safety_and_claim_firewall.md`; `docs/proofs/r1074-annular-devkit/sensor_feedback_report.md`; `pyproject.toml`; +66 more
- Untracked in linked worktree: none
- Proof/test directories: `docs/cwatlas/r1082/receipts`; `docs/cwatlas/receipts`; `docs/proofs`; `docs/v4/proof`; `docs/v7/receipts`; `docs/v8/receipts`; `evidence`; `proof_bundle_110mm/reports`; `rgcs_ardk/reports`; `rgcs_ardk/tests`; `tests`
