# V4 Piezoelectric & Multiphysics Spec (RSCS2-E.5/E.6/E.7/E.11)

**Status:** PLANNING. Staged fidelity Levels 0–5; **no level is required
for the first usable milestone** (M3 is L1–2). All equations EST/standard.

## Fidelity levels

| Level | Physics | Governing | Milestone |
|---|---|---|---|
| L0 | analytic / reduced (reuse v3 `rgcs_core`) | frozen | M0 (exists) |
| L1 | isotropic 3D elasticity | RSCS2-E.1/E.2 | M3 |
| L2 | anisotropic α-quartz elasticity | RSCS2-E.3/E.4 | M4 |
| L3 | coupled piezoelectric elastodynamics | RSCS2-E.5 | M4 |
| L4 | thermal + fixture perturbations | RSCS2-E.6/E.7 | M6 |
| L5 | optical/photoelastic + EM drive projection | RSCS2-E.8..E.11 | M6 |

## L3 — piezoelectric coupling (RSCS2-E.5, EST)

Linear piezoelectricity (IEEE 176): σ = C:S − eᵀ·E, D = e:S + ε·E,
with ∇·σ + ρω²u = 0 and ∇·D = 0 (quasi-static electric field). FE form:
the coupled generalized eigenproblem in (u, φ) with blocks K_uu, K_uφ,
K_φφ; electrode-tagged surfaces impose Dirichlet potential; open surfaces
are charge-free. Outputs: electromechanical modes, effective coupling
coefficients k² per mode (DER), electric-energy-density field (feeds
RSCS2-D.4). **Single-element constitutive round-trip** (RSCS2-V.7)
validates the tensors against the IEEE-176 form before any full crystal.

## L4 — thermal & fixture perturbations (RSCS2-E.6/E.7, EST-perturbative)

- Thermal: C(T)=C₀+(∂C/∂T)ΔT and geometric CTE → eigenfrequency drift
  predictions with uncertainty; perturbative (first-order) unless a
  benchmark forces full re-solve. Reproduces the v3 thermal-drift
  systematic magnitude (~1e-4/K) as a cross-check.
- Fixture / hand-loading-equivalent: added-mass/elastic-support boundary
  (RSCS2-B.3/B.4) reproducing the v3 loading model (H-08/H-08b) within
  its band; used to bound the fixture systematic in eye robustness.

## L5 — drive projection (RSCS2-E.11, EST)

Body-force / surface-traction / electric drive → modal force
f_n = ∫ φ_n·b dV. Coil EM drive (`V4_COIL_AND_EM_COUPLING_SPEC`) and
optical intensity/polarization modulation (`V4_OPTICAL_MODELLING_SPEC`)
enter here as the source term b, synchronized via the frozen v3 timing
phase budget (`rgcs_core.timing`). This is projection onto modes, **not**
a new full-wave solve.

## Coupled-mode reduction

The N-mode FE result reduces to the frozen 2-mode coupled picture
(RSCS2-S.6 → RSCS2-E.12) where strong coupling holds; the reduction
must reproduce `rgcs_core.coupled_modes` (RSCS2-V.9).

## Tests

V.7 (piezo single-element), electromechanical coupling k² sanity vs
literature order-of-magnitude (DER, not a precision claim), thermal-drift
sign/magnitude vs v3, fixture shift vs v3 loading band, drive-projection
energy conservation, reduction anchor V.9.
