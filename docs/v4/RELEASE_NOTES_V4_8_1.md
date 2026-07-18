# RGCS v4.8.1 — workbook column-loss fix

**SOFTWARE_VERIFIED, PHYSICAL_SPIN_UNTESTED.** A patch on
[v4.8.0](https://github.com/andrew867/rgcs/releases/tag/v4.8.0). No
science changed; no physical claim moved.

## The defect

`_write_table` built its header row from `rows[0].keys()`, so any field
present only on a *later* record in the same table was silently
dropped from the sheet. The data was always correct in the canonical
store — it simply never reached the spreadsheet.

Impact measured across the workbook: **52 columns lost from ten
heterogeneous sheets**, including:

- the R4 **negative-control gate** result and every
  `beats_any_baseline` verdict (so a reader could not see that the
  codec fails on random data — the single most important honesty
  signal in the R4 campaign);
- PMWR travel-claim `why_unsupported` reasons;
- R3 root statuses and forbidden-collapse refusals;
- CSCP spacetime and tetrahedron detail columns.

This is pre-existing: it has quietly degraded the shipped workbook
since v4.5, and every release from v4.6 onward shipped sheets missing
columns.

## The fix

Headers are now the ordered union of every row's keys — a record that
carries a field always gets a column. Two regression tests: one
asserts no sheet drops a field present in its canonical table, the
other asserts the negative-control gate and both random-data verdicts
are readable from the workbook itself.

## Verify

```bash
python -m pytest -q --deselect tests/regression/test_generator_determinism.py::test_generator_deterministic
# expect: 1219 passed
python tools/r4_release_gate.py     # TAG_MAY_PROCEED
python tools/qa_audit_v4.py --fast  # 19/19
```
