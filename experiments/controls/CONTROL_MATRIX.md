# RGCS v2 — Control Matrix

**Author:** Sub-Agent 06 · **Date:** 2026-07-14 · **Version:** 1.0.0
**Machine-readable:** `control_matrix.example.json` (validates against `experiments/schemas/control_matrix.schema.json`; one object per branch). Roles and gates defined there; this file is the readable summary and rationale.

**Binding rule (Agent 03 handoff / KOS-13):** instrument-only and no-specimen controls must be complete (`status: done`) at identical settings BEFORE any coherence or enhancement claim on a branch. Positive-injection detection-limit controls are prerequisites for any null claim (H-14 logic). Control runs are full runs with manifests (`control_role` field) — subtraction is auditable, never implicit.

| Branch | Negative controls | Positive controls | Sham / randomization / blinding |
|---|---|---|---|
| 1 modal_survey | fixture-only tap; geometry-matched glass/printed dummy | calibrated reference resonator each session | tap-station order seeded-random; scrambled mode-index null (H-01); alternate mount + sensor reposition; second-operator replication |
| 2 electrode_pulse | instrument-only (shielded RC dummy); dummy electrodes on glass blank; no-crystal energized jig | weak-tone injection (detection limit); piezo-driven known response | relay-open sham (0 V, full procedure); 19.8/20/21 Hz randomized + blinded (tests "20 Hz is special") |
| 3 sound_key | speaker-only (no specimen); matched-SPL off-key tones (±10% and inter-key midpoints) | reference resonator via speaker; weak-tone injection | muted-amplifier sham; key/off-key order randomized, analyst blinded, SPL matched ±0.5 dB |
| 4 opposed_coil | instrument-only; no-crystal energized coils (JH-033 pickup floor); resistor dummy load at matched energy; rotated coil | weak-tone injection; shaker-driven known response | condition + envelope family seeded-random; analyst blinded to condition codes |
| 5 human_loading | fixture-only loading (matched contact area/force); surrogate gel/saline load | calibrated added masses (2/5/10 g) validating the ΔM pipeline | free/held/fixture/surrogate order randomized; blinded peak extraction; ethics sign-off is a pre-campaign hard gate |
| 6 spiral_cone | matched disk, plain cone, Archimedean spiral, flat log spiral (mass/material/thickness-matched, RG-08); jig-only sweep | reference resonator through the same jig | shapes coded at fabrication; blind sweeps + blind analysis until primary estimator locked; remount repeats |
| 7 water | sham (muted, full handling); thermal control matched to drive heating; evaporation (sealed/open); crystal-absent field | ultrasonic-cleaner comparator (known cavitation); deliberate 1 °C heat (readout sensitivity) | vessels batch-prepared, seeded-random assignment, coded labels; chemistry + photo scoring before unblinding |
| 8 spatial_mapping | instrument-only on rigid dummy bar (inter-channel phase budget); underlying drive-branch negatives | common-signal injection to all channels (σ_φ² ≈ 0 check — session-invalidating if failed) | sensor-swap and reposition schedules randomized; channel-label scrambling null (H-03); blind station identity during parity assignment |

## Why each control class exists

- **Instrument-only** — measures what the chain does with no physics available: coherence baseline b_w, phase drift, IQ artifacts. Without it every coherence number is uninterpretable (triplet rule).
- **No-specimen / dummy-load** — the JH corpus's own history demands it: the 101 mm coil signals were attributed to drive pickup (JH-033, RG-20). Field/transient effects must be separated from specimen response before any attribution.
- **Matched specimens** (glass dummy, four spiral controls) — isolate *material* and *shape-specific* claims from generic resonator behavior; matching variables are declared in the JSON (`matched_variables`).
- **Matched-SPL off-frequency** — the decisive test of "key" claims: if any equal-loudness tone does the same, the key is not a key.
- **Sham** — full procedure, zero drive: handling, timing, and expectation artifacts.
- **Positive injection** — establishes detection limits so nulls are quantitative (SAP §9), and proves the pipeline can see what it claims to look for (KOS-10 test consequence).
- **Randomization/blinding** — pre-empts sequence and analyst-expectation effects; seeds recorded in manifests.
- **Sensor swap/reposition** — anisotropy or parity that follows the sensor, not the specimen, is a channel artifact (H-03 failure condition; KOS-11 aperture logic).

## Status tracking

Campaign copies of `control_matrix.example.json` update `status` and `run_ids` per control. Agent 08 QA gate: an `analysis_result` on branch B with claims beyond amplitude estimation FAILS if any `required_before_claim` control for B is not `done`.
