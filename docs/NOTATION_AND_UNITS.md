# RGCS v2 — Notation and Units (FROZEN)

**Author:** Sub-Agent 02 (Mathematical Foundations, Notation, and Model Unification)
**Date:** 2026-07-14
**Status:** FROZEN. This table is the single project-wide authority on symbols and units. All agents (03 coherence, 04 core, 05 workbook/CAD, 06 protocols, 07 manuscript, 08 QA) defer to it. Any new symbol must be added here before use elsewhere.

## 0. Policy

1. **Single-owner base letters.** The following base letters have exactly one unsubscripted meaning and may not be reused bare: `p` (pair multiple), `a` (spiral pitch parameter), `Q` (quality factor), `S` (engineering merit score), `q` (spiral growth ratio per turn), `ρ` (mass density), `L` (crystal length), `g` (two-mode coupling), `n` (compact/parity mode index), `N` (axial harmonic index).
2. **Subscript rule.** A base letter may carry additional meanings only through registered subscripted forms in this table (e.g. `σ_x`, `σ_φ²`, `p_z`, `z_Q`). Unregistered subscripts are non-compliant.
3. **Units.** Every symbol has a canonical unit. Internal computation uses the canonical unit exactly; code identifiers carry unit suffixes (`length_mm`, `wave_speed_m_s`, `tau_c_s`). Display conversions never change stored values. Frequencies are in Hz, angular frequencies in rad/s, lengths in mm (geometry) or m (wave formulas — the conversion appears explicitly in the equation), masses in g, time in s.
4. **Classification** follows `SCIENTIFIC_CLASSIFICATION_POLICY.md`: Established / Derived / Hypothesis / Source claim. A symbol's classification is the classification of its *definition*, not of any particular value.
5. **Python types** refer to the target `rgcs_core` implementation (Agent 04). `float` means IEEE-754 double; arrays are `numpy.ndarray[float64]` unless stated; complex arrays are `numpy.ndarray[complex128]`.

## 1. Resolution of symbol collisions (closes INCONSISTENCY D-07)

| Collision (old corpus) | Frozen resolution |
|---|---|
| `p` = pair multiple (TEX §7) vs cone exponent (TEX §5) vs pulse-mode label (WB5) | `p` = pair multiple ONLY. Cone exponent → **`p_z`** (already used in WB2 Design Inputs "Cone exponent pz"). Pulse/drive modes are text enums (`"standard"`, `"half_spacing"`, `"double_rate"`), never a math symbol. |
| `a` = spiral pitch parameter vs GAN scale factor | `a` = spiral pitch parameter ONLY (`a = ln q / 2π`). GAN's scale factors are not adapted as symbols; RGCS per-axis observables use `Ω₁, Ω₂, Ω₃` (phase rates), never `a_i`. |
| `γ` = node fraction (TEX §10) vs Barbero–Immirzi (GAN) vs damping | `γ_n` = modal amplitude damping rate ONLY (rad/s). Node fraction → **`c_g`** (dimensionless, `x/L`). Barbero–Immirzi γ is excluded from RGCS (source-summary text only). Linewidths stay `Γ_n` (Hz, FWHM). |
| `σ` = node uncertainty vs GAN shear scalar | Bare `σ` is FORBIDDEN. Registered forms: `σ_x` (node position uncertainty, mm), `σ_φ²` (phase-rate shear scalar, s⁻²), `σ_v` (wave-speed standard uncertainty, m/s). |
| `S` = engineering score vs state vector 𝒮 (TEX §3) | `S` = engineering merit score ONLY. State vector renamed **`Ψ(t)`**. |
| `Q` = quality factor vs LT charge Q_E vs I/Q quadrature | `Q`, `Q_n`, `Q_eff` = quality factors ONLY. LT's charge is excluded (not adapted). I/Q quadratures → **`z_I(t)`, `z_Q(t)`**, components of the complex analytic signal `z(t)`. |
| `H` = spiral cone height vs coupled-mode matrix vs GAN Hubble rates | `H` (scalar, mm) = spiral cone height. `𝐇` (bold, matrix, Hz) = coupled-mode matrix. GAN's directional Hubble rates are NOT imported as `H_i`; the RGCS analogues are phase rates `Ω_j` (rad/s). |
| `Ω` = spiral phase winding (TEX §5) vs per-axis rates | `Ω_s` = spiral phase winding rate (rad per rad of θ, dimensionless). `Ω_j` (j = 1,2,3) = per-axis instantaneous phase rates (rad/s). |
| `θ` = spiral polar angle vs mixing angle vs parameter vector | `θ` = spiral polar angle ONLY (rad). Mixing angle → `ϑ_mix` (rad). Model parameter vector → `Θ` (capital). |
| `ρ` = density vs phase residue (TEX §13) | `ρ` = mass density ONLY (g/cm³ display, kg/m³ internal where SI needed). Phase residue in cycles → **`r_φ`**. |
| `ε` = resonance offset vs noise | `ε_R^(f)` = resonance offset (dimensionless, signed). Measurement noise → `ε_ns` (units of the observable). |

