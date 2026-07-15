# Coil, Laser, Timing, and Phase (RGCS v3)

**Author:** Agent 07. **Date:** 2026-07-15. Governance: DECISION_LOG
D7-001..003 (no new RSCS ids; "shorter by half" naming binding; safety
envelope frozen). Implementation: `rgcs_core.timing` (all functions carry
v2 `@classified`); machine schema
`experiments/schemas/timing_program.schema.json`.

## 1. One master timebase

`master_clock()` models the single authoritative reference (default
32.768 kHz TCXO ÷ 8 → 4096 Hz carrier, matching the v2 drive_config
wording). Rules:
- **Every channel derives from one reference.** Channels report their exact
  rational ratio; a channel whose frequency is not an integer divider is
  flagged for DDS/PLL fractional synthesis (Agent 08's DDS/TCXO/PLL design).
- **Latency calibration is a required field.** `latency_calibration_s:
  null` means uncalibrated — the schema keeps it representable but any
  phase claim from an uncalibrated channel is invalid (embedded acceptance
  requirement §7).
- Jitter (≤ 100 ns rms) and drift (≤ 2 ppm) are declared *budgets*
  (acceptance requirements to verify), not performance claims.

## 2. Exact-cycle closures (carrier × keys)

`closure_window_s` / `exact_closure` / `key_closures` compute rational
closure windows (T = 1/gcd over ℚ). Machine-tested golden rows:

| Pair | Window | Cycles |
|---|---|---|
| 4096 Hz + 1496 Hz | **125 ms** | **512 & 187** (brief item 7) |
| 4096 Hz + 644 Hz | 250 ms | 1024 & 161 |
| 4096 Hz + 587 Hz | 1 s | 4096 & 587 (587 coprime to 4096) |

The key values 1496/644/587 Hz are **Source claims (RG-13)** that
parameterize windows; closure arithmetic gives them no truth value.

## 3. Modulation families

`MODULATION_FAMILIES`: 20 Hz and 21 Hz are the Source-stated electrode
rates (RG-13); **20.48 Hz = 4096/200** and **40.96 Hz = 4096/100** are the
Derived exact-cycle engineering variants (integer sub-harmonics of the
carrier; 20.48 Hz closes with the carrier in 48.828125 ms). The exact
variants do NOT replace the source values — both are kept, distinctly
labelled, exactly as v2 keeps millisecond presets beside cycle-exact
allocations.

## 4. Macro sequences and the "shorter by half" ambiguity

The frozen v2 `rgcs_core.drive` module already encodes the three envelope
modes with cycle-exact allocations (golden G-12):
`standard` (46/46×4/184 ms), `half_spacing` (46/23×4/92), `double_rate`
(23/23×4/92). The source's ambiguous "shorter by half" statement maps to
the LAST TWO as its two defensible readings; **D7-002 makes the naming
binding** — neither is ever called "double pulse" (nothing doubles a
rate in `half_spacing`). Agent 07 adds nothing here except the schema enum
that only accepts these names.

## 5. Coil A/B and the phase at the interaction coordinate

`coil_pair_phases`: `opposed` (complementary, B = A + 180°, the WB3
source setting), `in_phase`, or explicit `offset` for sweeps.

`phase_at_coordinate` is the central deliverable: the **actual** phase at
the measured interaction coordinate, never inferred from GPIO timing
alone. Terms, each reported separately:

| Term | Model | Source of the number |
|---|---|---|
| cable | L/(vf·c) | measured cable length + velocity factor |
| driver | fixed latency | datasheet, then measured |
| inductive | atan(ωL/R) | coil L, R measured at the load |
| acoustic | path/v | **oriented speed from `rgcs_core.anisotropy`** (Agent 05), not a guessed scalar |
| optical | transit | `rgcs_core.optics.ray_to_target` (Agent 06) |
| group | Δτ_g | RSCS-O.18/O.8 dispersion operators |

The interaction coordinate is one of **geometric_center /
prismatic_shaft_prior / predicted_node / measured_node / custom** — three+
distinct locations, never conflated (node menu §3). Coil current, voltage,
field, and phase are measured **at the load** (schema instrumentation:
current probe + Hall/fluxgate at the coordinate).

## 6. Coil electrical model

`coil_impedance` (series RL ∥ distributed C), `self_resonance_hz`
(1/2π√LC — above which the coil is not "an inductor"),
`mutual_inductance_h` (M = k√(L₁L₂) for the opposed pair),
`ring_response` (series-RLC ringing: f_ring, Q, ζ, overshoot — drives the
ringing/overshoot control), `pulse_energy_uj` (E = ½LI², v2 micro-pulse
convention), `safe_drive_check` (§8).

## 7. Optical synchronization

Laser trigger, intensity modulation, and polarization modulation are
channels of the SAME master clock (`synchronized_to: master_clock`);
the timing programme links Agent 06 `optical_probe` records by id
(`optical_probe_ids`), inheriting their laser-class/interlock limits and
reversal-pair structure. Entry-facet and ray-path coordinates come from
`ray_to_target`; its transit time feeds the optical term of §5.

## 8. Safety envelope (D7-003, binding)

`SAFETY_LIMITS`: V ≤ 30 V, I ≤ 3 A peak, pulse energy ≤ 5 mJ, specimen
ΔT stop at 5 °C (schema max 10), laser ≤ 5 mW class ≤ 3R. `safe_drive_check`
enforces **dummy-load-first**: no operating point reaches a specimen until
cleared on an instrumented dummy load. Function-generator presets
(`function_generator_presets`) are signal-level recipes (≤ 10 Vpp into a
driver input) — no high-voltage construction instructions, no
body-connected stimulation, no human exposure protocol anywhere in the
programme.

## 9. Embedded timing acceptance requirements (for Agent 08)

1. Single reference oscillator; all outputs integer or DDS/PLL-derived
   from it; document the synthesis chain per channel.
2. Complementary coil outputs with commanded phase resolution ≤ 1° at
   4096 Hz and verified 180° complement (opposed mode).
3. Isolated (opto/transformer) trigger outputs for laser and ADC sync.
4. Per-channel latency calibration procedure; stored with the programme
   record; jitter ≤ 100 ns rms verified at the connector.
5. Measurement ADC synchronization to the same reference; sample clock
   phase-locked, not free-running.
6. Macro-sequence engine reproduces the three v2 envelope modes with
   cycle-exact boundaries (G-12 allocations).
7. A channel with `latency_calibration_s: null` must be flagged by the
   software as phase-invalid (Agent 08 UI requirement).

## 10. Fidelity and cross-correlation

`cross_correlation` (normalized, peak + signed lag) and `signal_fidelity`
(zero-lag normalized correlation ∈ [−1,1]) are the measurement-layer
figures for §5 phase verification and for the H-2x observables — the
classical adaptation of the EP-05-02 correlation-figure principle (no
quantum-optics import).
