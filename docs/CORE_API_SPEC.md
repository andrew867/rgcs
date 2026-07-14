# RGCS v2 — Core API Specification (`rgcs_core`)

**Author:** Sub-Agent 04 (Computational Core and Verification)
**Date:** 2026-07-14
**Status:** Complete; matches `rgcs_core` 2.0.0. Every function names its
registry id(s) from `docs/model_registry.yaml` and its classification per
`docs/SCIENTIFIC_CLASSIFICATION_POLICY.md`.

## 1. Scope and engineering contract

`rgcs_core` is the deterministic, typed, tested computational core of
RGCS v2, independent of the desktop UI (`rgcs_desktop` depends on it, never
the reverse).

* **Python:** runs on 3.11 (development environment); targets 3.12
  compatibility. No 3.12-only syntax is used.
* **Dependencies:** numpy, scipy, pydantic v2 (see `pyproject.toml`;
  extras `desktop` = PySide6 + pyqtgraph, `dev` = pytest + hypothesis +
  pytest-qt).
* **Determinism:** no hidden global state; all randomness goes through
  `numpy.random.default_rng(seed)` with caller-supplied seeds (a seed is
  *required* whenever noise is requested).
* **Units:** each module docstring declares its units; unit conversions
  (mm ↔ m, mm³ → cm³) appear **exactly once per function**. Frequencies Hz,
  angular frequencies rad/s, geometry lengths mm, wave speeds m/s, masses g,
  time s.
* **Serialization:** `rgcs_core.provenance.to_jsonable` / `json_dumps`
  produce JSON-compatible dicts; NaN/±inf always serialize as `null`
  (D-03). Pydantic models, dataclasses, numpy types and `UncertainValue`
  are handled.
* **Validation:** malformed inputs raise `ValueError` (or pydantic
  `ValidationError` on the models); nothing is silently coerced.

## 2. Classification-metadata contract (policy §4.1)

Every claim-bearing public function carries the decorator

```python
@classified(label, registry=("RGCS-M.x", ...), sources=("RG-xx", "LT-xx", ...), note="...")
```

which attaches a frozen `Classification` object at
`function.classification` with fields `label`
(`Established | Derived | Hypothesis | Source claim` — hybrid labels are
rejected at construction), `registry`, `sources`, `note`. Functions that
return dicts additionally embed a human-readable `"classification"` string.
Heuristics state "engineering heuristic - not evidence" in docstring and
output. `tests/unit/test_experiments_provenance.py::
test_classification_metadata_on_every_public_function` enforces coverage;
a forbidden-vocabulary lint (`rgcs_core.provenance.FORBIDDEN_TERMS`,
assembled at runtime so the phrases never appear in source) is enforced by
`test_forbidden_vocabulary_absent_from_source`.

## 3. Uncertainty type

`rgcs_core.uncertainty.UncertainValue(mean, u_rel)` — frozen dataclass; a
scalar with relative 1-σ uncertainty. Properties/methods: `.sigma`,
`.interval(k=1)`, `.scale(f)`, `.reciprocal_scale(num)`, `.to_dict()`
(keys `mean, u_rel, sigma, lo_1sigma, hi_1sigma`).
`default_wave_speed()` returns v̄_L = 6310 m/s with u_v = 0.05
(RGCS-M.10; the 6310 value is a Source claim pending citation, D-19a).
**Every ladder/compact frequency or length output is an UncertainValue,
never a bare float.**

## 4. Public API by module

### 4.1 `rgcs_core.geometry` (mm, mm², cm³, g, deg)

| Symbol | Registry | Notes |
|---|---|---|
| `CrystalGeometry` (pydantic, frozen) | — | L, D_w ≥ D_n, N_f ≥ 3, angles, ρ, `diameter_mode`, `angle_mode`; defaults 51.843°/60° are Source claim |
| `polygon_area_mm2(d, n, mode)` | M.1/M.2 | across_vertices / across_flats |
| `apothem_mm(d, n, mode)` | M.3 | |
| `termination_height_mm(r_a, angle, mode)` | M.4 | face_slope / axis_to_face / apex_included |
| `crystal_geometry(g)` → dict | M.5/M.6/M.39 | volume, mass, `node_prior_female_frame_mm` = (L+h_f−h_m)/2 and its male-frame pair. **`geometry_balance_node_mm` is deleted and must never be reintroduced (D-01).** |
| `solve_diameter_scale_for_mass(g, m*)` | M.7 | Newton + bisection, \|Δm\|/m* < 1e-10 |
| `SpiralGeometry` (pydantic) | M.30 | q, T, R_0, H, p_z (`cone_exponent`), Ω_s (`phase_winding`) |
| `spiral_pitch_parameter(q)` | M.31 | a = ln q/2π |
| `spiral_curve(g, samples)` | M.30 | returns theta, r, x, y, z, chi arrays |
| `spiral_path_length_3d_mm(g)` | M.35 | AUTHORITATIVE converged polyline (≥1200 samples, doubling to rel 1e-6) |
| `spiral_metrics(g)` | M.31–M.37 | λ_s, rκ, ℓ_pl, ℓ_3D, per-turn ℓ_k, `compact_radius_prior_mm` (M.36), `per_turn_compact_radius_mm` (M.37), retired closed form with its error |
| `metric_center_mm`, `node_prior_mm`, `female_to_male_frame_mm` | M.38–M.40 | female-apex frame throughout |
| `node_positions(L, h_f, h_m, measured=None)` | M.38–M.40 | measured takes precedence; `measured_node_mm` is `None` (JSON null) when absent |
| `node_alignment_factor(x_d, x_*, σ_x)` | M.41 | heuristic; feeds only S |
| `angle_audit(angle)` | RG-16 | numerology containment; arithmetic only |

