# R10.8.5A reproduction runlog

```
python tools/r1085a_outer_in_projection.py
python -m pytest tests/cwatlas/r1085a/ -q
python -m pytest -q          # full regression suite
```

Inputs: packet grammar r12.icosapacket / r12.icosarefine (verbatim,
untouched); sealed R10.8.2 CALFREEZE orientations (verbatim,
untouched); training equality 165876523 = Stonehenge; orange slice
['165892743', '165892763', '165892783'] with registered shell correction
3 -> 7 on the middle vector. Epoch 2025.0, ground reference
TERRA_SURFACE_SYNC_V1, field-line step 5000.0 m.

Deterministic: no RNG, no wall clock; every family member enumerated
in declared order. Outputs: TEST_RECEIPT.json (machine verdict),
SWEEP_ROWS.json (all 48 x 4 projection rows), and the
eleven narrative receipts in this directory.

Verdict: `RGCS_R10_8_5A_YELLOW_PACKET_AUTHORITY_HELD_PROJECTION_UNDERDETERMINED`
SOURCE_ORIGIN_VALIDATED: no
