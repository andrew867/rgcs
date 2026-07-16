# Agent 04 Handoff — Anisotropic alpha-quartz (COMPLETE)

Module: rscs2_core/quartz.py. Tests: tests/v4/test_rscs2_quartz.py (9).
Evidence: evidence/v4/agent04/ (wave_speed_surfaces.png,
orientation_sweep_modes.png/.csv, christoffel_axis_anchors.csv).
Validation record: docs/plans-v4/ANISOTROPIC_QUARTZ_VALIDATION.md.

APIs for downstream agents:
- material_record() / QUARTZ: constants+convention+provenance+uncertainty
- euler_zxz_matrix(a,b,g); rotate_stiffness/rotate_piezo/
  rotate_dielectric (exact full-tensor; crystal->lab)
- christoffel_speeds(C_full, rho, dirs) batched; == frozen v3 pointwise
- orientation_sweep() surfaces
- quartz_piezo_tensor_c_m2(), quartz_dielectric_f_m() for Agent 06

Key facts: Iris Xe iGPU is fp32-only in OpenCL (i5-1135G7 CPU-CL device
has fp64) -> A07 parity policy fp32-with-error-bounds on iGPU.
Rigid-mode residuals are NaN by design. Degeneracy taxonomy covers
numerical/symmetry/section splitting; the coupled-2g case rides on the
Agent 10 fork with the frozen RSCS-O.4 anchor.

Open items for A05/A06: canonical crystal geometry (gmsh subprocess per
DV4-006); piezo coupled block over rotate_piezo/rotate_dielectric.