## 2. Frozen symbol table

### 2.1 Crystal geometry and material

| Symbol | Definition | Unit | Domain/Range | Classification | Source / derivation | Python type |
|---|---|---|---|---|---|---|
| `L` | total crystal length (female/wide apex to male/narrow apex) | mm | (0, ∞) | Established (measured/spec) | RG-04 | `float` |
| `D_w`, `D_n` | wide / narrow cross-section diameter (per `diameter_mode`) | mm | (0, ∞), `D_w ≥ D_n` | Established | RG-04 | `float` |
| `N_f` | facet (side) count of the regular polygonal section | — | integer ≥ 3 | Established | RG-04 | `int` |
| `α_f`, `α_m` | female (wide) / male (narrow) termination angle, per `angle_mode` ∈ {face_slope, axis_to_face, apex_included} | deg | (0, 180) | Source claim (values 51.843°, 60°) / Established (conventions) | RG-04, RG-16 | `float` + `str` enum |
| `r_a` | apothem of polygonal section | mm | (0, ∞) | Established | RGCS-M.3 | `float` |
| `h_f`, `h_m` | female / male cap (termination) height | mm | (0, L), `h_f + h_m < L` | Derived | RGCS-M.4 | `float` |
| `h_s` | shaft (frustum) length, `L − h_f − h_m` | mm | (0, L) | Derived | RGCS-M.4 | `float` |
| `A_w`, `A_n` | wide / narrow polygonal section area | mm² | (0, ∞) | Established | RGCS-M.1/M.2 | `float` |
| `V` | total crystal volume | cm³ | (0, ∞) | Derived | RGCS-M.5 | `float` |
| `m` | crystal mass | g | (0, ∞) | Derived (predicted) or Established (measured) | RGCS-M.6 | `float` |
| `ρ` | mass density of α-quartz | g/cm³ | (0, ∞); default 2.65 | Established (handbook; citation required per D-19) | RG-04 | `float` |
| `s_D` | diameter scale factor in the density-inverse problem | — | (0, ∞) | Derived | RGCS-M.7 | `float` |

### 2.2 Wave speed, ladder, harmonic classification

| Symbol | Definition | Unit | Domain/Range | Classification | Source / derivation | Python type |
|---|---|---|---|---|---|---|
| `v_L` | effective longitudinal wave speed along the crystal axis; a first-class UNCERTAIN parameter | m/s | (0, ∞) | Hypothesis (that a single effective scalar suffices) / Established (that quartz has direction-dependent speeds) | D-05; RGCS-M.10 | `UncertainValue` (dataclass: `mean: float`, `u_rel: float`) |
| `v̄_L` | central value of `v_L`; default 6310 m/s (consistent with α-quartz Z-axis longitudinal speed √(c₃₃/ρ) ≈ 6320 m/s; X-axis √(c₁₁/ρ) ≈ 5720 m/s) | m/s | (0, ∞) | Source claim (uncited corpus import) pending citation to a quartz elastic-constant reference | RG-01, D-19 | `float` |
| `u_v` | relative standard uncertainty of `v_L`; default 0.05 until specimen orientation is measured | — | [0, 1) | Derived (declared uncertainty budget) | RGCS-M.10 | `float` |
| `σ_v` | absolute standard uncertainty `u_v · v̄_L` | m/s | [0, ∞) | Derived | RGCS-M.10 | `float` |
| `f_0` | ladder base frequency; default 4096 Hz | Hz | (0, ∞) | Source claim (JH corpus) | RG-01 | `float` |
| `f_ax` | first-order axial half-wave frequency | Hz | (0, ∞) | Derived (from Established formula + Hypothesis A-01) | RGCS-M.8 | `UncertainValue` |
| `N` | axial harmonic index | — | integer ≥ 1 | Established (index) | RG-01 | `int` |
| `L_N` | ideal ladder length for harmonic N | mm | (0, ∞) | Derived | RGCS-M.9 | `UncertainValue` |
| `N_eff` | continuous harmonic coordinate `f_ax / f_0` | — | (0, ∞) | Derived | RGCS-M.12 | `float` |

