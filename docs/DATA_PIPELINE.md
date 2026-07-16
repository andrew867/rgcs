# Data Pipeline (Agent 14) — ENG

From sensor to register with no hand-carried numbers. Everything below
uses formats and code that already exist in the repository; the
pipeline adds orchestration, not physics.

## 1. Data formats (existing contracts, binding)

- **Time series:** CSV (or Parquet) per the v2 `timeseries_channel`
  schema — UTF-8, one header row, unit-suffixed columns (`t_s`,
  `accel_m_s2`, `i_coil_a`, `pd_v`, …), `t_s` from acquisition start,
  sha256 of file bytes recorded in the manifest.
- **Run manifest:** the v2 `run_manifest` schema — embeds specimen,
  drive, acquisition, environment; lists every data file with checksum.
  *A run without a valid manifest does not exist.*
- **Programme/optical records:** `timing_program` and `optical_probe`
  schemas (v3) — one per block, referenced by run manifests.
- **Session header:** environment record (v2 schema) + calibration
  block (dates, values, pass/fail) per CALIBRATION_GUIDE.
- **HG store:** session spatial records persisted via
  `rscs_core.memory` (`save_store`) — the H-15..H-19 soak.

## 2. Directory layout (bench data volume, mirrors to two backups)

```
data/
  sessions/S-YYYYMMDD-nn/
    session_header.json
    calibrations.json
    runs/RUN-*/manifest.json + *.csv
    blind/codes.enc          (sealed until SAP §7 unblinding)
  registry_snapshots/        (git rev + registry hashes per session)
  derived/                   (pipeline outputs, never hand-edited)
```

## 3. Pipeline stages (each idempotent; rerunning never changes inputs)

1. **Ingest**: checksum every file; validate all JSON against the
   schema set (`experiments/schemas/validate.py` machinery); reject
   loudly on any violation.
2. **Gate check**: session calibrations in date? H-29 phase gate PASS?
   channel latency non-null for any phase-bearing analysis? KOS
   acquisition gates satisfied for coherence claims? Runs failing a
   gate are marked `gated_out` with the reason — never silently used,
   never deleted.
3. **Condition**: sensor response curves applied
   (CALIBRATION_GUIDE §4); analytic signal via the frozen v2
   `analytic_signal` (RGCS-M.55); no filtering beyond the
   pre-registered settings.
4. **Extract**: per-branch estimators — peak tables, Q, two-sensor
   phase, ladders, splittings 2g, node maps, 𝒞_w windows (v2
   `coherence_window`, always with the amplitude report beside it),
   ensemble phase statistics, demodulated optical response, paired
   differences for the null tests.
5. **Uncertainty**: every extracted quantity wrapped as
   `UncertainValue` with the CALIBRATION_GUIDE §8 budget propagated
   (v2 uncertainty rules / RSCS-O.11).
6. **Statistics**: exactly the pre-registered tests of
   `VALIDATION_PLAN.md` §3 / v2 SAP; blinded labels until the SAP §7
   step; exploratory analyses allowed but always labelled EXPLORATORY
   and never promoted within the same phase.
7. **Report + register**: per-block analysis_result records (v2
   schema), phase reports, and register appends (CLAIM_REGISTER status
   notes, NEGATIVE_RESULTS rows, DEFECT rows for artifacts). Register
   appends are git commits — the audit trail is the repo history.

## 4. Reproducibility rules

- The pipeline runs from a tagged repo state; every derived output
  records the git rev + input checksums (same discipline as the
  desktop reproducibility bundles, same verifier).
- Derived outputs are regenerable byte-stably from `data/` + repo (the
  D-V3-02/04 lessons applied: SOURCE_DATE_EPOCH pinned; tolerance-aware
  cross-platform comparisons where serialization is involved).
- No spreadsheet step exists anywhere. If a number was typed by a
  human, it is provenance metadata (serials, station positions), and it
  lives in a schema-validated record.

## 5. Analysis software surface (already shipped)

`rgcs_core.coherence` (M.55/M.56 metrics), `rgcs_core.coupled_modes`
(splitting fits), `rgcs_core.resonance`/`harmonics` (ladders),
`rgcs_core.anisotropy` (oriented speeds), `rgcs_core.experiments`
(control-subtracted metrics, merit scores), `rgcs_core.timing`
(cross-correlation, signal fidelity, phase budget), `rgcs_core.optics`
(ray/OPL/photoelastic predictions), `rscs_core` operators for typed
composition. New estimators, if a measurement demands one, enter
through the governance path (registered, unit-tested, classified)
before first use on unblinded data — never as a notebook one-off.
