# RGCS v2 — Statistical Analysis Plan (SAP)

**Author:** Sub-Agent 06 (Experiments, Controls, and Data Schemas)
**Date:** 2026-07-14
**Version:** 1.0.0 — pre-registered. Amendments after first data acquisition are versioned and dated; silent edits are non-compliant (policy §3.2).
**Companions:** `EXPERIMENT_PROTOCOL.md` (designs), `COHERENCE_METRICS.md` (COH-M1..M14 definitions), `ROADMAP_TO_FALSIFICATION.md` (failure conditions), `analysis_result.schema.json` (output format).

## 1. Philosophy: estimation first

1. The primary output of every analysis is an **effect estimate with a bootstrap confidence interval**, not a p-value: G_c and d_c (RGCS-M.57), coherence triplets, τ_c, κ_χ, k_H, threshold locations. Verdict-style hypothesis tests exist only where a ROADMAP failure condition demands one, and each is pre-registered here with its α, its family, and its exclusion rules.
2. **Amplitude and coherence are separate observables and are always reported together** (KOS-03; schema-enforced).
3. No result is ever "consistent with the source" (forbidden hybrid); outcomes map to `evidential_status` ∈ {untested, testing, supported, refuted, ambiguous}.
4. All analysis code is versioned; every result records software versions and the git commit; analyses are re-runnable from manifests alone.

## 2. Estimators and uncertainty

- **Bootstrap CIs:** percentile bootstrap over runs (or specimens/vessels — the pre-registered resampling unit per family below), n_boot ≥ 500, seeded; 95% unless stated. Reported as (estimate, ci_low, ci_high, n_boot, unit-of-resampling).
- **Circular quantities:** circular mean, R̄, V per COH-M3; Rayleigh test per COH-M4 with the small-sample correction; n_s ≥ 100 for any ensemble-phase claim.
- **Spectral peaks:** local parabolic interpolation on Welch/FFT magnitude with pre-registered window and zero-padding; peak uncertainty from repeat scatter, not fit residual alone.
- **Ringdown parameters:** γ_n from log-envelope least squares on SNR > 3 segments after noise-floor subtraction (E|noise| = σ√π/2 convention, COH-M14 procedure).
- **Thresholds:** COH-M12 midpoint-crossing estimator with bootstrap CI; the estimator is documented as biased for soft transitions; a threshold claim additionally requires day-replication (KOS-09 rule).

## 3. Pre-registered decay-law model comparison (COH-M14)

Applied to: post-drive coherence traces 𝒞_w(t), amplitude envelopes, σ_φ²(t), and Σ̄_φ(t).

| Model | Form | k |
|---|---|---|
| exponential | A·e^(−t/τ) | 2 |
| power law | A·(1 + t/t₀)^(−p) | 3 |
| damped oscillatory | g·A·e^(−t/τ)·\|cos 2πft\| + c | 4 |
| no change (null) | c | 1 |

Rules (binding):

1. All four models are fitted on every eligible trace; the full AIC/BIC table is published (schema requires exactly 4 rows). Winner = min AIC; **ΔAIC < 2 is a tie**; support for H-10 (exponential relaxation) additionally requires **ΔAIC ≥ 4 against the no-change null** AND τ_c stability across same-specimen repeat runs.
2. Eligibility: ≥ 3 windows on the falling segment; SNR > 3 after noise-floor subtraction; window w fixed before fitting with a mandatory sensitivity scan over ≥ 3 window lengths (a winner that flips with window choice is reported `ambiguous`).
3. The exponential form is the GAN Eq. (6) analogy **as a fit form only**; τ_c (and any rate λ) is a bench parameter; no numerical coefficient is ever imported (GAN-09; policy §3.5). Comparison plots follow the three-model layout of GAN-11 with the model set above.
4. H-11 (branch independence): τ_c fitted per branch at matched energy; the pre-registered criterion is overlap of combined-uncertainty intervals across electrode/coil/acoustic branches; disagreement reclassifies τ_c as a calibration term.

## 4. Model comparison for spectra (H-01/H-06a)

Compact spectrum f_n² = f_b² + (nκ_χ)² vs (a) linear ladder f_n = n·f₁, (b) plate law f_n ∝ n², (c) unconstrained per-mode fit. Discipline: train/test split of identified modes (fit on a pre-registered training subset, score on held-out modes by RMS and AIC); **scrambled-n label null** (≥ 1000 seeded permutations) controls look-elsewhere; H-01 requires the compact model to beat *every* simpler model on held-out performance AND to beat the scrambled null. Identifiability: report κ_χ (never v_χ and R_χ separately) unless H-06a supplies an independent spiral prior (RGCS-M.60).

