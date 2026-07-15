# Agent 07 Handoff — Coil, Laser, Timing, and Experimental Design

**Date:** 2026-07-15. **Status: COMPLETE, GREEN.** Consumers: Agent 08
(embedded/desktop implementation), Agent 09 (manuscripts), Agent 10 (QA).

## What exists now

- **`rgcs_core.timing`** (all functions v2-`@classified`; no new RSCS ids,
  D7-001): master clock (single reference, per-channel latency slots,
  DDS/PLL flags), exact-cycle closures (`closure_window_s` — rational gcd;
  golden 4096+1496 → 125 ms / 512 & 187; 644 → 250 ms; 587 → 1 s),
  modulation families (20/21 Source; 20.48/40.96 Derived exact),
  `coil_pair_phases`, `phase_at_coordinate` (cable/driver/inductive/
  acoustic/optical/group terms, each declared; acoustic speed from Agent 05
  anisotropy, optical transit from Agent 06 `ray_to_target`), coil model
  (impedance ∥ distributed C, self-resonance, mutual inductance, RLC ring
  response, pulse energy), `SAFETY_LIMITS` + `safe_drive_check`
  (dummy-load-first mandatory), sweeps + `control_matrix` (10 branches ×
  grid, seeded shuffle + blind codes), `cross_correlation` /
  `signal_fidelity`, `function_generator_presets` (signal-level only).
- **Schema:** `experiments/schemas/timing_program.schema.json` + validated
  example. Macro-mode enum accepts ONLY the frozen v2 names
  `standard/half_spacing/double_rate` (D7-002). Safety block capped at the
  D7-003 envelope; `dummy_load_first` is `const: true`.
- **Docs:** `COIL_LASER_TIMING_AND_PHASE.md` (§9 = embedded timing
  acceptance requirements), `EXPERIMENTAL_PROGRAMME.md` (pre-registration
  spine; §4 = new hypothesis rows).
- **Claims:** H-24..H-28 (node-menu definitions 4–8, closing the Agent 05
  flag), H-29 (±5° phase-prediction gate), H-30 (sham-timing
  indistinguishability). All with failure conditions.

## Binding rules downstream agents inherit

1. **D7-002:** never rename `half_spacing`/`double_rate`; the schema enum
   enforces it.
2. **D7-003 envelope** is a ceiling for every preset, schema, manuscript
   number, and hardware doc: V ≤ 30 V, I ≤ 3 A, ≤ 5 mJ/pulse, laser ≤ 3R/
   5 mW, specimen ΔT stop 5 °C, dummy-load-first, no human exposure.
3. **Phase validity gate (H-29):** a channel with
   `latency_calibration_s: null` is phase-invalid; software must flag it
   (Agent 08 UI requirement, acceptance §9.7).
4. Source operating points (46 ms envelopes, keys, 20 Hz family) stay
   Source claims; closure arithmetic is Derived and never upgrades them.

## For Agent 08 (next)

- Implement the **embedded timing acceptance requirements**
  (`COIL_LASER_TIMING_AND_PHASE.md` §9): single-reference DDS/TCXO/PLL
  chain, complementary coil outputs (≤ 1° resolution at 4096 Hz), isolated
  trigger outputs, ADC sync, macro engine reproducing G-12 allocations,
  null-calibration flagging.
- Desktop: waveform/timing preview from `function_generator_presets` +
  v2 `drive_sequence`; experiment builder over `timing_program` +
  `optical_probe` schemas; phase-budget view over `phase_at_coordinate`.
- Packaging: declare `jsonschema` + `referencing` (Agent 06 flag) and
  `pydantic` status; Windows fixes V2-WIN-01 (zip arcname) remain open.

## Test state after Agent 07

Full suite: **364 passed, 2 inherited failures** (V2-WIN-01 zip arcname,
NR3-001 golden CSVs), zero new regressions. 17 new tests
(`tests/unit/test_rgcs_timing.py`). Schema validation green (11 targets).
Frozen paths verified untouched.
