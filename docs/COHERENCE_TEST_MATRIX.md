# RGCS v2 — Coherence Test Matrix (golden datasets × metrics)

**Author:** Sub-Agent 03. **Date:** 2026-07-14. **Status:** Frozen.
**For:** Agent 04 (port + pytest in `tests/`), Agent 06 (measurement
protocol cross-reference).

## Header

1. Golden data: `experiments/sample_data/golden_coherence/` (7 CSV datasets
   + `case_e_plv_summary.csv` + `manifest.json` + `plots/`). Regenerate
   bit-identically with `python3 tools/generate_golden_coherence.py`
   (master seed 20260714; numpy 2.x; Python 3.11).
2. **The manifest is the normative source of expected values** — the values
   below are copied from it for readability; on any discrepancy the
   manifest wins. Tests must READ expected values from `manifest.json`, not
   hard-code this table.
3. Tolerance semantics (manifest `notes`): `atol` ⇒ |got − value| ≤ atol;
   `rtol` ⇒ |got − value| ≤ rtol·|value|; `min`/`max` ⇒ one-sided bound on
   the *recomputed* quantity; `exact` ⇒ string equality.
4. Metric IDs COH-M1..M14: `docs/COHERENCE_METRICS.md`. All datasets are
   **Derived** synthetic records (no measurements); the Stuart–Landau
   generator as RGCS physics is **Hypothesis** (DC-H2/H3).
5. Analysis parameters for all recomputation: fs = 100 kHz, f₀ = 5 kHz,
   window w = 2 ms, hop 0.5 ms (manifest header fields).

## Matrix

### Case (a) — white noise → coherence near 0 (`case_a_white_noise.csv`)

| Metric | Expected | Tolerance | pytest (Agent 04) |
|---|---|---|---|
| COH-M5 mean 𝒞_w | 0.088587 | atol 0.03 | `test_case_a_coherence_mean_at_baseline` |
| COH-M5 max 𝒞_w | 0.096482 | atol 0.05 | `test_case_a_coherence_never_high` |
| baseline theory (2√π/3)/√N_w | 0.083554 | atol 0.03 vs measured mean | `test_case_a_baseline_formula` |
| COH-M8 P_occ(5 kHz, 500 Hz) | 0.010712 | atol 0.01 | `test_case_a_occupancy_flat` |
| COH-M6 PL | 0.031647 | atol 0.15 | `test_case_a_phase_linearity_low` |

### Case (b) — pure sinusoid → coherence near 1 (`case_b_pure_sinusoid.csv`)

| Metric | Expected | Tolerance | pytest |
|---|---|---|---|
| COH-M5 min 𝒞_w | 1.0 | atol 1e−6 | `test_case_b_coherence_exactly_one` |
| COH-M6 PL | 1.0 | atol 1e−6 | `test_case_b_phase_linearity_one` |
| COH-M2 mean f_inst (edges trimmed) | 5000.0 Hz | atol 1.0 | `test_case_b_instantaneous_frequency` |
| COH-M8 P_occ(5 kHz, 500 Hz) | 1.0 | atol 1e−3 | `test_case_b_occupancy_full` |

### Case (c) — decaying sinusoid (`case_c_decaying_sinusoid.csv`; t_on = 5 ms, τ_amp = 8 ms, σ_noise = 0.05)