## 5. Per-branch primary analyses (families)

| Family | Branch | Primary pre-registered analysis | Verdict tests in family |
|---|---|---|---|
| F1 | modal_survey | H-01 held-out comparison + scrambled null; H-01a coverage count; H-07 node interval | 3 |
| F2 | electrode_pulse | H-14 coherence re-adjudication vs detection limit; H-12 change point; H-13 Rayleigh; 19.8/20/21 contrast (estimation) | 3 |
| F3 | sound_key | H-02 within-linewidth vs FAR band contrast (d_c); key vs matched off-key contrast; H-14 | 3 |
| F4 | opposed_coil | H-14 vs no-crystal/rotated-coil controls; H-12; H-13; H-09 linear-null AIC; H-10 decay set | 5 |
| F5 | human_loading | H-08 repeatability tolerance SD(k_H) ≤ 0.002; ΔM_H cross-mode consistency; H-08b equivalence margin | 3 |
| F6 | spiral_cone | H-06 spiral > every control (one-sided, blinded, remount-bootstrap); H-06a prior-in-interval; H-05 ratio 2σ | 3 |
| F7 | water | Estimation-only: (active − sham) CIs per readout; blinded photo scoring κ | 0 (replication statement only) |
| F8 | spatial_mapping | H-03 swap-robust parity + scrambled null; H-10 on σ̄_φ(t); H-11 cross-branch τ_c | 3 |

## 6. Multiple-comparison control

1. **Families are fixed above.** Within each family, verdict-style tests use **Benjamini–Hochberg FDR at q = 0.05** over the listed comparisons; estimation outputs (CIs) are not corrected but are labeled with their family.
2. Secondary/exploratory analyses are unlimited in number but must be labeled `exploratory` (no `prereg_ref`) and can never produce `supported`/`refuted` status — only new pre-registrations.
3. Look-elsewhere in spectra and parity assignments is controlled by scrambled-label nulls (§4; RGCS-M.60 item 4), not by α adjustment alone.
4. Sweeps (ε-sweep, power ladder) are analyzed as single pre-registered curve contrasts (band contrast, change point), never as per-point tests.

## 7. Blinding and unblinding procedure

1. **What is blinded:** condition identity (active/sham/control), shape identity (spiral branch), key vs off-key labels, participant identity, and — for water — vessel condition. Blind codes live in `randomization.blind_code`; the code→condition map is held by the run coordinator, outside the analysis repository, in a sealed (hash-committed) file.
2. **Analysis freeze before unblinding:** peak extraction, exclusions (`decided_while_blinded: true`), window choices, and the primary estimator are computed and committed on blinded data. The commit hash is recorded.
3. **Unblinding event:** logged (date, analyst, commit hash of frozen analysis, sha256 of the code map). After unblinding, only the pre-registered estimators feed verdicts; any further analysis is exploratory.
4. **Sham-aware operators:** where operators cannot be blinded (they hear the speaker), instrument-facing blinding still applies: analysts never see condition labels before freeze.

## 8. Exclusions, missing data, stopping

- Only pre-registered exclusion criteria (per branch, EXPERIMENT_PROTOCOL.md) may remove runs; every exclusion is a manifest record with the criterion cited; excluded-run counts are published with every result.
- Runs are never partially excluded (no sample-range cherry-picking); artifact windows may be masked only via criteria in the artifact checklist, declared before analysis.
- **No optional stopping on significance.** Campaign sizes are fixed by the protocol; early stops are allowed only for safety or hardware failure and are reported.
- Sensitivity analysis: primary results re-computed with exclusions reversed; a verdict that flips is downgraded to `ambiguous`.

## 9. Detection limits and null claims

A null claim ("no effect") is always quantitative: "no effect exceeding X (95% CI upper bound) at detection limit Y (from the positive-injection control G-C)". The H-14 upgrade path — "amplitude-null AND coherence-null" — requires the coherence detection-limit test to have been run in the same campaign at the same settings.

## 10. Software and reproducibility

Reference implementations: `rgcs_core` (Agent 04) reproducing the golden values of `COHERENCE_TEST_MATRIX.md` before first use on data; analysis notebooks pinned by commit; seeds recorded for every bootstrap/permutation; all outputs emitted as `analysis_result.schema.json` instances (validated in CI by Agent 08).