### 2.3 Compact spectrum, parity, resonance offset

| Symbol | Definition | Unit | Domain/Range | Classification | Source / derivation | Python type |
|---|---|---|---|---|---|---|
| `χ` | compact phase/path coordinate (closed coordinate; a modeling construct, NOT a spatial extra dimension) | rad | [0, 2π) | Hypothesis | RG-05, LT-01 | `float` |
| `R_χ` | effective compact radius: the FITTED parameter of the compact spectrum | mm | (0, ∞) | Hypothesis | RG-05, LT-09 | `float` |
| `v_χ` | compact-path propagation speed | m/s | (0, ∞) | Hypothesis; default v̄_L with u_v | RG-05 | `UncertainValue` |
| `κ_χ` | compact spectral slope `v_χ/(2π R_χ)` — the only combination identifiable from mode spacing alone | Hz | (0, ∞) | Derived | RGCS-M.14 | `UncertainValue` |
| `n` | compact/parity mode index | — | integer ≥ 0 | Established (index) | LT-03/04 | `int` |
| `f_b` | compact base frequency (analogue of base mass m_B) | Hz | [0, ∞) | Hypothesis | RG-05, LT-09 | `float` |
| `f_n` | frequency of compact mode n | Hz | [f_b, ∞) | Hypothesis (spectrum) | RGCS-M.13 | `UncertainValue` |
| `P` | parity family selector ∈ {P−, P+, all} | — | enum | Established (index-set definition) / Hypothesis (physical relevance) | RGCS-M.16 | `Literal["odd","even","all"]` |
| `f_m` | mediator-like (bridge) measured mode frequency | Hz | (0, ∞) | Established (measured) | RG-06 | `float` |
| `f_x` | matter-like (target) measured mode frequency | Hz | (0, ∞) | Established (measured) | RG-06 | `float` |
| `p` | pair multiple in the resonance offset; default 2 | — | (0, ∞) | Derived (choice), template LT Eq. (13) | RG-06 | `float` |
| `ε_R^(f)` | dimensionless signed resonance offset | — | (−1, ∞) | Derived (definition) / Hypothesis (enhancement near 0) | RGCS-M.18, LT-15 | `float` |
| `d_lin` | linear fractional detuning `f_m/(p f_x) − 1` | — | (−1, ∞) | Derived | RGCS-M.19 | `float` |

### 2.4 Coupled modes and quality factors

| Symbol | Definition | Unit | Domain/Range | Classification | Source / derivation | Python type |
|---|---|---|---|---|---|---|
| `𝐇` | coupled-mode frequency matrix (symmetric, real) | Hz | ℝ^{N×N} sym | Established | RGCS-M.23/M.28 | `numpy.ndarray` |
| `f_A`, `f_B` | uncoupled mode frequencies | Hz | (0, ∞) | Established (measured) | RG-07 | `float` |
| `g` | two-mode coupling strength | Hz | [0, ∞) | Derived (fitted) | RG-07 | `float` |
| `g_nm` | N-mode coupling matrix element | Hz | ℝ | Derived (fitted) | RGCS-M.28 | `numpy.ndarray` |
| `f_±` | hybrid eigenfrequencies | Hz | (0, ∞) | Established | RGCS-M.24 | `float` |
| `ϑ_mix` | two-mode mixing angle | rad | (−π/4, π/4] | Established | RGCS-M.25 | `float` |
| `Q`, `Q_n` | quality factor (of mode n) | — | (0, ∞) | Established (measured) | RG-07 | `float` |
| `Q_eff` | harmonic-mean effective Q, `2/(1/Q_A + 1/Q_B)` | — | (0, ∞) | Derived (modeling choice, D-19d) | RG-18 | `float` |
| `Γ_n` | FWHM linewidth of mode n, `f_n/Q_n` | Hz | (0, ∞) | Established (FWHM convention, stated) | RGCS-M.26 | `float` |
| `R_g` | strong-coupling ratio `2g/(Γ_A + Γ_B)` | — | [0, ∞) | Derived | RGCS-M.27 | `float` |