| Metric | Expected | Tolerance | pytest |
|---|---|---|---|
| COH-M5 max 𝒞_w | 0.994420 | atol 0.02 | `test_case_c_coherence_high` |
| COH-M5 𝒞_w at t = 10 ms (amplitude ↓ ~2×) | 0.994032 | atol 0.05 | `test_case_c_coherence_survives_amplitude_fall` |
| COH-M9 t_on (θ=0.5, hold=3) | 0.005 s | atol 2·hop = 1 ms | `test_case_c_onset_time` |
| COH-M10 τ_c of coherence | 0.023891 s | rtol 0.5 | `test_case_c_coherence_decay_tau` |
| KOS-10 property: max 𝒞_w where envelope < σ_noise | 0.545864 | atol 0.15; must also exceed 3× baseline | `test_case_c_coherence_below_amplitude_floor` |
| COH-M14 best model (noise-corrected envelope) | `exponential` | exact | `test_case_c_envelope_model_selection` |
| COH-M14 AIC(exp) − AIC(power) | −141.477 | max 0.0 (recomputed must be < 0) | `test_case_c_exp_beats_power` |
| COH-M14 AIC(exp) − AIC(no-change) | −271.993 | max −10.0 | `test_case_c_exp_crushes_nochange` |
| COH-M10 envelope fit τ | 0.0074006 s (true 0.008) | rtol 0.15 | `test_case_c_envelope_tau` |

### Case (d) — random-phase repeated runs (`case_d_random_phase_runs.csv`; 100 runs)

| Metric | Expected | Tolerance | pytest |
|---|---|---|---|
| COH-M5 per-run mean 𝒞_w, run-averaged | 0.990197 | atol 0.03 | `test_case_d_per_run_coherence_high` |
| COH-M6 min per-run PL | 0.997225 | atol 0.1 | `test_case_d_per_run_phase_stable` |
| COH-M3 ensemble R̄ (first-window demod phases) | 0.109620 | atol 0.1 | `test_case_d_ensemble_resultant_small` |
| COH-M4 Rayleigh p | 0.301420 | min 0.05 (must NOT reject) | `test_case_d_rayleigh_does_not_reject` |
| COH-M3 circular variance | 0.890380 | atol 0.1 | `test_case_d_circular_variance_high` |

This is the KOS-06 spontaneous-order signature: per-run coherent, ensemble
uniform. Cases (d) and (f) MUST be implemented as a contrasting pair.

### Case (e) — coupled oscillators, parameter-dependent locking (`case_e_coupled_oscillators.csv` + `case_e_plv_summary.csv`; f₁ = 5000, f₂ = 5080 Hz, K_c theory = π·80 ≈ 251.33 s⁻¹)

| Metric | Expected | Tolerance | pytest |
|---|---|---|---|
| COH-M11 mean PLV at K = 0 | 0.086519 | atol 0.15 | `test_case_e_unlocked_below_threshold` |
| COH-M11 mean PLV at K = 1000 | 0.999999 | atol 0.05 | `test_case_e_locked_above_threshold` |
| PLV vs K monotonicity (Spearman of mean curve) | ≥ 0.9 | min 0.9 | `test_case_e_plv_monotone_in_K` |
| COH-M12 threshold (midpoint estimator) | 204.1917 | atol 60 (contains K_c theory) | `test_case_e_threshold_detection` |
| COH-M12 bootstrap 95% CI (n_boot=500, seed 20260769) | [203.826, 204.884] | reproduce within atol 5 on each bound | `test_case_e_threshold_bootstrap_ci` |

Note: full waveforms stored for run 0 of each K; PLV recomputation for all
8 runs must use `case_e_plv_summary.csv` OR regenerate via the seeded
generator. The midpoint estimator is biased low vs K_c theory (soft
transition) — documented in COH-M12; tests check reproducibility, not
theory recovery.

### Case (f) — shared pump leakage → false coherence caught by controls (`case_f_pump_leakage.csv`; pump phase 0.4 rad fixed across runs; 100 sample + 100 control runs)

| Metric | Expected | Tolerance | pytest |
|---|---|---|---|
| COH-M5 sample mean 𝒞_w | 0.801126 | atol 0.05 (HIGH — the trap) | `test_case_f_false_coherence_is_high` |
| COH-M5 control mean 𝒞_w | 0.802514 | atol 0.05 | `test_case_f_control_coherence_equal` |
| Control-subtracted coherence excess | −0.001387 | atol 0.02 (≈ 0 ⇒ no genuine effect) | `test_case_f_control_subtraction_nulls_effect` |
| COH-M4 Rayleigh p (sample ensemble) | 1.045e−41 | max 1e−6 (MUST reject) | `test_case_f_rayleigh_rejects_imprinted_phase` |
| COH-M3 ensemble R̄ (sample) | 0.999657 | atol 0.1 | `test_case_f_ensemble_resultant_near_one` |
| COH-M3 circular mean vs pump phase | 0.400923 rad | atol 0.1 (clusters at 0.4) | `test_case_f_phase_clusters_at_pump` |

