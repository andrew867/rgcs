# RGCS v2 — Experiment Protocols

**Author:** Sub-Agent 06 (Experiments, Controls, and Data Schemas)
**Date:** 2026-07-14
**Version:** 1.0.0
**Status:** Pre-registered protocol set. Changes after first data acquisition require a versioned amendment; silent edits are non-compliant (policy §3.2).

**Normative references:** `SCIENTIFIC_CLASSIFICATION_POLICY.md` (labels), `NOTATION_AND_UNITS.md` (frozen symbols — all symbols below comply), `ROADMAP_TO_FALSIFICATION.md` (H-01..H-14), `DYNAMIC_COHERENCE_SPEC.md` §3 (drive/measurement contract — NORMATIVE here), `COHERENCE_METRICS.md` (COH-M1..M14), `STATISTICAL_ANALYSIS_PLAN.md` (analysis), `SAFETY_AND_ARTIFACT_CHECKLIST.md` (safety/artifacts), `DATA_SCHEMA.md` + `experiments/schemas/` (data), `experiments/controls/CONTROL_MATRIX.md` (controls).

---

## 0. Common requirements (apply to every branch)

### 0.1 Measurement contract (binding; DYNAMIC_COHERENCE_SPEC §3, KOS-05/12/13/14, KOS-11)

1. **Shared reference clock.** All generation and detection instruments lock to one reference; the run manifest records the derivation (`drive_config.reference_clock`, `acquisition.iq`). Phase or coherence claims from unshared-clock runs are non-compliant.
2. **Single-shot I/Q.** No averaging across excitation cycles before coherence analysis. Each shot is stored individually.
3. **N ≥ 100 runs** before any ensemble-phase (Rayleigh, COH-M4/RGCS-M.61) statement. KOS used 1000; N is a protocol parameter recorded per campaign.
4. **Acquisition window ≥ 2.5× past drive-off** for any coherence claim (`acquisition.post_drive.post_drive_ratio ≥ 2.5`). Runs below this ratio are amplitude-only.
5. **Controls precede attribution.** Instrument-only and no-crystal/no-specimen controls at identical settings must be complete before any coherence or enhancement claim (control matrix `required_before_claim` gates).
6. **Coherence reporting triplet.** Every coherence value ships as (𝒞_w, w, b_w) and ALWAYS alongside an amplitude report (COH-M5 contract; enforced by `analysis_result.schema.json` `dependentRequired`).
7. **Sensor geometry recorded per run.** Position and aperture of every sensor (`acquisition.channels[].position_xyz_mm`, `aperture_mm`); the aperture is a spatial low-pass filter on mode shapes (KOS-11; golden case (g)).
8. **Artifact register.** Each campaign maintains a known-instrument-artifact list (frequencies, conditions) referenced from every manifest (KOS-14).
9. **Thresholds are apparatus-specific.** No threshold from any other apparatus — in particular the KOS 21 dBm value — is ever a bench target, comparison point, or default (KOS-09; policy §3.5).
10. **Vocabulary.** Multi-channel disagreement metrics are called **spatial phase anisotropy** or **directional coherence disagreement** — never "quantum shear". No BEC/condensate/dark-sector vocabulary for RGCS quantities (policy §2).

### 0.2 Calibration gates (before any hypothesis test; ROADMAP ordering rule 1)

- **G-A Instrument phase-drift budget:** measured per session, recorded in `environment.instrument_phase_drift_deg` (KOS-13).
- **G-B Coherence baseline b_w:** measured on instrument-only noise for every window length used; window-sensitivity scan (≥3 window lengths) reported.
- **G-C Detection-limit injection:** known weak tone injected at the sensor; establishes the amplitude and coherence detection floors (KOS-10 test consequence; prerequisite for H-14 re-adjudication).
- **G-D Sensor calibration:** each channel carries a `calibration_ref` traceable to a dated calibration record.
- **G-E Correction-ledger stability:** repeated δ_k measurements stable before any ε_R^(f) interpretation (LT-13 consequence; gates H-02).

### 0.3 Statistics, exclusions, blinding (see STATISTICAL_ANALYSIS_PLAN.md)

Estimation-first: effect sizes with bootstrap CIs are the primary outputs; hypothesis tests use pre-registered α = 0.05 with per-family Benjamini–Hochberg control. Exclusion criteria are only those listed per branch below; exclusions are decided blinded where blinding applies and recorded in `run_manifest.exclusion`. All repeat counts below are honest **pilot-scale precision arguments**, not confirmatory power claims: no prior effect-size estimates exist for any RGCS hypothesis (all `untested`), so first campaigns estimate variances that future power calculations will consume.

### 0.4 Specimen and environment metadata (every run)

Specimen record per `specimen.schema.json` (geometry, mass measured vs predicted, orientation-known flag driving u_v, defects, photos with sha256). Environment per `environment.schema.json` (temperature start/end, humidity, pressure, ambient SPL, mains frequency, EMI note, fixture ID, phase-drift budget). Temperature enters the correction ledger δ_T (RGCS-M.45).

