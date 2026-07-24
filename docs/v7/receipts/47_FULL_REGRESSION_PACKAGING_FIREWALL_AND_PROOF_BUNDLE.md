# R13 Phase Receipt

```text
phase_id: 47
phase_title: Full Regression, Packaging, Firewall, and Proof Bundle
status: COMPLETE
start_commit: 8ae9574
end_commit: v7.0.0 (branch v630-r13)
files_added: (none)
files_modified: docs/v4/RELEASE_METADATA.json (count refresh); release-owned evidence workbook + manifest
tests_added: 0
focused_test_result: n/a (verification phase); full suite run twice, both 5638 passed
full_regression_result: 5638 passed, 8 skipped, 1 deselected, exit 0
source_hashes_used: build_meta source hash over SOURCE_ROOTS (incl. r13)
claim_classes_emitted: REPOSITORY_COMPUTATIONAL_RESULT
private_files_read: false
```

## Work completed

Proved the complete implementation and artifact set before release:

- **Full regression (twice).** The complete suite passes at **5638 passed,
  8 skipped, 1 deselected**, exit 0, run twice (the second confirming the
  first). The single deselection is the archived-environment byte-equality
  node `tests/regression/test_generator_determinism.py::test_generator_deterministic`
  (policy D-V3-04). The count is derived from an actual pytest run by
  `tools/v4x_release_metadata.py --refresh` → `docs/v4/RELEASE_METADATA.json`;
  the guard test then requires every documented count (README, release notes,
  CHANGELOG) to agree. 5638 = 5175 baseline + 463 new R13 tests (447 focused/
  negative + 16 red-team).
- **Packaging parity.** `r13` is registered in both the `pyproject.toml`
  `include` list and `build_meta.py` `SOURCE_ROOTS`.
- **Privacy firewall.** `r10/firewall.py` `scan_working_tree` and
  `scan_committed` both return **zero findings** over the staged tree;
  the `private_do_not_commit/` marker remains guarded and unread.
- **Release-owned artifacts.** `tools/r4_release_gate.py --write` refreshed
  the public evidence workbook and its manifest for v7.0.0 and returns
  **`TAG_MAY_PROCEED`**.
- **Source hashes.** The `build_meta` source hash resolves over all
  `SOURCE_ROOTS` including `r13`.

## Evidence and equations implemented

None new — verification phase. The verifiable facts are the regression count
(5638, twice), zero firewall findings, packaging-parity membership of `r13`,
and the `TAG_MAY_PROCEED` gate verdict.

## Negative results

No benchmark, bench, or facility data are present or invented. Every result is
a labelled model / prediction / blocked input. Passing regression, packaging,
firewall, and gate checks proves the artifact set is complete and consistent —
not that any physical claim is validated.

## Deviations from prompt

None.

## Blocking inputs, when applicable

None — verification phase.

## Downstream impact

The green regression count and `TAG_MAY_PROCEED` gate are the preconditions for
the phase-48 v7.0.0 tag; the refreshed count 5638 is the number phase 48
stamps into the release notes and CHANGELOG.

## Reopening test

Re-run the full suite plus `r10/firewall.py` scans; reopen if the count is not
5638 passed / 8 skipped / 1 deselected, if any firewall finding appears, if
`r13` drops out of packaging parity, or if the release gate stops returning
`TAG_MAY_PROCEED`.

## Acceptance checklist
- [x] focused tests pass
- [x] receipt written
- [x] claim classes recorded
- [x] no private files read
- [x] PHYSICAL_VALIDATION_NOT_CLAIMED
