# RGCS v2 — Source Delta Report

**Author:** Sub-Agent 01 (Source Ingestion and Evidence Ledger)
**Date:** 2026-07-14

## Header: assumptions

1. Baseline = the v1.8 corpus (Vogel/JH package: manuscript v1.8, workbook v5 JH-audit, timing calculator v3, SCAD v5, 60-item curated findings) **plus** the existing v2 prototype (manuscript TEX, `rgcs_v2/core.py`, RGCS v2 workbook, app.py, SCAD v6), which already integrated Lee & Tsai.
2. "Delta" = what each of the three recent papers adds *beyond* what the baseline already contains, and what the baseline must change as a consequence.
3. Classification labels follow `SCIENTIFIC_CLASSIFICATION_POLICY.md`.

---

## 1. State of the baseline

**v1.8 (pre-paper) provided:** the 4096 harmonic length ladder; exact faceted/tapered/double-terminated volume model; density-constrained inverse sizing (Newton iteration on width scale); golden-angle audit (51.843° vs atan√φ, quantified mismatch 0.0157°); powers-of-eight ladder decoding with source-typo corrections; pulse phase-closure calculator (46/46/184 family, exact-cycle allocations 2261/1508/1131); apparatus audit (26 µH / 117 µJ inference, 62,415 e/s unit correction); unified least-squares objective J; human-loading first-order model; hyperbolic spiral-cone geometry with merit Γ_s = Q·|Λ|·rκ·P_c; JH audit (60 findings, eye-node separation, drive-branch separation, negative-result ledger, measurement matrix).

**v2 prototype (Lee–Tsai integration, already done) added:** compact-coordinate spectrum f_n² = f_b² + (nv_χ/2πR_χ)²; odd/even parity families; resonance level ε_R^(f); coupled two-mode eigenproblem + strong-coupling ratio; correction ledger framing ("radiative corrections" analogue); coupling merit S; Gradio app, workbook, SCAD v6, tests.

**Gap analysis of the baseline:** only ONE of the three reference papers is integrated. The v2 prototype's Lee–Tsai integration is broad but shallow (only Eqs. 9–10 and 13 are actually used; boundary conditions, radiative-correction structure, zero-mode exclusion, and the generic/dark-sector split are not documented). There is **no dynamics** (nothing evolves in time), **no anisotropy treatment** (v_L = 6310 m/s is used isotropically for a strongly anisotropic trigonal crystal), and **no coherence metric** (all planned observables are amplitude/frequency-based).

---

## 2. Delta from Lee & Tsai 2026 (beyond the existing shallow integration)

| # | Addition | Over baseline | Classification | Consequence |
|---|---|---|---|---|
| LT-Δ1 | Exact boundary-condition table (Table I) and mode decompositions (Eqs. 1–2): parity is *derived* from three-point boundary data (y=0, πR/2, πR), including the zero-flux removal of the n=0 mediator mode | Baseline treats parity as a cosmetic index filter (`n%2`) with no boundary-condition backing | Established math / Source claim (field content) | Math-foundations agent must state which RGCS boundary conditions would generate each family; core must support "no zero mode" flags; manuscript must stop implying parity is arbitrary |
| LT-Δ2 | Radiative-correction structure with explicit signs and forms: m′_B(2) shifts *down* (−g₁²ζ(3)/16π⁴R²), m′_E(1) shifts *up* (log term), so corrections *move ε_R through zero* | Baseline has a flat multiplicative correction ledger (1+Σδ) with no statement that corrections can flip the resonance sign | Established (given model) | Correction model must be signed and propagate into ε_R^(f) uncertainty; test: ε_R^(f) computed from corrected vs uncorrected frequencies |
| LT-Δ3 | Quantified resonance windows: 10⁻⁸–10⁻⁴ (self-interaction), 0<ε<δ≲0.5 (freeze-out), ε=1.25 as canonical non-resonant point | Baseline's class bins (10⁻⁴/0.01/0.1) were unexplained | Source claim (windows) / Derived (RGCS bins) | Bins must be re-derived from measured Q (linewidth), with the LT windows cited only as the template's convention; ε=1.25 adopted as far-detuned-control convention |
| LT-Δ4 | Coupling normalization g₁ = g₁^(5)/√L — coupling scales with compact geometry | Absent | Established | Predicts how fitted coupling g should scale when spiral/compact geometry changes; adds a falsifiable scaling test |
| LT-Δ5 | Explicit generic-vs-dark-sector split (kinetic mixing κ, axial-vector coupling, σ̄_e, relic abundance, SN1987A, detection experiments = NOT adaptable) | Baseline README/mapping gestures at this but has no enumerated exclusion list | Derived (audit) | SOURCE_EVIDENCE_LEDGER rows LT-10/18/19/20/21 become the canonical "not adapted" list; QA gate added |

