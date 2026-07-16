# V4 Mathematical Model Plan — RSCS 2.0

**Status:** PLANNING. **No new physics** (DV4-012): every governing
equation below is standard continuum mechanics / linear piezoelectricity
/ geometric optics, classified **EST** with textbook provenance. v4
*composes and validates* them. New ids are registered here before first
use (governance path); the machine registry row (id, signature, units,
class, provenance, exclusions, module, tests, doc-target) is authored
when the object is implemented, not in this pass.

Frozen and untouched: `RGCS-M.*`, `RSCS-C.*`, `RSCS-O.*`. All ids below
carry the `RSCS2-` prefix (DV4-002).

## 1. Governing & constitutive equations — `RSCS2-E.*` (all EST)

| id | Name | Form | Provenance | Fidelity |
|---|---|---|---|---|
| RSCS2-E.1 | Linear elastodynamic eigenproblem | ∇·σ + ρω²u = 0; σ = C:ε; ε = sym∇u | continuum mechanics (Landau–Lifshitz; Achenbach) | L1–2 |
| RSCS2-E.2 | Isotropic constitutive | C = λ I⊗I + 2μ 𝕀 (Lamé) | standard | L1 |
| RSCS2-E.3 | Anisotropic constitutive (Voigt) | σ_i = C_ij ε_j, C = α-quartz 6×6 | frozen `rgcs_core.anisotropy` (Bechmann 1958; Auld 1973) | L2 |
| RSCS2-E.4 | Christoffel relation | Γ_ik = c_ijkl n_j n_l; Γu = ρv²u | reproduces frozen `RSCS-O.17` (validation anchor) | L2 |
| RSCS2-E.5 | Linear piezoelectric coupling | σ = C:S − eᵀ·E; D = e:S + ε·E; ∇·σ+ρω²u=0; ∇·D=0 | IEEE 176 std piezoelectricity; Auld | L3 |
| RSCS2-E.6 | Thermal perturbation | C(T)=C₀+(∂C/∂T)ΔT; ρ(T); geometric CTE | standard thermoelastic (perturbative) | L4 |
| RSCS2-E.7 | Fixture/mass-loading perturbation | added-mass/elastic-support boundary term | reproduces v3 loading (H-08 family) | L4 |
| RSCS2-E.8 | Geometric ray + Snell | n₁sinθ₁=n₂sinθ₂; ordinary/extraordinary indices | frozen `rgcs_core.optics`; Hecht | L5 |
| RSCS2-E.9 | Photoelastic index perturbation | Δ(1/n²)_I = p_IJ S_J | frozen optics; Narasimhamurty | L5 |
| RSCS2-E.10 | Quasi-static magnetic (coil) | ∇×H=J, ∇·B=0, B=μ₀H (magnetoquasistatic) | standard EM (Jackson); integration-contract level | L5 |
| RSCS2-E.11 | Modal drive projection | f_n = ∫ φ_n·b dV (body-force → modal force) | standard modal analysis | L3–5 |
| RSCS2-E.12 | Coupled-mode reduction | 2-mode H = diag(f)+g; K=i·2πg | reproduces frozen `RSCS-O.4`/`RGCS-M.24` (anchor) | L2–3 |

**Exclusions binding on every row** (extend EXCLUSION_MATRIX): no
therapeutic/consciousness/metric-engineering import; no literal compact
quartz dimension; ether is not established physics; a visualization
containing circulation does not establish a physical vortex.

## 2. Mesh & geometry objects — `RSCS2-G.*` (EST/ENG)

| id | Name | Class | Notes |
|---|---|---|---|
| RSCS2-G.1 | Geometry source record | ENG | SCAD-exported / STL / OBJ / STEP / Gmsh + coordinate-frame provenance |
| RSCS2-G.2 | Tetrahedral volume mesh | ENG | nodes, tets, quality metrics |
| RSCS2-G.3 | Surface mesh | ENG | facets, normals |
| RSCS2-G.4 | Region/boundary tag set | ENG | material regions, surfaces, electrodes, coil, optical-entry, fixture |
| RSCS2-G.5 | Mesh quality diagnostic | DER | aspect ratio, min dihedral, Jacobian, edge-length histogram |
| RSCS2-G.6 | Deterministic mesh manifest | ENG | element counts, sha256, generator+version, seed, frame |

## 3. Boundary operators — `RSCS2-B.*` (EST)

| id | Name | Reproduces / basis |
|---|---|---|
| RSCS2-B.1 | Free (traction-free) | rigid-body modes present; standard |
| RSCS2-B.2 | Fixed (Dirichlet) | closed-form cantilever anchor |
| RSCS2-B.3 | Elastic support (spring foundation) | Robin BC |
| RSCS2-B.4 | Mass loading / hand-loading-equivalent | v3 loading (H-08/H-08b), added-mass |

## 4. Solver operators — `RSCS2-S.*` (EST/DER)

