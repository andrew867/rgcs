# RGCS v2 — Coherence Metrics Specification

**Author:** Sub-Agent 03 (Dynamic Coherence and Phase-Evolution Model)
**Date:** 2026-07-14
**Status:** Frozen. Reference implementation:
`tools/generate_golden_coherence.py` (functions named below). Port target:
`rgcs_core/coherence/` (Agent 04). Golden values:
`experiments/sample_data/golden_coherence/manifest.json`.

## Header: conventions

1. Discrete records: sample rate `fs` (Hz), samples indexed n = 0..N−1,
   t_n = n/fs. Complex baseband signal z_n = I_n + iQ_n.
2. All metric IDs COH-M1..COH-M14 are cited by dataset manifest, test
   matrix, and code docstrings. Each carries a classification per
   `docs/SCIENTIFIC_CLASSIFICATION_POLICY.md`.
3. Symbols are Koster-aligned pending Agent 02's `NOTATION_AND_UNITS.md`
   (see DYNAMIC_COHERENCE_SPEC.md §6).
4. Every function must return/attach its classification metadata (policy
   §4.1) and must never emit forbidden vocabulary ("BEC", "condensate",
   "quantum shear", ...) for RGCS quantities.

---

## COH-M1 — Complex analytic signal *(Established)*

**(a) From I/Q hardware:** z(t) = I(t) + iQ(t) directly (KOS-05 chain: all
instruments phase-locked to a shared reference; LO derivation recorded).

**(b) From a single real record x(t):** FFT Hilbert transform.
Z = FFT(x); multiplier h = [1, 2,…,2, (1 if N even at n=N/2), 0,…,0];
z = IFFT(Z·h). Edge effects: discard w/2 at each end for downstream
windowed metrics. Reference: `analytic_signal`.

## COH-M2 — Instantaneous phase and frequency *(Established)*

φ_n = unwrap(arg z_n)   (radians, `instantaneous_phase`)
f_inst,n = (fs/2π) · central-difference gradient of φ_n   (Hz,
`instantaneous_frequency`). Meaningful only where |z| is well above noise;
report alongside amplitude.

## COH-M3 — Circular mean, resultant, variance *(Established)*

For phases {φ_j}, complex resultant ρ = (1/n) Σ e^{iφ_j}:
circular mean = arg ρ; mean resultant length R̄ = |ρ| ∈ [0,1];
circular variance V = 1 − R̄ ∈ [0,1].
Reference: `circular_mean`, `circular_resultant`, `circular_variance`.

## COH-M4 — Ensemble phase-uniformity (Rayleigh test) *(Established)*

Across N_runs repeated runs, take one phase per run (the demodulated phase
of the first analysis window). Rayleigh statistic Z = n R̄²; p-value with
standard small-sample correction:
p ≈ e^{−Z} [1 + (2Z − Z²)/(4n) − (24Z − 132Z² + 76Z³ − 9Z⁴)/(288n²)].
Interpretation rule (KOS-06/KOS-13 template):

* p ≥ α (default α = 0.05): consistent with uniform ensemble phase — the
  *necessary* signature of spontaneous (non-imprinted) order.
* p < α with high per-run coherence: phase is externally imprinted (drive
  or pump leakage) — Stage-III claims are **blocked** (golden case (f)).

Reference: `rayleigh_test`. The decision threshold α is a protocol
parameter (Derived heuristic), not physics.

## COH-M5 — Normalized autocorrelation coherence 𝒞_w(t) *(Established; adapted from KOS-07, Koster et al. 2026 Methods)*

For a boxcar window of N_w samples centred at t (window length
w = N_w/fs; sliding with hop h):

    ACF(τ) = Σ_n z_{n+τ} · conj(z_n)        (over the window)
    𝒞_w(t) = Σ_τ |ACF(τ)| / ( N_w · Σ_n |z_n|² )

The denominator equals Σ_τ |ACF_tone(τ)| for a perfect tone e^{iω₀t} of the
same power, since |ACF_tone(τ)| = (N_w − |τ|)·A² and Σ_τ (N_w − |τ|) = N_w².
This is the discrete form of the KOS-07 normalization against a perfectly
coherent dummy signal. Substitution map (policy §2): their z(t)=I+iQ → ours;
their 100 ns window at GHz carriers → window parameter `w` chosen per
apparatus with the same ~tens-of-carrier-cycles compromise (golden data use
w = 2 ms at f₀ = 5 kHz, fs = 100 kHz ⇒ N_w = 200).

Properties (encoded in golden cases (a)/(b)):
* pure tone → exactly 1 (any amplitude, any frequency within band);
* circular white noise → baseline ≈ (2√π/3)/√N_w  (≈ 0.084 for N_w = 200;
  KOS report ≈ 0.2 for their pipeline — baseline is window-dependent and
  must be reported with every 𝒞 value);
* amplitude scale cancels within a window (per-window normalization).

Report triplet: (𝒞_w(t), w, baseline(N_w)). A bare coherence number is
non-compliant. Reference: `coherence_window`, `coherence_series`.

## COH-M6 — Phase-linearity score *(Derived definition, Established parts)*

Least-squares line (a n + b) through unwrapped φ_n over the analysis span;
PL = | (1/N) Σ_n e^{i(φ_n − a n − b)} | ∈ [0,1].
PL = 1 ⇔ perfectly linear phase (single stable tone); phase diffusion → 0.
Distinct from 𝒞_w: PL is global and model-based (assumes one tone);
𝒞_w is local and model-free. Reference: `phase_linearity`.

## COH-M7 — Amplitude-independent coherence tracking *(Derived definition)*

