# R13 Phase Receipt

```text
phase_id: 03
phase_title: Source Normalization and Equation Registry
status: COMPLETE
start_commit: 8ae9574
end_commit: v7.0.0 (branch v630-r13)
files_added: r13/srcregistry.py, tests/v6/test_r13_srcregistry.py
files_modified: none
tests_added: 15
focused_test_result: 15 passed
full_regression_result: 5638 passed, 8 skipped, 1 deselected, exit 0
source_hashes_used: build_meta source hash over SOURCE_ROOTS (incl. r13); references hashed by srcregistry
claim_classes_emitted: CONVENTIONAL_LITERATURE
private_files_read: false
```

## Work completed

Normalized the source corpus R13 draws on into five typed record kinds —
`SourceEquation`, `MechanismRecord`, `ObservableRecord`, `AssumptionRecord`,
`NonClaimRecord` — each carried with a source id and the SHA-256 digest of its
source's public citation label. Verdict **`SOURCE_CORPUS_REGISTERED_BY_HASH`**.
Registration is a statement about provenance, not physics: a `SourceEquation`
may only hold a `REGISTRABLE_CLASSES` value (`SOURCE_ESTABLISHED_PHYSICS` or
`CONVENTIONAL_LITERATURE`), and its `__post_init__` refuses any record marked
`rederived_here` or `bench_validated`. Two governance refusals are
load-bearing: `refuse_paper_as_carrier_evidence` refuses reading a registered
paper as evidence that anything in it is an RGCS carrier, and
`refuse_unregistered_equation` refuses any equation the registry does not
carry.

## Evidence and equations implemented

Provenance is pinned by digest: `register_hash` / `verify_hash` compute the
SHA-256 over each source's own public citation label, and a wrong digest fails
verification. The seed digests are hashes of citation labels only — no private
document is read. The five typed record kinds and the `REGISTRABLE_CLASSES`
gate are the registry's schema.

## Negative results

A registered equation is neither re-derived nor measured here — citing a
paper's equation is not re-deriving or confirming it. A registered paper is
refused as evidence for any RGCS carrier. Nothing in the corpus is promoted
above `CONVENTIONAL_LITERATURE` by registration.

## Deviations from prompt

None.

## Blocking inputs, when applicable

None — software/architecture phase.

## Downstream impact

Every module that quotes literature constants or equations (07 crystal frame,
09 continuum stiffness, 10 piezo constants, 36 published-response validation)
references sources through this registry; the build_meta source-hash pipeline
hashes registry references.

## Reopening test

Re-run `tests/v6/test_r13_srcregistry.py`; reopen if the verdict string
changes, if either refusal stops raising, or if a record marked
`rederived_here`/`bench_validated` is accepted.

## Acceptance checklist
- [x] focused tests pass
- [x] receipt written
- [x] claim classes recorded
- [x] no private files read
- [x] PHYSICAL_VALIDATION_NOT_CLAIMED
