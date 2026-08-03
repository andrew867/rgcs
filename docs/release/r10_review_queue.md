# R10 Public Release Review Queue

Items here are not release inputs. A human may later approve a file-level subset after provenance and private-lane review; silence is not approval.

Queue count: **30 branches**

| Branch | HEAD | Class | Ahead/behind main | Reason |
|---|---|---|---:|---|
| claude/hydrogenuine-nexus-workbench-8a8ac1 | `8077e04395b0` | **review-needed** | +0/-0 | integration tree contains mixed historical lanes; publish only through the exclusion-first manifest |
| claude/rgcs-integration-agent-4c2405 | `b98b490a742d` | **review-needed** | +0/-74 | already contained in main; no delta to merge and no automatic publication decision |
| claude/rgcs-r10-62-terminal-vertex-4aca40 | `710e5947c80e` | **quarantine** | +37/-0 | mixed 37-commit line contains public engineering commits and private decode/privacy commits; whole-branch merge prohibited |
| emergent-resonator | `0af811f77975` | **review-needed** | +0/-195 | historical resonator lane requires file-level public review |
| main | `8077e04395b0` | **review-needed** | +0/-0 | integration tree contains mixed historical lanes; publish only through the exclusion-first manifest |
| r1084-recursive-coordinate-recovery | `3235f05c3064` | **review-needed** | +0/-71 | authority is held and the branch title carries an ambiguous physical interpretation |
| v4-dev | `661d406e2bb6` | **review-needed** | +0/-169 | historical release tip is already contained in main but is not an automatic public-RC input |
| v4.6-cspc | `caa15c35dcbf` | **review-needed** | +0/-180 | historical release tip is already contained in main but is not an automatic public-RC input |
| v4.7-pmwr | `e339b887b938` | **review-needed** | +0/-176 | historical release tip is already contained in main but is not an automatic public-RC input |
| v4.7x-r3 | `6b359c2d23ad` | **review-needed** | +0/-174 | historical release tip is already contained in main but is not an automatic public-RC input |
| v4.8-r4 | `bb62b5918a63` | **review-needed** | +0/-172 | historical release tip is already contained in main but is not an automatic public-RC input |
| v49-r6 | `7847c2e34e18` | **review-needed** | +0/-161 | historical release tip is already contained in main but is not an automatic public-RC input |
| v50-r7 | `ea1cb0a37458` | **review-needed** | +0/-153 | historical release tip is already contained in main but is not an automatic public-RC input |
| v51-r8 | `a7f77308a21f` | **review-needed** | +0/-137 | historical release tip is already contained in main but is not an automatic public-RC input |
| v52-r10 | `cf7be2246d06` | **review-needed** | +0/-117 | historical release tip is already contained in main but is not an automatic public-RC input |
| v52-r9 | `f40f4a8e840a` | **review-needed** | +0/-128 | historical release tip is already contained in main but is not an automatic public-RC input |
| v53-r10-1 | `3fb687475197` | **review-needed** | +0/-110 | historical release tip is already contained in main but is not an automatic public-RC input |
| v531-r10-2 | `41537be8b438` | **review-needed** | +0/-106 | historical release tip is already contained in main but is not an automatic public-RC input |
| v540-r10-2b | `a76174b2e5c4` | **review-needed** | +0/-103 | historical release tip is already contained in main but is not an automatic public-RC input |
| v541-r10-3 | `f73376331bd1` | **review-needed** | +0/-100 | historical release tip is already contained in main but is not an automatic public-RC input |
| v550-r10-6 | `95cd7504ea73` | **review-needed** | +0/-96 | historical release tip is already contained in main but is not an automatic public-RC input |
| v560-r10-7 | `977e0b6a6e3c` | **review-needed** | +0/-93 | historical release tip is already contained in main but is not an automatic public-RC input |
| v570-r10-8 | `3fca1e54ed7d` | **review-needed** | +0/-90 | historical release tip is already contained in main but is not an automatic public-RC input |
| v580-r10-10 | `d2381c6ff994` | **review-needed** | +0/-88 | historical release tip is already contained in main but is not an automatic public-RC input |
| v590-r11 | `06e5e69b71ae` | **review-needed** | +0/-86 | historical release tip is already contained in main but is not an automatic public-RC input |
| v600-r11-delta | `81eea7e86c55` | **review-needed** | +0/-84 | historical release tip is already contained in main but is not an automatic public-RC input |
| v610-r11-1 | `a6f8c94371db` | **review-needed** | +0/-82 | historical release tip is already contained in main but is not an automatic public-RC input |
| v620-r12 | `103b7e186a55` | **review-needed** | +0/-79 | historical release tip is already contained in main but is not an automatic public-RC input |
| v630-r13 | `59667f9f5998` | **review-needed** | +0/-77 | historical release tip is already contained in main but is not an automatic public-RC input |
| v800-r15 | `2f49122a771a` | **review-needed** | +0/-76 | historical release tip is already contained in main but is not an automatic public-RC input |

## Explicit Decisions Needed

- The mixed R10.62-R10.73 branch cannot be merged whole. Only independently audited public commits may be replayed onto a clean integration branch.
- Historical release tips remain provenance references, not automatic RC content.
- R10.8.4 remains held because its authority and physical-language review are unresolved.
