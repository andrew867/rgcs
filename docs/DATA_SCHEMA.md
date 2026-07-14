# RGCS v2 — Data Schema

**Author:** Sub-Agent 06 (Experiments, Controls, and Data Schemas)
**Date:** 2026-07-14
**Version:** 1.0.0 (`schema_version` field in every manifest)
**Machine-readable source of truth:** `experiments/schemas/*.schema.json` (JSON Schema draft 2020-12). This document is the human-readable companion; on any conflict the JSON Schema files win. Validator: `python3 experiments/schemas/validate.py` (consumed by Agent 05's experiment builder and Agent 08's QA gates).

## 0. Design rules

1. **One run, one manifest.** Every experimental run (or shot ensemble under identical settings) is anchored by a `run_manifest` that embeds the specimen, drive, acquisition, and environment records and lists every data file with its SHA-256. A run without a valid manifest does not exist for analysis.
2. **Units in names.** Field and column names carry unit suffixes (`length_mm`, `sample_rate_hz`, `tau_c_s`) per `NOTATION_AND_UNITS.md` §0.3. Canonical units: Hz, s, mm, g, V; declared observable unit X per campaign.
3. **Classification travels with data.** Source-claim presets (20 Hz/15 V, 1496 Hz, coil points, envelope families) are flagged in `source_claim_refs` / `classification_note` fields. Analysis outputs carry a `classification` and `evidential_status` (policy §3.3).
4. **Provenance is hashes.** Files are bound by SHA-256; synthetic data are marked `provenance.synthetic: true` and never enter evidential claims.
5. **Pre-registration hooks.** Manifests carry `hypothesis_ids` (H-01..H-14, DC-H1..4, or EXPLORATORY); results carry `prereg_ref`; exclusions must cite pre-registered criteria.

## 1. Schema inventory

| Schema | File | Purpose | Example instance |
|---|---|---|---|
| Specimen | `specimen.schema.json` | Crystal / spiral cone / control shape / water vessel / fixture / dummy record: geometry (frozen symbols §2.1), mass, ladder placement, orientation-known flag (drives u_v), defects, photos+sha256 | `templates/specimen.example.json` |
| Drive config | `drive_config.schema.json` | Exact drive parameters per branch: carrier, pulse, envelope families (2261/1508/1131 exact cycles), sound keys, coil hardware, placement x_d, matched-energy grouping, shared reference clock | `templates/drive_config.example.json` |
| Acquisition | `acquisition.schema.json` | fs, duration, single-shot flag, n_runs, post-drive ratio, I/Q chain, channels with position/aperture, artifact-register pointer | `templates/acquisition.example.json` |
| Environment | `environment.schema.json` | Bench/fixture IDs, temperatures, humidity, ambient SPL, EMI, phase-drift budget, water baselines | `templates/environment.example.json` |
| Time-series descriptor | `timeseries_channel.schema.json` | One data file: path, sha256, format, columns with units, fs, t0, run_index | `templates/timeseries_channel.example.json` |
| Run manifest | `run_manifest.schema.json` | The anchor: embeds all of the above + control_role, randomization/blinding, human-loading ethics block, provenance, exclusion | `templates/run_manifest.example.json`, `templates/branch_0*.template.json` |
| Control matrix | `control_matrix.schema.json` | Per-branch control declarations with roles, `required_before_claim` gates, status | `templates/control_matrix.example.json`, `controls/control_matrix.example.json` |
| Analysis result | `analysis_result.schema.json` | Metrics (COH-M1..M14): coherence triplet + mandatory amplitude report, Rayleigh, four-model decay comparison, spatial phase anisotropy, thresholds, effects, fits; classification + evidential status | `templates/analysis_result.example.json` |

## 2. Run manifest (`run_manifest.schema.json`)

Required: `schema_version`, `run_id` (`RUN-*`), `protocol_branch` (one of the 8), `protocol_version`, `hypothesis_ids`, `timestamp`, `operator_id` (pseudonymous), `control_role`, `specimen`, `drive_config`, `acquisition`, `environment`, `timeseries[]`, `provenance`.

Key semantics:

- **`control_role`** states what the run IS: `active`, `instrument_only`, `no_specimen`, `dummy_load`, `sham`, `matched_control`, `off_frequency`, `positive_injection`. Control runs are first-class runs with full manifests — this is what makes control subtraction auditable.
- **`randomization`**: seed, scheme, `blinded` flag, and the coded label the analyst sees. Unblinding is an event in the SAP (§7), not a field edit.
- **`human_loading`** (schema-enforced for that branch): `ethics_review_ref` and `no_energized_contact_confirmed: true` are hard gates; participant codes are pseudonymous — no personal data anywhere in the repository.
- **`exclusion`**: `excluded`, `reason` (must cite a pre-registered criterion), `decided_while_blinded`.
- **`provenance`**: software name→version map, git commit, and for synthetic data the generator script + seed + `synthetic: true`.

