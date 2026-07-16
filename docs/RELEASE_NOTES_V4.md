# RGCS v4.0.0 Release Notes (RSCS 2.0)

All results are computational; no experimental confirmation exists.
The historical eye is a Source claim; computed candidates are
diagnostics; CPU float64 is the numerical authority; GPU claims
reflect measured device evidence only; the nominal (110.000000 mm)
and ideal (110.037667410714… mm) geometries are distinct.

## Headline

- **Validated 3-D FEM stack** (`rscs2_core`): isotropic + fully
  anisotropic elastodynamics on P2 tetrahedra, benchmark-anchored
  (Euler–Bernoulli <0.5%, Timoshenko +0.03%, exact cube Lamé mode
  +0.03–0.05%, frozen Christoffel ladder rtol 1e-3), bit-deterministic
  solves.
- **Canonical 110 mm crystal**: exact parametric geometry (both
  variants), deterministic gmsh meshes (subprocess, GPL-isolated),
  machine-exact volumes, first converged mode tables.
- **Piezoelectric coupling**: stress-charge saddle formulation with
  energy-patch-pinned conventions; short/open circuits; k_eff².
- **Real Intel iGPU acceleration**: Iris Xe (fp32) Christoffel sweep
  ~52× vs fair CPU baseline at 500k directions, parity 3.4e-05;
  i5-1135G7 CPU-CL (fp64) parity 1.8e-14 → kernel
  MULTI_DEVICE_REPRODUCED. CUDA remains INTERFACE_TESTED (no
  hardware). No silent fallbacks.
- **Optical/coil/drive projections** on frozen v3 models: Sellmeier
  indices anchored to frozen constants; Biot–Savart pair fields;
  modal drive projection; leakage-gated coupling records; octave
  wavelength presets declared as arithmetic.
- **Eye diagnostic + consensus engine** (16 registered diagnostics,
  adversarially validated): the canonical crystal verdict is
  **CONVENTIONAL_NODE_FOUND** — no stable special region; the one
  cross-family region is ordinary modal structure. Null results are
  first-class outcomes.
- **Reference systems**: acoustic cavity vs exact spectrum (1.7e-4),
  base-fixed tuning fork pair with common-mode rejection, and the
  frozen two-mode model reproducing FEM avoided-crossing splitting
  within 6.4% (RSCS2-V.9 conservative-extension anchor).
- **Reproducibility**: `python -m rscs2_core.proofbundle` builds the
  111-file proof bundle bit-deterministically (SHA256 manifest);
  `rgcs-v4` CLI (14 commands); 10-step scripted demo; hosted 3-OS CI.

## QA

Independent adversarial audit (19 checks) green; defects
V4-D-001..004 registered, fixed, regression-tested
(docs/plans-v4/DEFECT_REGISTER_V4.md). Gate table G1–G30:
docs/plans-v4/RELEASE_RECOMMENDATION.md.

## Compatibility

The frozen v2/v3 authorities are untouched (tags, archive, registries,
published equations). New objects live exclusively in the RSCS2
namespace. Python ≥3.11. New optional runtime deps for the v4 stack:
scikit-fem, meshio, matplotlib, gmsh (subprocess), pyopencl (optional).

## Known limitations

STEP export documented/implemented/untested (declared status record in
the bundle); phase diagnostics (D9/D10) apply to driven complex
responses; eye consensus covered the first 4 elastic modes; GPU
evidence is device-specific; cross-platform bit-identity is not
claimed (tolerance-level CI). Full list: proof bundle
reports/LIMITATIONS.md.
