# RGCS v2 — Mathematical Model (Master Document)

**Author:** Sub-Agent 02 (Mathematical Foundations, Notation, and Model Unification)
**Date:** 2026-07-14
**Status:** Complete. Every equation carries an ID `RGCS-M.x` (traceable in `model_registry.yaml` and checked in `DIMENSIONAL_ANALYSIS.md`), a classification per `SCIENTIFIC_CLASSIFICATION_POLICY.md`, and a source. All symbols are defined in `NOTATION_AND_UNITS.md` (frozen). Assumptions `A-xx` are enumerated in `MODEL_ASSUMPTIONS.md`; hypotheses `H-xx` are mapped to tests in `ROADMAP_TO_FALSIFICATION.md`.

---

## 1. The state vector Ψ(t)

**[RGCS-M.0]** (Derived — bookkeeping definition)

```
Ψ(t) = ( 𝒢, 𝒮_sp, ℬ, {ω_n}, {Q_n}, {u_n}, {z_n(t)}, χ(t), Λ, Σ_φ(t), 𝒞_w(t), 𝒪(t) )
```

Typed components and their justification:

| Component | Type | Content | Why it is in the state |
|---|---|---|---|
| `𝒢` | frozen dataclass | crystal geometry & material: L, D_w, D_n, N_f, α_f, α_m, ρ, diameter/angle conventions, v_L = (v̄_L, u_v) | Static inputs of every forward prediction; wave speed lives here as an uncertain parameter (D-05). |
| `𝒮_sp` | frozen dataclass | spiral state: q, T, R_0, H, p_z, Ω_s | Generates the geometric prior R_χ^(s) (Module 7). |
| `ℬ` | dataclass | boundary/parity state: family P ∈ {P−, P+, all}, `include_zero_mode` flag, boundary-condition assignment record | Parity must be derived from boundary data, not a cosmetic filter (LT-Δ1, D-14). |
| `{ω_n}` | `ndarray[float64]`, rad/s | modal angular frequencies | Spectral backbone (Modules 2–4, 6). |
| `{Q_n}` | `ndarray[float64]` | modal quality factors | Sets linewidths Γ_n and damping γ_n; drives the resonance-class bins (D-06). |
| `{u_n}` | `ndarray`, normalized | mode shapes in the sensor basis | Needed for overlap Λ, node prediction, parity assignment. |
| `{z_n(t)}` | `ndarray[complex128]`, unit X | complex modal amplitudes A_n e^{iφ_n} | The dynamic degrees of freedom (Module 10). Amplitude and phase are carried together and reported separately (KOS-03 lesson). |
| `χ(t)` | `float`, rad | compact phase coordinate, mod 2π | The closed coordinate of the compact-spectrum hypothesis (Module 3, 7). |
| `Λ` | `float` ∈ [0,1] | normalized drive–mode overlap | The (weakest) LT coupling analogue (LT-11); measured, never theoretical. |
| `Σ_φ(t)` | `ndarray (3,3)` | circular-variance phase-anisotropy tensor | The anisotropy/coherence state (Module 11, GAN adaptation). |
| `𝒞_w(t)` | `ndarray[float64]` ∈ [0,1] | autocorrelation coherence trace | First-class order parameter, separate from amplitude (KOS-Δ1). |
| `𝒪(t)` | dataclass | measured observables, controls, artifact register, negative-result ledger | Measurement is part of the state; controls are not an afterthought (KOS-13). |

The v1 TEX state 𝒮 = (𝒢_c, 𝒢_s, 𝓜, 𝒞, 𝒟, 𝓛, 𝒪) is superseded: 𝓜 → (ℬ, {ω_n}, {Q_n}, {u_n}), 𝒞 → ({z_n}, K_nm), 𝒟 → drive parameters inside 𝒪/G_n, 𝓛 → correction ledger δ_k (Module 9).

---

## 2. Module 1 — Faceted crystal geometry and density inverse

Coordinate frame: x from the female (wide) apex toward the male (narrow) apex, 0 ≤ x ≤ L.

**[RGCS-M.1]** Polygon area, across-vertices diameter (Established, plane geometry; RG-04):

    A(D) = (N_f/8) · D² · sin(2π/N_f)

**[RGCS-M.2]** Polygon area, across-flats diameter (Established):

    A(D) = N_f · (D/2)² · tan(π/N_f)

**[RGCS-M.3]** Apothem (Established): `r_a = (D/2)·cos(π/N_f)` (across-vertices); `r_a = D/2` (across-flats).

**[RGCS-M.4]** Cap height by angle convention (Established, given the convention declaration; Source claim for the default angle values 51.843°/60°, RG-16):

    h = r_a·tan(α)        (face_slope)
    h = r_a/tan(α)        (axis_to_face)
    h = r_a/tan(α/2)      (apex_included)