### 2.5 Spiral geometry and compact-radius prior

| Symbol | Definition | Unit | Domain/Range | Classification | Source / derivation | Python type |
|---|---|---|---|---|---|---|
| `q` | radial growth (contraction) ratio per turn | — | (1, ∞); default e | Source claim (JH spiral) / Established (log-spiral math) | RG-08 | `float` |
| `a` | spiral pitch parameter `ln q / (2π)` | — | (0, ∞) | Established | RGCS-M.31 | `float` |
| `T` | number of turns | — | (0, ∞); default 4 | Derived (design choice) | RG-08 | `float` |
| `θ` | spiral polar angle | rad | [0, 2πT] | Established | RGCS-M.30 | `numpy.ndarray` |
| `R_0` | outer spiral radius | mm | (0, ∞); default 60 | Derived (design choice) | RG-08 | `float` |
| `H` | cone height | mm | (0, ∞); default 80 | Derived (design choice) | RG-08 | `float` |
| `p_z` | cone (z-law) exponent | — | (0, ∞); default 1.5 | Derived (design choice) | RG-08, D-07 | `float` |
| `Ω_s` | spiral phase winding rate (cycles of χ per turn of θ) | — | (0, ∞); default 1 | Hypothesis | RG-08 | `float` |
| `λ_s` | planar scale-rotation eigenvalue `−a + i` | — | ℂ | Established | RGCS-M.32 | `complex` |
| `rκ` | dimensionless curvature invariant `1/√(1+a²)` | — | (0, 1] | Established | RGCS-M.33 | `float` |
| `ℓ_pl` | exact planar log-spiral arc length | mm | (0, ∞) | Established | RGCS-M.34 | `float` |
| `ℓ_3D` | numeric 3D path length (AUTHORITATIVE; converged polyline) | mm | (0, ∞) | Derived | RGCS-M.35 | `float` |
| `ℓ_k` | 3D path length of turn k | mm | (0, ∞) | Derived | RGCS-M.37 | `numpy.ndarray` |
| `R_χ^(s)` | spiral-derived compact-radius prior `ℓ_3D/(2πT)` | mm | (0, ∞) | Hypothesis (definition choice; averaging assumption A-07) | RGCS-M.36, RG-09 | `float` |
| `R_χ,k` | per-turn compact radius `ℓ_k/(2π)` | mm | (0, ∞) | Hypothesis (alternative definition) | RGCS-M.37 | `numpy.ndarray` |

### 2.6 Node coordinate (closes D-01)

Coordinate frame: **x is measured from the female (wide) apex toward the male (narrow) apex**, 0 ≤ x ≤ L. All node quantities are in this frame; conversions to the male frame are `L − x`.

| Symbol | Definition | Unit | Domain/Range | Classification | Source / derivation | Python type |
|---|---|---|---|---|---|---|
| `x_m` | metric center `L/2` | mm | (0, L) | Established | RGCS-M.38 | `float` |
| `x_g` | geometry node prior = shaft midpoint `(L + h_f − h_m)/2` | mm | (0, L) | Derived (from stated principle) | RGCS-M.39 | `float` |
| `x̂_e` | measured node coordinate (axial scan) | mm | [0, L] | Established (measured) | RG-11 | `float | None` |
| `x_*` | selected node: `x̂_e` if available, else `x_g` | mm | [0, L] | Derived (precedence rule) | RGCS-M.40 | `float` |
| `c_g` | node fraction `x_*/L` | — | [0, 1] | Derived | RGCS-M.40 | `float` |
| `x_d` | drive placement coordinate | mm | [0, L] | Established (set by experimenter) | RG-11 | `float` |
| `σ_x` | node position uncertainty / mode-width scale | mm | (0, ∞) | Established (measured) | RG-11 | `float` |
| `ξ` | normalized node offset `(x_d − x_*)/σ_x` | — | ℝ | Derived | RGCS-M.41 | `float` |
| `N_x` | node alignment factor `exp(−ξ²)` | — | (0, 1] | Derived (heuristic) | RGCS-M.41 | `float` |

