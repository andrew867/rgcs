# R13 Phase Receipt

```text
phase_id: 37
phase_title: Icosahedral Packet Finalizer and Decoder Holdout
status: COMPLETE
start_commit: 8ae9574
end_commit: v7.0.0 (branch v630-r13)
files_added: r13/coordfinal.py, r13/holdout.py, tests/v6/test_r13_coordfinal.py, tests/v6/test_r13_holdout.py
files_modified: (none)
tests_added: 27
focused_test_result: test_r13_coordfinal.py 14 passed; test_r13_holdout.py 13 passed
full_regression_result: 5638 passed, 8 skipped, 1 deselected, exit 0
source_hashes_used: build_meta source hash over SOURCE_ROOTS (incl. r13)
claim_classes_emitted: REPOSITORY_COMPUTATIONAL_RESULT
private_files_read: false
```

## Work completed

Completed the F5|Q22|S3 coordinate codec and pinned exactly what is and is not
identifiable from a packet. `r13/coordfinal.py` reuses `r12.icosapacket`;
`PacketGrammar` is an exact bijection at the **symbol** level (encode↔decode
round-trip), versioned by a SHA-256 `version_hash`. `r13/holdout.py` supplies
the blinded no-peeking decoder-evaluation protocol. Verdicts emitted:
**`COORDINATE_CODEC_FINALIZED_ALIAS_SET_ONLY`** and
**`DECODER_HOLDOUT_PROTOCOL_BLINDED`**.

## Evidence and equations implemented

- **Codec.** `decode_to_alias_set(packet)` returns **32** candidate
  coordinates — the Cartesian product of the five R12 conventions (face
  numbering, body orientation, magnetic root, handedness, shell projection).
  `true_candidate_is_distinguishable()` is always `False`: no packet field
  selects a frame.
- **Holdout.** Deterministic salted TRAIN/HOLDOUT split; `commit_holdout`
  seals ids **and** labels under SHA-256 (tamper-evident). `power_check`
  shows a rule-aware decoder recovers TRAIN while a constant decoder stays at
  chance.
- **Load-bearing refusals.** `refuse_alias_as_destination` (no collapse of
  the alias set to one location), `refuse_numeric_match_as_authentication`,
  `refuse_decode_before_commit`, `refuse_holdout_in_training`,
  `refuse_overfit_as_generalization`.

## Negative results

A packet decodes to a 32-member **alias set**, never a single destination: no
field selects a frame, so there is no unique decoded location. A coincident
number is at most `RETROSPECTIVE_NUMERIC_MATCH`, not authentication; perfect
train performance is not holdout performance.

## Deviations from prompt

None.

## Blocking inputs, when applicable

None — software/architecture phase. (The decisive independent-vector test that
would attempt to break the alias tie is phase 42, where it is BLOCKED.)

## Downstream impact

The alias-set codec and the blinded holdout protocol are composed by phase 42
(the decisive known-destination protocol) and attacked by phase 43 (red team).

## Reopening test

Re-run `tests/v6/test_r13_coordfinal.py` and `tests/v6/test_r13_holdout.py`;
reopen if the alias-set size stops being > 1, if
`true_candidate_is_distinguishable()` ever returns `True`, or if any of the
five refusals stops raising.

## Acceptance checklist
- [x] focused tests pass
- [x] receipt written
- [x] claim classes recorded
- [x] no private files read
- [x] PHYSICAL_VALIDATION_NOT_CLAIMED