**[RGCS-M.5]** Total volume: tapered polygonal frustum plus two pyramidal caps (Established, solid geometry; RG-04):

    V = (h_s/3)·(A_w + A_n + √(A_w·A_n)) + A_w·h_f/3 + A_n·h_m/3,   h_s = L − h_f − h_m > 0

**[RGCS-M.6]** Mass (Established): `m = ρ·V` (with V in cm³, ρ in g/cm³, m in g).

**[RGCS-M.7]** Density inverse (Derived): given a measured mass m*, fixed L and taper ratio, solve for the diameter scale s_D in

    ρ·V(s_D·D_w, s_D·D_n; L) = m*

by Newton iteration. V is strictly increasing in s_D (all area terms scale as s_D², cap heights as s_D), so the root is unique; convergence criterion |Δm|/m* < 10⁻¹⁰, guarded by bisection fallback. Classification: Derived; inherits Source-claim status of any source-specified dimensions.

---

## 3. Module 2 — 4096 harmonic ladder with wave-speed uncertainty (closes D-05)

**[RGCS-M.8]** Axial half-wave estimate (formula Established; applicability to a faceted tapered crystal is Hypothesis H-01a / assumption A-01; RG-01):

    f_ax = v_L / (2L)        (L in m)

**[RGCS-M.9]** Ladder length (Derived; f_0 = 4096 Hz is Source claim RG-01):

    L_N = v_L / (2·N·f_0)

**[RGCS-M.10]** Wave-speed uncertainty model (Derived — declared uncertainty budget; closes D-05). v_L is a first-class uncertain parameter:

    v_L = v̄_L·(1 + δ_v),   E[δ_v] = 0,   sd(δ_v) = u_v,   σ_v = u_v·v̄_L