---

## 1. Branch 1 — Free crystal modal survey

**Template:** `experiments/templates/branch_01_modal_survey.template.json` · **Sample data:** `experiments/sample_data/modal_survey_*`

- **Research question.** What is the free modal spectrum (frequencies, Q_n, mode families, node positions) of each specimen, and does any identified mode family follow the compact spectrum f_n² = f_b² + (nκ_χ)² better than simpler models?
- **Hypotheses.** **H-01** (compact spectrum on held-out modes), **H-01a** (1D half-wave applicability: measured fundamental within f_ax·(1 ± u_v)), **H-03** (parity families via two-sensor phase), **H-04** (zero-mode presence/absence), **H-07** (node coordinate x̂_e vs shaft-midpoint prior x_g), **H-09 partial** (γ_n from free ringdown — identifiability gate for all driven branches).
- **Primary observables.** Peak frequencies f_n (Hz) with uncertainties; ringdown damping γ_n (s⁻¹) and Q_n; axial node coordinate x̂_e (mm, female-apex frame) with σ_x.
- **Secondary observables.** Two-sensor relative phase per mode (0 vs π parity assignment); mode-shape amplitude profile along the axial scan; mass check (measured vs predicted, RGCS-M.6).
- **Drive.** Instrumented tap (force channel recorded; energy < 10 mJ) at ≥ 5 axial stations, ≥ 6 taps per station; alternate excitation: non-contact swept sine 500 Hz–30 kHz at ≤ 74 dB(A) via speaker for Q refinement. No electrical drive.
- **Specimen metadata.** Full geometry record; ladder placement (N, L_target, k̃_H); orientation-known flag (if false, u_v = 0.05).
- **Environment.** §0.4 set; mount/fixture ID mandatory (fixture resonances are the dominant artifact).
- **Positive control.** A calibrated reference resonator (e.g., tuning bar with certificate or FEA-verified aluminum bar) measured each session: recovered f/Q within calibration tolerance.
- **Negative controls.** Fixture-only tap (no specimen); geometry-matched glass/printed dummy (separates geometry-generic from quartz-specific modes).
- **Sham/randomization/blinding.** Tap-station order randomized (seeded); compact-spectrum fitting performed with specimen identity and ladder-target labels masked; scrambled mode-index null mandatory for H-01 (RGCS-M.60 item 4).
- **Repeat count rationale.** ≥ 6 taps × 5 stations × 2 mount cycles per specimen: with 6 repeats the standard error of a peak frequency is √6 ≈ 2.4× below single-shot scatter, and 2 mount cycles bound mounting variance — the quantity that decides whether H-03 parity assignments are believable. Specimen count: ≥ 5 spanning the ladder (RG-21 presets) so H-01a has a majority criterion to fail on. Pilot status: variances from this branch feed all later power calculations.
- **Calibration.** G-A, G-D; tap-hammer force calibration; frequency axis verified against a counter or GPS-disciplined reference.
- **Data schema.** Run manifest + timeseries per `DATA_SCHEMA.md`; analysis via `analysis_result.schema.json` `fit` block (κ_χ, f_b reported — never separate v_χ, R_χ, per RGCS-M.60 identifiability gate).
- **Exclusion criteria (pre-registered).** Double-hit taps (force channel shows > 1 impulse); runs with fixture-band overlap flagged by the fixture-only control; temperature drift > 2 °C within a session.
- **Failure conditions.** H-01: compact model fails to beat linear ladder, plate law, AND unconstrained per-mode fit on held-out RMS/AIC, or survives label scrambling no better than chance. H-01a: majority of specimens outside f_ax·(1 ± u_v). H-03: parity assignments not reproducible across sensor placements. H-07: |x̂_e − x_g| > 2σ_x reproducibly (then x̂_e supersedes per RGCS-M.40).
- **Statistical analysis.** SAP §5.1: held-out model comparison (train/test split of modes, AIC + held-out RMS); bootstrap CIs on f_n, Q_n; circular statistics for parity phases.
- **Safety limits.** Tap energy < 10 mJ; never clamp crystal tips; eye protection when tapping; SPL ≤ 74 dB(A) for sweeps (checklist §2).
- **Artifact checks.** Fixture resonance overlay; sensor-mass loading (repeat one station with a lighter sensor; shift must be < peak uncertainty); aliasing check (fs ≥ 4× highest mode of interest); mount repeatability.

## 2. Branch 2 — 19.8/20/21 Hz electrode pulse branch

**Template:** `experiments/templates/branch_02_electrode_pulse.template.json`

