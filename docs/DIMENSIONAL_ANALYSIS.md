# RGCS v2 — Dimensional Analysis of Every Numbered Equation

**Author:** Sub-Agent 02
**Date:** 2026-07-14
**Scope:** Every equation RGCS-M.0–M.61 in `MATHEMATICAL_MODEL.md`. Notation per `NOTATION_AND_UNITS.md`. `X` denotes the declared observable unit of a measurement campaign (m/s, V, Pa, …); it cancels wherever required. `[—]` = dimensionless. Unit-mixing rules: geometry formulas operate in mm; wave formulas require m and s — every mm→m conversion appears explicitly in the equation or the implementing function signature.

| Eq. | LHS | RHS analysis | Verdict |
|---|---|---|---|
| M.0 | state tuple | typed container; each member checked at its own row | PASS (composite) |
| M.1 | A [mm²] | [—]·[mm²]·[—] | PASS |
| M.2 | A [mm²] | [—]·[mm²]·[—] | PASS |
| M.3 | r_a [mm] | [mm]·[—] | PASS |
| M.4 | h [mm] | [mm]·tan([rad]) = [mm]·[—]; angle converted deg→rad explicitly | PASS |
| M.5 | V [mm³→cm³] | [mm]·[mm²] summed = [mm³]; ÷1000 → cm³ conversion explicit | PASS |
| M.6 | m [g] | [g/cm³]·[cm³] | PASS |
| M.7 | root equation [g] = [g] | ρV(s_D) and m* both g; s_D [—] | PASS |
| M.8 | f_ax [Hz = s⁻¹] | [m/s]/[m] = s⁻¹; L converted mm→m explicitly (÷1000) | PASS |
| M.9 | L_N [m→mm] | [m/s]/([—]·[s⁻¹]) = m; ×1000 → mm explicit | PASS |
| M.10 | v_L [m/s] | [m/s]·(1 + [—]); σ_v = [—]·[m/s] = m/s | PASS |
| M.11 | u(f)/f [—] | u_v [—] | PASS |
| M.12 | N_eff [—] | [Hz]/[Hz]; interval intersection of Hz intervals | PASS |
| M.13 | f_n² [Hz²] | f_b² [Hz²] + ([—]·[m/s]/([—]·[m]))² = [s⁻¹]² = Hz²; R_χ mm→m explicit | PASS |
| M.14 | κ_χ [Hz] | [m/s]/([—]·[m]) = s⁻¹ | PASS |
| M.15 | u(f_n)² [Hz²] | ([—])²·[Hz²] + ([—])²·[Hz²]·[—] — each ∂f/∂· term dimensionless or Hz-carrying as shown; f_b/f_n [—] × u(f_b) [Hz] → Hz | PASS |
| M.16 | u_n^±(χ) [—] | sin/cos of [rad]·[—]; normalized shapes dimensionless | PASS |
| M.17 | rule (no equation beyond f_{n=0} = f_b [Hz]) | Hz = Hz | PASS |
| M.18 | ε_R^(f) [—] | ([Hz²] − [Hz²])/[Hz²] | PASS |
| M.19 | ε [—] | (1 + [—])² − 1 | PASS |
| M.20 | ε_Q [—] | 1/Q_eff [—]; bin edges pure numbers × ε_Q | PASS |
| M.21 | Span [Hz] | max of {Hz, [—]·Hz, [—]·Hz} | PASS |
| M.22 | ε_corr [—]; u(ε_R) [—] | frequencies × (1 + Σ[—]); quadrature sum of relative uncertainties [—] | PASS |
| M.23 | 𝐇 [Hz] | all entries Hz (a rotating-frame frequency matrix, not an energy Hamiltonian — stated) | PASS |
| M.24 | f_± [Hz] | Hz ± √(Hz² + Hz²) = Hz | PASS |
| M.25 | ϑ_mix [rad] | atan2(Hz, Hz) — arguments same unit, ratio dimensionless | PASS |
| M.26 | Γ_n [Hz] | [Hz]/[—] | PASS |
| M.27 | R_g [—] | [Hz]/[Hz] | PASS |
| M.28 | eigenproblem [Hz] | symmetric Hz matrix → Hz eigenvalues, dimensionless eigenvectors | PASS |
| M.29 | g [Hz] ∝ (2πR_χ)^(−1/2) [m^(−1/2)] | proportionality with dimensionful constant absorbed in the fitted prefactor g_0 [Hz·m^(1/2)]; scaling STATEMENT is a ratio test g(R₁)/g(R₂) = √(R₂/R₁) [—] | PASS (as ratio law) |
| M.30 | X(θ): [mm, mm, mm, rad] | R_0 e^{−aθ} [mm·—]; H·(1−[—]^{p_z}) [mm]; χ_0 + Ω_s·θ [rad + —·rad] | PASS |
| M.31 | a [—] | ln([—])/[—] | PASS |
| M.32 | λ_s [—] | −a + i, both dimensionless | PASS |
| M.33 | rκ [—] | 1/√(1+[—]²); note κ itself is [mm⁻¹], r·κ cancels | PASS |
| M.34 | ℓ_pl [mm] | [mm]·[—]/[—]·(1 − e^{−[—]}) | PASS |
| M.35 | ℓ_3D [mm] | sum of Euclidean norms of mm differences | PASS |
| M.36 | R_χ^(s) [mm] | [mm]/[—] | PASS |
| M.37 | R_χ,k [mm] | [mm]/[—] | PASS |
| M.38 | x_m [mm] | [mm]/2 | PASS |
| M.39 | x_g [mm] | (mm + mm − mm)/2 | PASS |
| M.40 | x_* [mm]; c_g [—] | selection of mm; mm/mm | PASS |
| M.41 | ξ [—]; N_x [—] | (mm − mm)/mm; exp(−[—]²) | PASS |
| M.42 | k_H [—] | Hz/Hz | PASS |
| M.43 | ΔM_H [g] | [g]·(1/[—]² − 1) | PASS |
| M.44 | k̃_H [—] | mm/mm | PASS |
| M.45 | f_meas [Hz] | Hz·(1 + Σ[—]) + ε_ns; ε_ns must be in Hz here (frequency-observation noise) — declared | PASS |
| M.46 | ż_n [X/s] | (s⁻¹ + s⁻¹ + i·rad/s)·X → X/s (rad dimensionless); β_nm|z|²z: [s⁻¹X⁻²]·[X²]·[X] = X/s; K_nm z_m: [s⁻¹]·[X] = X/s | PASS |
| M.47 | Ȧ_n [X/s] | s⁻¹·X + s⁻¹X⁻²·X³ + s⁻¹·X·[—] | PASS |
| M.48 | φ̇_n [rad/s] | ω_n [rad/s] + s⁻¹·(X/X)·[—] = s⁻¹ ≡ rad/s (rad dimensionless); singular as A_n→0 — implementation integrates M.46 in complex form to avoid the 1/A_n singularity | PASS (with implementation note) |
| M.49 | γ_n [s⁻¹] | [rad/s]/[—]; rad dimensionless | PASS |
| M.50 | χ(t) [rad] | rad + [—]·rad; 2π·f_d·t: [—]·s⁻¹·s = [—] interpreted as rad — 2π carries rad/cycle | PASS |
| M.51 | Ω_j [rad/s] | d[rad]/d[s] | PASS |
| M.52 | σ_φ² [s⁻²] | (1/3)·Σ[rad/s]² = s⁻² (rad dimensionless); NOTE the GAN original is likewise [time⁻²] — substitution map H_i→Ω_j preserves dimension | PASS |
| M.53 | Σ_φ,jk [—] | 1 − |mean of unit-modulus complex numbers| ∈ [0,1] | PASS |
| M.54 | Σ̄_φ(t) [—] | [—]·e^{−[s]/[s]}; power law (1+t/t_0)^{−α} needs t_0 [s], α [—]; stretched form β_s [—] | PASS |
| M.55 | z(t) [X] | X + i·X | PASS |
| M.56 | 𝒞_w(t) [—] | 𝒩_w has unit [X⁻²·s⁻²] cancelling the ∫dτ|correlation| unit [X²·s²]; normalization by construction (perfect tone → 1) makes 𝒞 dimensionless | PASS |
| M.57 | G_c [—]; d_c [—] | (X − X)/X; (X − X)/X | PASS |
| M.58 | D_f, P_φ, S [—] | 1/(1+([—]·[—])²); cos²(π·[cycles]) — π carries rad/half-cycle, argument rad; product of dimensionless factors | PASS |
| M.59 | −2 ln L [—] | (Hz − Hz)²/Hz² + ln(Hz²) — the ln term requires s_i in declared units; standard likelihood convention (constant offset irrelevant to fits) — declared | PASS (convention noted) |
| M.60 | AIC/BIC [—] | counts and log-likelihoods | PASS |
| M.61 | R̄ [—]; Z_R [—] | modulus of mean unit vectors; [—]·[—]² | PASS |