**Retired estimators:** `geometry_balance_node_mm = h_m·L/(h_f+h_m)` (core.py, 70.806 mm; no derivation, presumed transcription error — DELETED); WB5 Sheet 13 estimator (75.725 mm) is exactly `L − x_g`, i.e. the same shaft midpoint expressed in the male-end frame — RETIRED as a separate quantity, documented as a frame conversion.

### 2.7 Loading, damping, corrections

| Symbol | Definition | Unit | Domain/Range | Classification | Source / derivation | Python type |
|---|---|---|---|---|---|---|
| `k_H` | loading factor `f_loaded/f_free` (measured) | — | (0, ∞) | Established (measured ratio) | RGCS-M.42 | `float` |
| `k̃_H` | length-shortfall proxy `L_actual/L_target` (NOT the same quantity as k_H) | — | (0, ∞) | Hypothesis (that it approximates k_H) | RGCS-M.44, D-10 | `float` |
| `η` | modal mass fraction; default 0.5 (asserted, unmeasured) | — | (0, 1] | Hypothesis | RG-10 | `float` |
| `M_eff` | effective modal mass `η·m` | g | (0, ∞) | Hypothesis-conditioned Derived | RGCS-M.43 | `float` |
| `ΔM_H` | equivalent added modal mass | g | ℝ | Hypothesis-conditioned Derived | RGCS-M.43 | `float` |
| `δ_k` | signed fractional correction term k ∈ {geometry, anisotropy, loading, T, fixture, drive} | — | ℝ, small | Derived (ledger form) | RGCS-M.45, LT-13/14 | `dict[str, float]` |

### 2.8 Dynamic state, coherence, anisotropy

| Symbol | Definition | Unit | Domain/Range | Classification | Source / derivation | Python type |
|---|---|---|---|---|---|---|
| `Ψ(t)` | full system state vector (see MATHEMATICAL_MODEL §1) | mixed | — | Derived (bookkeeping) | RGCS-M §1 | `dataclass State` |
| `z_n(t)` | complex modal amplitude `A_n e^{iφ_n}` | X (observable unit, declared per campaign: m/s, V, Pa…) | ℂ | Derived | RGCS-M.46 | `complex` / `ndarray[complex128]` |
| `A_n(t)` | modal amplitude `|z_n|` | X | [0, ∞) | Derived | RGCS-M.47 | `float` |
| `φ_n(t)` | modal phase | rad | ℝ (mod 2π for display) | Derived | RGCS-M.48 | `float` |
| `ω_n` | angular frequency `2π f_n` | rad/s | (0, ∞) | Established | — | `float` |
| `u_n` | normalized mode shape vector (sensor basis), ‖u_n‖ = 1 | — | ℝ^{N_s} or ℂ^{N_s} | Derived (FEA/measured) | RG-11, LT-02 | `numpy.ndarray` |
| `G_n` | linear gain rate supplied by drive to mode n | s⁻¹ | [0, ∞) | Hypothesis | RGCS-M.46 | `float` |
| `γ_n` | amplitude damping rate `ω_n/(2Q_n)` | s⁻¹ (rad/s) | (0, ∞) | Established | RGCS-M.49 | `float` |
| `β_nm` | saturation (self/cross) coefficient | s⁻¹·X⁻² | [0, ∞) | Hypothesis | RGCS-M.46 | `numpy.ndarray` |
| `K_nm` | mode-coupling rate (phase-reduction coupling) | s⁻¹ | ℝ, symmetric | Hypothesis | RGCS-M.46 | `numpy.ndarray` |
| `z(t)` | complex analytic/demodulated signal `z_I + i z_Q` | X | ℂ | Established | RGCS-M.55, KOS-05 | `ndarray[complex128]` |
| `z_I`, `z_Q` | in-phase / quadrature components | X | ℝ | Established | KOS-05 | `ndarray[float64]` |
| `𝒞_w(t)` | autocorrelation coherence over window w | — | [0, 1] | Established (definition) | RGCS-M.56, KOS-07 | `ndarray[float64]` |
| `w` | coherence analysis window length (declared analysis parameter) | s | (0, ∞) | Derived (choice; sensitivity analysis required) | KOS-07 | `float` |
| `b_w` | coherence noise baseline for window w (measured on noise) | — | (0, 1) | Established (measured) | KOS-07 | `float` |
| `Ω_j` | per-axis instantaneous phase rate, j = 1,2,3 | rad/s | ℝ | Derived (from measured φ_j) | RGCS-M.51 | `ndarray[float64]` |
| `σ_φ²` | phase-rate shear scalar (GAN Eq. 2 adaptation) | s⁻² | [0, ∞) | Derived (definition Established, GAN-05) | RGCS-M.52 | `float` |
| `Σ_φ(t)` | circular-variance phase-anisotropy tensor (3×3, symmetric, zero diagonal) | — | entries [0, 1] | Derived (definition) | RGCS-M.53 | `ndarray (3,3)` |
| `Σ_φ,0` | initial value of a chosen scalar reduction of Σ_φ | — | [0, 1] | Derived | RGCS-M.54 | `float` |
| `τ_c` | anisotropy/coherence relaxation time (FITTED; never imported from GAN) | s | (0, ∞) | Hypothesis (exponential model to TEST) | RGCS-M.54, GAN-09 | `float` |
| `V_j` | circular variance of channel j over window, `1 − R̄_j` | — | [0, 1] | Established (circular statistics) | RGCS-M.53 | `float` |
| `R̄_j` | mean resultant length of channel-j phase | — | [0, 1] | Established | RGCS-M.53/M.61 | `float` |

