# V4 CPU Solver Spec — `rscs2_core.fem` + `.solve` (RSCS2-S.*, RSCS2-B.*)

**Status:** PLANNING. **The CPU solver is the numerical authority
(DV4-004).** Stack: numpy + scipy + **scikit-fem** (BSD-3, pure-Python,
scipy-only) for assembly; scipy sparse eigensolvers for the eigenproblem.
No GPU, no heavy deps required for the first usable milestone (M3).

## 1. Assembly (`rscs2_core.fem`)

- scikit-fem elements: tetrahedral P1/P2 for 3D elasticity; the
  displacement field is a vector element (3 DoF/node). Assemble the
  stiffness **K** = ∫ Bᵀ C B dV and consistent mass **M** = ∫ ρ NᵀN dV
  (RSCS2-E.1). C from RSCS2-E.2 (isotropic, L1) or RSCS2-E.3 (Voigt
  anisotropic, L2, from frozen `rgcs_core.anisotropy`).
- Piezoelectric assembly (L3, RSCS2-E.5): the coupled block
  [[K_uu, K_uφ],[K_φu, −K_φφ]] with the scalar-potential DoF and the
  e/ε tensors; electrode tags give Dirichlet potential BCs.
- Output: scipy CSR sparse K, M (and coupled blocks) + the DoF map back
  to mesh nodes/tags, all serialized deterministically.

## 2. Eigensolve (RSCS2-S.1)

- Generalized symmetric problem **K u = ω² M u**. CPU authority:
  `scipy.sparse.linalg.eigsh` (shift-invert, `sigma`) for the lowest N
  modes; `lobpcg` as an SPD alternative for large problems; dense
  `scipy.linalg.eigh` for small validation cases (the analytic
  benchmarks) as an independent cross-check.
- **Rigid-body modes (RSCS2-S.2):** for free bodies (RSCS2-B.1) the six
  zero(≈)-frequency modes are detected (ω²≈0 within a tolerance tied to
  conditioning) and either projected out (null-space deflation) or
  reported+separated; never silently mixed into the elastic spectrum.

## 3. Boundary operators (RSCS2-B.*)

Free (B.1, natural — nothing imposed, rigid modes handled), Fixed (B.2,
Dirichlet on tagged surfaces), Elastic support (B.3, spring stiffness
added to K on tagged surfaces), Mass/hand-loading (B.4, added-mass to M
on tagged contacts — reproduces v3 loading H-08 family within its band).

## 4. Post-processing

- **Normalization (RSCS2-S.3):** mass-orthonormal uᵀMu = I.
- **Checks (RSCS2-S.4):** cross-orthogonality uᵢᵀMuⱼ = δᵢⱼ (tol); modal
  residual ‖Ku − ω²Mu‖/‖ω²Mu‖ (tol) recorded per mode — a mode failing
  its residual is flagged, not reported as physical.
- **Harmonic response (RSCS2-S.5):** (K − ω²M) u = f for a projected
  drive f (RSCS2-E.11) over a frequency sweep → FRF for inverse fitting.
- **Coupled-mode reduction (RSCS2-S.6):** project to the 2–N modal
  subspace; the 2-mode case must reproduce frozen `rgcs_core.coupled_modes`
  splitting (RSCS2-V.9 / DV4-009).

## 5. Convergence (RSCS2-S.7)

Eigenvalue vs DoF over uniform refinement levels; Richardson order
estimate; a benchmark passes only when the converged value sits inside
the reference tolerance AND the observed order matches element theory
(≈2 for P1 eigenvalues, higher for P2) within a band.

## 6. Conservative-extension anchors (DV4-009, CI-gated)

- **RSCS2-V.6:** a thin α-quartz slab / plane-wave setup recovers
  `rgcs_core.anisotropy.wave_speeds` along X/Y/Z within rtol tied to
  mesh resolution → the solver provably reproduces frozen v3.
- **RSCS2-V.9:** two weakly-coupled identical resonators reproduce the
  2g splitting of frozen `RSCS-O.4`/`RGCS-M.24`.

## 7. Determinism & uncertainty

Deterministic serialization of K, M, modes (JSON+`.npz`); seeds fixed;
outputs compared tolerance-aware cross-platform. Every eigenfrequency is
wrapped as `UncertainValue` (frozen `rgcs_core.uncertainty`, RSCS-O.11)
carrying material + dimensional + mesh-discretization uncertainty for
downstream diagnostics and UQ (RSCS2-U.1).

## 8. Tests

Analytic-reference (V.1/V.2/V.3/V.5), Christoffel anchor (V.6), splitting
anchor (V.9), orthogonality, energy-balance (Σ modal energy vs input),
residual, rigid-body detection, convergence (V.8), dense-vs-sparse
cross-check on small cases, serialization round-trip, malformed-input
(singular M, disconnected mesh) loud failure, float32/float64 policy
(f64 authority; f32 only with a recorded error bound).