Decision rule under test: coherence HIGH + Rayleigh REJECTS + control
coherence equal ⇒ classify as induced/leakage, never Stage III. Any future
pipeline reporting case (f) as spontaneous coherence FAILS the gate.

### Case (g) — sensor geometry / spatial filtering (`case_g_sensor_geometry.csv`; point sensors at 35/75/115 mm, wide aperture 60 mm = 3λ_short)

| Metric | Expected | Tolerance | pytest |
|---|---|---|---|
| COH-M5 λ=300 mm, point mean 𝒞_w | 0.960502 | atol 0.05 | `test_case_g_long_point_coherent` |
| COH-M5 λ=300 mm, wide 𝒞_w | 0.974445 | atol 0.05 (aperture passes long λ) | `test_case_g_long_wide_coherent` |
| COH-M5 λ=20 mm, point mean 𝒞_w | 0.978417 | atol 0.05 | `test_case_g_short_point_coherent` |
| COH-M5 λ=20 mm, wide 𝒞_w | 0.088800 | atol 0.08 (≈ noise baseline: aperture-averaged out) | `test_case_g_short_wide_filtered` |
| COH-M13 σ_φ² coherent-long | 735.48 rad²/s² | rtol 0.5 | `test_case_g_anisotropy_small_when_common` |
| COH-M13 σ_φ² detuned channels | 198152.8 rad²/s² (theory ((2π50)²+(2π100)²+(2π50)²)/3 ≈ 1.97e5) | rtol 0.2 | `test_case_g_anisotropy_matches_detuning` |
| COH-M13 ratio detuned/long | 269.42 | min 10 | `test_case_g_anisotropy_contrast` |

Naming gate: all outputs say "spatial phase anisotropy"; the string
"quantum shear" must not appear anywhere (`test_forbidden_vocabulary`).

## Cross-cutting tests (Agent 04)

| Requirement | pytest |
|---|---|
| Port of each COH-M1..M14 reproduces every manifest `expected` entry when run on the golden CSVs | `test_manifest_roundtrip` (parametrized over manifest) |
| Regenerating datasets with the tool yields byte-identical CSVs + manifest | `test_generator_deterministic` (slow marker) |
| 𝒞_w invariance: scaling z by 7.3 leaves case (b) coherence = 1 | `test_coherence_amplitude_invariance` |
| σ_φ² permutation invariance + zero for identical channels + common-rate shift invariance (GAN-05 identity, ledger G-15 analogue) | `test_anisotropy_identities` |
| Rayleigh test: n=100 uniform seeded sample p > 0.05; concentrated sample p < 1e−6 | `test_rayleigh_calibration` |
| Classification metadata present on every public function (policy §4.1) | `test_classification_metadata` |
| Forbidden vocabulary absent from module strings/outputs | `test_forbidden_vocabulary` |

## Plot ↔ dataset map (`plots/`)

| Plot | Shows |
|---|---|
| `case_ab_coherence_bounds.png` | noise baseline vs tone = 1 with theoretical baseline line |
| `case_c_decaying_sinusoid.png` | envelope vs 𝒞_w vs amplitude-normalized 𝒞: coherence outlives amplitude |
| `case_d_random_phase_runs.png` | uniform ensemble phase histogram + high per-run coherence |
| `case_e_locking_threshold.png` | PLV(K) with K_c theory line and bootstrap CI band |
| `case_f_pump_leakage_controls.png` | identical sample/control coherence + pump-locked phase histogram |
| `case_g_sensor_geometry.png` | aperture filtering of short λ + anisotropy scalar contrast (log scale) |
