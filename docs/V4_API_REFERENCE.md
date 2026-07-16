# RGCS v4 API Reference (rscs2_core)

Developer-facing summary; authoritative signatures are the docstrings.

## rscs2_core.fem
- `box_mesh(lengths_m, divisions) -> MeshTet`
- `assemble_isotropic(mesh, E_pa, nu, rho) -> ElasticProblem`
- `assemble_anisotropic(mesh, c_full_pa, rho) -> ElasticProblem`
- `component_dofs(basis, comp)`; `ElasticProblem.total_mass_kg()`
- `solve_modes(problem, n, fixed_dofs=None)` → frequencies_hz,
  elastic_frequencies_hz, n_rigid_modes, modes (full dof space,
  mass-orthonormal), residuals (NaN for rigid), orthonormality_error,
  ndof. Bit-deterministic.
- `add_elastic_support(problem, facet_pred, k_pa_m)` (Robin, B.3)
- `add_surface_mass(problem, facet_pred, sigma_kg_m2)` (B.4)
- `harmonic_response(problem, force, freqs_hz, ...)` (S.5)
- `static_tip_deflection(...)`; `save_modes`/`load_modes`

## rscs2_core.quartz
- `QUARTZ` / `material_record()`; `quartz_piezo_tensor_c_m2()`;
  `quartz_dielectric_f_m()`
- `euler_zxz_matrix(a,b,g)`; `rotate_stiffness/piezo/dielectric`
- `christoffel_speeds(c_full, rho, dirs)`; `orientation_sweep(...)`

## rscs2_core.crystal110
- `build_crystal("ideal_n7"|"nominal", ...) -> CanonicalCrystal`
  (`record()` carries the full provenance frame; eye_coordinate null)
- `mesh_crystal(c, clmax_mm, workdir, order=1)` → nodes_m, tets,
  quality, SHA256 manifest; `analytic_volume_mm3(c)`; `mesh_quality`

## rscs2_core.piezo
- `PiezoProblem(mesh, c_full, e_full, eps, rho)` (u: P2 vector,
  φ: P2 scalar; blocks Kuu/Muu/Kup/Kpp)
- `solve_piezo_modes(prob, n, electrodes, condition="short"|"open")`
- `static_potential_response(prob, el_plus, el_minus, volts, fixed_u)`
- `coupling_factor(f_short, f_open)`

## rscs2_core.accel
- `discover_devices()`; `capability_report()`;
  `write_capability_report(json_path, md_path)`
- `sweep(c_full, rho, dirs, backend="cpu"|"opencl"|"cuda_interface"|"auto",
  device="")` — explicit unavailable backend raises (no fallback)
- `OpenCLChristoffel(device_substring)`; `PARITY_TOL`

## rscs2_core.projections
- `WAVELENGTH_PRESETS_NM`; `quartz_sellmeier(nm)`; `uniaxial_index`
- `refract_ray(direction, outward_normal, n1, n2)`
- `crystal_targets(c)`; `probe_paths(c, wavelength_nm, eye_candidate_mm=None)`
- `photoelastic_phase_shift_rad(strains, seg_mm, n, p, nm)`
- `absorption_deposition_w`; `jones_waveplate`; `apply_jones`
- `circular_coil`; `biot_savart_polyline`; `loop_axis_field_t`;
  `coil_pair_field`; `field_gradient`; `magnetic_energy_density_j_m3`
- `assemble_body_force(problem, force_fn)`; `project_force_vector`
- `capacitive_drive_traction_pa`; `coil_coupling_report` (leakage
  baseline REQUIRED); `macro_sequences`; `drive_phase_table`

## rscs2_core.eye
- `DIAGNOSTIC_SPECS` (D1–D16 metadata); `ALLOWED_STATUSES`
- `evaluate_elastic_diagnostics(problem, sol, mode_i, c_full, ...)`
- `electric_energy_density_field(p_basis, phi, eps)` (refuses None)
- `phase_coherence_field` / `phase_singularities_on_plane` (refuse
  real input); `em_circulation` (refuses missing field)
- `extract_candidates(field, quantile, link_radius_mm)`
- `eye_consensus(fields, geometry, refined_fields, boundary_fields,
  uncertainty_fields, ...) -> EyeConsensusResult` — refined_fields
  required for any STABLE verdict (G21)

## rscs2_core.refsystems
- `cavity_modes_analytic` / `cavity_modes_fem`
- `fork_mesh(workdir, ...)` (gmsh OCC subprocess)

## rscs2_core.proofbundle / rscs2_core.cli
- `build_bundle(outdir=None, fast=False) -> Path`
- CLI: `rgcs-v4 <command>` — see USER_GUIDE_V4.md.

## Registry
`rscs2_core/registry/rscs2_registry.yaml` — append-only; every object
above is registered with id/units/class/provenance/exclusions/tests.
