# RGCS v2 — Dynamic Coherence and Phase-Evolution Specification

**Author:** Sub-Agent 03 (Dynamic Coherence and Phase-Evolution Model)
**Date:** 2026-07-14
**Status:** Frozen for Agent 04 implementation. Metric formulas in
`docs/COHERENCE_METRICS.md`; golden data in
`experiments/sample_data/golden_coherence/`; tests in
`docs/COHERENCE_TEST_MATRIX.md`.

## Header: assumptions and scope

1. Governed by `docs/SCIENTIFIC_CLASSIFICATION_POLICY.md`. Every claim below
   carries one of: **Established / Derived / Hypothesis / Source claim**.
2. Source anchors: Koster et al. 2026 (KOS rows of
   `docs/SOURCE_EVIDENCE_LEDGER.md`) for the *measurement architecture and
   conceptual stages*; Gan et al. 2025 (GAN rows) for **one mathematical
   analogy only** — the exponential decay of a directional-disagreement
   scalar. **No physical equivalence is claimed in either direction.** RGCS
   crystals are not magnon systems and do not "condense"; nothing here is
   cosmology (KOS-15, GAN-15, policy §2).
3. Symbols follow the Koster paper conventions pending Agent 02's freeze of
   `docs/NOTATION_AND_UNITS.md` (see "Symbol register" at the end).

---

## 1. Purpose

RGCS v1 was a static resonance calculator (frequencies, offsets, splittings).
This spec adds the **time axis**: how a drive populates modes, how phase
order can (or cannot) emerge, and how both amplitude and phase order decay.
Its central normative rule, imported from KOS-03/KOS-10:

> **Amplitude and coherence are separate observables.** High amplitude is not
> evidence of phase order, and phase order can outlive detectable amplitude.
> Every dynamic RGCS measurement reports both. (Established as a metric
> property; the applicability payoff for RGCS is Hypothesis DC-H4 below.)

## 2. The four conceptual stages (KOS template)

Koster et al. observe four temporal stages in a parametrically pumped magnon
gas (KOS-02, KOS-06, KOS-08, KOS-12). RGCS adopts the *stage structure* as a
protocol and analysis template — **Source claim** as their physics,
**Established** as an experiment-design pattern, **Hypothesis** wherever we
posit that an RGCS crystal exhibits the analogous stage.

### Stage I — Incoherent injection (drive on, no phase order)

* **KOS observation (Source claim):** parametric pump at f_p injects
  quasiparticle *pairs* at f_p/2 with fixed phase *sums* per pair but no
  global phase; large population, zero coherent signal at the parametric
  frequency (KOS-02, KOS-03).
* **RGCS mapping (Hypothesis DC-H1):** an RGCS drive branch (electrode,
  coil, or acoustic; presets per RG-12/RG-13) delivers energy into a broad
  set of crystal modes without imprinting a common phase, *if* the drive is
  incoherent with respect to the observed band (e.g., pulse trains, noise
  drive, or parametric f/2 response). Bookkeeping: `f_drive`,
  `f_response = f_drive/2` (parametric channel), and observed band are three
  distinct recorded fields (KOS-02 implementation consequence).
* **Measurement signature:** high band amplitude possible; coherence
  𝒞_w(t) near the white-noise baseline; ensemble phase uniform.

### Stage II — Redistribution / thermalization

* **KOS observation (Source claim):** nonlinear scattering redistributes the
  pumped population toward the spectral minimum without a deterministic
  phase reference (KOS-12); coherence rises, with a characteristic dip near
  drive-off (KOS-08).
* **RGCS mapping (Hypothesis DC-H2):** nonlinear inter-mode coupling in the
  crystal + transducer chain redistributes energy among modes; modeled at
  simulation level by the coupled Stuart–Landau system of §4.
* **Measurement signature:** amplitude migrates between bands; coherence
  intermediate and rising; per-run phase partially clustered but ensemble
  still uniform.

### Stage III — Coherent phase emergence

* **KOS observation (Source claim):** above a setup-specific threshold
  (≈21 dBm *in their apparatus* — never an RGCS number, KOS-09), each run
  develops a stable, linearly evolving phase, while the phase across 1000
  runs stays uniformly distributed: order is spontaneous, not imprinted
  (KOS-06, KOS-13).
