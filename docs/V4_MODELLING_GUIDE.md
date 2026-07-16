# RGCS v4 Modelling Guide

How to build a correct model with `rscs2_core`, and the pitfalls the
programme actually hit.

## Meshes

- `fem.box_mesh(lengths_m, divisions)` for rectangular bodies;
  `crystal110.mesh_crystal` (gmsh subprocess) for the canonical body;
  `refsystems.fork_mesh` for OCC boolean shapes. Everything downstream
  expects METERS; crystal meshes return `nodes_m`.
- Check the manifest: `n_inverted == 0`, `volume_rel_err`, dihedral,
  aspect. Refine until your quantity of interest moves less than your
  tolerance (three levels in the proof bundle).

## Assembly and solving

- Isotropic: `assemble_isotropic(mesh, E, nu, rho)`. Anisotropic:
  `assemble_anisotropic(mesh, c_full_3x3x3x3, rho)` — expand frozen
  Voigt constants with `rscs_core.propagation.voigt_to_tensor`.
- `solve_modes(problem, n, fixed_dofs=None)`: free bodies report
  exactly 6 rigid modes separately; residuals per mode; modes are
  mass-orthonormal and returned in FULL dof space even with
  `fixed_dofs`. Solves are bit-deterministic (fixed ARPACK v0).
- DOF layout is interleaved (x,y,z per node): use
  `component_dofs(basis, c)`; never slice by thirds.

## Pitfalls (each cost real debugging time; all now guarded by tests)

1. **Vector mass forms**: `rho*dot(u,v)`, never `ddot` (V4-D-001 —
   ~480× mass inflation, frequencies 4–22× low, worsens with
   refinement).
2. **Hand-rolled stiffness**: verify symmetry before trusting it; the
   validated paths are skfem's `linear_elasticity` and the einsum
   anisotropic form.
3. **Mode identification**: never assume mode ordering. The free
   tuning fork's first four modes are x-anti, y-anti, x-sym, y-sym —
   classify by signed component amplitudes at physical stations.
4. **Coupling regimes**: a free fork is STRONGLY coupled through base
   flexure (kHz split); clamp the base for the weak-coupling
   (two-mode-model) regime.
5. **Degeneracy**: symmetry-protected pairs (hexagonal bending,
   cubic cavity triplets) must be reported as degenerate, not
   averaged; their eigenbasis is arbitrary — never build claims on
   one member's spatial pattern (this arbitrariness exposed V4-D-004).
6. **Thick beams**: mode 1 may be the weak-axis bend; compare against
   Timoshenko, not just Euler–Bernoulli.
7. **Determinism**: if you add an `eigsh` call, pass a fixed `v0`.
8. **Units end-to-end**: Pa, kg/m³, meters in → Hz out; the mass
   patch (uᵀMu = ρV) is the cheapest smoke test of your assembly.

## Coupled and projected quantities

- Piezo: `piezo.PiezoProblem` + `solve_piezo_modes` (short/open) /
  `static_potential_response`; always ground a gauge DoF.
- Projections: `projections.probe_paths`, `photoelastic_phase_shift_rad`,
  `biot_savart_polyline`, `assemble_body_force` +
  `project_force_vector`. Coupling reports REQUIRE a leakage baseline.
- Eye analysis: evaluate fields per mode, then `eye.eye_consensus`
  with refined fields (mandatory for STABLE), boundary variants, and
  material draws — see EYE_METHODOLOGY.md.
