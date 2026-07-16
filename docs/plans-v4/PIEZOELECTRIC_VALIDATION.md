# Piezoelectric Validation (Agent 06)

Module: rscs2_core/piezo.py (RSCS2-E.5, RSCS2-B.5). Tests:
tests/v4/test_rscs2_piezo.py (7; v4 suite 41/41).

- Constitutive: stress-charge form sigma=C:S-e^T.E, D=e:S+eps.E,
  quasi-static E=-grad(phi); symmetric saddle block
  [[Kuu,Kup],[Kup^T,-Kpp]]; phi eliminated by static condensation with
  grounded-DoF gauge. Tensors from the Agent 04 record (Bechmann 1958,
  IEEE-176), rotated consistently with crystal orientation.
- SINGLE-ELEMENT ENERGY PATCH: uniform strain + uniform field on a tiny
  mesh -- each discrete block energy equals its closed-form volume
  integral to 1e-9 (u.Kuu.u = V S:C:S; phi.Kpp.phi = V g.eps.g;
  u.Kup.phi = V e_kij g_k S_ij). This pins the tensor ordering and sign
  conventions mechanically.
- ZERO-e LIMIT: coupled solver reproduces the pure elastic spectrum to
  1e-9 relative (exact uncoupled reduction).
- OPEN vs SHORT: f_open >= f_short mode-by-mode; the X-cut bar
  length-extensional mode carries k_eff^2 in the physical band
  (0.002-0.05; quartz literature k~0.1 -> k^2~0.01). No precision claim
  beyond supplied tensors/BCs.
- ELECTRODE REVERSAL: +V/-V vs -V/+V gives exactly negated
  displacement; zero drive gives zero response (no artificial field).
- Mesh convergence (short-circuit f1 stable <2%, from above) and frame
  invariance (all three tensors rotated by a body-symmetry rotation ->
  spectrum unchanged at 2e-3).

Block symmetry: Kuu/Kpp symmetric to 5e-17; dielectric SPD enforced at
construction. Matrices: u = P2 vector, phi = P2 scalar, shared mesh.
