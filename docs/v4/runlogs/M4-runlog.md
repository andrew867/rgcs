# Run log — Agent M4 (reduced spin/magnon/exciton/phonon models)

- Base commit: `035b5b4`. Owned paths: `rscs2_core/refmodels/{__init__,
  exciton_magnon,avoided_crossing,block_hamiltonian,dressed_spin}.py`,
  `tests/v4/test_v4c_refmodels_m4.py`,
  `docs/v4/V4_SPIN_EXCITON_MAGNON_PHONON_MODELS.md`,
  `docs/v4/runlogs/M4-*`.

## Tests
`pytest tests/v4/test_v4c_refmodels_m4.py` -> **10 passed** (gates
E1: zero/small-angle/sidebands/damping; E2: frozen anchor 1e-12,
2g minimum, linewidths, participation, uncertainty; E3: dressed
regimes deterministic; E5: quartz rejected at every entry incl. block
construction).

## Debugging record
Small-angle tolerance initially 5e-6 vs true O(x^3) remainder ~9.1e-6
at x=0.05 -> corrected bound with the remainder arithmetic in-line.

## Classification
All models REDUCED_ORDER_VALIDATED w/ DER (+EST for the frozen-anchor
crossing); dressed-spin protection factor tagged ENG-adjacent;
export_interface INTERFACE_ONLY.