### 4.2 `rgcs_core.harmonics` (mm in, Hz/mm out as UncertainValue)

* `axial_half_wave(length_mm, wave_speed=None)` → UncertainValue (M.8/M.11).
* `ladder_length_mm(N, f0=4096, wave_speed=None)` → UncertainValue (M.9).
* `harmonic_classification(length_mm, f0, wave_speed)` → dict with
  `n_eff`, **set-valued** `harmonic_class_set`, `ambiguous` flag (M.12;
  116 mm at u_v = 0.05 → {6, 7}), and the D-04 interpretation rule string.

### 4.3 `rgcs_core.compact_modes` (Hz; mm→m once inside `kappa_chi_hz`)

* `parity_index_set(parity, n_max, include_zero_mode=True)` (M.16/M.17):
  odd = {1,3,5,…} (never 0); even = {0,2,4,…} gated by the flag.
* `kappa_chi_hz(v_chi, R_chi_mm)` → UncertainValue (M.14) — the ONLY
  identifiable spectral parameter; the 100 mm default radius is a
  placeholder (D-21).
* `compact_mode_spectrum(f_b, kappa=..., | v_chi=..., compact_radius_mm=...,
  n_max, parity, include_zero_mode, u_base_frequency_hz)` (M.13/M.15/M.17,
  Hypothesis H-01): mutually exclusive parameterizations; reports
  `kappa_chi_hz`, per-mode UncertainValue frequencies, `zero_mode_present`;
  n = 0 excluded unconditionally when f_b = 0.

### 4.4 `rgcs_core.resonance` (Hz, dimensionless)

`resonance_offset` (M.18), `linear_detuning` (M.19),
`linewidth_fwhm_hz` (M.26, FWHM), `effective_q`, `epsilon_q` = 1/Q_eff
(M.20), `classify_resonance(eps, Q_m, Q_x, u_eps)` — **u_eps mandatory**
(policy §3.4); bins WITHIN_LINEWIDTH/NEAR/MODERATE/FAR at 1/5/50 × ε_Q,
`sweep_span_hz` (M.21, with 6-linewidth floor),
`corrected_resonance_offset(...)` (M.22, signed δ ledger + first-order
u(ε)). `NONRESONANT_CONTROL_EPSILON = 1.25` (control convention only).

### 4.5 `rgcs_core.coupled_modes` (Hz; rates 1/s)

* `coupled_two_mode(f_A, f_B, g, Q_A, Q_B)` (M.23–M.27): hybrids, 2g
  splitting, atan2 mixing angle, R_g, and `coupling_rate_s` = |K| = 2πg
  (anti-Hermitian time-domain coupling K = i·2πg; QA-D-04 erratum).
* `n_mode_eigenproblem(f, g_matrix)` (M.28): validates symmetric,
  zero-diagonal g; `numpy.linalg.eigh`.
* `avoided_crossing_sweep(f_A_grid, f_B, g)` (M.24).
* `coupling_geometry_scaling(g, R_ref, R_new)` (M.29, Hypothesis H-05).
* `coupling_rate_from_g_hz` / `g_hz_from_coupling_rate` / 
  `coupling_consistency(K_fit, g_fit)` — |K| = 2π·g map (anti-Hermitian
  structure K = i·2π·g) with the pre-registered warning flag. Erratum
  2026-07-14 (QA-D-04): the former K = π·g real-symmetric map was wrong.
* `integrate_stuart_landau(omega, G, gamma, beta, K, z0, fs, n, noise,
  seed)` (M.46/M.49, Hypothesis H-09): integrates the COMPLEX canonical
  form (the polar form is singular at A→0) with an exponential
  integrating factor for the stiff linear part; seed required when
  noise > 0. Returns t, z, amplitude and phase separately (KOS-03).
* `stuart_landau_pair(...)`: exact port of the golden-dataset generator.