## 3. Delta from Gan et al. 2025 (entirely new to the project)

| # | Addition | Over baseline | Classification | Consequence |
|---|---|---|---|---|
| GAN-Δ1 | Directional state formalism: Bianchi I three-scale-factor bookkeeping; per-axis rates Hᵢ; expansion/vorticity/shear kinematic decomposition | Baseline is entirely isotropic (single v_L=6310 m/s) despite quartz being trigonal with distinct axial/transverse velocities; no per-axis observables exist anywhere in v1.8/v2 | Established (decomposition) | New anisotropy module: three-channel measurement decomposition; math-foundations agent defines RGCS directional variables |
| GAN-Δ2 | Shear scalar σ² = (1/3)Σ(Hᵢ−Hⱼ)² as a single non-negative anisotropy metric; classical conservation baseline Σ² = (α₁₂²+α₂₃²+α₃₁²)/18, σ² ∝ a⁻⁶ | Nothing comparable in baseline | Established | Implement `shear_scalar`; golden tests G-15; gives RGCS its first quantitative anisotropy functional |
| GAN-Δ3 | Exponential damping result σ²(t) ≃ σ₀²e^{−σ₁t}, σ₁ ≃ 2.498 m_Pl, valid t ≳ 26 t_Pl, deep quantum regime | Baseline has no relaxation/dynamics model at all | Source claim (coefficient) / Established (fit form) | RGCS gains a *dynamic* coherence/anisotropy relaxation ansatz with fitted bench-scale rate λ; coefficient never imported |
| GAN-Δ4 | Matter-independence within modeled cases (dust, radiation, massless scalar, EKP, PCP all give the same exponent) | No cross-load invariance concept in baseline | Source claim (their models) | Test-design pattern: RGCS relaxation rate should be compared across drive branches; invariance would be a strong model signature, dependence a calibration term |
| GAN-Δ5 | Bounce/isotropization conditions: bounce replaces singularity (LQC t_B≈26 t_Pl, mLQC-I ≈24 t_Pl vs GR singularity ≈22 t_Pl); mLQC-I uniquely drives shear→0 ("perfect filter", snᵢ(t)→0); isotropization happens in the deep quantum regime independent of collapsing matter | None | Source claim | Only the *comparison methodology* (three models, identical initial conditions, Fig. 1 panel layout) is adopted; the bounce physics is explicitly not analogized |
| GAN-Δ6 | GR vs LQC vs mLQC-I divergence figures (Fig. 1 a–d, Fig. 2) | None | Source claim (data) | Template for RGCS null-model / partial-model / damped-model comparison plots |
| GAN-Δ7 | Bounded-variable regularization pattern (c → sin(μ̄c)/μ̄ with classical limit Eq. 1) | None | Established (technique) | Optional: saturating drive-response models cite this pattern; not required for v2 core |

## 4. Delta from Koster et al. 2026 (entirely new to the project)

