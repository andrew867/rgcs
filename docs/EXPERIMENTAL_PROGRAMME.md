# Experimental Programme (RGCS v3, pre-registered)

**Author:** Agent 07. **Date:** 2026-07-15. This is the pre-registration
spine for the v3 synchronized experiments. It extends (does not replace)
the frozen v2 `docs/EXPERIMENT_PROTOCOL.md` and `ROADMAP_TO_FALSIFICATION.md`.
Machine form: `experiments/schemas/timing_program.schema.json` (+ the v2
run-manifest schema set). Statistical rules: v2
`STATISTICAL_ANALYSIS_PLAN.md` unchanged.

## 1. Programme structure

Every campaign is a `timing_program` record: one master clock, calibrated
channels, one named interaction coordinate, a sweep grid, the full control-
branch declaration, randomization seed, safety block, and the hypothesis
rows it feeds. A campaign without a valid record does not exist for
analysis purposes (v2 manifest rule, inherited).

## 2. Factorial control matrix (binding)

`rgcs_core.timing.control_matrix` crosses every declared sweep point with
the ten branches: `coil_only, optical_only, acoustic_only, combined,
dummy_crystal, glass_control, rotated_crystal, sham_timing,
thermal_control, randomized_blinded`. Branches may be *declared* skipped
with a reason; silent omission is non-compliant. Randomized order is
seeded (`randomized_order`), blind codes are generated from the seed, and
the seed is stored for unblinding (v2 SAP §7).

## 3. Sweeps

Pre-registered sweep axes: phase (0–360°, `phase_sweep`), delay,
frequency (carrier + keys + modulation families), amplitude (≤ envelope),
polarization (linear/σ⁺/σ⁻), direction (forward/backward reversal pairs),
loading (v2 loading branch). Sweep grids are cartesian and deterministic
(`sweep_grid`).

## 4. New pre-registered hypothesis rows

### Node-menu falsification rows (crystal application §3, definitions 4–8)

Definitions 1–3 (metric centre, prismatic prior, measured vibration node)
are frozen v2. The five HYP definitions each get a row, observable, and
failure condition:

| ID | Node definition | Observable | Failure condition |
|---|---|---|---|
| H-24 | electrical node (impedance minimum) | impedance vs position along shaft | no reproducible minimum distinct from geometry, or moves with fixture ⇒ definition rejected |
| H-25 | optical path/phase feature | O.18 phase map along ray paths (Agent 06 probe) | no feature above phase-noise floor at the claimed location |
| H-26 | maximal multimode overlap | overlap-integral argmax from measured mode shapes | argmax unstable across re-measurement (> ±5 mm) ⇒ definition rejected |
| H-27 | coupling-integral maximum (RSCS-O.4/O.19 overlap) | fitted g vs probe position | no position-dependence of fitted g above uncertainty |
| H-28 | phase singularity / saddle | phase-field critical point in the spatial map branch | no critical point, or artifact of sensor aperture (KOS-11 check) |

Adjudication rule (inherited H-07): the **measured vibration node
supersedes** any definition that disagrees with measurement; definitions
are a menu to be measured, not facts.

### Timing architecture claims

| ID | Class | Claim | Failure condition |
|---|---|---|---|
| H-29 | ENG | Channel latency calibration + `phase_at_coordinate` predicts the measured phase at the interaction coordinate within ±5° at 4096 Hz | measured-vs-predicted phase error > 5° after calibration ⇒ timing chain not phase-valid; all phase claims blocked |
| H-30 | ENG | Sham-timing branch (correct waveforms, scrambled inter-channel phase) is statistically indistinguishable from combined branch on every NON-phase observable | sham differs on amplitude-only observables ⇒ uncontrolled artifact in the drive chain |

## 5. Signal fidelity gates

Every phase-bearing analysis requires: (i) H-29 passed for the session;
(ii) `signal_fidelity` ≥ 0.99 between commanded and measured drive
waveform at the load; (iii) cross-correlation lag consistent with the §5
delay budget within the jitter budget. Coherence claims additionally
inherit ALL v2 gates (single-shot, ≥ 2.5× post-drive, n ≥ 100, amplitude
reported alongside — DYNAMIC_COHERENCE_SPEC).

## 6. Ringing, damping, saturation, thermal

`ring_response` characterizes the pulse-edge ringing (f_ring, Q,
overshoot); runs record whether the drive point is underdamped. Saturation
and thermal limits are hard stops (`safe_drive_check`, D7-003): specimen
ΔT ≥ 5 °C aborts the run (v2 stop condition). Crystal protection: energy
per pulse ≤ 5 mJ AND dummy-load-first, always.

## 7. Instrumentation set

Synchronized instruments (one reference clock, §1): oscilloscope, current
probe, Hall/fluxgate at the coordinate, accelerometer/contact mic,
photodiode, temperature, optional interferometry. Data formats: the v2
`timeseries_channel` CSV/Parquet contract with sha256 binding, unchanged.

## 8. What this programme does NOT contain

No human exposure, no body-connected stimulation, no therapeutic protocol,
no high-voltage construction instructions, no laser above class 3R/5 mW.
The programme tests **crystal + instrument physics only**, and the
pre-registered expectation for every directional/asymmetry observable is
the conventional null (D6-003).
