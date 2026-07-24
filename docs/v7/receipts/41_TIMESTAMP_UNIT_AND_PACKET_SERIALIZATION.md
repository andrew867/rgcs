# R13 Phase Receipt

```text
phase_id: 41
phase_title: Timestamp, Unit, and Packet Serialization
status: COMPLETE
start_commit: 8ae9574
end_commit: v7.0.0 (branch v630-r13)
files_added: r13/serialize.py, tests/v6/test_r13_serialize.py
files_modified: (none)
tests_added: 20
focused_test_result: test_r13_serialize.py 20 passed
full_regression_result: 5638 passed, 8 skipped, 1 deselected, exit 0
source_hashes_used: build_meta source hash over SOURCE_ROOTS (incl. r13)
claim_classes_emitted: REPOSITORY_COMPUTATIONAL_RESULT
private_files_read: false
```

## Work completed

Finalized right-to-left display, shell-first reading, timestamp fields, and
local-unit declarations as a deterministic, tamper-evident record in
`r13/serialize.py`. Verdict emitted: **`DETERMINISTIC_SERIALIZATION_HASHED`**;
claim class `REPOSITORY_COMPUTATIONAL_RESULT`.

## Evidence and equations implemented

- `serialize(obj)` emits canonical bytes (sorted keys, fixed float
  formatting, explicit UTF-8; non-finite floats and non-string keys refused):
  two serializations of an equal object are byte-identical and dict key order
  does not change the output.
- `content_hash(obj)` = SHA-256 of the canonical bytes — stable, and changes
  on any field mutation.
- `Record(payload, claim_class, epoch, prev_hash)` links into a hash chain;
  `append_record` chains via `prev_hash`, and `verify_chain` fails when any
  past record is mutated (verified by tampering a record and confirming the
  downstream back-link breaks).
- Timestamps/epochs are **passed in**, never read from the clock.
- Refusals: `refuse_wallclock_timestamp`,
  `refuse_hash_match_as_authentication`.

## Negative results

A matching content hash proves **byte integrity, not source authentication**;
there are no wall-clock timestamps (all epochs are supplied). Deterministic
serialization plus a verifying hash chain certify the bytes, and no more.

## Deviations from prompt

None.

## Blocking inputs, when applicable

None — repository-computational phase.

## Downstream impact

The canonical serialization and hash chain provide the tamper-evident record
format that the preregistration seal (phase 44) and the proof bundle
(phase 47) depend on.

## Reopening test

Re-run `tests/v6/test_r13_serialize.py`; reopen if serialization stops being
byte-deterministic, if `verify_chain` stops detecting a tampered record, or if
either refusal stops raising.

## Acceptance checklist
- [x] focused tests pass
- [x] receipt written
- [x] claim classes recorded
- [x] no private files read
- [x] PHYSICAL_VALIDATION_NOT_CLAIMED
