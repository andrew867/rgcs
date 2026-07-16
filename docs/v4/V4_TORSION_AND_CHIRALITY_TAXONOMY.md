# V4 Torsion and Chirality Taxonomy (Agent M3)

Machine authority: `rscs2_core/quantity_registry.py` (12 registered
quantities, each with dimensions, SI units, coordinate/origin
dependence, P/T behavior, state block, material predicate,
classification ceiling, forbidden aliases). Frozen boundary 7 is
enforced by type: `assert_identity` between distinct IDs ALWAYS
raises; `compare_geometric` returns a record with
`physical_identity: false`.

| quantity_id | units | validated fixture |
|---|---|---|
| torsion.mechanical.twist_rate | rad/m | Saint-Venant circular shaft (exact); square-bar FEM twist profile |
| torsion.mechanical.mode_energy | J | modal strain energy ½ω² |
| torsion.curve.frenet_serret | 1/m | helix κ=R/(R²+p²), τ=±p/(R²+p²); planar τ=0; straight line → NaN+flag (never fabricated) |
| circulation.mechanical.velocity / .displacement | m²/s, m² | rigid-rotation Stokes check (∮u·dl vs curl flux, <2%); orientation sign; irrotational null |
| angular_momentum.optical.spin | J·s/m³ | RCP/LCP ±1 helicity; linear-pol null |
| angular_momentum.optical.orbital | J·s/m³ | LG ℓ=±1,±2 signs; intrinsic for zero transverse momentum (origin-independent, tested); extrinsic under phase ramp (origin-dependent, tested) |
| angular_momentum.optical.transverse_spin | J·s/m³ | evanescent TM fixture; spin-momentum locking sign |
| angular_momentum.phonon.chiral_mode | kg·m²/s | two-mode ⟨L_z⟩=q₀²ω·sin(φ); ±π/2 signs; linear nulls; field-reversal Zeeman sign |
| chirality.spin_texture | — | registered; models in M4+ |
| toroidal_moment.magnetic | A·m² (micro) | M11 |
| torsion.historical.spacetime_claim | UNDECLARED | ceiling SOURCE_HYPOTHESIS; `has_solver` = False; every physical quantity is a forbidden alias |

## Key honesty rails (tested)

- Topological charge requires actual phase winding; a REAL field
  (nodal lines, phase ∈ {0,π}) returns charge 0 — an intensity null is
  never a vortex (gates D4/D5).
- Canonical vs Poynting-based azimuthal quantities are separate
  outputs, never interchanged (gate D6).
- A uniform static torque is orthogonal to every free-free torsional
  mode (cos-profile integral = 0) — the projection reproduces this
  null exactly; coupling to the fundamental requires a matched axial
  profile (documented in `torque_mode_overlap`).
- Chiral-phonon Zeeman splitting refuses to run without a
  material-specific g factor and returns NOT_APPLICABLE for quartz.

Figures: `docs/v4/proof/M3/figures/` (5, manifest-hashed, produced by
`tools/v4/gen_m3_figures.py`).