u(t) = z(t)/max(|z(t)|, ε_floor); apply COH-M5 to u. Separates phase order
from amplitude weighting inside the window (KOS-03/KOS-10 lesson). Report
alongside plain 𝒞_w; divergence between the two flags amplitude-transient
artifacts. Reference: `amplitude_normalized_coherence`.

## COH-M8 — Mode occupancy proxy *(Derived; proxy only)*

P_occ(f₀, bw) = Σ_{|f−f₀|≤bw/2, f≥0} |FFT(z)|² / Σ_{f≥0} |FFT(z)|² ∈ [0,1].
A *band-power fraction*, not an occupation number of anything; the name
"occupancy proxy" is mandatory in outputs. Reference:
`band_power_fraction`.

## COH-M9 — Coherence onset time *(Derived definition)*

t_on = earliest window centre where 𝒞_w ≥ θ_on for `hold` consecutive
windows (defaults θ_on = 0.5, hold = 3; protocol parameters). NaN if never.
Resolution = hop h; uncertainty ± h at best. Reference:
`coherence_onset_time`.

## COH-M10 — Coherence decay time *(Derived definition)*

On the falling segment from argmax 𝒞 to the first window with
𝒞 ≤ baseline + 0.05: fit (𝒞 − baseline) with A e^{−t/τ_c} by log-linear
least squares. Report τ_c and log-RMS residual; if the segment has < 3
windows, NaN. The *choice* of exponential form is the GAN-09 analogy (fit
form only — never the coefficient); competing forms go through COH-M14.
Reference: `fit_exponential_decay`, `coherence_decay_time`.

## COH-M11 — Phase-locking value (pairwise) *(Established)*

PLV = | (1/N) Σ_n e^{i(φ_a,n − φ_b,n)} | ∈ [0,1] for two channels/modes.
Discard the initial transient (golden case (e) discards 10 ms) before
averaging. Reference: `phase_locking_value`.

## COH-M12 — Threshold detection with bootstrap uncertainty *(Established methodology; Derived estimator choice)*

Given control-parameter grid x (drive level, coupling K, …) and an order
parameter y (PLV or 𝒞) with n_runs repeats per x:

1. Estimator: x* where the run-mean curve crosses the midpoint between its
   min and max plateaus (linear interpolation between grid points).
2. Uncertainty: bootstrap over runs (resample columns with replacement,
   n_boot ≥ 500, seeded); report percentile 95% CI.

The midpoint-crossing estimator is deliberately simple and is *biased*
relative to any theoretical critical point when the transition is soft
(golden case (e): estimate ≈ 204 s⁻¹ vs phase-reduction K_c ≈ 251 s⁻¹);
the golden test checks reproducibility of the estimator, not theory
recovery. Thresholds are always **setup-specific** (KOS-09): never reuse a
threshold across apparatus. Reference: `threshold_detect_bootstrap`.

## COH-M13 — Spatial phase anisotropy (multi-channel) *(Established algebra; GAN-04/05 mathematical analogy — NEVER "quantum shear")*

For M spatial sensor channels with unwrapped phases φ_i(t):

1. Windowed phase rates h_i(t_k) = least-squares slope of φ_i over boxcar
   windows (length w, hop h), rad/s. Windowed slopes, not raw gradients, so
   additive-noise jitter does not swamp sustained disagreement
   (`windowed_phase_rates`).
2. Isotropic part h̄(t_k) = (1/M) Σ_i h_i(t_k)   (analogue of the expansion
   scalar θ in the GAN-04 decomposition).
3. **Tensor** T_φ[j,k] = ⟨ (h_j − h̄)(h_k − h̄) ⟩_t   (M×M, rad²/s²).
4. **Scalar** σ_φ² = ⟨ (1/M) Σ_{i<j} (h_i − h_j)² ⟩_t. For M = 3 this is
   the GAN Eq. (2) form ((h₁−h₂)² + (h₂−h₃)² + (h₃−h₁)²)/3 applied to phase
   rates (cited per policy §2; substitution map H_i → h_i).

Zero iff all channels share one phase rate in every window; permutation
invariant; adding a common rate to all channels leaves it unchanged
(golden case (g) checks small-vs-large contrast). Decay fits of σ_φ²(t) use
COH-M10/COH-M14. **This is a mathematical analogy to the cosmological shear
scalar; no physical equivalence with cosmology (or any quantum system) is
claimed, and the term "quantum shear" is forbidden in all RGCS artifacts.**
Reference: `spatial_phase_anisotropy`.

## COH-M14 — Decay-law model comparison (AIC/BIC) *(Established)*

Fit y(t) > 0 (coherence trace, envelope, or σ_φ² trace) with:

| Model | Form | k |
|---|---|---|
| exponential | A e^{−t/τ} | 2 |
| power law | A (1 + t/t₀)^{−p} | 3 |
| damped oscillatory | g·A e^{−t/τ}·\|cos 2πft\| + c | 4 |
| no change | c | 1 |

Gaussian-residual scores: AIC = n ln(SSR/n) + 2k; BIC = n ln(SSR/n) +
k ln n. Winner = min AIC (report full table and ΔAIC; ΔAIC < 2 is a tie).
Reference fits are scipy-free (log-linear + coarse grids) so results are
bit-reproducible; the port may refine optimizers but must reproduce the
golden winners and ΔAIC signs. Before fitting envelopes, subtract the
noise-floor mean amplitude (E|noise| = σ√π/2 for circular complex Gaussian)
and restrict to SNR > 3 (golden case (c) procedure). Reference:
`model_comparison`.

---

## Reporting contract (all metrics)

Every coherence report includes: fs, window w, hop h, N_w baseline, number
of runs, seed/provenance for synthetic data, classification label, and —
for Stage-III claims — the COH-M4 result and control-subtracted coherence
(golden case (f) logic). Amplitude and coherence are always reported
together (KOS-03).
