# Calibration Guide (Agent 14) — ENG

Every calibration has: a procedure, an acceptance number, a cadence,
and a storage location (the session record; a channel or instrument
without a stored, in-date calibration is invalid for its claim class).
The uncertainty budget of §8 feeds every confidence metric in
`VALIDATION_PLAN.md`.

## 1. Calibration chain and cadence

| Level | Item | Method | Acceptance | Cadence |
|---|---|---|---|---|
| 0 | TCXO reference | against GPS-disciplined source or NTP-disciplined counter (10-min average) | ≤ 2 ppm | monthly |
| 1 | AWG frequency/amplitude | scope + DMM against level 0 | f: ≤ 2 ppm; V: ≤ 1 % | monthly |
| 2 | DAQ sample clock | driven by level 0 (external clock) — verify lock, not value | locked flag | each session |
| 3 | Channel latencies | §3 | ≤ 100 ns rms jitter; latency known to ≤ 200 ns | each session |
| 4 | Sensors (accel, mic, PD, Hall, shunt) | §4–§6 | per row | weekly + after any cable change |
| 5 | Phase at coordinate | §7 end-to-end check | ≤ 5° at 4096 Hz (H-29) | each session |

## 2. Instrument warm-up and session start

30 min warm-up (TCXO, laser, preamps). Session header record:
temperatures, RH, pressure, SPL floor, mains frequency, instrument
serials + firmware, calibration dates. A session without this header
does not exist for analysis (v2 manifest rule).

## 3. Channel latency calibration (feeds H-29)

For each output channel k:
1. T-split the channel at its LOAD-side connector into scope ch2; scope
   ch1 takes the master-clock reference edge (isolated tap).
2. 1000-edge average of the delay reference→channel: that is
   `latency_calibration_s[k]`; record the rms spread as jitter.
3. Acceptance: jitter ≤ 100 ns rms; repeatability day-to-day ≤ 200 ns.
4. Store in the `timing_program` record. **Channels left null are
   phase-invalid** and the pipeline blocks phase claims from them.

Coil pair complement check: with both coils driven "opposed", measure
phase(I_A)−phase(I_B) at the shunts at 4096 Hz. Acceptance: 180° ± 1°.

## 4. Acoustic sensors

- **Accelerometer + charge amp:** back-to-back against a reference
  accelerometer if available; otherwise gravity-flip 2g static check +
  manufacturer sensitivity, uncertainty booked at 5 %. Frequency
  response: white-noise shaker/piezo disc sweep 100 Hz–50 kHz, deviation
  curve stored and applied by the pipeline.
- **Contact mic:** relative calibration against the accelerometer on the
  same specimen station (transfer function stored; used as a shape/phase
  channel, not an absolute-amplitude channel).
- **Two-sensor phase match** (critical for H-03/H-13): both sensors on
  ONE station driven by one source; residual inter-channel phase
  ≤ 2° across 1–25 kHz after correction. Repeat after any cable swap.

## 5. Coil electrical calibration

- L, R at 1 kHz and at 4096 Hz (4-wire); distributed C via
  self-resonance ring-down (`ring_response` fit: f_ring, Q). Acceptance:
  parameters stable ≤ 2 % across a session.
- Current probe vs 0.1 Ω shunt: agreement ≤ 2 % at 4096 Hz.
- Field constant: Hall probe at the geometric centre vs I; B/I slope
  stored with 3 % uncertainty; repeated at 3 axial stations.
- `safe_drive_check` clearance table regenerated whenever L changes.

## 6. Optical calibration

- Laser power at specimen: calibrated PD/power meter after the last
  optic; **abort if > 5 mW**. Power drift logged; ≤ 2 %/h acceptance.
- Photodiode responsivity: two-point (blocked / known power) each
  session; linearity spot check with ND filter (±1 %).
- Polarizer axes: Malus-law sweep, extinction ratio ≥ 10³; λ/4 plate
  verified by circularity check (rotating analyzer ripple ≤ 5 %).
- Interferometer (when used): fringe calibration with the PZT reference
  mirror — volts-per-fringe measured before and after each run block;
  drift between the two ≤ λ/20 or the block is re-run.
- Photothermal control calibration: matched-power off-node path
  verified to deposit equal absorbed power (PD monitor behind specimen,
  ± 5 %).

## 7. End-to-end phase-budget verification (the H-29 gate)

1. Compute predicted phase at the interaction coordinate with
   `rgcs_core.timing.phase_at_coordinate` from: measured cable lengths ×
   velocity factors, measured driver latency (§3), coil L/R (§5),
   acoustic path with the **oriented** wave speed (anisotropy module;
   scalar band if orientation unknown), optical transit
   (`ray_to_target`), group delay if any.
2. Measure the actual phase: Hall probe (field phase) and accelerometer
   (acoustic phase) at the coordinate vs the reference edge.
3. **Acceptance (H-29): |measured − predicted| ≤ 5° at 4096 Hz** for the
   field channel; for the acoustic channel ≤ 5° + the propagation-speed
   band contribution (computed, not hand-waved).
4. PASS unlocks phase-bearing claims for the session; FAIL → phase
   claims blocked, defect investigation, no physics runs that day.

## 8. Measurement uncertainty budget (session-level, 1σ)

| Quantity | Budget | Source |
|---|---|---|
| Frequency (any measured f) | 2 ppm + resolution bin/√12 | level 0 + FFT bin |
| Acoustic amplitude | 5 % | accel calibration |
| Relative two-channel phase | 2° (1–25 kHz) | §4 phase match |
| Drive phase at coordinate | 5° at 4096 Hz | §7 |
| Coil current | 2 % | §5 |
| B field at coordinate | 3 % | §5 |
| Optical power | 2 % + 2 %/h drift | §6 |
| Optical phase (interferometric) | λ/20 per block | §6 |
| Specimen temperature | 0.2 °C | Pt100 class |
| Position (sensor/support stations) | 0.05 mm | stage + fixture |

Every derived quantity in the pipeline carries these through the v2
uncertainty machinery (`UncertainValue`, RSCS-O.11); a bare number
without uncertainty is non-compliant output.

## 9. Calibration failure handling

A failed calibration NEVER loosens an acceptance number to pass. It is
logged in the session record, the affected claim classes are locked for
the session, and if it repeats it becomes a DEFECT_REGISTER row. The
5 °C specimen temperature-rise stop and the D7-003 electrical limits
are not calibrations and are never adjusted.
