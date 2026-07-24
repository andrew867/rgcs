# R13 Phase Receipt

```text
phase_id: 42
phase_title: Independent Vector and Known-Destination Protocol
status: COMPLETE (protocol); a positive decode result BLOCKED_MISSING_INPUT
start_commit: 8ae9574
end_commit: v7.0.0 (branch v630-r13)
files_added: (none — composes r13/holdout.py + r13/coordfinal.py)
files_modified: (none)
tests_added: 0
focused_test_result: test_r13_holdout.py 13 passed; test_r13_coordfinal.py 14 passed
full_regression_result: 5638 passed, 8 skipped, 1 deselected, exit 0
source_hashes_used: build_meta source hash over SOURCE_ROOTS (incl. r13)
claim_classes_emitted: REPOSITORY_COMPUTATIONAL_RESULT
private_files_read: false
```

## Work completed

Created the decisive protocol for validating or rejecting the coordinate
decoder by composing `r13/holdout.py` (blinded commitment + no-peeking) with
`r13/coordfinal.py` (the alias-set codec). The protocol:

1. An **independent vector** — a coordinate produced outside the codec, with a
   **known** destination — is sealed via `commit_holdout` before any decode
   (blinding; `refuse_decode_before_commit`).
2. The decoder is run and its output compared **only** against the committed
   label.
3. **Pass condition (falsifiable):** the decoder singles out the correct
   destination on held-out independent vectors, above the alias-set chance
   rate, without having seen the answer.

Claim class `REPOSITORY_COMPUTATIONAL_RESULT`; a decoder that ever claimed a
unique destination would be `RETROSPECTIVE_NUMERIC_MATCH` at best.

## Evidence and equations implemented

No new module. The protocol is exercised through the composed test files
`tests/v6/test_r13_holdout.py` and `tests/v6/test_r13_coordfinal.py` (the
blinded-commit path and the 32-member `decode_to_alias_set`). Run against the
alias set, `decode_to_alias_set` yields 32 candidates with no packet field
selecting a frame, so the decoder cannot beat chance on a held-out vector.

## Negative results

Against the alias set the decoder **does not beat chance** — this is evidence
**against** a unique decode, not for one. `refuse_alias_as_destination` holds.
The protocol is the honest falsification hook: it *could* validate the
decoder, and run as available it does not.

## Deviations from prompt

None. The positive-decode outcome is left BLOCKED (falsifiable, not fabricated)
exactly as prescribed.

## Blocking inputs, when applicable

A positive decode result is **BLOCKED_MISSING_INPUT**: it requires an
independent known-destination vector set produced outside the codec. Absent
that input, no unique-destination claim is made or is recoverable.

## Downstream impact

This is the decisive gate that keeps the coordinate decoder from being
promoted to a location claim; phase 43 red-teams the same refusal and phase 48
lists the independent decoder vector among the R14 blocked inputs.

## Reopening test

Re-run `tests/v6/test_r13_holdout.py` and `tests/v6/test_r13_coordfinal.py`;
reopen if the decoder ever beats the alias-set chance rate on a committed
held-out vector, or if `refuse_alias_as_destination` /
`refuse_decode_before_commit` stops raising.

## Acceptance checklist
- [x] focused tests pass
- [x] receipt written
- [x] claim classes recorded
- [x] no private files read
- [x] PHYSICAL_VALIDATION_NOT_CLAIMED
