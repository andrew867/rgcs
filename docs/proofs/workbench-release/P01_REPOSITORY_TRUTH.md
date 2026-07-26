# P01 — Repository truth and active R10.8.5A reconciliation

Recorded 2026-07-26 by inspection, before any workbench edit.

## Repository truth

* branch at inspection: `r1084-recursive-coordinate-recovery`;
  workbench workstream branched from it as `rcw-public-workbench`
* HEAD at inspection: `e5864a5` ("R10.8.5: octal packet recovery —
  F5|Q22|S3 via reused R12 grammar (7839, exit 0)"), based on `c918b0b`
* tags (all LOCAL-ONLY, unpushed): v8.2.0, v8.1.0, v8.0.0, v7.0.0,
  v6.3.0 …; **no tag was created by the packet-recovery run** —
  matches the authority lock's prior receipt
* frozen parser: `r12/icosapacket.py` (30-bit F5|Q22|S3);
  frozen refinement: `r12/icosarefine.py` (4-child triangular operator)
* rejected decoders preserved as typed receipts in
  `cwatlas/r1082/decoder_candidates.py` (base-100 fold, field-split,
  bary-digit, flattened-XYZ, recursive-XYZ) — none revived
* the R10.8.4 decimal-recursive source decoder remains
  `REJECTED_FOR_SOURCE_DECODE`; code retained in `cwatlas/r1084/`

## Uncommitted R10.8.5A work found and preserved

Untracked at inspection, since committed intact as `3235f05`
("R10.8.5A: outer-in gravity-shell projection — YELLOW, authority
held") on `r1084-recursive-coordinate-recovery`:

* `cwatlas/r1085a/` — 9 modules: shell_profile, land_zero,
  gravity_field_line, magnetic_shell, ground_time_frame,
  outer_in_radial, orange_slice, final_projection
* `tests/cwatlas/r1085a/` — 28 tests (2 files), all passing
* `tools/r1085a_outer_in_projection.py` — reproduction runner
* `docs/proofs/r1085a-outer-in-gravity-shell-projection/` — 13
  receipts incl. TEST_RECEIPT.json and SWEEP_ROWS.json
* `docs/v4/baseline/*.json` — R6-D-008-class snapshot refresh
  (test suite rewrites the inventory baseline; committed as refreshed
  truth, consistent with prior practice on this branch)

## Active R10.8.5A result, exactly as repository truth supports it

`RGCS_R10_8_5A_YELLOW_PACKET_AUTHORITY_HELD_PROJECTION_UNDERDETERMINED`

* packet authority held; parser and Q22 operator untouched
* Stonehenge held as a hard TRAINING equality under a declared
  training alignment (2-DOF minimal rotation on sealed context
  F1_CANONICAL_DIRECT_BE, 24.142°; roll DOF recorded UNDETERMINED);
  terminal cell contains the anchor; forward residual 1.65–5.15 km
  across the 48 declared configurations
* every sealed R10.8.2 context still misses — the freeze was not
  retuned in place
* orange slice: active shells 7,7,7; raw 7,3,7 in provenance as
  registered operator correction; physical 7,3,7 theory refused
* radial lane misfit open: best declared config ≥ 6.695 km between
  decoded height and the site's physical height
* `SOURCE_ORIGIN_VALIDATED: no`;
  `STONEHENGE_INDEPENDENTLY_DECODED: no`

## Broad regression at this receipt

Command: `.venv/Scripts/python.exe -m pytest -q` (Python 3.13.2, repo
checkout, 2026-07-26):

```
1 failed, 7867 passed, 8 skipped, 7 warnings in 1118.89s
FAILED tests/regression/test_generator_determinism.py::test_generator_deterministic
```

The single failure is the **D-V3-04 byte-equality tier**, documented
to pass only in the archived v2 build environment (Python 3.11.15,
numpy 2.4.4); hosted CI deselects exactly this node. The portable
numeric-equivalence tier passed. Anomaly recorded honestly: the prior
day's receipt at `e5864a5` recorded exit 0 on this machine, so the
local environment drifted between runs; investigation spun off as a
separate task, not absorbed silently.

## Source-root / mirror / generated boundaries

* source root: repository top-level packages enumerated in
  `pyproject.toml` `[tool.setuptools.packages.find]` (rgcs_core*,
  rscs_core*, rscs2_core*, cwatlas*, r3*–r15*, …)
* the workbench package `rgcs_coordinate*` is NEW in this workstream
  and is added to that enumeration in P04 with packaging parity kept
* generated artifacts: `docs/proofs/**` receipts and
  `docs/v4/baseline/*.json` snapshots are outputs, never imported code
* tests live under `tests/**` with globally unique basenames and no
  `__init__.py` (established repo convention)

## Migration / compatibility

No established public path is renamed or mutated. `rgcs_coordinate`
is additive; existing `cwatlas`, `r12` and release consumers are
untouched. Adapters, not rewrites: the workbench structural codec is
cross-checked bit-for-bit against `r12.icosapacket` in tests.

VERDICT: P01 complete — truth recorded, active work preserved and
committed, no authority lock violated.
