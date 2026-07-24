# R13 Phase Receipt

```text
phase_id: 46
phase_title: Manuscripts, Research Archive, and Public Documentation
status: COMPLETE
start_commit: 8ae9574
end_commit: v7.0.0 (branch v630-r13)
files_added: docs/v7/R13_FINDINGS.md, docs/v7/R13_NON_CLAIMS.md, docs/v7/receipts/01..48
files_modified: (none)
tests_added: 0
focused_test_result: n/a (documentation phase); code<->manuscript agreement enforced by tests/v6/test_r13_redteam.py 16 passed
full_regression_result: 5638 passed, 8 skipped, 1 deselected, exit 0
source_hashes_used: build_meta source hash over SOURCE_ROOTS (incl. r13)
claim_classes_emitted: REPOSITORY_COMPUTATIONAL_RESULT
private_files_read: false
```

## Work completed

Published a complete, honest record of the mathematical framework, conventional
physics, experiment architecture, and unresolved hypotheses:

- **`docs/v7/R13_FINDINGS.md`** — the R13 manuscript / research archive: what
  R13 is, the three standing rules, the load-bearing (model) physics results,
  the headline non-claims, and the verdict.
- **`docs/v7/R13_NON_CLAIMS.md`** — the explicit non-claim register.
- **`docs/v7/receipts/01`–`48`** — 48 phase receipts, one per pack phase, each
  naming its deliverable, verdict, claim class, and explicit non-claims.
- The module docstrings (`r13/__init__.py` and each module) carry the same
  rules, so the public record and the code agree.

Claim class `REPOSITORY_COMPUTATIONAL_RESULT` (documentation of computational
results).

## Evidence and equations implemented

None new — this is a documentation phase. The verifiable fact is code↔manuscript
agreement (the release-gate requirement):

- The seven forbidden promotions in the manuscript are exactly the seven in
  `r13/claimtypes.py` (`FORBIDDEN_PROMOTIONS`, length asserted == 7).
- Every "we do not claim X" in the findings maps to a `refuse_*` function that
  raises, asserted by `tests/v6/test_r13_redteam.py`.
- No number in the manuscript is presented as measured; all are labelled
  model / prediction / blocked, matching each module's `*_report()`.

## Negative results

The archive documents an **architecture**; it reports **no measurement** and
asserts no physical validation. Where inputs are missing, the record says so.

## Deviations from prompt

None.

## Blocking inputs, when applicable

None — documentation phase.

## Downstream impact

The findings, non-claims register, and receipts are the release-owned
documentation packaged by phases 47–48; their code-agreement is the property
the phase-47 gate and phase-48 tag depend on.

## Reopening test

Re-run `tests/v6/test_r13_redteam.py` (the code↔manuscript enforcer); reopen if
`FORBIDDEN_PROMOTIONS` diverges from seven, if any documented "we do not claim
X" loses its raising `refuse_*`, or if any manuscript number is presented as
measured.

## Acceptance checklist
- [x] focused tests pass
- [x] receipt written
- [x] claim classes recorded
- [x] no private files read
- [x] PHYSICAL_VALIDATION_NOT_CLAIMED