- **Research question.** Does pulsed electrode drive (silver electrodes at the selected node, ~15 V sharp pulses at 19.8/20/21 Hz — all Source claims, RG-13) produce any control-surviving mechanical or charge response, and does coherence analysis change the verdict on the JH amplitude-null results?
- **Hypotheses.** **H-14** (re-adjudication of JH-015 progressive sequence with coherence metrics — primary), **H-12** (threshold-then-saturation vs drive level), **H-13** (spontaneous vs drive-imprinted phase), **H-11 contribution** (τ_c at matched energy vs other branches). The 19.8/20/21 Hz comparison itself tests the Source claim that 20 Hz is preferred — an estimation target, not an H-xx.
- **Primary observables.** Control-subtracted band amplitude at pulse harmonics and crystal modes; coherence triplet (𝒞_w, w, b_w) on drive and post-drive windows; G_c and d_c vs the dummy-electrode control.
- **Secondary observables.** Charge-amplifier response beyond the drive transient; ensemble phase distribution (Rayleigh Z_R, p); τ_c from post-drive decay (feeds H-11); response at parametric f/2 channels (bookkept per DC spec Stage I).
- **Drive (exact).** Pulse rate ∈ {19.8, 20, 21} Hz randomized across runs; amplitude ladder 5/10/15/20 V (15 V = source point); "sharp narrow pulse" realized as ≤ 1 ms rectangular pulse, rise ≤ 10 µs, recorded on the shunt channel; session 60 s drive + ≥ 150 s post-drive (ratio ≥ 2.5); electrodes at x_* (measured node from Branch 1, else x_g). The 9-step progressive sequence 10→550 Hz (5 s dwell, 20/40/60 V) is a sub-protocol replicating JH-015 with reverse/shuffled/direct-550 order controls (WB3).
- **Specimen metadata.** Branch 1 modal survey MUST precede this branch for each specimen (mode map + x̂_e are inputs).
- **Environment.** §0.4 set; electrode contact force/area recorded; specimen temperature monitored (stop > 5 °C rise).
- **Positive controls.** Injection detection-limit test (G-C); a piezo-driven known response at a crystal mode verifying the sensing chain end-to-end.
- **Negative controls.** Instrument-only (pulser into shielded RC dummy); dummy electrodes on a glass blank (direct-pickup path); no-crystal energized jig; sham (relay-open, 0 V, full procedure).
- **Sham/randomization/blinding.** Rate (19.8/20/21) and condition (active/sham/dummy) drawn from seeded RNG; analyst sees coded condition labels until SAP §7 unblinding.
- **Sample size rationale.** N = 100 runs per (rate × level) cell is not feasible initially; pilot design: N = 100 runs at the source point (20 Hz/15 V) for ensemble-phase statistics (Rayleigh detectable R̄ ≈ √(3/N) ≈ 0.17 at α = 0.05), plus N = 20 per remaining cell for amplitude/coherence estimation (bootstrap CI half-width ≈ 0.46·SD). Honest status: powered to detect only moderate-to-large effects; a null here is a precision statement, not proof of absence — except for H-14, where the pre-registered detection limit (G-C) makes "coherence-null" quantitative.
- **Calibration.** G-A..G-E; shunt and charge-amp calibration; pulse shape verified on scope before each session.
- **Data schema.** Manifest with `drive_config.pulse`; I/Q channels per contract; JH-replication runs flagged via `hypothesis_ids: ["H-14"]`.
- **Exclusion criteria.** Electrode contact resistance drift > 20% within a run; visible arcing (also a stop condition); mains-transient contamination flagged on the shunt channel.
- **Failure conditions.** H-14: if coherence analysis of the replicated JH-015 branches is also null at the measured detection limit, the negative result upgrades to "amplitude-null AND coherence-null" (strong null); if coherence detects order, the amplitude-null label was incomplete. H-12: no reproducible change point across the level ladder. H-13: ensemble phase locks to drive phase (Z_R, p < α) ⇒ response is *driven*; "spontaneous" vocabulary forbidden for that result.
- **Statistical analysis.** SAP §5.2/5.4: estimation of G_c, d_c per cell with bootstrap CIs; COH-M12 change-point for H-12; COH-M4 for H-13; COH-M14 four-model comparison on post-drive traces; family F2 multiplicity control.
- **Safety limits.** ≤ 60 V ceiling, current-limited supply ≤ 100 mA; no human contact with energized electrodes; silver-electrode handling per checklist §1; enclosure for > 24 V runs.
- **Artifact checks.** Direct electrical pickup (dummy-electrode subtraction is mandatory, not optional); ground-loop audit; pulse-harmonic comb overlap with crystal modes documented before interpretation; charge-amp microphonics test.

## 3. Branch 3 — 1496/644/587 Hz non-contact sound-key branch

**Template:** `experiments/templates/branch_03_sound_key.template.json`