### 2.9 Coupling metric, drive, statistics

| Symbol | Definition | Unit | Domain/Range | Classification | Source / derivation | Python type |
|---|---|---|---|---|---|---|
| `Λ` | normalized drive–mode overlap | — | [0, 1] | Derived (measured, normalized) | RG-18, LT-11 | `float` |
| `r_φ` | phase residue | cycles | ℝ (typically [−0.5, 0.5]) | Derived | RG-12, D-13 | `float` |
| `Δ_f` | fractional detuning `(f_A − f_B)/√(f_A f_B)` | — | ℝ | Derived | RG-18 | `float` |
| `D_f` | detuning factor `1/(1 + (2 Q_eff Δ_f)²)` | — | (0, 1] | Derived (heuristic; Lorentzian half-power form) | RGCS-M.58 | `float` |
| `P_φ` | phase-closure factor `cos²(π r_φ)` | — | [0, 1] | Derived (heuristic) | RGCS-M.58 | `float` |
| `G_c` | control-subtracted fractional gain, clipped at 0 | — | [0, ∞) | Established (measured) | RGCS-M.57 | `float` |
| `d_c` | standardized effect size of control subtraction | — | ℝ | Established (statistics) | RGCS-M.57 | `float` |
| `S` | engineering merit score `|Λ|² D_f P_φ N_x G_c` — heuristic, never evidence | — | [0, ∞) | Derived (heuristic) | RGCS-M.58, RG-18 | `float` |
| `Θ` | model parameter vector (fit context) | mixed | — | Derived | RGCS-M.59 | `dict[str, float]` |
| `ε_ns` | additive measurement noise | X | ℝ | Established (model) | RGCS-M.59 | — |
| `Z_R` | Rayleigh test statistic `n_s R̄²` | — | [0, ∞) | Established | RGCS-M.61 | `float` |
| `n_s` | number of shots / repetitions | — | integer ≥ 1 | Established | KOS-06 | `int` |

## 3. Excluded symbols (never used in RGCS outputs)

Per the classification policy and ledger exclusion lists: κ (kinetic mixing), Q_E (LT charge), γ (Barbero–Immirzi), μ̄ᵢ, Δ (LQC area gap), m_Pl, t_Pl, σ₁ = 2.498 m_Pl (GAN coefficient), α_D, σ̄_e, and all dark-sector/BEC vocabulary applied to RGCS quantities. These may appear only in source-summary text.
