# Magnetic shell model audit

Magnetics are geometry: Sigma_s(t) = {x : W(x,t) + kappa*M(x,t) =
C_s(t)}. The bounded scalar family (all run, all retained;
`refuse_post_reveal_scalar_selection` bans picking the best after
seeing the training anchor; no per-vector offsets — locked by a
signature test):

[
 {
  "member_id": "GRAVITY_ONLY",
  "scalar": "NONE",
  "kappa": 0.0,
  "status": "ACTIVE",
  "fractional_uncertainty": 0.0,
  "note": "null member: pure gravity level surfaces (kappa = 0)."
 },
 {
  "member_id": "DIPOLE_B_MAGNITUDE",
  "scalar": "B_MAGNITUDE",
  "kappa": 200000000.0,
  "status": "ACTIVE",
  "fractional_uncertainty": 0.2,
  "note": "kappa*|B| ~ 1e4 m^2/s^2 at the surface (~1 km of geopotential)."
 },
 {
  "member_id": "DIPOLE_SCALAR_POTENTIAL",
  "scalar": "SCALAR_POTENTIAL",
  "kappa": 0.002,
  "status": "ACTIVE",
  "fractional_uncertainty": 0.2,
  "note": "signed hemispheric deformation via the dipole scalar potential."
 },
 {
  "member_id": "DIPOLE_INCLINATION",
  "scalar": "INCLINATION",
  "kappa": 6000.0,
  "status": "ACTIVE",
  "fractional_uncertainty": 0.2,
  "note": "dip-angle-derived correction, kappa*I ~ 1e4 m^2/s^2 at the pole."
 },
 {
  "member_id": "CRUST_CORRECTED",
  "scalar": "B_MAGNITUDE",
  "kappa": 200000000.0,
  "status": "BLOCKED_MISSING_DATA",
  "fractional_uncertainty": null,
  "note": "requires a lithospheric anomaly model; none ships, none is fabricated."
 },
 {
  "member_id": "CORE_PLUS_LITHOSPHERE",
  "scalar": "B_MAGNITUDE",
  "kappa": 200000000.0,
  "status": "BLOCKED_MISSING_DATA",
  "fractional_uncertainty": null,
  "note": "requires real IGRF-14 Gauss coefficients plus a crustal model; r12.igrf14root records the coefficient block and it is honoured."
 }
]

The magnetic source model is a declared tilted centred dipole with
linear epoch drift (moment 7.71e+22 A m^2 at
2025.0, rate -2.7e+19/yr; tilt
9.7 deg, rate -0.05 deg/yr).
No real IGRF-14 Gauss coefficient set ships in this repository
(r12.igrf14root: BLOCKED_MISSING_DATA) and that block is honoured: the
crust-corrected and core+lithosphere members REFUSE evaluation instead
of fabricating coefficients. Epoch dependence of the deformation is
locked by test (1975 vs 2025 differ).