## 3. Time-series file format

CSV convention (Parquet allowed for large campaigns; same column rules):

- UTF-8, one header row, no comment lines; columns named with unit suffixes; time column `t_s` = seconds from acquisition start (`t0_s` offset in the descriptor).
- I/Q records store `z_i_*` and `z_q_*` columns (components of z(t) = z_I + i·z_Q, RGCS-M.55); the LO frequency and derivation live in `acquisition.iq`, never in the file.
- One file per shot (`run_index`) or per channel group; every file appears in `timeseries[]` with `sha256`, `channel_ids`, `sample_rate_hz`, `n_rows`, and full column descriptions.
- Slow channels (water branch: 1 Hz temperature/pH/conductivity) use the same convention.

Worked examples: `experiments/sample_data/modal_survey_response.csv` + `modal_survey_run_manifest.json`; `experiments/sample_data/opposed_coil_iq.csv` + `opposed_coil_run_manifest.json` (both synthetic, generated by the seeded `make_samples.py`).

## 4. Specimen record

Geometry uses the frozen frame: x from the female (wide) apex toward the male apex; `diameter_mode` and `angle_mode` enums are mandatory with any diameter/angle (the corpus angle-convention ambiguity, RG-04). `orientation.crystallographic_axis_known = false` ⇒ u_v = 0.05 applies to every wave-speed-derived quantity (RGCS-M.10). `mass_predicted_g` vs `mass_measured_g` is an intake artifact check. Spiral parts carry the `spiral` block including converged `path_length_3d_mm` and the Hypothesis-labeled `compact_radius_prior_mm`; matched controls declare `matched_control_shape`. Water vessels carry the `water` block (schema-conditional).

## 5. Environment record

Temperature (start/end + specimen), humidity, pressure, ambient SPL, mains frequency, EMI and vibration notes, fixture ID, and the session `instrument_phase_drift_deg` (KOS-13 gate). Water branch adds `water_baseline` (pre-run pH/conductivity/temperature/mass).

## 6. Control matrix

Per-branch JSON declaring every control with a `role` (negative_instrument_only, negative_no_specimen, negative_dummy_load, negative_off_frequency, negative_matched_specimen, sham, positive_injection, positive_known_resonator, randomization, sensor_swap, sensor_reposition, operator_replication, blinding), a `required_before_claim` boolean, a `gate` (pre_campaign / per_session / per_run / per_specimen), and completion `status` with the `run_ids` that satisfied it. QA rule (Agent 08): any analysis result on a branch whose required controls are not `done` fails the gate. Full matrix: `experiments/controls/CONTROL_MATRIX.md` + `control_matrix.example.json`.

## 7. Analysis result

Enforced reporting contract:

- `coherence_report` requires the full triplet (`c_w`, `window_w_s`, `baseline_b_w`) plus `n_window_samples` and `sample_rate_hz`; `dependentRequired` makes an `amplitude_report` mandatory whenever coherence is reported (KOS-03 rule) and a `coherence_report` mandatory for any `rayleigh` or `threshold` block.
- `decay_model_comparison` must contain exactly the four pre-registered models (exponential, power_law, damped_oscillatory, no_change) with AIC/BIC each (COH-M14); `tau_c_s` is a bench parameter.
- `spatial_phase_anisotropy` uses σ_φ² (rad²/s²) and Σ̄_φ naming; "quantum shear" is forbidden vocabulary in every free-text field (QA grep gate).
- `threshold` requires bootstrap CI (n_boot ≥ 500) and `reproduced_across_days`; thresholds are apparatus-specific.
- `classification` ∈ {Established, Derived, Hypothesis, Source claim} (no hybrids) and `evidential_status` ∈ {untested, testing, supported, refuted, ambiguous}.

## 8. Provenance and hashing rules

- SHA-256 over raw file bytes; manifests reference files relative to the manifest location.
- A manifest may be amended only by writing a new manifest version alongside the old one (append-only discipline); data files are immutable once hashed.
- Photos, CAD files, and analysis traces are hashed the same way (`condition.photos[]`, `geometry.cad_sha256`, `coherence_report.trace_sha256`).
- Recommended layout per campaign: `campaigns/<YYYY-MM>/<session>/RUN-.../manifest.json` + `data/`; the repository's `experiments/` tree holds schemas, templates, and synthetic samples only.

## 9. Versioning

`schema_version` follows semver. Additive optional fields → minor bump; any change to required fields, enums, or semantics → major bump plus a migration note here. Agent 05's builder must refuse manifests with a major version it does not know.
