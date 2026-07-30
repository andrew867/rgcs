# R10.9 Final Report — Variable-Depth Octal Codec Integration (2026-07-27)

**Verdict:
`RGCS_R10_9_YELLOW_TYPED_VARIABLE_DEPTH_ARCHITECTURE_RECOVERED_T11_ALIASES_REMAIN`**

The typed architecture, authority migration, header-table search
result, corrected direct-Montréal model, Earth V1/V2 versioning and
comparison, shell integration, registries, tests, and receipts are all
complete and executed. GREEN is not available because (a) the T11
interleave is not uniquely selected — the bounded 46-candidate search
has ZERO survivors (reported as an explicit finite-ambiguity /
unresolved result rather than aliases chosen by preference), (b) the
historical header table could not be recovered from any project
history (explicit UNRESOLVED alias set returned, none invented), and
(c) Earth V2 maps its anchors exactly but FAILS no-fold numerical
verification (361 level-6 orientation reversals vs V1's 0) — a real,
transparently documented tension, not a hidden failure.

## What is now true in the repository

- **Typed T10/T11 family** (`r109/`): depth dispatch, no truncation,
  frozen compact parser untouched, refusals for every stale model
  (affine bridge, decimal-triplet XYZ, reserved-face promotion,
  literal F5=23, marker collapse) — all test-enforced.
- **Direct Montréal `165879243`** is current authority
  (R109-MTL-01); the affine bridge and the `168729543` transcription
  are SUPERSEDED and preserved; regression tests fail if they return
  to production.
- **Earth V1 preserved and reproduced**: archive byte-for-byte;
  face-12 packet→pre-warp convention recovered EXACTLY (orange triplet
  to 1e-14); V1 blind-holdout receipt PRODUCED from the frozen
  operator: `167854923 -> (41.730, −80.834)` — consistent with the
  described candidate-Ohio output; face-19 convention remains
  approximate/UNRESOLVED.
- **Earth V2 built** with the corrected anchor set; exact anchor
  mapping; fold failure honestly measured and reported; holdout not
  fitted and barely moved (0.38°).
- **Shells**: crustal band (variable depth), orbital class,
  body-specific thickness, marker firewall, provisional outer-in
  radial model — implemented and tested.
- **Headers**: primary list stored as UNRESOLVED aliases with exact
  binary renderings; frequency-key list quarantined from header
  parsing; group codes 16 / 16-5 / 16-7 typed SOURCE_REPORTED with no
  invented wire encoding.
- **Registry V2**: all eleven wire values with roles, statuses, fit
  permissions; corrupted Gander/Argentia collision excluded from
  fitting; blind holdout locked.

## Standing unresolved items (explicit)

1. T11 interleave (R109-PKT-05) — bounded space exhausted; future
   bounded extensions listed in the alias report.
2. Historical header-table semantics — awaiting an operator-supplied
   archived artifact.
3. Face-19 pre-warp convention — approximate recovery only.
4. Direct-Montréal vs smooth-warp tension — V2 folds; resolutions all
   open (T11-informed decode, face-dependent stages, anchor revision).
5. Epoch/phase closure — UNRESOLVED.
6. Everything physical: no source-origin validation, no physical
   coordinate-system validation, publication HOLD.

## Sealed holdout intake (2026-07-27)

Five additional raw records were sealed mid-run into
`R10_9_SEALED_HOLDOUT_INTAKE.json` (hashed before decoding; the
referenced external receipt file was not found on disk and that fact
is recorded). Pre-reveal geometric predictions under BOTH frozen
operators exist for the four decodable T10 vectors
(`R10_9_PREREVEAL_PREDICTIONS.json`, self-hashed); `1687209343`
(T11 depth) has no prediction because the interleave is unresolved;
its relationship to `168724343` is untested by rule until T11 freezes.
None of these values may enter T11 selection or any calibration fit
(test-enforced), no gazetteer lookup occurs before the full freeze
set, and no retuning will follow label reveal. Their uniform decimal
terminal `3` against non-uniform decoded S3 {3,7,7,1} is preserved as
direct evidence for the marker firewall.

## Evidence

All artifacts under `docs/r109/evidence/` (SHA256SUMS.txt covers
them); V1 archive under `docs/r109/earth_v1/`; private operator notes
in gitignored `internal-docs/provenance/` (not committed).