| # | Addition | Over baseline | Classification | Consequence |
|---|---|---|---|---|
| KOS-Δ1 | Autocorrelation coherence metric: normalized |autocorrelation| of complex I/Q signal over sliding 100-ns boxcar window vs perfect-tone reference; dimensionless 0–1 | Baseline has *no coherence observable at all*; "coupling merit" and amplitude/Q are its only figures of merit | Established (signal processing) | New `coherence_value()` in core; the single most important new measurable for the RGCS measurement plan; window length is a declared analysis parameter |
| KOS-Δ2 | I/Q phase-referenced single-shot detection chain (shared 10 MHz reference, IQ mixer, LO, phase-locked generators, full parts list) | Baseline plans FFT/amplitude measurements only; phase-residue quantities (P_φ = cos²πρ) exist in the score but nothing can measure them | Established (technique) | Experiment-protocol agent gets a concrete reference architecture; RGCS phase quantities become measurable; parts-list discipline adopted |
| KOS-Δ3 | Random-phase ensemble concept + 1,000-shot phase histograms: per-run coherence with ensemble-uniform phase distinguishes spontaneous ordering from drive-imprinted response | Baseline has repetition counts but no ensemble phase statistics | Established (methodology) / Source claim (BEC interpretation) | N-run phase-histogram protocol (with uniformity test) added to all branches; this is the decisive control against "the drive did it" |
| KOS-Δ4 | Pumping → thermalization → free-evolution three-stage timing; condensation develops further *after* drive-off | Baseline acquisition windows end at drive-off | Source claim / Established (protocol) | All protocols extended ≥2.5× past drive-off; post-drive windows become primary analysis regions |
| KOS-Δ5 | Threshold behavior: coherence onset at ≈21 dBm *in their setup*; coherence saturates above threshold while amplitude keeps growing | Baseline has no threshold concept | Source claim (value) / Established (sweep methodology) | Drive-power sweeps with coherence as order parameter; thresholds always reported as setup-specific |
| KOS-Δ6 | Amplitude vs coherence distinction; coherence persists below amplitude-detection threshold (remanence at 3.5 µs) | Baseline null results (JH-015 "no singing", JH-031 plant test) were adjudicated on amplitude only | Source claim (their data) / Established (metric property) | Re-analysis mandate: RGCS null branches must be re-run/re-analyzed with the coherence metric before final null classification |
| KOS-Δ7 | Anisotropy/geometry dependence: bias-field orientation selects condensation wavevector (out-of-plane ⇒ k≈0); antenna width acts as spatial low-pass (factor-18 suppression of 18-µm modes under 100-µm antenna) | Baseline sensor plans ignore transducer spatial filtering | Source claim / Established (antenna filtering) | Sensor-size vs mode-wavelength correction enters the measurement model; crystal-orientation field required in schema |
| KOS-Δ8 | Half-frequency parametric pumping (f_p → f_p/2 pairs) | Baseline drive branches are all direct-frequency | Established (parametric excitation) | Optional new drive-branch class: parametric f/2 excitation with pair-phase bookkeeping |
| KOS-Δ9 | Artifact cross-validation (two independent measurement paths; known IQ artifacts listed at 3.77 GHz and 3.2–3.3 GHz) | Baseline measurement matrix lists artifact *sources* but no dual-path validation requirement | Established (methodology) | Dual-path validation gate for headline results |

## 5. Consolidated deltas the baseline must absorb (priority order)

1. **Coherence metric + I/Q ensemble protocol (KOS-Δ1..Δ3)** — highest priority: gives RGCS its first instrument-grade, domain-neutral order parameter and its decisive spontaneity control. Affects core (new module), schema, manuscript, tests.
2. **Anisotropy functional + relaxation dynamics (GAN-Δ1..Δ4)** — turns the static v2 into a dynamic model; fixes the isotropic-v_L blind spot. Affects math foundations, core, manuscript.
3. **Deepened LT integration (LT-Δ1, LT-Δ2, LT-Δ5)** — parity from boundary conditions, signed corrections propagating into ε_R^(f), and the enumerated not-adapted list. Affects math foundations, classification policy enforcement, manuscript traceability matrix.
4. **Protocol upgrades (KOS-Δ4..Δ7, GAN-Δ6)** — post-drive windows, power sweeps, dual-path validation, three-model comparison plots. Affects experimental-protocols agent.
5. **Null-result re-adjudication (KOS-Δ6 × RG-20)** — JH negative results ("no singing", plant test) must be re-classified as "amplitude-null, coherence-untested" pending coherence re-analysis. Affects manuscript and evidence ledger.

## 6. What none of the papers changes

- The 4096 Hz base-frequency choice remains purely a Source claim; no paper strengthens it.
- The spiral-cone hypothesis is untouched by all three papers (the spiral analogy predates them); its status stays Hypothesis with matched-control test plans.
- All human-loading, electrode, sound-key, and coil operating points remain Source claims from the JH corpus.
- No paper licenses any physical-equivalence claim between crystals and dark matter, quantum cosmology, or magnon condensates. The papers supply mathematics and measurement method only.
