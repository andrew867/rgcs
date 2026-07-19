# R8.1 Final Gate Zero Receipt

Verified against the live repository on 2026-07-19. Operator
summaries and prior prompts were not treated as authority.

## Identity and ancestry

| Check | Result |
|---|---|
| Branch continued | `v51-r8` (not restarted, not rebranched) |
| Baseline | v5.0.0 at `ea1cb0a` |
| Release commit | `cfcfaa5` |
| `main` | `cfcfaa5` |
| `v5.1.0` dereferences to | `cfcfaa5` |
| Post-tag commits | 0 |
| Working tree | clean at tag time |
| Visibility at gate | **PRIVATE** |

## Test and artifact counts — measured, not recalled

| Quantity | Value | Source |
|---|---|---|
| Clean-clone tests | **2420 passed, 11 skipped, 1 deselected** | clean clone of tagged commit |
| Working-copy tests | 2425 | five tests need untracked optional content |
| Canonical evidence records | 271 | `rgcs_workbench.canonical.build` |
| Workbook sheets | 39 | generated |
| Workbench panels | 14 | frozen binary `--smoke-check` |
| QA audit | 19/19 | `tools/qa_audit_v4.py --fast` |
| Release gate | `TAG_MAY_PROCEED` | `tools/r4_release_gate.py` |
| Physical-evidence records | **0** | every generation |

The clean-clone figure is authoritative and is what the published
test-report asset contains.

## Defects closed in this closeout

| ID | Defect | Status |
|---|---|---|
| R8-D-001 | Pound–Rebka "validation" compared a formula against itself | corrected, withdrawal stated inline |
| R8-D-002 | frame-chain quadrature contradicted the covariance field | fixed, correlation-aware |
| R8-D-003 | MDEV/TDEV named but not implemented | implemented, validated against definitional anchors |
| R8-D-004 | `frozen: true` implied external preregistration | now `INTERNAL_ANALYSIS_FREEZE` |
| R8-D-005 | non-PSD correlation returned 0.0 m — perfect knowledge | refused, bound named |
| R8-D-006 | `SOURCE_ROOTS` omitted r6, r7, r8 across three releases | fixed, guarded by test |

Two process failures are also recorded rather than hidden: a broad
`git add` swept a specialist's unreviewed files into a commit (audited
retroactively), and a freeze-wording change was committed before the
suite finished, breaking four tests.

## Release-gate history

The first tag attempt was **blocked by CI**: a null-calibration test
asserted exact float equality on an RNG-dependent path, passing on
Python 3.13 locally and failing on 3.11 across all three platforms.
The second was **withdrawn by me** on discovering R8-D-006. No release
existed at either point, so nothing published was affected.

That is the gate working. A single-interpreter local run was green
both times.

## Publication decision

`PUBLIC_OPEN_COMMONS`, superseding `PRIVATE_RC`, on the owner's
written authorization. See `V5_1_PUBLICATION_DECISION.md`.

## Disclosure position

v3.0.0 through v4.8.1 were public under MIT between 2026-07-15 and
2026-07-18 — a dated public source release, **not** an organised
defensive publication. R6, R7 and R8.1 were developed privately and
are first published at v5.1.0. The exact visibility-flip timestamp is
**inferred** from branch-protection API behaviour and must be
confirmed from the owner's account audit log.

## Safety verification

No API keys, tokens or credentials in tracked files. The only email
is the author's own published contact address. `internal-docs/` is
gitignored and untracked, so no prompt packs publish. `source_claims/`
is untracked, so no third-party corpus publishes. No private
filesystem paths.

Personal provenance material unrelated to the scientific record was
excluded from every artifact at the owner's explicit instruction.

## Outstanding at gate

- Repository visibility flip (human action or tooling, after asset
  verification).
- The full per-result knowledge inventory in the contract's 18-field
  schema remains a summary layer; gaps are listed in the audit.
- Three manuscripts exist as Markdown; LaTeX/PDF builds were not
  produced.
- The channelling transcript referenced by the closeout prompt was
  never supplied in-conversation and therefore was not archived. No
  placeholder was created, because an empty record that looks like an
  archive is worse than an absent one.