- **Research question.** Do the source "sound keys" (1496 Hz primary; 644/587 Hz alternates; 3 s ON/3 s OFF ×4 + 12 s pause — Source claims, RG-13) produce specimen responses that exceed SPL-matched off-key tones, and does any enhancement localize where ε_R^(f) → 0 for identified mode pairs?
- **Hypotheses.** **H-02** (enhancement localizes near ε_R^(f) = 0: sweep the key frequency through an identified mode with sign-resolved ε), **H-12**, **H-14** (JH keys were amplitude-assessed by ear/absence — re-run with coherence), **H-11 contribution**.
- **Primary observables.** Control-subtracted modal amplitude gain G_c and effect size d_c: key vs SPL-matched off-key; coherence triplet on drive/post-drive windows; ε-resolved response curve (WITHIN-LINEWIDTH |ε| ≤ ε_Q band vs FAR band, far-detuned convention ε = 1.25 per LT-20).
- **Secondary observables.** Q and node-position shift under acoustic load; macrocycle-locked amplitude modulation; ensemble phase.
- **Drive (exact).** Speaker at 150 mm, on-axis with the node region; key presets 1496/644/587 Hz with 3/3/4/12 s macrocycle (36 s); measured SPL at specimen position 60–74 dB(A), matched within ±0.5 dB across conditions via reference mic; off-key comparators pre-registered: f_key·(1 ± 0.10) and the geometric midpoints between keys; fine ε-sweep: 21 points across ±3 linewidths of the nearest identified mode. Post-drive acquisition ≥ 2.5× (session 36 s → record ≥ 126 s).
- **Specimen metadata.** Requires Branch 1 mode map; the mode nearest each key documented with Q (defines ε_Q band).
- **Environment.** §0.4 set + room acoustic note; reflective-surface geometry photographed (standing waves are a leading artifact).
- **Positive controls.** Speaker driving a reference resonator with known response; injection detection-limit test.
- **Negative controls.** Speaker-only (specimen removed, sensor on empty mount) — acoustic leakage floor; matched-SPL off-key runs (the decisive comparison); sham (muted amplifier, full timing).
- **Sham/randomization/blinding.** Key vs off-key condition order seeded-random; analyst blinded to key/off-key labels; SPL matching verified before unblinding.
- **Sample size rationale.** Paired design (each specimen serves as its own control across conditions): n = 20 key/off-key pairs per key detects a paired standardized effect d ≈ 0.65 at α = 0.05, power 0.8 (two-sided) — pre-registered as the smallest effect this pilot can rule in/out; smaller effects yield CIs, not verdicts. N = 100 shots at the primary key (1496 Hz) for ensemble-phase statistics.
- **Calibration.** G-A..G-D; reference-mic SPL calibration (94 dB calibrator); speaker THD measured (harmonics of 644/587 land near other modes — artifact register entry).
- **Data schema.** `drive_config.sound_key` block; SPL at specimen mandatory.
- **Exclusion criteria.** SPL match failure > 0.5 dB; ambient SPL intrusion > 10 dB below drive; specimen temperature drift > 2 °C.
- **Failure conditions.** H-02: no localized increase of d_c within the within-linewidth band relative to the FAR band at pre-registered α. Key-preference (Source claim audit): key does not beat matched off-key comparators ⇒ recorded as "no key-specific effect at the stated detection limit". H-12/H-14 as in Branch 2.
- **Statistical analysis.** SAP §5.2: paired estimation with bootstrap CIs; ε-band contrast (within-linewidth vs far) as the pre-registered H-02 test; family F3.
- **Safety limits.** SPL ≤ 85 dB(A) continuous at operator position; hearing protection above; ≤ 100 dB(A) absolute ceiling at specimen, never with persons < 1 m (checklist §2).
- **Artifact checks.** Acoustic leakage into sensor cabling (speaker-only subtraction); room standing waves (move specimen 50 mm, effect must survive); speaker harmonic distortion overlap; sensor-mount airborne coupling.

## 4. Branch 4 — 4096 Hz opposed-coil branch

**Template:** `experiments/templates/branch_04_opposed_coil.template.json` · **Sample data:** `experiments/sample_data/opposed_coil_*`