### 4.6 `rgcs_core.loading` (Hz, mm, g)

`loading_factor(f_loaded, f_free)` = k_H (M.42, measured) and
`length_shortfall_ratio(L_actual, L_target)` = k̃_H (M.44, Hypothesis
H-08b) are **distinct functions**; `added_modal_mass_g(k_H, m, η=0.5)`
(M.43, conditioned on H-08); `loading_from_length(...)` states its
conditioning in `mass_loading_compatible`; `apply_correction_ledger(f,
deltas, u_deltas)` (M.45, signed, warns when |Σδ| > 0.02).

### 4.7 `rgcs_core.drive` (ms/µs, Hz, V, A, µH, µJ)

`DRIVE_PRESETS` + `drive_sequence(mode, carrier)` (RG-12): exact-cycle
families 2261 = 754+754+753 / 1508 = 754+377+377 / 1131 = 377+377+377
with exact macro times; `phase_residue_cycles(c)` = c − round(c) —
defined on cycle counts only (D-13; +0.328 for 1507.328).
`electrode_pulse_metrics`, `sound_key_macro`, `micro_pulse_metrics(...,
pulses_per_period=1)` — the pulses-per-carrier-period assumption is now
an explicit parameter (RG-14); coil golden 26 µH / 117 µJ.
`source_preset_catalog()` (all Source claim).

### 4.8 `rgcs_core.coherence` (s, Hz, rad; metrics in [0,1])

Exact ports of `tools/generate_golden_coherence.py` (normative):
`analytic_signal` (M1), `instantaneous_phase`/`instantaneous_frequency`
(M2), `circular_mean`/`circular_resultant`/`circular_variance` (M3),
`rayleigh_test` (M4/RGCS-M.61), `coherence_window`/`coherence_series`/
`noise_baseline_theory` (M5, KOS-07 adaptation), `phase_linearity` (M6),
`amplitude_normalized_coherence` (M7), `band_power_fraction` (M8, proxy),
`coherence_onset_time` (M9), `coherence_decay_time`/
`fit_exponential_decay` (M10), `phase_locking_value` (M11),
`threshold_detect_bootstrap` (M12, seeded), `windowed_phase_rates` +
`spatial_phase_anisotropy` (M13 — windowed slopes are normative),
`model_comparison` (M14, AIC/BIC over exponential/power/damped/no-change).
Extras: `phase_rate_shear_scalar` (RGCS-M.52 direct form) and
`circular_variance_tensor` (RGCS-M.53). Defaults `DEFAULT_WINDOW_S` =
2 ms, `DEFAULT_HOP_S` = 0.5 ms (the golden-dataset analysis parameters);
callers must report (C, w, baseline) together.

### 4.9 `rgcs_core.experiments`

Pydantic schemas `SensorChannel`, `ApparatusRecord` (KOS-01/05 apparatus
contract: shared-reference declaration, artifact register),
`RunRecord` with `null_label()` (D-20: "amplitude-null,
coherence-untested") and `post_drive_coverage_ok()` (KOS-12: ≥ 2.5×
past drive-off). `control_subtracted_metrics(y_cfg, y_ctl)` → G_c and
the evidence-bearing d_c (M.57). `merit_score(...)` → S = |Λ|²·D_f·P_φ·
N_x·G_c with all factors reported and "not evidence" note (M.58).
`current_to_electron_rate(I)` (RG-15). `run_record_to_json(run)`.

### 4.10 `rgcs_core.provenance`

`MODEL_VERSION`, `Classification`, `classified`, `classification_string`,
`FORBIDDEN_TERMS`, `contains_forbidden_vocabulary(text)`,
`to_jsonable`, `json_dumps` (allow_nan=False), `sha256_file`,
`sha256_of_jsonable`.

## 5. Testing layout

* `tests/unit/` — 97 tests: per-module behavior, classification-metadata
  and forbidden-vocabulary gates, JSON-null policy, malformed inputs.
* `tests/property/` — 17 Hypothesis suites: spectrum monotonicity,
  two-mode bracketing, Cauchy eigenvalue interlacing, offset/detuning
  identity, unit and frame round-trips, coherence/circular-statistic
  bounds, shear-scalar invariances.
* `tests/golden/` — 19 tests: ledger Part E values G-01..G-15 plus the
  D-13 residue and the D-01 frame pair.
* `tests/regression/` — 47 tests: every `expected` entry of the golden
  coherence manifest recomputed from the CSVs with manifest tolerance
  semantics (values read from `manifest.json`, never hard-coded;
  bootstrap seed MASTER_SEED+55), the byte-identical generator
  regeneration test (`slow` marker), and non-gating benchmarks
  (`benchmark` marker).

Run: `python3 -m pytest tests/unit tests/property tests/golden
tests/regression` (pytest config in `pyproject.toml`; `pythonpath = ["."]`).