* **RGCS mapping (Hypothesis DC-H3, the falsifiable core of this spec):**
  above some drive threshold an RGCS mode may develop per-run-stable phase
  with ensemble-uniform phase. **Pre-registered failure condition:** if the
  response phase always locks to the drive/pump phase (Rayleigh test rejects
  ensemble uniformity), the response is *driven*, not spontaneous, and DC-H3
  is refuted for that configuration (golden case (f) encodes exactly this
  trap).
* **Measurement signature:** 𝒞_w(t) rises to a plateau; phase-linearity
  score PL near 1 per run; Rayleigh p ≥ 0.05 across runs.

### Stage IV — Free evolution and decay

* **KOS observation (Source claim):** after pump-off, the ordered state
  evolves freely; amplitude decays but coherence persists, detectable below
  the amplitude noise floor (KOS-10); acquisition must extend well past
  drive-off (KOS-12: ≥ 2.5× beyond drive-off adopted as RGCS protocol).
* **RGCS mapping (Hypothesis DC-H4):** post-drive ringdown carries the
  strongest ordering signal; coherence analysis must be applied to all
  "amplitude-null" branches before declaring a null (motivates re-analysis
  of JH negative results, RG-20).
* **Decay-law analysis (GAN mathematical analogy, Established as a fitting
  form):** directional/phase disagreement statistics are fitted with the
  candidate laws exponential / power-law / damped-oscillatory / no-change
  and compared by AIC/BIC (COH-M14). The exponential ansatz
  σ²(t) = σ₀² e^(−λt) is adapted from GAN-09 **as a fit form only**; λ is a
  fitted bench parameter; the GAN coefficient σ₁ ≃ 2.498 m_Pl is
  Planck-scale cosmology and is never reused (GAN-09, policy §3.5). The
  no-decay null model mirrors the classical conserved-shear baseline
  (GAN-07). This is a **mathematical analogy for decay of a
  directional-disagreement scalar; physical equivalence is claimed in
  neither direction.**

### Stage-to-measurement mapping table

| Stage | Drive state | Amplitude | 𝒞_w(t) | Ensemble phase | Per-run phase | Stage classification |
|---|---|---|---|---|---|---|
| I injection | on | any (can be high) | ≈ baseline | uniform | diffusive | Hypothesis DC-H1 |
| II redistribution | on | migrating | rising, dip near drive-off | uniform | partially stable | Hypothesis DC-H2 |
| III emergence | on (above threshold) | any | plateau | uniform (Rayleigh p ≥ 0.05) | linear (PL ≈ 1) | Hypothesis DC-H3 |
| IV free decay | off | falling | high, then decaying; persists below amplitude floor | uniform | linear | Hypothesis DC-H4 |

The stage *labels* are analysis outputs, never inputs: a run is assigned a
stage only by its measured (amplitude, coherence, ensemble-phase) triple.

## 3. Drive/measurement contract

Adopted from KOS-05/KOS-13/KOS-14 (Established measurement methodology):

1. **Phase-referenced I/Q chain:** all generation and detection share one
   reference clock; record I(t), Q(t); z(t) = I(t) + iQ(t). Phase claims
   without a shared reference are non-compliant.
2. **Single-shot, N-run protocol:** no averaging across excitation cycles
   before coherence analysis; N ≥ 100 repeated runs for ensemble phase
   statistics (KOS used 1000; N is a protocol parameter).
3. **Post-drive window:** acquisition extends ≥ 2.5× beyond drive-off.
4. **Controls precede attribution:** instrument-only and no-crystal control
   runs with identical settings; control-subtracted coherence and
   ensemble-phase uniformity tests are mandatory before any Stage-III claim
   (KOS-13 exclusion logic; golden case (f)).
5. **Artifact register:** known instrument artifacts listed per campaign
   (KOS-14).
6. **Sensor geometry recorded:** transducer aperture and positions are
   first-class metadata; aperture acts as a spatial low-pass filter
   (KOS-11; golden case (g)).

## 4. Simulation-level dynamical model (synthetic data only)

Golden data are generated by coupled **Stuart–Landau** amplitude/phase ODEs.