- **Research question.** Does the opposed copper/silver coil drive (4096 Hz carrier, complementary 180°, microsecond pulses, envelope families 46/46/184, 46/23/92, 23/23/92 — Source claims, RG-12/RG-14) produce any crystal response that survives no-crystal, dummy-load, and rotated-coil controls — specifically re-adjudicating the JH-033 "minute signals attributed to drive pickup"?
- **Hypotheses.** **H-14** (JH-033/coil-branch re-adjudication — primary), **H-12** (threshold vs voltage ladder), **H-13** (spontaneity), **H-09** (ring-up/saturation envelope fits; K_nm vs g_nm consistency), **H-10** (post-drive decay-law adjudication), **H-11 contribution**.
- **Primary observables.** Control-subtracted response in crystal-mode bands (contact mic I/Q at LO = 4096 Hz and at identified modes); coherence triplet drive-on and post-drive; coil current waveform (energy accounting).
- **Secondary observables.** Hall/TMR field map channel; charge-collector channel beyond drive transient; ring-up/ringdown envelopes (H-09 fits); f/2 and 2f parametric bookkeeping.
- **Drive (exact).** Carrier 4096 Hz square, two outputs 180° (complementary non-overlap, dead-time verified on scope); pulse width 1–4 µs (source range; 1.3 µs at the 101 mm point), voltage ladder 20/30/45/60 V (45 V = as-built point, 60 V = 101 mm point), peak current ≤ 3 A; envelope families with exact-cycle allocations 2261 = 754+754+753 / 1508 = 754+377+377 / 1131 = 377+377+377 (G-12); coils 40+40 turns (21+21 replication sub-protocol for the 101 mm configuration), 0.33 mm wire; inductance MEASURED per coil (the 26 µH figure is an inference — RG-14 "measure, don't infer"); macrocycle count per run recorded; acquisition ≥ 2.5× past drive-off.
- **Specimen metadata.** Branch 1 prerequisite; coil-pair axial position recorded as drive_x_mm.
- **Environment.** §0.4 set; coil temperature channel; MOSFET/driver temperature.
- **Positive controls.** Injection detection-limit test; current-loop-driven known mechanical response (small shaker) through the same analysis chain.
- **Negative controls.** Instrument-only; no-crystal energized coils (JH-033 pickup floor — mandatory subtraction); resistor dummy load at matched delivered energy; rotated-coil runs (field-orientation vs fixed-geometry pickup).
- **Sham/randomization/blinding.** Condition order seeded-random; envelope family randomized within sessions; analyst blinded to condition codes.
- **Sample size rationale.** N = 120 shots at the primary point (45 V, standard envelope) — satisfies N ≥ 100 ensemble-phase floor with 20% exclusion headroom; N = 25 per remaining (voltage × envelope) cell for estimation (CI half-width ≈ 0.41·SD). Threshold claim (H-12) additionally requires day-repeat: full ladder on ≥ 3 days; a change point not reproduced across days is not a threshold (KOS-09 rule, COH-M12).
- **Calibration.** G-A..G-E; current-probe and Hall calibration; coil L/R measured before each campaign; switching-transient spectrum registered (artifact list).
- **Data schema.** `drive_config.coil` + `envelope` blocks mandatory; I/Q channels with LO derivation; per-shot files with run_index.
- **Exclusion criteria.** Shoot-through events (both gates high — also a stop condition); coil temperature rise > 10 °C; drive-current waveform deviating > 5% RMS from the session reference.
- **Failure conditions.** H-14: response indistinguishable from no-crystal control at the detection limit ⇒ "amplitude-null AND coherence-null" for this branch (upgrading JH-033); any surviving signal must beat the rotated-coil control before being called crystal response. H-09: linear null (β = K = 0) fits saturation data as well (ΔAIC < 2) as the full model, or K_nm ≠ π·g_nm beyond 2σ. H-10: exponential not preferred over the constant null by ΔAIC ≥ 4, or τ_c unstable across same-specimen repeats. H-12/H-13 as in Branch 2.
- **Statistical analysis.** SAP §5.3/5.4: COH-M14 four-model comparison (exponential/power-law/damped-oscillatory/no-change) on post-drive 𝒞_w(t) and σ̄_φ(t); COH-M12 bootstrap threshold; Stuart–Landau envelope fits for H-09; family F4.
- **Safety limits.** ≤ 60 V / ≤ 3 A absolute (source range ceiling); staged power ramp (logic-only → 5 V → 12 V → 24 V → enclosed full power, exit criteria per checklist §3); snubber/TVS on the half-bridge; no human contact with powered coil; enclosure above 24 V.
- **Artifact checks.** Switching-transient pickup (dummy-load subtraction); magnetic coupling into sensor cables (rotated-coil + cable-dress test); charge-amp saturation during pulses (blanking documented); event-rate assumption audit (one vs two pulses per carrier period — RG-14 hidden-assumption flag); IQ image/LO-leakage artifacts registered per KOS-14.

## 5. Branch 5 — Human/fixture loading

**Template:** `experiments/templates/branch_05_human_loading.template.json`

