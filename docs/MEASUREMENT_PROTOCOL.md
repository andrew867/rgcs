# Measurement Protocol (Agent 14) — ENG

Per-branch runbooks. Every run is described by a validated
`timing_program` record (+ `optical_probe` records for Phase III), is
listed in the pre-registered `control_matrix` output for its block, and
lands as a v2 run manifest (specimen + drive + acquisition +
environment + timeseries, sha256-bound). The v2 acquisition gates are
binding throughout: single-shot capture, acquisition ≥ 2.5× past
drive-off for any coherence claim, n ≥ 100 runs for ensemble-phase
claims, amplitude always reported beside coherence.

## 0. Common to every block

- Pre-registered: sweep grid, branch list, seed, analysis section
  (`prereg_ref`) — committed before the session.
- Controls drawn from the ten-branch set: coil_only, optical_only,
  acoustic_only, combined, dummy_crystal, glass_control,
  rotated_crystal, sham_timing, thermal_control, randomized_blinded.
  Skipped branches must be declared with reasons in the record.
- Stop conditions: specimen ΔT ≥ 5 °C; any interlock trip; SPL floor
  +10 dB; calibration expiry mid-block.

## 1. Modal survey (Phase I: H-01, H-01a, H-03, H-04)

1. Free-free mount (BENCH_HARDWARE §4); impulse tap (instrumented tap
   or piezo click) + swept-sine confirmation of each found peak.
2. Capture: fs ≥ 100 kHz, ≥ 2 s, both sensors; 10 taps per station;
   3 sensor stations along the axis.
3. Extract: peak frequencies (uncertainty = 2 ppm + bin), Q from
   ring-down, two-sensor relative phase per mode (parity assignment,
   0 vs π within the 2° budget).
4. Fit ladders: 1D half-wave f_ax band (with the anisotropic speed if
   orientation is measured, else the scalar band) → H-01a; compact
   spectrum fit f_n² = f_b² + (nκ_χ)² vs plain-rod baseline on
   held-out modes → H-01; presence/absence of the n = 0 member → H-04.
5. Support-sensitivity check: repeat 2 stations with pads shifted
   ± 5 mm (fixture systematic bound).

## 2. Node localization scans (Phases I–II: H-07, H-24, H-26, H-27, H-28)

1. Drive the identified fundamental (acoustic branch, swept-sine at
   resonance, amplitude within envelope).
2. Axial scan: accelerometer stepped in 2 mm stations end-to-end
   (0.05 mm station uncertainty); record amplitude and phase per
   station → displacement-node map (H-07: measured node vs shaft
   midpoint prior; the MEASURED node supersedes).
3. Electrical node (H-24): 4-terminal impedance vs axial electrode-pair
   station at fixed frequencies; minimum location vs geometry;
   repeat after fixture swap (fixture-artifact control).
4. Overlap/coupling maps (H-26/H-27): from the measured mode shapes,
   compute overlap argmax (`overlap_integral`) and fitted-g vs station
   (avoided-crossing splittings with the probe mass at each station);
   re-measure a fresh day for the ±5 mm stability criterion.
5. Phase-field critical point (H-28): two-sensor phase map on the
   spatial grid; sensor-aperture control per KOS-11 (repeat with the
   small-aperture mic).

## 3. Coupling and geometry scaling (Phase II: H-05, H-02, H-09)

- Avoided-crossing runs: detune with calibrated added mass; record
  splitting 2g and linewidths; strong-coupling ratio computed, model
  used only where R_g ≳ 1 (v2 rule).
- H-05: fitted g before/after a controlled compact-geometry change on
  the sacrificial specimen; compare to √(R₂/R₁).
- H-02: sweep ε through 0 (drive detuning protocol), control-subtracted
  gain G_c and effect size d_c, sign-resolved.
- H-09: ring-up/ring-down envelopes vs the amplitude–phase model
  (fitted, tolerance-aware); saturation curves within the envelope.

## 4. Coil branch (Phases II & IV; feeds H-11, H-30, node menu cross-checks)

- Presets: `carrier_4096` (opposed pair), macro modes standard /
  half_spacing / double_rate, modulation families 20/20.48/21/40.96 Hz
  — all from `function_generator_presets`, all dummy-load-cleared.
- Coil current, B field, and phase measured AT THE LOAD each block
  (never inferred from the generator).
- Full 0–360° phase sweeps (`phase_sweep(15)`) between coil pair and
  between coil↔acoustic branches, with reversal tests.
- Sham-timing twin for every live coil block (H-30).

## 5. Optical branch (Phase III: H-20..H-23, H-25)

- All runs as `optical_probe` records with reversal-pair ids.
- H-20: intensity-modulated probe through the measured overlap region;
  demodulate PD at f_drive; interferometric arm for direct ΔΦ; heating
  control = matched-power off-node path (H-22 must pass in the same
  block for H-20 to count).
- H-21 (expected NULL): forward/backward paired runs, ≥ 20 pairs,
  randomized order; asymmetry metric = paired response difference.
- H-23 (expected NULL): σ⁺/σ⁻ paired runs, same design.
- H-25: PD/interferometer response vs axial station of the crossing
  beam — optical node feature map vs the measured node.
- Glass blank and rotated-crystal twins for every configuration.

## 6. Coherence branch (Phase IV: H-10..H-14)

- Single-shot captures, ≥ 2.5× post-drive, n ≥ 100 per condition
  (KOS gates); I/Q or analytic-signal processing in the pipeline.
- H-10: post-drive Σ̄_φ(t) fit — exponential FORM is under test, not
  presumed; report fit residuals against alternatives (linear, power).
- H-11: τ_c per branch (electrode-analog piezo, coil, acoustic) at
  matched delivered energy (energy accounting from calibrated drive
  records).
- H-12: 𝒞_w vs drive power ladder within envelope; changepoint analysis
  per SAP.
- H-13: n-shot ensemble phase histograms, per-shot 𝒞_w, Rayleigh Z;
  drive-imprint control = deliberately phase-locked drive twin.
- H-14: re-run the v2 "no singing" JH branches with coherence metrics;
  amplitude-null-coherence-untested rows get adjudicated either way.

## 7. Software claims (H-15..H-19)

Already machine-tested (status: machine-tested-pass). Bench role:
nightly persistence soak — the pipeline writes every session's spatial
records through the HG store (`save_store`/`load_store`) and replays
retrieval; any violation would reopen the rows. No bench hardware
depends on them.
