# Validation Plan (Agent 14) — ENG

The campaign-level plan: statistics, acceptance/failure criteria, and
the complete per-hypothesis table. It restates and instantiates the
pre-registered rows of `CLAIM_REGISTER.md` /
`ROADMAP_TO_FALSIFICATION.md`; where wording differs, the registers
win. Outcome vocabulary (LAB_MANUAL §7): CONFIRMED-within-band, NULL,
FAILED, ARTIFACT — nothing else.

## 1. Statistical methods (inherits v2 SAP; summarized)

- **Pre-registration:** every test below is fixed before unblinding;
  the seed, sweep, and analysis section are committed pre-session.
- **Estimates over verdicts:** effect sizes with 95 % CIs are always
  reported alongside any test decision.
- **Tests:** paired differences → paired t / Wilcoxon (normality
  check decides, pre-registered); ensemble phase order → Rayleigh Z
  (RGCS-M.61); model comparison (ladder fits, decay forms) → AICc on
  held-out modes/points, Δ AICc ≥ 4 to prefer the richer model;
  changepoint (H-12) → pre-registered segmented fit vs no-break, F-test.
- **α = 0.01** per confirmatory test; within each phase,
  Holm–Bonferroni across that phase's confirmatory family.
- **Null claims** (H-21, H-23, and any NULL outcome elsewhere) are
  quantified by **equivalence bounds (TOST)**: the null is *accepted*
  (not merely "not rejected") only when the 90 % CI of the effect lies
  inside the pre-registered equivalence band stated in the table.
- **Power:** confirmatory blocks are sized for ≥ 0.9 power at the
  band edge (n ≥ 20 pairs for paired designs; n ≥ 100 shots for
  ensemble-phase claims — the KOS gate is also a power floor).
- **Coherence reporting:** 𝒞_w always as the triplet (value, window,
  baseline) beside an amplitude report (v2 contract; enforced by the
  analysis_result schema).

## 2. Campaign acceptance and failure criteria

**Phase gates:** Phase 0 passes only on H-29 PASS + H-30 PASS + full
calibration chain green. Any later phase runs only under an in-date
Phase 0.