- **Research question.** Are free→held frequency shifts under a defined contact protocol repeatable, first-order describable as added modal mass, and is the length-shortfall proxy k̃_H a usable stand-in for measured k_H?
- **Hypotheses.** **H-08** (loading is first-order added modal mass; k_H < 1; ΔM_H consistent across modes), **H-08b** (k̃_H ≈ k_H on a deliberately short-cut specimen).
- **Primary observables.** k_H = f_loaded/f_free per mode (measured ratio — Established); shift repeatability variance across repeats, participants, and days.
- **Secondary observables.** Q change under loading; ΔM_H per mode (Hypothesis-conditioned on η; reported only with the η caveat or after the two-loading protocol of RGCS-M.60); contact force/area.
- **Drive (exact).** Tap excitation ONLY (Branch 1 parameters). **No electrode, coil, or high-SPL acoustic drive is ever energized during human contact** (hard safety rule + schema gate `no_energized_contact_confirmed`).
- **Specimen metadata.** Branch 1 free-mode baseline same-day; for H-08b, one specimen deliberately cut short (k̃_H = L_actual/L_target recorded at intake).
- **Environment.** §0.4 set + hand-temperature note (thermal drift mimics loading shifts); repeat free measurement interleaved between held measurements (ABA design).
- **Positive control.** Calibrated added masses (2/5/10 g clamped at defined positions): recovered ΔM within calibration tolerance validates the modal-mass pipeline before any human data are interpreted.
- **Negative controls.** Fixture-only loading at matched contact area/force; surrogate load (gel/saline phantom); glove vs bare-hand comparison.
- **Sham/randomization/blinding.** Condition order (free/held/fixture/surrogate) randomized per session; analyst blinded to participant identity and condition during peak extraction.
- **Sample size rationale.** ABA design, ≥ 10 held repeats per participant per specimen, ≥ 3 participants, ≥ 2 days: 10 repeats give a CV estimate with 95% CI within ±0.23·CV, enough to state whether the protocol tolerance (pre-registered: SD(k_H) ≤ 0.002) is met — the H-08 repeatability criterion. Pilot status explicit: participant count bounds only gross inter-person variance.
- **Calibration.** G-A, G-D; calibrated masses (±0.01 g); force sensor for grip-force band.
- **Data schema.** `run_manifest.human_loading` block REQUIRED (schema-enforced): ethics reference, contact protocol ID, pseudonymous participant code, glove condition. No personal data in any file.
- **Exclusion criteria.** Grip force outside the protocol band; hand repositioning mid-run; free-baseline drift between ABA legs > 0.5× the held shift.
- **Failure conditions.** H-08: shifts not repeatable within protocol tolerance; or k_H > 1 observed (stiffness regime — model rejected as stated); or ΔM_H inconsistent across modes beyond fit uncertainty. H-08b: |k̃_H − k_H| > u(k_H) ⇒ proxy retired to design heuristic.
- **Statistical analysis.** SAP §5.5: variance-component estimation (repeat/participant/day); regression of Δf against added-mass predictions; equivalence-style reporting for H-08b (CI on k̃_H − k_H vs pre-registered margin).
- **Safety and ethics (binding).** **Human-subject boundary:** this is a NON-CLINICAL bench procedure — a volunteer holds an undriven crystal; no physiological measurement, no health-related claim, no therapeutic framing is permitted in any artifact (policy §2 extension). Ethics review (institutional IRB-equivalent, or documented exemption where applicable) is REQUIRED before any participant contact; informed-consent record kept outside the data repository; participants may withdraw at any time with data deletion. Electrical safety: participants never touch energized hardware; only SELV (< 25 V AC/60 V DC, current-limited) equipment may even be present on the bench during sessions, and all drive outputs are hardware-interlocked off.
- **Artifact checks.** Thermal shift control (hand warmth: compare glove/surrogate); fixture compliance; sensor cable damping changes when a person is near the bench (proximity capacitance test).

## 6. Branch 6 — Spiral-cone versus matched controls

**Template:** `experiments/templates/branch_06_spiral_cone.template.json`

- **Research question.** Does the log-spiral cone resonator outperform mass-, material-, and thickness-matched control shapes on the pre-registered response observable, and does the spiral path length predict fitted mode spacing?
- **Hypotheses.** **H-06** (spiral beats every matched control on the pre-registered observable), **H-06a** (spiral-derived κ_χ prior — mean R_χ^(s) vs per-turn R_χ,k — falls within the fitted κ_χ interval), **H-05** (coupling scaling g(R₁)/g(R₂) = √(R₂/R₁) under controlled geometry change).
- **Primary observable (pre-registered, single).** Control-subtracted apex/cusp gain G_c at the strongest common resonance band, with d_c. Everything else is secondary.
- **Secondary observables.** Full transfer spectra; Q per shape; nodal map; fitted κ_χ vs spiral priors (H-06a); avoided-crossing splitting before/after geometry change (H-05).
- **Drive (exact).** Contact transducer at the base, swept sine 200 Hz–20 kHz, 200 Hz/s, randomized sweep direction; identical mounting jig, torque-controlled clamps; drive level recorded and matched across shapes (±0.2 dB).
- **Specimen metadata.** Spiral: q = e, T = 4, R₀ = 60 mm, H = 80 mm, p_z = 1.5 (design choices, RG-08); ℓ_3D from converged polyline (tolerance 10⁻⁶, RGCS-M.35) recorded per as-built part; controls: disk, plain cone, Archimedean spiral, flat log spiral — matched in mass (±2%), material lot, and wall thickness (RG-08 set).
- **Environment.** §0.4 set; jig ID; remount count.
- **Positive control.** Reference resonator through the same jig each session.
- **Negative controls.** The four matched shapes ARE the controls; plus jig-only sweep.
- **Sham/randomization/blinding.** Shape identity coded at fabrication; sweeps run and analyzed blind to shape; measurement order randomized; unblinding after the primary estimator is locked (SAP §7).
- **Sample size rationale.** ≥ 8 remount-sweep repeats per shape: mounting variance is the known killer (RG-08 fabrication/mounting uncertainty); 8 repeats bound the remount SD with 95% CI within ±0.28·SD and give a paired spiral-vs-control comparison detecting d ≈ 1.1 at power 0.8 — appropriate for a pilot expected to find either a clear win or a null; ≥ 2 fabrication replicas per shape guard against unit-specific accidents.
- **Calibration.** G-A, G-D; transducer response flattened by reference sweep; jig torque calibration.
- **Data schema.** Specimen `spiral` block (including `matched_control_shape` for controls); one manifest per shape per remount.
- **Exclusion criteria.** Clamp torque out of band; visible part damage; sweep-level drift > 0.2 dB.
- **Failure conditions.** H-06: spiral does not beat EVERY matched control on the primary observable (pre-registered, one-sided) — partial wins are recorded as failure with the ranking published. H-06a: neither spiral prior falls in the fitted κ_χ interval, or per-mode fit beats both priors without penalty. H-05: measured coupling ratio differs from √(R₂/R₁) beyond 2σ.
- **Statistical analysis.** SAP §5.6: blinded ranked comparison with remount-level bootstrap; κ_χ prior-vs-fit interval logic; family F6.
- **Safety limits.** Contact transducer ≤ 5 W; sharp metal edges (handling gloves); SPL limits as Branch 3 if airborne drive is added.
- **Artifact checks.** Mass/thickness mismatch audit before data (weigh + ultrasonic thickness map — mismatch is the registered failure mode from WB2); jig resonance overlay; transducer-bond repeatability.