| id | Name | Class | Basis |
|---|---|---|---|
| RSCS2-S.1 | Sparse generalized eigensolve Ku=ω²Mu | EST | scipy `eigsh`/`lobpcg` (CPU authority); SLEPc optional |
| RSCS2-S.2 | Rigid-body mode handling | EST | null-space projection / shift-invert |
| RSCS2-S.3 | Modal normalization (mass-orthonormal) | EST | uᵀMu=I |
| RSCS2-S.4 | Orthogonality/residual check | DER | uᵢᵀMuⱼ=δ; ‖Ku−ω²Mu‖ |
| RSCS2-S.5 | Harmonic response | EST | (K−ω²M)u=f driven response |
| RSCS2-S.6 | Coupled-mode reduction | DER | project to 2–N modal subspace; anchor to RSCS2-E.12 |
| RSCS2-S.7 | Convergence estimator | DER | eigenvalue vs mesh size / DoF; Richardson |

## 5. Accelerator operators — `RSCS2-A.*` (ENG)

| id | Name | Notes |
|---|---|---|
| RSCS2-A.1 | Backend-neutral array API | numpy-subset seam; CPU default |
| RSCS2-A.2 | Device capability detection | enumerate, memory budget, dtype support |
| RSCS2-A.3 | Chunked sparse matvec / SpMV | memory-budgeted; CPU + CuPy + PyOpenCL |
| RSCS2-A.4 | Precision policy | f64 authority; f32 opt-in w/ recorded error bound |
| RSCS2-A.5 | CPU/GPU parity harness | per-op tolerance record → the four-status ladder |

## 6. Field / eye diagnostics — `RSCS2-D.*` (DER unless noted)

Fifteen registered diagnostics + the consensus functional; full
definitions and classifications in `V4_EYE_DIAGNOSTICS_SPEC.md`. Ids
RSCS2-D.1..15 (displacement amplitude, strain-energy density,
kinetic-energy density, piezo charge/electric-energy density, optical
intensity + path sensitivity, drive-mode overlap, cross-modal overlap,
local phase coherence, phase singularity/topological charge,
displacement vorticity/circulation, Poynting circulation,
boundary-perturbation sensitivity, mesh persistence, uncertainty
persistence, cross-channel agreement) + **RSCS2-D.0 Eye Consensus
Functional** (DER/ENG; never EST until experimentally correlated).

## 7. Validation benchmarks — `RSCS2-V.*` (EST references)

| id | Benchmark | Reference truth |
|---|---|---|
| RSCS2-V.1 | Uniform free-free rod | analytic longitudinal eigenfrequencies |
| RSCS2-V.2 | Fixed-free Euler–Bernoulli beam | closed-form βₙL roots + mode shapes |
| RSCS2-V.3 | Timoshenko correction | shear/rotary-inertia corrected eigenfrequencies |
| RSCS2-V.4 | Tuning fork | symmetric/antisymmetric modes; analytic + published |
| RSCS2-V.5 | Isotropic cube/sphere | published eigenvalues |
| RSCS2-V.6 | α-quartz Christoffel axes | **reproduces frozen `rgcs_core.anisotropy`** (DV4-009) |
| RSCS2-V.7 | Piezoelectric single element | constitutive round-trip vs IEEE-176 form |
| RSCS2-V.8 | Mesh-refinement convergence | monotone eigenvalue convergence, order estimate |
| RSCS2-V.9 | Degenerate two-mode splitting | **reproduces frozen `RSCS-O.4`/`RGCS-M.24`** (DV4-009) |
| RSCS2-V.10 | Asymmetric geometry | diagnostic shifts in the predicted direction |

## 8. Uncertainty & inverse operators — `RSCS2-U.*` (DER)

| id | Name | Basis |
|---|---|---|
| RSCS2-U.1 | Uncertainty Monte Carlo | sample material/dimension σ; → linear `UncertainValue` in small-σ limit (regression anchor) |
| RSCS2-U.2 | Frequency-response fit | fit registered model families to |FRF| |
| RSCS2-U.3 | Mode matching | measured↔computed mode correspondence (MAC) |
| RSCS2-U.4 | Parameter estimation (deterministic) | least-squares w/ CIs |
| RSCS2-U.5 | Bayesian parameter estimation | posterior w/ registered, classified priors |
| RSCS2-U.6 | Held-out validation / null-model comparison | no dataset leakage; null-model baseline |

## 9. Classification & provenance rules (unchanged, restated)

Every `RSCS2-*` object is EST (standard math), DER (project
computation), HYP (falsifiable claim), SRC (source), or ENG
(engineering). The v3 firewall applies: a DER/EST output computed from
HYP/SRC/ENG inputs is rejected without an explicit boundary. Solver
outputs are DER from their declared inputs; fitted parameters carry
uncertainty; **no solver output upgrades a HYP**, and no diagnostic
upgrades the SRC "eye" to EST.