**Campaign-level acceptance** (the platform is "experimentally
grounded") — ALL of:
1. every hypothesis row H-01..H-30 adjudicated to one of the four
   outcomes with its pre-registered analysis (NULL and FAILED count as
   full adjudications — grounding ≠ confirmation);
2. uncertainty budget attached to every reported quantity;
3. all controls for claimed effects complete (v2 KOS-13 gate);
4. registers updated; every ARTIFACT has a defect row.

**Campaign-level failure criteria** — ANY of:
- the bench cannot hold the H-29 gate across sessions (phase claims
  impossible → campaign halts at Phase 0, reported as such);
- an effect survives its in-protocol controls but is later traced to
  the bench (ARTIFACT after unblinding) **twice for the same row** —
  that row is frozen ARTIFACT and the fixture redesigned before retry;
- any safety-envelope breach → immediate campaign stop, incident
  report, restart only after a documented cause and fix.

**Honesty criterion:** a campaign in which most physics rows end NULL
or FAILED is a *successful* campaign if the adjudications are clean.

## 3. Per-hypothesis validation table

Legend: Obs = observable; Meas = measurement; Exp = pre-registered
expected result; Null = the null result and its equivalence band;
Ctrl = controls; Conf = confidence metric. Full failure conditions:
the registers.

### Phase I — acoustic/modal

| H | Obs | Meas | Exp | Null | Ctrl | Conf |
|---|---|---|---|---|---|---|
| **H-01** | mode-family frequencies vs f_n² = f_b² + (nκ_χ)² | modal survey ladder fit vs plain-rod baseline | compact fit beats rod on ≥ 3 held-out modes | rod fits equally well (ΔAICc < 4) → H-01 FAILED, scalar retained | support-shift, sensor-swap, second specimen | ΔAICc ≥ 4 + residuals < f-uncertainty |
| **H-01a** | free fundamental vs 1D f_ax band | tap + sweep fundamental | inside the band (oriented speed if orientation measured; else scalar ±5 %) | outside band → 1D model rejected for that geometry class | FEA cross-prediction, 2 specimens | band coverage w/ 2 ppm+bin f-uncertainty |
| **H-03** | two-sensor relative phase per mode | phase at matched stations | families at 0 vs π matching assignment | phases neither 0 nor π beyond 2° budget → parity model FAILED | sensor swap + station swap | phase ± 2°, ≥ 5 modes |
| **H-04** | presence of n = 0 member | low-frequency search below f_b | as flagged per specimen registry | flagged-present but absent (or inverse) → flag corrected in registry | second sensor type | detection SNR ≥ 10 dB or bounded absence |
| **H-07** | displacement-node location | 2 mm axial scan amplitude/phase map | measured node; midpoint prior x_g only a prior | node ≠ x_g is NOT a failure — measured supersedes (H-07 adjudicates the prior's usefulness: |x_node−x_g| within fixture budget?) | 2 support configs, fixture swap | node position ± 0.5 mm |
| **H-08** | free/held Δf under defined contact | repeated shifts, protocol contact | first-order added-mass prediction band | outside band → loading model demoted | fixture-only loading twin | Δf CI vs prediction band |
| **H-08b** | k_H on short-cut specimen | direct measurement vs proxy k̃_H | |k̃_H − k_H| within registered tolerance | outside → proxy retired | repeat cut increments | difference CI |
| **H-09** | ring-up/saturation envelopes | envelope fits vs amplitude–phase model | fits within tolerance-aware residual band | systematic residual structure → model term flagged | drive-off twin, two drive levels | residual RMS vs noise floor |

### Phase II — node menu + coupling

| H | Obs | Meas | Exp | Null | Ctrl | Conf |
|---|---|---|---|---|---|---|
| **H-02** | G_c, d_c vs ε through 0 | sign-resolved ε sweep | localization near ε = 0 | flat response (TOST: |d_c| < 0.2 across sweep) → H-02 FAILED | off-frequency + dummy | d_c CI per ε bin, Holm-corrected |
| **H-05** | g(R₁)/g(R₂) | splittings before/after geometry change | √(R₂/R₁) within CI | ratio ≠ prediction → scaling law FAILED | unmodified twin re-measure | ratio CI vs prediction |
| **H-06** | spiral vs matched control | pre-registered G_c/d_c/𝒞_w battery | spiral ≠ control claimed by source; OUR pre-registered expectation: no difference (null) | TOST |d_c| < 0.2 → NULL stands | matched control, blinded order | d_c CI + TOST |
| **H-06a** | κ_χ from spiral spacing vs R_χ^(s) | mode spacing fit | prediction within CI if H-06 shows structure | no relation → spiral-path reading FAILED | per-turn variant fit | fit CI |
| **H-24** | impedance minimum location | 4-terminal axial scan | reproducible minimum distinct from geometry | none/fixture-follows → definition RETIRED | fixture swap, dummy | minimum position ± 1 mm, 2 days |
| **H-26** | overlap argmax stability | mode-shape overlap maps, re-measured | argmax stable ≤ ±5 mm | unstable → definition RETIRED | re-measurement day 2 | argmax spread |
| **H-27** | fitted g vs probe station | splitting vs station | position dependence above uncertainty | flat → definition RETIRED | sensor reposition | slope CI |
| **H-28** | phase-field critical point | two-sensor spatial phase map | critical point exists, aperture-robust | none or aperture artifact → RETIRED | small-aperture repeat (KOS-11) | location ± 2 mm across apertures |

### Phase III — optical (D6-003: directional rows are expected NULLs)

| H | Obs | Meas | Exp | Null | Ctrl | Conf |
|---|---|---|---|---|---|---|
| **H-20** | PD/interferometer sideband at f_drive | demodulated probe through overlap region | sideband within 10× of DER estimate (ΔΦ ~ 3×10⁻² rad interferometric) | no sideband above floor with drive verified on → H-20 FAILED | H-22 controls in-block, glass twin, no-drive | SNR ≥ 10 dB + magnitude CI vs prediction |
| **H-21** | fwd/bwd paired response difference | ≥ 20 randomized reversal pairs | **NULL expected** (reciprocity) | TOST: |asym| < 3σ_pair band → NULL ACCEPTED (the pre-registered outcome) | sham timing, coil-phase flip, rotated crystal | TOST 90 % CI inside band |
| **H-22** | geometry vs heating separability | matched-power off-node twin | controls separate the channels | cannot separate → optical branch UNUSABLE (ENG fail) | dummy crystal | contrast ratio ≥ 5 between paths |
| **H-23** | σ⁺ vs σ⁻ response difference | ≥ 20 randomized polarization pairs | **NULL expected** | TOST inside band → NULL ACCEPTED | polarization flip + no-drive | TOST 90 % CI |
| **H-25** | optical response vs axial station | beam-station map | feature at measured node if any | no feature above phase-noise floor → definition RETIRED | glass twin, off-node stations | feature SNR + location CI |

### Phase IV — coherence/statistics

| H | Obs | Meas | Exp | Null | Ctrl | Conf |
|---|---|---|---|---|---|---|
| **H-10** | Σ̄_φ(t) decay form | post-drive ensembles, n ≥ 100 | exponential beats alternatives (form under TEST) | no decay or non-exp preferred → form rejected, alternative registered | no-drive baseline | ΔAICc ≥ 4 across forms |
| **H-11** | τ_c per drive branch | matched-energy branches | equal within CI | branch-dependent → independence FAILED | energy accounting audit | τ_c CIs overlap test |
| **H-12** | 𝒞_w vs power | power ladder | threshold-then-saturation changepoint | monotone/featureless → phenomenology not reproduced | instrument-only ladder | segmented-fit F-test |
| **H-13** | ensemble phase order | n-shot histograms + Rayleigh Z | spontaneity: order without drive imprint | uniform phases → no order (clean NULL) | phase-locked-drive twin (imprint control) | Z_R at α = 0.01 + twin contrast |
| **H-14** | 𝒞_w on "no singing" branches | re-run JH-negative branches | adjudication either way | amplitude-null AND coherence-null → row closed as full negative | matched positive-injection | 𝒞_w triplet vs baseline |

### Software rows (already adjudicated)

| H | Status |
|---|---|
| **H-15..H-19** | machine-tested-pass (Agents 04/08); bench role = nightly HG-store soak (DATA_PIPELINE §1); any soak violation reopens the row |

### Gates (Phase 0)

| H | Obs | Meas | Exp | Null | Ctrl | Conf |
|---|---|---|---|---|---|---|
| **H-29** | measured vs predicted phase at coordinate | CALIBRATION_GUIDE §7 | ≤ 5° at 4096 Hz | > 5° → all phase claims blocked (gate, not physics) | uncalibrated-channel negative control | 1000-edge averages, session repeatability |
| **H-30** | sham vs live on non-phase observables | paired sham-timing blocks | indistinguishable (TOST) | distinguishable → drive-chain artifact hunt before ANY physics | randomized/blinded order | TOST on amplitude family |

## 4. Register flow after adjudication

CONFIRMED-within-band → CLAIM_REGISTER status note (class unchanged —
one campaign does not upgrade HYP). NULL → status note; for H-21/H-23
this is the pre-registered success of the reciprocity posture. FAILED →
row retired with evidence to `NEGATIVE_RESULTS.md`. ARTIFACT →
`DEFECT_REGISTER.md` row + quarantined block. Any outcome that would
require NEW mathematics goes through the notation-ledger governance
path before a single equation is written (D14-001).
