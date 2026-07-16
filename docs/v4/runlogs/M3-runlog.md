# Run log — Agent M3 (torsion / circulation / optical AM / chirality)

- Base commit: `5293188`. Owned paths:
  `rscs2_core/{quantity_registry,curves,torsion_mech,optical_am,
  circulation,chiral_phonon}.py`, `tools/v4/gen_m3_figures.py`,
  `tests/v4/test_v4c_torsion_oam.py`,
  `docs/v4/V4_TORSION_AND_CHIRALITY_TAXONOMY.md`,
  `docs/v4/proof/M3/`, `docs/v4/runlogs/M3-*`.

## Delivered

12-quantity registry with mechanical identity prohibition; Frenet-
Serret with helix/planar/degenerate fixtures (NaN, never fabricated);
Saint-Venant twist rate (exact) + square-bar torsional FEM benchmark
(overlap-identified mode, 5% vs warping closed form) + twist-profile
extraction + torque-mode projection; Stokes-checked circulation with
orientation signs and no-vortex-claim posture; canonical optical
SAM/OAM/helicity/transverse-spin/topological-charge diagnostics with
real-field winding guard and Poynting/canonical separation;
chiral two-mode phonon with capability-gated Zeeman interface
(quartz NOT_APPLICABLE; refuses default g factors). 5 hashed figures.

## Debugging record (honest)

- Straight-line curvature floor was absolute → scale-relative
  (roundoff curvature scales with coordinate size).
- Two of my test expectations were WRONG PHYSICS, caught by the
  implementations: (1) a uniform torque cannot excite free-free
  torsional modes (cos profile orthogonality) — now asserted as a
  null; (2) displaced zero-transverse-momentum beams have INTRINSIC
  (origin-independent) OAM — now asserted, with the extrinsic case
  demonstrated via a phase ramp. (3) np.isclose default atol swamped
  1e-24-scale comparisons → atol=0.
- Real-superposition "dark beam" exposes the vortex-claim trap: added
  the real-field guard returning charge 0 (gate D4/D5).

## Tests

`tests/v4/test_v4c_torsion_oam.py` → **14 passed** (gates D1–D7).