## Notes and non-trivial checks

1. **M.13 golden check:** 1 × 6310/(2π × 0.100) = 10042.6769091 Hz ✓ (G-06). Dimensions: (m/s)/m = s⁻¹.
2. **M.24 golden check:** (1000+1000)/2 ± √(0 + 10²) = 990/1010 Hz ✓ (G-08).
3. **M.39 golden check:** (154.052734375 + 17.415434 − 14.812763)/2 = 78.3277 mm; L − x_g = 75.7250 mm = WB5 Sheet 13 value ✓ (frame conversion, closes D-01).
4. **M.43 golden check:** 154 g × 0.5 × (1/0.9866751189² − 1) = 2.0937873 g ✓ (G-09).
5. **M.46/M.47/M.48 consistency:** substituting z_n = A_n e^{iφ_n} into M.46 and separating real/imaginary parts reproduces M.47 and M.48 exactly; hence a single dimensional check of M.46 covers all three (each performed anyway above).
6. **M.29 caveat:** a bare proportionality between quantities of different dimensions is not an equation; it is frozen as the dimensionless ratio law g(R₁)/g(R₂) = √(R₂/R₁), which is what the test measures.
7. **rad convention:** radians are treated as dimensionless throughout (SI); factors of 2π always carry the cycle↔radian conversion explicitly (M.14, M.50, M.58).
8. **mm↔m discipline:** M.8, M.9, M.13, M.14 are the only equations mixing mm inputs with m/s wave speeds; each implementing function must perform the ÷1000 (or ×1000) conversion exactly once, at the location shown in `MATHEMATICAL_MODEL.md`, and unit-suffixed argument names make the contract explicit (Agent 04).
9. **X-unit discipline:** β_nm is the only coefficient whose unit depends on the observable unit X; campaigns must declare X before β_nm fits are comparable across data sets. Normalizing z_n by a reference amplitude A_ref (making z dimensionless and β_nm [s⁻¹]) is the recommended implementation, with A_ref recorded.