**Classification:** as a *generator of synthetic test data* the model is
**Derived** (fully specified, seeded, reproducible). As a *description of
RGCS crystal dynamics* it is **Hypothesis DC-H2/DC-H3** — chosen because the
Stuart–Landau normal form is the generic (Established) reduction of any
system near a Hopf bifurcation, i.e. the weakest structural assumption that
can produce threshold behavior, phase locking, and ringdown.

For modes k = 1..M with complex amplitudes a_k(t):

    da_k/dt = (μ_k(t) + i 2π f_k) a_k − (β_k + i γ_k) |a_k|² a_k
              + Σ_{j≠k} K_kj (a_j − a_k) + η_k ξ_k(t)

* μ_k(t): net linear gain = drive-injection rate minus loss f_k/(2Q_k) in
  angular units; drive on/off switches μ_k sign (Stage I → IV).
* f_k: mode frequency from the static RGCS spectrum (RG-01/RG-05 supply
  candidate f_k; this spec does not re-derive them).
* β_k > 0: amplitude saturation; γ_k: nonlinear frequency pull.
* K_kj: inter-mode coupling (diffusive form); redistribution (Stage II) and
  locking (Stage III) live here. Phase-reduction locking threshold for a
  detuned pair with symmetric coupling: K_c = π |f_j − f_k| (Established
  for the reduced phase model).
* ξ_k: unit complex white noise, η_k its strength; per-run random initial
  phases model spontaneous (ensemble-uniform) phase.
* Pump leakage is modeled as an *additive coherent term with run-independent
  phase* — deliberately outside the oscillator state, because it is an
  instrument effect, not dynamics (golden case (f)).

Reference integrator: Euler–Maruyama, dt = 1/fs, seeded
(`stuart_landau_pair` in `tools/generate_golden_coherence.py`). The golden
datasets (cases (e)) use M = 2; the M-mode form above is the implementation
target for `rgcs_core/coherence/` simulation utilities.

**What the model is NOT:** not a magnon kinetic equation, not
Gross–Pitaevskii, not LQC dynamics. It makes no claim that crystals
thermalize like quasiparticle gases; it exists so that every metric has
ground-truth synthetic data with known answers.

## 5. Falsifiable hypotheses and failure conditions (pre-registered)

| ID | Hypothesis | Failure condition |
|---|---|---|
| DC-H1 | RGCS drives can inject energy without imprinting global phase | coherence at baseline never observed with high amplitude in any branch ⇒ untestable/withdrawn; drive-phase-locked response ⇒ trivially driven |
| DC-H2 | Inter-mode redistribution occurs and is Stuart–Landau-describable to first order | no parameter set reproduces measured amplitude migration within stated tolerances |
| DC-H3 | Above a drive threshold, per-run-stable phase with ensemble-uniform phase emerges | Rayleigh test rejects uniformity (drive-imprinted) in all above-threshold runs, or no PL ≈ 1 plateau exists at any drive level |
| DC-H4 | Post-drive coherence persists below the amplitude noise floor and decays exponentially with branch-independent rate λ | coherence dies with amplitude; or decay-law model comparison (COH-M14) prefers non-exponential; or λ differs across matched-energy drive branches (GAN-10 test pattern) |

Evidential status of all four: `untested` (policy §3.3).

## 6. Symbol register (pending Agent 02 freeze — flag, do not fork)

Koster-aligned symbols used by this spec and `docs/COHERENCE_METRICS.md`:
z(t) = I(t) + iQ(t); 𝒞_w(t) (coherence, window w); φ(t) (instantaneous
phase); f_inst(t); R̄ (mean resultant length); V (circular variance);
PL (phase-linearity); PLV (phase-locking value); P_occ (mode occupancy
proxy); t_on (coherence onset); τ_c (coherence decay time); σ_φ² and T_φ
(spatial phase anisotropy scalar/tensor — **never "quantum shear"**);
K, K_c (coupling, critical coupling); μ, β, γ, η (Stuart–Landau
parameters). If Agent 02's `NOTATION_AND_UNITS.md` freezes different
symbols, that file wins and this spec plus `COHERENCE_METRICS.md` are
renamed mechanically; the definitions and golden values are frozen here.
