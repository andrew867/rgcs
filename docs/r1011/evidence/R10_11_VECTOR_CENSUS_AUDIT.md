# R10.11 Vector Census Audit

Census: 44 unique raw vectors (docs/r1011/evidence/RGCS_COMPLETE_VECTOR_CENSUS_2026-07-27.csv, imported verbatim from the pack).

## Cross-check vs repository registries

- r109 registry V2 (11 vectors): MISSING from census: [168500683]
- Census-only vectors new to repo registries: 34 — the eleven-member British landing-site set, the legacy corpus records (incl. 167829573, 683742917), the orange triplet, the CYYT pair, and the superseded/bridge records.
- Duplicates: none (44 rows, 44 unique raws).
- Corrections captured: Montréal direct 165879243 CURRENT; 168729543 superseded; affine target 168500683 recorded via notes (bridge disabled); CYYT compact 165892733 marked CRITICAL_NEW_CODEC_CONSTRAINT.
- Collisions: 1658792343 (Gander/Argentia) retained as corrupted, DO_NOT_FIT.
- Sealed holdouts present with SEALED status and DO_NOT_FIT: 165892323, 1687209343, 168724343, 165872943, 165829473, 167854923.

## Registry disposition

The census is imported as the R10.11 registry-of-record for THIS phase
(r1011 reads it read-only). r109.registry V2 remains the fit-permission
authority: fit anchors stay exactly {Stonehenge, Erie, Montréal-direct,
Toronto}; nothing in the census widens the fit set. UK cluster and
sealed holdouts remain excluded from all calibration and grammar
selection (test-enforced).
