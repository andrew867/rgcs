# R13 Phase Receipt

```text
phase_id: 01
phase_title: Gate Zero and R12 State Import
status: COMPLETE
start_commit: 8ae9574
end_commit: v7.0.0 (branch v630-r13)
files_added: r13/__init__.py
files_modified: pyproject.toml, rgcs_desktop/build_meta.py
tests_added: 0
focused_test_result: packaging parity + privacy guards pass
full_regression_result: 5638 passed, 8 skipped, 1 deselected, exit 0
source_hashes_used: build_meta source hash over SOURCE_ROOTS (incl. r13); references hashed by srcregistry
claim_classes_emitted: REPOSITORY_COMPUTATIONAL_RESULT
private_files_read: false
```

## Work completed

Verified the exact R12 release, imported all inherited verdicts, created the
`r13` package, and proved packaging and privacy parity before any feature
work. Gate Zero at the branch cut confirmed: `main` HEAD `8ae9574` (the v6.3.0
provenance successor), tag `v6.3.0` at `103b7e1`, clean worktree, release
metadata count **5175** with `exit_code 0`, `r12` present in both the
`pyproject.toml` include and `build_meta.py` `SOURCE_ROOTS`, the
`private_do_not_commit/` tree guarded by `r11/sources.py` `PRIVATE_MARKERS` and
never read, and a CLEAN committed-tree firewall scan.

Inherited verdicts reconcile: R10 (band-clustering null, `EXPLAINED_BY_RANGE`),
R11 / R11.1 (all transfer refused; identifiability null), and R12
(`NO_AUTOMATIC_EQUIVALENCE` + `TRANSFER_ALLOWED_WITH_EXPLICIT_COUPLING_CERTIFICATE`).
R13 **extends** the R12 certificate rule with a coupling-graph search and
deletes no prior refusal.

The `r13` package was created (`r13/__init__.py` with a sorted `__all__` and a
docstring stating the three standing rules — simulation is not measurement /
certificate is not evidence; no promotion; blocked is stated), and registered
for packaging (`"r13*"` added to the `find` include) and freshness hashing
(`"r13"` added to `SOURCE_ROOTS`), closing the R8-D-006 / R10-D-001 new-package
parity trap for this generation.

## Evidence and equations implemented

None — this is a repository/provenance verification phase. The verifiable
facts are the commit hashes, the release count (5175), the packaging-parity
membership of `r13` in both include and `SOURCE_ROOTS`, and the privacy-guard
membership of `private_do_not_commit/` in `PRIVATE_MARKERS`.

## Negative results

The declared tag/main provenance split verified benign: the `v6.3.0` tag
commit `103b7e1` carries the R12 release-gate workbook with the
pre-confirmation `exit_code`; the successor commit `8ae9574` on `main` records
the confirming measurement (count **5175**, `exit_code 0`). The count agrees
across both; only the exit-code annotation differs. This is the R13 pack's
declared post-tag rule (the tag is immutable, the confirming run is recorded
on `main` separately) — not a mismatch, not a stop condition. No physical claim
is validated: Gate Zero certifies repository and release provenance only.

## Deviations from prompt

None.

## Blocking inputs, when applicable

None — software/architecture phase.

## Downstream impact

Every subsequent R13 module (phases 03+) is imported from the `r13` package
created here and is hashed through the `SOURCE_ROOTS` entry added here. All
inherited refusals carried in are relied on by the bridge phases (06, 10, 30,
43).

## Reopening test

Re-run the packaging-parity and privacy-guard suites; reopen if `r13` drops
out of either the `pyproject.toml` include or `SOURCE_ROOTS`, if
`private_do_not_commit/` leaves `PRIVATE_MARKERS`, or if the release count no
longer reconciles to 5175 across tag and main.

## Acceptance checklist
- [x] focused tests pass
- [x] receipt written
- [x] claim classes recorded
- [x] no private files read
- [x] PHYSICAL_VALIDATION_NOT_CLAIMED