## 7. Branch 7 — Water branch

**Template:** `experiments/templates/branch_07_water.template.json`

- **Research question.** Do the JH-reported water observations (clouding, bubbles, solubility changes in dissolved-silica / saturated salt water after ~10 min of 4096 Hz acoustic exposure near a crystal — Source claims, JH pp.234–237, 252–253) survive blinded, randomized, physically-accounted controls?
- **Hypotheses.** None of H-01..H-14 — this branch is **pre-registered as estimation-only / adversarial replication** (`hypothesis_ids: ["EXPLORATORY"]`). Any positive finding generates a new hypothesis with its own pre-registration before confirmatory claims; nothing here can "support" existing RGCS hypotheses.
- **Primary observables.** Pre/post differences: temperature-corrected conductivity (µS/cm), pH, dissolved-oxygen proxy, mass (evaporation-accounted), turbidity/UV-Vis absorbance.
- **Secondary observables.** Photographic bubble/clouding record (blinded scoring by two raters); water temperature trace; SPL in-vessel (hydrophone).
- **Drive (exact).** 4096 Hz sine via speaker, 10 min continuous, SPL at vessel matched across conditions; crystal-present vs crystal-absent factorial; vessel at fixed geometry from speaker and crystal.
- **Specimen metadata.** Vessel record (`specimen.water` block): volume, solute, preparation log, sealed flag, vessel material/lot; crystal record as secondary specimen.
- **Environment.** §0.4 set + `environment.water_baseline` (pre-run pH/conductivity/temperature/mass) mandatory.
- **Positive controls.** Ultrasonic-cleaner exposure at matched acoustic power (known cavitation/degassing comparator); deliberate 1 °C heating (validates that the chemistry readouts detect small real changes).
- **Negative controls.** Sham (muted, full handling); thermal control matched to measured drive heating; evaporation control (sealed/open pairs); crystal-absent runs at identical field.
- **Sham/randomization/blinding.** Vessels prepared identically in batches, assigned to condition by seeded RNG, labeled with codes; all chemistry readouts and photo scoring completed before unblinding.
- **Sample size rationale.** 6 vessels per condition × 4 conditions (active, sham, thermal, crystal-absent) per batch, ≥ 2 batches: with n = 6, a between-condition difference of ~1.3 SD is detectable at power 0.8; primary output is the CI on (active − sham) for each chemistry readout. Pilot; explicitly not powered for subtle effects.
- **Calibration.** pH 2-point and conductivity calibration each batch; balance ±0.01 g; hydrophone SPL check.
- **Data schema.** Slow-channel CSV (1 Hz) + pre/post chemistry in the manifest; photos with sha256.
- **Exclusion criteria.** Vessel contamination (visible particulate at pre-check); temperature-control failure > 0.5 °C between paired vessels; seal failure in sealed condition.
- **Failure condition.** (active − sham) CIs include zero for all readouts AND blinded photo scoring shows no condition separation ⇒ recorded as "not replicated under controls at the stated precision"; the Source claim keeps its Source-claim label either way — this branch can only fail to replicate it or generate a new pre-registerable hypothesis, never "confirm" it as stated.
- **Statistical analysis.** SAP §5.7: estimation-only (CIs, no NHST verdicts beyond the pre-registered replication statement); inter-rater agreement (Cohen's κ) for photo scoring; family F7.
- **Safety limits.** SPL as Branch 3; saturated salt solutions handled with eye protection; no ingestion-related framing anywhere (non-clinical rule); electrical equipment away from liquids, RCD/GFCI-protected outlets.
- **Artifact checks.** Cavitation/degassing (ultrasound comparator); evaporation accounting; temperature-driven solubility (thermal control); vessel-lot chemistry variance (batch design); electrode drift on pH/conductivity meters (re-calibration mid-batch).

## 8. Branch 8 — Multi-sensor spatial phase/coherence mapping

**Template:** `experiments/templates/branch_08_spatial_mapping.template.json`

- **Research question.** Do simultaneous multi-station phase records on a driven crystal show measurable **spatial phase anisotropy** (directional coherence disagreement), how does it relax after drive-off, and are parity-family assignments reproducible?
- **Hypotheses.** **H-03** (parity via multi-sensor phase, sensor-swap-robust), **H-10** (Σ̄_φ(t) relaxation: exponential vs alternatives), **H-11** (τ_c branch-independence at matched energy — this branch performs the cross-branch comparison), **H-13** (ensemble spontaneity with spatial resolution).
- **Primary observables.** σ_φ² (phase-rate shear scalar, rad²/s², RGCS-M.52 — GAN Eq. (2) adaptation, mathematical analogy only); Σ_φ tensor and scalar reduction Σ̄_φ (RGCS-M.53); their post-drive time courses; per-channel coherence triplets.
- **Secondary observables.** Per-station parity phases (0/π) per mode; PLV between station pairs (COH-M11); per-channel V_j, R̄_j; amplitude maps.
- **Drive (exact).** Reuses Branch 2/3/4 drive configurations unchanged (this branch is a measurement overlay); matched-energy groups across the three drive branches for H-11 (`drive_config.energy.matched_energy_group_id`); acquisition ≥ 2.5× past drive-off, single-shot, N ≥ 100 at the primary configuration.
- **Sensors (exact).** ≥ 3 axial stations + ≥ 1 circumferential station, identical sensor models; positions and apertures recorded per run; aperture ≤ 1/4 of the shortest expected mode wavelength at the highest analysis frequency, else the spatial low-pass correction is documented (KOS-11).
- **Specimen metadata.** Branch 1 mode map required (station placement is chosen relative to predicted node/antinode pattern and documented BEFORE acquisition).
- **Environment.** §0.4 set; inter-channel timing skew measured (< 1 sample).
- **Positive control.** Common-signal injection to all channels: σ_φ² must read ≈ 0 (golden case (g) small-contrast leg) — validates that anisotropy is not fabricated by the pipeline.
- **Negative controls.** Instrument-only on a rigid dummy bar (inter-channel phase budget); channel-label scrambling null (H-03); drive-branch negative controls inherited from the underlying branch.
- **Sham/randomization/blinding.** Sensor-swap and reposition schedule randomized; analyst blinded to station identity during parity assignment.
- **Sample size rationale.** N = 120 shots at the primary configuration (ensemble floor + headroom); sensor-swap repeats: full map × 3 swap permutations — a parity assignment must survive all permutations (H-03 criterion is reproducibility, not significance); H-11: ≥ 3 matched-energy groups × 3 branches, τ_c compared with combined fit uncertainty.
- **Calibration.** G-A..G-D per channel; inter-channel phase calibration with common injection at 3 frequencies spanning the analysis band, repeated per session.
- **Data schema.** One multi-column timeseries file per shot (all stations synchronous); `analysis_result.spatial_phase_anisotropy` block; windowed phase-rate parameters (w, hop) recorded.
- **Exclusion criteria.** Inter-channel skew > 1 sample; any channel SNR < 3 in the analysis band (COH-M14 rule); sensor detachment (impedance check fails).
- **Failure conditions.** H-03: parity assignments change under sensor swap/reposition or are indistinguishable from the scrambled-label null. H-10: exponential not preferred over the constant (no-change) null by ΔAIC ≥ 4 on Σ̄_φ(t), or τ_c unstable across same-specimen runs. H-11: τ_c differs across matched-energy branches beyond combined fit uncertainty ⇒ τ_c reclassified as a calibration term, not a model signature. Common-injection control failure (σ_φ² not ≈ 0) invalidates the session.
- **Statistical analysis.** SAP §5.8: COH-M13 estimation with window-sensitivity scan; COH-M14 four-model comparison on σ̄_φ(t) and σ_φ²(t) (three-model comparison PLOT layout per GAN-11, models per COH-M14); cross-branch τ_c meta-comparison; family F8.
- **Safety limits.** Inherited from the underlying drive branch.
- **Artifact checks.** Channel gain/phase mismatch (swap control); crosstalk between channels (single-driven-channel test); aperture spatial aliasing (reposition control); common-mode pickup masquerading as isotropic rate (h̄ reported separately from anisotropy).

---

## 9. Cross-branch ordering

1. Calibration gates §0.2 (per campaign/session).
2. Branch 1 (modal survey) per specimen — prerequisite for Branches 2, 3, 4, 5, 8.
3. Branches 2/3/4 in any order; Branch 8 overlays them; matched-energy groups scheduled across branches for H-11.
4. Branch 5 requires ethics sign-off; Branch 6 and 7 independent.
5. No coherence/enhancement claim on any branch before that branch's `required_before_claim` controls are `done` (control matrix gate).
