# Agent 10 Handoff — Conventional Reference Systems

Status: COMPLETE. v4 suite 52/52 green.

## Delivered

- `rscs2_core/refsystems.py`: acoustic-cavity Helmholtz eigensolver
  (P2 scalar, exact closed-form reference) + gmsh OCC tuning-fork
  mesher (subprocess, DV4-006).
- `tests/v4/test_rscs2_refsystems.py`: 4 tests (cavity exact, cube
  3-fold degeneracy, fork sym/antisym + CMR, V.9 avoided crossing).
- `rscs2_core/fem.py`: `solve_modes` now expands condensed
  eigenvectors back to full DOF space when `fixed_dofs` is given
  (zeros at fixed dofs), so modes are indexable by `basis.doflocs`.
- Registry: RSCS2-V.4, RSCS2-V.9 registered VALIDATED.
- `docs/plans-v4/REFERENCE_SYSTEM_COMPARISON.md` + evidence in
  `evidence/v4/agent10/` (cavity CSV, fork pair summary,
  avoided-crossing CSV + plot).

## Findings the next agents must not re-derive

1. **Free fork is strongly coupled** (in-plane pair split 2699 Hz —
   the symmetric mode hybridizes with base flexure; thinning the base
   makes it WORSE). The weak-coupling regime the two-mode model
   describes requires the base clamped at z = 0 → S₀ = 8.70 Hz.
2. **Never assume mode ordering**: the free fork's modes 0–3 are
   x-anti, y-anti (out-of-plane), x-sym, y-sym. Identify pairs by
   signed mean tip displacement per component.
3. V.9 anchor: frozen `coupled_two_mode` tracks FEM splitting within
   6.4% over a 0–16 Hz detuning sweep using the Rayleigh tip-mass map
   (m_eff = 0.2427·m_prong). Errors grow smoothly with detuning —
   attributable to the single-mode Rayleigh map, not the frozen model.

## Next

Agent 08 (optical/coil projections on frozen `rgcs_core.optics` /
`timing`), then Agent 09 (eye diagnostic + consensus engine).