Default v̄_L = 6310 m/s. Provenance note: α-quartz is trigonal; the pure longitudinal speed along Z is √(c₃₃/ρ) ≈ 6320 m/s and along X is √(c₁₁/ρ) ≈ 5720 m/s (Established elastic-constant physics; a specific reference, e.g. Bechmann's 1958 constants, must be cited by Agent 07 — D-19a). The corpus value 6310 m/s is consistent with the Z-axis longitudinal speed but is uncited; until a specimen's crystallographic orientation is measured, the default relative uncertainty is **u_v = 0.05**, chosen to cover the X–Z longitudinal spread (≈ ±5%). When orientation is measured and cited constants are used, u_v may be reduced and its value recorded per specimen.

**[RGCS-M.11]** Mandatory propagation into every frequency/length prediction (Derived): since f_ax ∝ v_L and L_N ∝ v_L,

    u(f_ax)/f_ax = u_v,      u(L_N)/L_N = u_v

Every ladder output is an interval: f_ax ± f_ax·u_v (1-sigma). **Interpretation rule:** with u_v = 0.05, a 0.03% "match" (RG-02) is ~170× smaller than the systematic band; such matches are Derived-from-Hypothesis arithmetic, never confirmation (D-04).

**[RGCS-M.12]** Harmonic classification with uncertainty (Derived):

    N_eff = f_ax/f_0;  N = round(N_eff);  classification is SET-VALUED:
    𝒩 = { N' ∈ ℕ : [f_ax(1−u_v), f_ax(1+u_v)] ∩ [ (N'−½)f_0, (N'+½)f_0 ] ≠ ∅ }

If |𝒩| > 1 the specimen's harmonic class is reported as ambiguous (e.g. the 116 mm example, RG-03, is {6, 7} at u_v = 0.05).

---

## 4. Module 3 — Compact phase-coordinate mode spectrum

**[RGCS-M.13]** Compact spectrum (Hypothesis H-01, built on Established KK algebra; adapted from LT Eqs. (9)–(10) with substitution map m → f, m_B → f_b, 1/R → v_χ/(2πR_χ); RG-05, LT-08/09):

    f_n² = f_b² + ( n·v_χ / (2π·R_χ) )²,     R_χ in m inside this formula

Golden value: n = 1, f_b = 0, v_χ = 6310 m/s, R_χ = 100 mm → 10042.6769091 Hz (G-06).

**[RGCS-M.14]** Identifiable spectral slope (Derived — identifiability statement, closes part of Module 14): only the combination

    κ_χ ≡ v_χ / (2π·R_χ)     [Hz]

enters RGCS-M.13. **v_χ and R_χ are NOT separately identifiable from mode spacing alone.** Fits report κ_χ (with uncertainty); R_χ is quoted only when v_χ is independently fixed (e.g. v_χ := v_L with its u_v), and then u(R_χ)/R_χ ≥ u_v necessarily. The spiral prior R_χ^(s) (Module 7) constrains R_χ, breaking the degeneracy only under Hypothesis H-06a (that the spiral path is the compact path).

**[RGCS-M.15]** Uncertainty propagation (Derived; first-order):

    u(f_n)² = (∂f_n/∂f_b)²u(f_b)² + (∂f_n/∂κ_χ)²u(κ_χ)²·n²
    ∂f_n/∂f_b = f_b/f_n;   ∂f_n/∂(nκ_χ) = nκ_χ/f_n

With v_χ carrying u_v and R_χ fixed: u(f_n)/f_n = (nκ_χ)²/f_n² · u_v (→ u_v when f_b = 0). All compact-spectrum outputs are intervals.

---

## 5. Module 4 — Boundary parity and mode families (closes D-14)

Boundary-condition story (adapted from LT Table I and Eqs. (1)–(2); the *classification math* is Established, the *applicability to RGCS resonators* is Hypothesis H-03). On a compact coordinate χ ∈ [0, 2π) with two distinguished boundary points (drive node and free end, or the two termination apices), mode functions divide into:

**[RGCS-M.16]** Parity families (Established as index-set/function definitions):

    P− (odd / antisymmetric):  u_n^−(χ) ∝ sin(n·χ/2),  n ∈ 𝕀− = {1, 3, 5, …}
    P+ (even / symmetric):     u_n^+(χ) ∝ cos(n·χ/2),  n ∈ 𝕀+ = {0, 2, 4, …}
    all:                       𝕀 = 𝕀− ∪ 𝕀+

The physical meaning in RGCS: odd = antisymmetric displacement/current/pressure pattern about the reference plane; even = symmetric. Assignment is made by two-sensor phase or FEA mode shape (LT-02 analogue), never by which family contains a desired frequency.

**[RGCS-M.17]** Zero-mode rule (Derived — decision, closes D-14):

1. The odd family NEVER contains n = 0 (sin ≡ 0: not a mode). Established.
2. The even family contains n = 0 mathematically, with f_{n=0} = f_b (uniform/breathing pattern). RGCS exposes an explicit boolean `include_zero_mode` on family P+:
   - `include_zero_mode = True` (RGCS default when f_b > 0): the base mode is physical and listed.
   - `include_zero_mode = False`: reproduces the strict LT template, where the zero-flux condition ∮B_μ dχ = 0 removes the mediator zero mode (LT-04). Used when testing the LT analogy exactly.
3. When f_b = 0, the n = 0 member has f = 0 (a DC/rigid-body pattern, not a vibratory mode) and is excluded from spectra unconditionally.
4. Manuscript rule (Agent 07): any spectrum table citing LT must state which flag was used; a measured low-lying symmetric mode where the LT template forbids one is evidence that the analogy is partial (LT-04 test consequence).

---

## 6. Module 5 — Dimensionless resonance offset ε_R^(f) (closes D-06)

**[RGCS-M.18]** Definition (Derived — definition; sign convention identical to LT Eq. (13), LT-15; enhancement near zero is Hypothesis H-02):

    ε_R^(f) = [ f_m² − (p·f_x)² ] / (p·f_x)²

Default p = 2 (LT mediator-pair threshold analogue). ε > 0: bridge mode above threshold; ε < 0: below. LT's invisible/visible interpretation has NO RGCS analogue.

**[RGCS-M.19]** Relation to linear detuning (Established algebra):

    ε_R^(f) = (1 + d_lin)² − 1 ≈ 2·d_lin  for |d_lin| ≪ 1,   d_lin = f_m/(p·f_x) − 1

**[RGCS-M.20]** Q-derived resonance classes (Derived heuristic — replaces the borrowed 10⁻⁴/0.01/0.1 bins; closes D-06). A pair with effective quality factor Q_eff = 2/(1/Q_m + 1/Q_x) has fractional half-linewidth 1/(2Q_eff); by RGCS-M.19 the corresponding ε scale is

    ε_Q ≡ 1/Q_eff

Classes:

    WITHIN LINEWIDTH:  |ε_R^(f)| ≤ ε_Q          (|d_lin| within half the combined FWHM)
    NEAR:              ε_Q < |ε_R^(f)| ≤ 5·ε_Q
    MODERATE:          5·ε_Q < |ε_R^(f)| ≤ 50·ε_Q
    FAR:               |ε_R^(f)| > 50·ε_Q

Example: Q_m = 1000, Q_x = 800 → Q_eff = 888.9, ε_Q = 1.125×10⁻³ — 10× wider than the retired 10⁻⁴ bin and actually resolvable. LT's 10⁻⁸–10⁻⁴ window and ε = 1.25 far-detuned reference (LT-12/20) appear only as source-summary context; ε = 1.25 is retained as the *convention* for a deliberately non-resonant control configuration.

**[RGCS-M.21]** Sweep-span heuristic (Derived heuristic — labeled, not physics):

    Span = max( 10 Hz, 4·|f_m − p·f_x|, 6·max(Γ_m, Γ_x) )

The added 6-linewidth floor guarantees the sweep resolves the lineshape even at small detuning (the old `max(10, 4|Δf|)` collapses to 10 Hz at zero detuning regardless of linewidth).

**[RGCS-M.22]** Corrected, uncertainty-carrying offset (Derived; LT-Δ2 — corrections are SIGNED and can move ε through zero, template LT Eqs. (11)–(13)):

    f_i,corr = f_i,0·(1 + Σ_k δ_k^(i)),  δ_k signed
    ε_R^(f),corr = [f_m,corr² − (p·f_x,corr)²]/(p·f_x,corr)²
    u(ε_R) ≈ 2(1+d_lin)·√[ u(f_m)²/f_m²·(1+d_lin)² + u(f_x)²/f_x²·(1+d_lin)² ]·(1+O(d_lin))
           ≈ 2·√[ (u(f_m)/f_m)² + (u(f_x)/f_x)² ]   near ε = 0

A resonance-class string without u(ε_R) is non-compliant (policy §3.4).

---

## 7. Module 6 — Coupled two-mode and N-mode eigenproblem

**[RGCS-M.23]** Two-mode matrix (Established; standard avoided-crossing model, RG-07):

    𝐇 = [[f_A, g], [g, f_B]]     (all entries Hz)

**[RGCS-M.24]** Hybrid eigenfrequencies (Established):

    f_± = (f_A + f_B)/2 ± √( ((f_A − f_B)/2)² + g² )

Golden: f_A = f_B = 1000 Hz, g = 10 Hz → 990/1010 Hz (G-08). Splitting at zero detuning = 2g.

**[RGCS-M.25]** Mixing angle (Established; sign-safe atan2 form):

    ϑ_mix = ½·atan2(2g, f_A − f_B)

**[RGCS-M.26]** Linewidth (Established; FWHM convention, stated per D-19c): `Γ_n = f_n/Q_n`.

**[RGCS-M.27]** Strong-coupling ratio (Established criterion, citation required — standard cavity/optomechanics lore, D-19c):

    R_g = 2g / (Γ_A + Γ_B);  R_g ≳ 1 ⇔ splitting resolved against combined linewidth

**[RGCS-M.28]** N-mode generalization (Established linear algebra; fitted g_nm are Derived):

    𝐇_nm = f_n·δ_nm + g_nm (g_nm = g_mn real, g_nn = 0);  eigenpairs (f_k^hyb, u_k) of 𝐇

Symmetric-real ⇒ real eigenvalues, orthogonal eigenvectors (numpy.linalg.eigh). Valid in the near-degenerate weak-coupling regime (assumption A-04); NOT a substitute for full elastodynamics.

**[RGCS-M.29]** Coupling-normalization scaling (Hypothesis H-05; analogue of LT Eq. (6), g₁ = g₁^(5)/√L):

    g ∝ (2π·R_χ)^(−1/2)   at fixed transducer and mode pair

Testable: refit g after a controlled change of compact-path geometry; failure to scale kills the analogy row (LT-06).

---

## 8. Module 7 — Spiral/conical 4D projected path and compact radius (closes D-09)

**[RGCS-M.30]** 4D spiral state path (Established differential geometry; physical relevance is Hypothesis H-06; RG-08):

    X(θ) = [ R_0·e^{−aθ}·cosθ,  R_0·e^{−aθ}·sinθ,  H·(1 − (r/R_0)^{p_z}),  χ_0 + Ω_s·θ ],  θ ∈ [0, 2πT]

(The z-law is written in radius-normalized form, matching core.py; the TEX form H(1−e^{−p_z aθ}) is identical because (r/R_0)^{p_z} = e^{−p_z aθ}.) The fourth coordinate reduced mod 2π is the compact phase χ.

**[RGCS-M.31]** Pitch parameter (Established): `a = ln q / (2π)`. Golden: q = e → a = 0.15915494309 (G-10).

**[RGCS-M.32]** Planar scale-rotation eigenvalue (Established): `λ_s = −a + i`.

**[RGCS-M.33]** Curvature invariant (Established): `rκ = 1/√(1+a²)`; q = e → 0.98757049215 (G-10).

**[RGCS-M.34]** Exact planar arc length (Established):

    ℓ_pl = R_0·√(1+a²)/a · (1 − e^{−2πaT})

**[RGCS-M.35]** AUTHORITATIVE 3D path length (Derived — the single project definition; closes D-09):

    ℓ_3D = lim over refinement of Σ_i ‖X_3D(θ_{i+1}) − X_3D(θ_i)‖

computed as a numeric polyline over θ with sample count doubled until |ℓ^(2s) − ℓ^(s)|/ℓ^(2s) < 10⁻⁶ (Richardson-checked; ≥ 1200 initial samples). The workbook closed form ℓ_pl·√(1 + (H/ℓ_pl)²) is RETIRED as a defining formula: it assumes the climb is distributed uniformly along the planar length and can err at the percent level for p_z ≠ 1. It may be shown only as a labeled approximation with its error against RGCS-M.35 reported.

**[RGCS-M.36]** Spiral compact-radius prior (Hypothesis — definition choice, averaging assumption A-07; RG-09):

    R_χ^(s) = ℓ_3D / (2π·T)

**[RGCS-M.37]** Per-turn alternative (Hypothesis — competing definition, to be model-compared):

    R_χ,k = ℓ_k / (2π),  ℓ_k = 3D length of turn k;  ℓ_k contracts ≈ 1/q per turn

Model comparison (Module 14) must test mean-R_χ^(s) vs per-turn-R_χ,k spectra against measured spacing (RG-09 test consequence). The TEX default "R_χ = 100 mm" is an arbitrary placeholder, unrelated to the spiral defaults (D-21); code must not present them as consistent.

---

## 9. Module 8 — Non-metric eye/node coordinate and measurement correction (closes D-01)

Frame: x from the female (wide) apex, 0 ≤ x ≤ L.

**[RGCS-M.38]** Metric center (Established): `x_m = L/2`.

**[RGCS-M.39]** Geometry node prior (Derived — from a stated principle): the displacement node of the fundamental extensional mode of a free–free uniform bar lies at the bar's midpoint; RGCS applies this to the prismatic shaft, whose midpoint in the female frame is

    x_g = h_f + h_s/2 = (L + h_f − h_m)/2

Default N=5 geometry (L = 154.052734, h_f = 17.415434, h_m = 14.812763): **x_g = 78.3277 mm** (x_m = 77.0264 mm). Resolution of the three competing estimators (D-01):
- WB5 Sheet 13's 75.7250 mm equals exactly `L − x_g` — the SAME point expressed from the male end. Retired as a separate quantity; documented as a frame conversion.
- core.py's `geometry_balance_node_mm` = h_m·L/(h_f+h_m) = 70.806 mm has no derivation (presumed transcription error) and is DELETED. Agent 04 must not reimplement it.

x_g is a PRIOR only (Source claim JH-001 says the vorticial "eye" is not the metric center; nothing in the corpus establishes that it is the shaft midpoint either).

**[RGCS-M.40]** Precedence and node fraction (Derived — rule):

    x_* = x̂_e if measured else x_g;    c_g = x_*/L

Measured x̂_e always takes precedence; JSON serialization uses `null`, never NaN (D-03).

**[RGCS-M.41]** Node alignment factor (Derived heuristic):

    ξ = (x_d − x_*)/σ_x;    N_x = exp(−ξ²)

σ_x is the measured spatial uncertainty or mode-width scale; N_x feeds only the merit score S (Module 13), never evidence.

---

## 10. Module 9 — Loading, damping, and stiffness corrections

**[RGCS-M.42]** Loading factor (Established as a measured ratio; RG-10):

    k_H = f_loaded / f_free

**[RGCS-M.43]** First-order added modal mass (Established SDOF algebra, conditioned on Hypothesis H-08 that loading is pure added modal mass with fraction η):

    ΔM_H = M_eff·(1/k_H² − 1),   M_eff = η·m

Golden: k_H = 0.9866751189 (152/154.052734375), m = 154 g, η = 0.5 → ΔM_H = 2.0937873 g (G-09). Derivation: f ∝ √(k_s/M); adding ΔM at the antinode with modal participation gives f_loaded/f_free = √(M_eff/(M_eff+ΔM)).

**[RGCS-M.44]** Length-shortfall proxy (Hypothesis H-08b — kept SEPARATE from k_H, closes D-10):

    k̃_H = L_actual / L_target

k̃_H equals k_H only under the assumptions that (i) f ∝ 1/L exactly and (ii) loading is intended to pull the short crystal down to the target frequency. Code and workbook must use the distinct symbol and carry the hypothesis label; `mass_loading_compatible` strings must state the conditioning.

**[RGCS-M.45]** Signed correction ledger (Derived — calibration bookkeeping; template LT Eqs. (11)–(12): corrections have definite signs and can flip ε_R through zero, LT-Δ2):

    f_meas = f_0,pred·(1 + δ_geometry + δ_anisotropy + δ_loading + δ_T + δ_fixture + δ_drive) + ε_ns

Each δ_k is signed, has its own uncertainty u(δ_k), and must be measured stably across repeated calibrations before ε_R^(f) is interpreted (LT-13 test consequence). The additive form is first-order only (assumption A-10); a nonlinear/Bayesian treatment supersedes it when |Σδ| > 0.02.

---

## 11. Module 10 — Dynamic phase and coherence state (amplitude–phase ODEs)

**Classification: Hypothesis (H-09) as a physical model of RGCS crystals; the mathematical structure is Established (slowly-varying-envelope / phase-reduction theory of weakly coupled, weakly nonlinear oscillators).** Nothing in the corpus yet measures these coefficients; the model exists to be fitted and potentially rejected.

**[RGCS-M.46]** Complex modal dynamics (canonical form; the polar forms below are exactly equivalent):

    ż_n = (G_n − γ_n + i·ω_n)·z_n − Σ_m β_nm·|z_m|²·z_n + Σ_m K_nm·z_m

**[RGCS-M.47]** Amplitude equation (polar decomposition of M.46):

    Ȧ_n = (G_n − γ_n)·A_n − Σ_m β_nm·A_m²·A_n + Σ_m K_nm·A_m·cos(φ_m − φ_n)

**[RGCS-M.48]** Phase equation:

    φ̇_n = ω_n + Σ_m K_nm·(A_m/A_n)·sin(φ_m − φ_n)

**[RGCS-M.49]** Damping rate from measured Q (Established):

    γ_n = ω_n / (2·Q_n)     [rad/s amplitude decay; energy decays at 2γ_n]

Term-by-term justification (required by brief):

| Term | Dimension | Origin | Classification | Observable that fixes it |
|---|---|---|---|---|
| (G_n − γ_n)z_n | [s⁻¹]·[X] | linear driven-damped oscillator in the rotating frame (slowly-varying envelope, valid for Q ≫ 1, A-05) | Established (structure); G_n values Derived from drive calibration | ring-up/ring-down exponential rates; γ_n independently from free ringdown |
| −β_nm|z_m|²z_n | [s⁻¹X⁻²]·[X³] = [X/s] | lowest-order amplitude-symmetric saturation (z → −z invariant); keeps trajectories bounded when G_n > γ_n | Hypothesis (that saturation is cubic) | steady-state amplitude vs drive power curve |
| K_nm z_m | [s⁻¹]·[X] | linear inter-mode coupling; the time-domain counterpart of the g_nm in RGCS-M.28 is the **anti-Hermitian** coupling K_nm = i·2π·g_nm (rad/s): at degeneracy the eigenvalues of [[iω, i2πg], [i2πg, iω]] are i(ω ± 2πg), i.e. spectral peaks at f₀ ± g — the 2g Hz splitting of RGCS-M.24/M.28 — and an amplitude beat with node spacing 1/(4g). A real-symmetric K of equal magnitude splits growth rates (cosh growth), not frequencies, and is not the counterpart. | Hypothesis (applicability); Established (phase-reduction math) | avoided-crossing splitting and beat notes |

Consistency requirement: a fitted coupling magnitude |K_nm| must reproduce the frequency-domain splitting of Module 6 (|K_nm| = 2π·g_nm with g in Hz, anti-Hermitian structure K_nm = i·2π·g_nm); disagreement between time-domain and frequency-domain coupling estimates is a pre-registered warning flag. *Erratum 2026-07-14 (QA-D-04): the previous map K_nm = π·g_nm (real-symmetric) was wrong in structure and magnitude — it produces exponential growth-rate splitting with no frequency splitting for a degenerate pair; the H-09 consistency gate would have flagged correct data as inconsistent.*

Alternatives considered (and why not adopted as default):
1. **Full linear coupled-mode equations (no envelope reduction).** Exact but conflates fast carrier and slow envelope; unnecessary at Q ≫ 1. Retained as validation harness.
2. **Van der Pol self-excitation** (G_n(A) = G_0 − G_2A²). Equivalent to M.46 when β_nn absorbs G_2; no extra structure justified by data.
3. **Sin-bounded (holonomy-type) saturation** z-response ∝ sin(μA)/μ (GAN-03 pattern, cited mechanism class). Adopted only if power sweeps show symmetric saturation-recovery; adds a parameter without present evidence.
4. **Parametric two-mode (f/2) terms** ż_n ⊃ P_nm·z̄_m e^{iω_p t} (KOS-02 half-frequency pumping). Added ONLY for the parametric drive branch; off by default.
5. **Kuramoto phase-only model.** Discards amplitude, contradicting the KOS amplitude/coherence separation lesson; rejected.

Failure conditions and fitting protocol: `ROADMAP_TO_FALSIFICATION.md` H-09.

**[RGCS-M.50]** Dynamic compact phase (Derived — definition):

    χ(t) = (χ_0 + Ω_s·θ(t)) mod 2π ;  for a driven system  χ(t) = 2π·f_d·t mod 2π relative to the shared reference clock

All phase claims require the KOS-05 measurement architecture (shared reference, I/Q capture); φ_n and χ are meaningless without a declared phase reference.

---

## 12. Module 11 — Shear/anisotropy functional (GAN adaptation)

Three orthogonal sensor channels j = 1, 2, 3 (aligned to declared specimen axes) yield per-channel analytic signals z_j(t) with instantaneous phases φ_j(t).

**[RGCS-M.51]** Per-axis phase rates and pairwise differences (Derived from measured phases):

    Ω_j(t) = dφ_j/dt  (discrete: centered difference of unwrapped phase);   Ω_jk = Ω_j − Ω_k

**[RGCS-M.52]** Phase-rate shear scalar (definition Established — exact adaptation of GAN Eq. (2), GAN-05, with substitution map H_i → Ω_j; RGCS physical meaning is a measured statistic, nothing cosmological):

    σ_φ²(t) = (1/3)·[ Ω_12² + Ω_23² + Ω_31² ]

Properties (golden tests G-15): σ_φ²(Ω,Ω,Ω) = 0; permutation invariant; non-negative; adding a common rate to all channels leaves it unchanged. The kinematic decomposition lesson (GAN-04): mean rate Θ_φ = (Ω_1+Ω_2+Ω_3)/3 (isotropic part) is reported alongside σ_φ² (shape-distorting part); their ratio σ_φ²/Θ_φ² is the dimensionless anisotropy.

**[RGCS-M.53]** Circular-variance phase-anisotropy tensor (Derived — definition; Established circular statistics):

    Σ_φ,jk(t) = 1 − | ⟨ e^{i(φ_j(τ) − φ_k(τ))} ⟩_{τ ∈ [t−w/2, t+w/2]} |,   j ≠ k;  Σ_φ,jj ≡ 0

Entries ∈ [0,1]: 0 = the two channels hold a fixed relative phase over the window (coherent, possibly anisotropic in rate but locked); 1 = uniformly random relative phase. Scalar reduction Σ̄_φ = (Σ_φ,12 + Σ_φ,23 + Σ_φ,31)/3. Per-channel circular variance V_j = 1 − R̄_j, R̄_j = |⟨e^{iφ_j}⟩_w| is reported per channel (needed for the Rayleigh spontaneity test, M.61).

**[RGCS-M.54]** Exponential relaxation model — **a model to TEST, not to presume** (Hypothesis H-10; form cited to GAN Eq. (6), GAN-09; the coefficient σ₁ ≃ 2.498 m_Pl is cosmology-only and NEVER imported):

    Model M_exp:    Σ̄_φ(t) = Σ̄_φ,0 · e^{−t/τ_c}
    Null model M_0: Σ̄_φ(t) = const                (classical-conservation analogue, GAN-07)
    Alt model M_pl: Σ̄_φ(t) = Σ̄_φ,0 · (1 + t/t_0)^{−α}
    Alt model M_se: Σ̄_φ(t) = Σ̄_φ,0 · exp[−(t/τ_c)^{β_s}]  (stretched)

τ_c is a fitted bench parameter per specimen and per drive branch. Adjudication by AIC/BIC on post-drive ringdown windows (RGCS-M.60), following the GAN three-model comparison layout (GAN-11). Branch-independence of τ_c (the GAN "matter-independence" analogue, GAN-Δ4) is a separate hypothesis H-11, tested by comparing τ_c across electrode/coil/acoustic branches at matched energy.

---

## 13. Module 12 — Coherence functional (KOS adaptation)

**[RGCS-M.55]** Analytic/demodulated signal (Established; KOS-05):

    z(t) = z_I(t) + i·z_Q(t)

acquired single-shot via phase-locked I/Q demodulation (shared 10 MHz-class reference); for audio-band RGCS branches, the Hilbert transform of a real sensor channel is the declared equivalent (analysis parameter recorded).

**[RGCS-M.56]** Autocorrelation coherence (Established definition — exact adaptation of KOS Methods, KOS-07):

    𝒞_w(t) = 𝒩_w · ∫ dτ | [ (z̄·Π_{t,w}) ⋆ (z·Π_{t,w}) ](τ) |,
    Π_{t,w}(τ) = 1 for |τ − t| ≤ w/2 else 0

with 𝒩_w chosen so a perfect tone e^{iω_0 t} gives 𝒞_w = 1. Properties: 𝒞_w ∈ [0,1]; pure tone → 1; white noise → small positive baseline b_w > 0 (finite window/discrete sampling; b_w is MEASURED per pipeline and reported, ≈ 0.2 in KOS's — setup-specific, never reused). Window w is a declared analysis parameter; a window-length sensitivity analysis is mandatory (KOS-07). KOS's 100 ns is their value, not ours; RGCS default w spans ≥ 100 carrier cycles of the band under analysis.

Normative rules (KOS-03/10): amplitude and coherence are ALWAYS reported as separate quantities; any null result adjudicated on amplitude alone is labeled "amplitude-null, coherence-untested" (D-20); coherence analysis extends ≥ 2.5× past drive-off (KOS-12).

---

## 14. Module 13 — Control-subtracted coupling/transfer metric

**[RGCS-M.57]** Control-subtracted gain and effect size (Established statistics):

    G_c = max( 0, (Ȳ_cfg − Ȳ_ctl)/Ȳ_ctl ),
    d_c = (Ȳ_cfg − Ȳ_ctl) / s_pooled,   s_pooled² = (s_cfg² + s_ctl²)/2

Ȳ is the mean of a pre-registered observable (amplitude, transfer power, or coherence 𝒞_w) over matched configuration/control runs (dummy-load, no-crystal, detuned ε ≈ 1.25 convention). G_c is the fractional gain used in S; d_c is the evidence-bearing quantity, reported with n_cfg, n_ctl, and test.

**[RGCS-M.58]** Engineering merit (Derived heuristic — "not a physical quantity"; RG-18):

    D_f = 1/(1 + (2·Q_eff·Δ_f)²),  Δ_f = (f_A − f_B)/√(f_A·f_B)
    P_φ = cos²(π·r_φ)
    S = |Λ|²·D_f·P_φ·N_x·G_c

Every factor is reported independently; S ranks configurations for replication priority and is never evidence (policy §3.2). D_f is the standard Lorentzian half-power form; the harmonic-mean Q_eff is a declared modeling choice (D-19d).

---

## 15. Module 14 — Statistical uncertainty, identifiability, null models

**[RGCS-M.59]** Measurement model and likelihood (Established):

    f_obs,i = f_model,i(Θ)·(1 + Σ_k δ_k) + ε_ns,i,   ε_ns,i ~ N(0, s_i²) independent (A-13)
    −2·ln L(Θ) = Σ_i [ (f_obs,i − f_pred,i(Θ))²/s_i² + ln(2π s_i²) ]

Fits minimize −2 ln L (or the weighted least squares J it reduces to); parameter uncertainties from the observed information matrix, checked by bootstrap when n < 20.

**[RGCS-M.60]** Model comparison and null models (Established):

    AIC = 2k − 2·ln L̂;   BIC = k·ln n − 2·ln L̂

Pre-registered comparisons (failure conditions RG-19):
1. Compact spectrum (M.13) vs simpler modal models (pure axial f_n = n·f_1; plate-law f_n ∝ n²; unconstrained per-mode fit) on HELD-OUT modes.
2. Mean-R_χ vs per-turn-R_χ spiral priors (M.36 vs M.37).
3. Σ̄_φ decay model set (M.54).
4. Scrambled-label null: n/parity labels permuted; any statistic that survives scrambling is discarded (kills the WB2 "nearest 4096 N" look-elsewhere trap, D-22).

Identifiability register: (v_χ, R_χ) degenerate — fit κ_χ only (M.14); (η, ΔM_H) degenerate in a single loading measurement — fix η or measure two loadings; (G_n, γ_n) only the difference identifiable from ring-up alone — γ_n from free ringdown first; (β_nm, K_nm) require power sweeps plus two-tone data.

**[RGCS-M.61]** Ensemble phase uniformity (Established; Rayleigh test; KOS-06 spontaneity control):

    R̄ = | (1/n_s)·Σ_{shots} e^{iφ_shot} |;   Z_R = n_s·R̄²;   p ≈ e^{−Z_R}·(1 + (2Z_R − Z_R²)/(4n_s))

Uniform ensemble phase (Z_R small) with high per-shot coherence 𝒞_w ⇒ spontaneous ordering; ensemble phase locked to the drive ⇒ driven response. Pre-registered per KOS-06.

---

## 16. Cross-reference summary

| Inconsistency | Closed by |
|---|---|
| D-01 (node estimators) | RGCS-M.38–M.40; frame declaration; deletion of `geometry_balance_node_mm` |
| D-05 (isotropic v_L) | RGCS-M.10–M.12, M.15; u_v = 0.05 default; set-valued harmonic class |
| D-06 (magic bins) | RGCS-M.20–M.21 (Q-derived) |
| D-07 (symbol collisions) | NOTATION_AND_UNITS.md §1 |
| D-09 (R_χ ambiguity) | RGCS-M.35–M.37 (numeric 3D authoritative; per-turn alternative registered) |
| D-10 (k_H conflation) | RGCS-M.42 vs M.44 (distinct symbols k_H, k̃_H) |
| D-13 (phase residue) | r_φ ≡ c − round(c) defined on CYCLE COUNTS only, never on duty (A-21); golden: half-spacing nominal c = 1507.328 → r_φ = +0.328 (+118.08°). NOTE: the INCONSISTENCY_REGISTER's stated sign (−0.328) is itself an erratum — round(1507.328) = 1507, so the residue is positive. Relative to the exact-cycle preset 1508 the offset is −0.672 cycles; the two quantities must not be conflated. |
| D-14 (zero mode) | RGCS-M.16–M.17 (`include_zero_mode` per family P+) |
| D-20 (amplitude-only nulls) | RGCS-M.56 normative rules |
| D-21 (default mismatch) | RGCS-M.37 note (100 mm = placeholder) |
| D-22 (numerology column) | RGCS-M.60 scrambled-label null |
