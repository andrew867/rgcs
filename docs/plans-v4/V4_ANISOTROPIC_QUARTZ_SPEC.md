# V4 Anisotropic Quartz Spec — primary example (RSCS2-E.3/E.4)

**Status:** PLANNING. The faceted Vogel-style α-quartz resonator is the
mandatory primary example (V4_PRODUCT_SPEC §5). This spec pins the
crystal-specific modelling; it **reuses frozen v3** and adds no new
constants.

## 1. Geometry

- Parametric faceted Vogel-style body from the v2 SCAD lineage (`scad/`
  v7, D-02 fixed) exported to STL/STEP → RSCS2-G pipeline. Parameters:
  length, wide/narrow diameters, facet count, termination angles
  (female/male apex), optional compact-spiral reference geometry.
- Dimensional uncertainty carried per parameter (σ), feeding RSCS2-U.1.
- Crystallographic-axis orientation (Euler z-x-z) is mandatory metadata;
  `orientation_known=false` forces the scalar-band fallback (v3 model-
  selection rule), not a false-precision anisotropic result.

## 2. Material (reuses frozen `rgcs_core.anisotropy`, EST)

- Voigt stiffness C (α-quartz class 32; Bechmann 1958 / Auld 1973),
  density ρ=2648 kg/m³, all from the frozen module — **no new numbers**.
- Piezoelectric e and permittivity ε tensors (α-quartz, IEEE-176
  handbook values) are the *only* new material constants; they enter as
  a governed material-card extension with declared provenance (D5-002
  pattern) and are EST handbook input. Registered before first use.
- Orientation applies the standard Bond rotation to C, e, ε for an
  arbitrarily oriented specimen.

## 3. Modes and taxonomy

Full 3D eigenmodes (RSCS2-S.1) classified into
longitudinal / shear / torsional / flexural / mixed by modal
participation and polarization (extends the v3 quasi-mode taxonomy).
Free/fixture/hand-loading boundaries (RSCS2-B.1/3/4) give the free vs
loaded spectra (H-08 family cross-check).

## 4. Coupling layers (staged)

- **L2:** anisotropic elastic spectrum; **must** reproduce
  `wave_speeds` at the axes (RSCS2-V.6) and the degenerate splitting
  (RSCS2-V.9).
- **L3:** piezoelectric coupling (`V4_PIEZOELECTRIC_MULTIPHYSICS_SPEC`)
  → electromechanical modes, coil-drive projection (RSCS2-E.11).
- **L4:** thermal drift (RSCS2-E.6, elastic-constant ∂C/∂T) + fixture
  perturbation → frequency-shift predictions with uncertainty.
- **L5:** optical path + photoelastic response
  (`V4_OPTICAL_MODELLING_SPEC`) and coil/EM drive
  (`V4_COIL_AND_EM_COUPLING_SPEC`).

## 5. Modal overlap & reduction

Modal overlap integrals (drive-mode and cross-modal) computed on the FE
fields (RSCS2-D.7/D.8), and coupled-mode reduction (RSCS2-S.6) to the
frozen 2-mode picture where R_g ≳ 1 (v3 "earn its complexity" rule).

## 6. Eye candidates

The crystal is where the eye-diagnostic family (`V4_EYE_DIAGNOSTICS_SPEC`)
is exercised most heavily: field maps + candidate regions + robustness +
uncertainty + comparison vs geometric centre / modal nodes / the v3 node
prior, with a NULL-capable verdict. The historical "eye" stays SRC; any
candidate is DER/HYP (DV4-010).

## 7. Tests

RSCS2-V.6 (Christoffel anchor), V.9 (splitting anchor), orientation/Bond-
rotation round-trip, free-vs-loaded shift vs v3 loading band, taxonomy
classification stability across refinement, piezo material-card
provenance lint, uncertainty propagation through the spectrum.
