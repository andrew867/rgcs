# Reference System Comparison (RGCS v4, Agent 10)

Status: VALIDATED (RSCS2-V.2/V.3/V.4/V.5/V.9 green)
Evidence: `evidence/v4/agent10/`
Tests: `tests/v4/test_rscs2_refsystems.py`, `tests/v4/test_rscs2_solver.py`

The v4 machinery is proven on **conventional reference systems whose
answers are known independently of any crystal application**, per
DV4-008 and the user decision selecting the acoustic cavity as the
fourth reference system (DV4-013).

## 1. Cantilever beam (RSCS2-V.2 / V.3) — validated in Agent 03

Fixed-free steel beam vs Euler–Bernoulli (slender) and Timoshenko
(thick) closed forms. First bending modes within 0.5% (EB, converged
mesh) and +0.03% (thick beam z-bend vs Timoshenko). This is the M3
gate that closed defect V4-D-001.

## 2. Isotropic cube Lamé mode (RSCS2-V.5) — validated in Agent 03

The exact ν-independent Lamé torsional mode f = v_s/(√2·a) (Demarest,
JASA 49, 768 (1971)) appears in the free-cube FEM spectrum within
0.03–0.05% at ν = 0.25 and ν = 0.33.

## 3. Acoustic cavity (RSCS2-V.4a) — EXACT reference

Rigid-wall rectangular cavity, Helmholtz eigenproblem
(P2 scalar elements, K = ∫∇p·∇q, M = ∫pq/c²):

- 0.5 × 0.4 × 0.3 m box, c = 343 m/s: first 8 FEM modes within
  **1.7 × 10⁻⁴** relative of the exact closed form
  f = (c/2)·√((l/Lx)² + (m/Ly)² + (n/Lz)²)
  (`cavity_fem_vs_exact.csv`).
- Exactly one constant-pressure (f = 0) mode — the scalar analogue of
  the rigid-body count check.
- **Degeneracy handling:** a cubic cavity's first mode is exactly
  3-fold degenerate (100/010/001, symmetry-protected). The FEM
  resolves all three within 10⁻³ relative spread at the exact
  frequency — degeneracy is reported, not averaged away.

## 4. Tuning fork (RSCS2-V.4b) — mode-pair structure and CMR

Steel fork (E = 210 GPa, ν = 0.3, ρ = 7850 kg/m³), 60 mm prongs
6 × 6 mm, 10 mm gap, 15 mm base; gmsh OCC boolean union (subprocess,
DV4-006).

**Coupling-regime finding (diagnosed, not assumed):**

| Configuration | In-plane pair | Split | Regime |
|---|---|---|---|
| Free fork | 1242.7 / 3941.3 Hz | 2699 Hz | STRONG (sym mode hybridizes with base flexure) |
| Base-fixed fork | 1233.4 / 1242.1 Hz | **8.70 Hz** | WEAK (prongs couple only through base elasticity) |

The free fork's first four elastic modes are x-antisym (1242.7),
y-antisym out-of-plane (1576.8), x-sym (3941.3), y-sym (5132.2) —
identified by signed mean tip displacement per component. The naive
assumption "modes 0 and 1 are the pair" is FALSE for a free fork; the
test suite identifies the in-plane pair by tip-x amplitude instead.

**Common-mode rejection (base-fixed pair):** normalized base x-motion
is 0.0006 (antisym) vs 0.0023 (sym) — ratio **0.26**, the classical
reason tuning forks ring long: the antisymmetric mode exerts no net
force on the mount.

## 5. Avoided crossing vs FROZEN v3 model (RSCS2-V.9)

Conservative-extension anchor (DV4-009): the weakly coupled base-fixed
pair (S₀ = 8.70 Hz, f̄ = 1237.8 Hz, g = S₀/2) is detuned by adding tip
mass σ to prong A only. The isolated-prong detuning is mapped by the
Rayleigh formula fₐ = f̄·√(m_eff/(m_eff+Δm)), m_eff = 0.2427·m_prong
(validated in test_mass_loading_b4). FEM splitting vs the **frozen**
`rgcs_core.coupled_modes.static.coupled_two_mode` prediction
S = √(Δ² + S₀²):

| σ (kg/m²) | detuning Δ (Hz) | FEM split (Hz) | frozen model (Hz) | error |
|---|---|---|---|---|
| 0.00 | 0.00 | 8.703 | 8.703 | 0% (anchor) |
| 0.25 | −1.35 | 8.807 | 8.807 | <0.01% |
| 0.50 | −2.70 | 9.078 | 9.112 | 0.37% |
| 1.00 | −5.38 | 10.052 | 10.231 | 1.8% |
| 1.50 | −8.04 | 11.463 | 11.850 | 3.4% |
| 2.00 | −10.69 | 13.166 | 13.783 | 4.7% |
| 3.00 | −15.93 | 17.061 | 18.152 | 6.4% |

(values from `avoided_crossing_v9.csv`.) Maximum deviation **6.4%**, growing smoothly
with detuning as the Rayleigh single-mode map becomes cruder — the
hyperbolic avoided-crossing structure of the frozen model is
quantitatively reproduced by full 3-D FEM on an independent system.
Plot: `avoided_crossing_v9.png`.

## Verdict

All four conventional reference systems reproduce independent physics
(closed forms, published exact solutions, the frozen v3 two-mode
model) with quantified error. The machinery is trustworthy outside the
crystal application.
