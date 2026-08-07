# Phryll Generator Designer v2 — final report

## Branch / commit

Implemented on `research/frequency-key-studio-v1` (user instruction:
no separate branch; one combined v8.5.0 release). Engine commit
`3834849`; UI/docs/demo commits follow it; see `git log`.

## Summary

Crystal-first parametric CAD generator: measured crystal dimensions →
custom cone (envelope + clearance + wall), coil sleeve with crossed
copper/silver grooves phased so a crossing plane lands exactly on the
Eye coordinate, full export bundle (SCAD/STL/3MF/DXF/SVG/PDF/JSON +
CHECKSUMS.sha256). No stock M1/M2/L/L2/V3 mesh is chosen or scaled —
enforced by test (`import(`/`.stl` absent from generated SCAD).

## Changed files (grouped)

- **services**: `rgcs_desktop/services/phryll_v2/{__init__, schemas,
  crystal_profile, cone_generator, coil_sleeve, eye_alignment,
  reference_assets, mesh_backend, openscad_export, flat_templates,
  pdf_exports, bundle_export, pipeline}.py`
- **data**: `rgcs_desktop/data/phryll_v2_{crystal_profile, cone_design,
  coil_sleeve, reference_asset}.schema.json` (schema major 2, local
  validator) + `phryll_v2_reference_registry.json` (12 CC-SA assets,
  M2_TEXT/M2_MESH kept separate, mesh-decode seed data)
- **UI**: `rgcs_desktop/viewers/phryll_v2_panel.py`, home card in
  `services/design_studio.py`, registration in `app/main_window.py`
  (22 panels), smoke set update
- **tests**: `tests/unit/test_phryll_v2_geometry.py` (22),
  `tests/unit/test_phryll_v2_cad.py` (8),
  `tests/integration/test_phryll_v2_bundle.py` (7),
  `tests/ui/test_phryll_v2_panel.py` (4) — includes every pack
  skeleton assertion (T001–T009 acceptance rows)
- **docs**: `docs/user/PHRYLL_GENERATOR_V2.md`,
  `docs/developer/PHRYLL_V2_CAD_ENGINE.md`, README + index rows
- **fixtures**: `tests/fixtures/phryll_v2/` (pack demo crystal + coil)

## Tests run

41 new phryll v2 tests, all green; UI smoke 22 panels OK; docs +
claim-firewall guards 250/250. Full-suite counts are reported in the
combined v8.5.0 release gate (this feature shipped together with
Frequency Key Studio).

## Demo crystal dimensions

CRY-DEMO-120: length 120.0 mm, top Ø 26.0 mm (60°), base Ø 39.0 mm
(51.84°), max body width 39.0 mm, 6 facets, 140 g, Eye z = 62.5 mm
(±0.25 mm, demo-entered).

## Generated artifacts (`docs/assets/design-studio/demo/phryll_v2/`)

`phryll_design_PHV2-CRY-DEMO-120/` — 18 files, checksums verified:
custom_cone.scad + coil_sleeve.scad (deterministic, full module set),
custom_cone.stl (36 864-triangle watertight shell, 43.92 mm max Ø,
120 mm height) + custom_cone.3mf from the built-in mesh backend,
axial_section.svg, top_template.svg, winding_template.dxf,
compatibility_sheet.pdf, build_sheet.pdf, design/coil/eye/fit receipts,
MANIFEST.json, CHECKSUMS.sha256, backend_status log. Screenshot proof:
`docs/assets/design-studio/screenshots/11_phryll_generator_v2.png`
(live app, in-app bundle export verified).

## Key numbers

- Generated cone: inner 40.32 → 27.32 mm, outer 43.92 → 30.92 mm
  (crystal + 2×0.66 clearance; + 2×1.8 wall) — fit PASS, min clearance
  0.66 mm across 96 stations.
- **Eye alignment residual: 0.0 mm** (z_cross = z_eye = 62.5 mm;
  tolerance 0.5 mm = 2 × 0.25 mm uncertainty; the crystal midpoint
  60.0 mm is 2.5 mm away and is *not* used).
- **Coil standoff**: nearest conductor 2.21 mm; coil centerline
  2.375 mm (≈7.2 wire diameters).
- **Wire pitch**: AWG 28 (0.33 mm) → clear gap 0.66 mm, groove pitch
  0.99 mm; crossing ladder spaced 0.495 mm with one rung exactly on
  the Eye.

## Reference assets used

REF-001…REF-012 (CC-SA supplied; STLs, L2 3MF, M-holder GCODE, adapt
SCAD) — registered with roles, licenses, and prior mesh-decode seed
dimensions (M2 103.712 mm / 44.911→30.244 inner; L 113.311; L2
113.084). Used as style/size references and advisory fit comparison
only; measurement tools re-measure files directly when present.
M2_TEXT (29/39/120) and M2_MESH (30.244/44.911/103.712) stored
separately, never reconciled.

## Blockers / honest list

- OpenSCAD CLI absent on this machine: coil_sleeve.stl (grooved shell)
  reports `unavailable`; the built-in mesh backend covers the cone
  shell STL/3MF, and the SCAD renders the full grooved model when
  OpenSCAD exists.
- The reference asset binary files themselves are not in the repo
  (registry + seed measurements are); direct re-measurement runs when
  the user supplies the files.
- v1.1/v1.2 scope (mesh overlay comparison UI, live 3D preview,
  clearance heat map, photo-assisted profile extraction, tolerance
  optimizer, winding simulator) is not implemented.
- The 7–8 wire-diameter standoff is a design default, not a proven
  optimum — recorded for sweeping.

## Boundary

Generated geometry is a model output and engineering plan. The
compatibility sheet documents fit geometry and does not assert
physical output. Source-language wiring/pulse notes are recorded, not
validated. Annular-ring craft locks stay in their own lane and never
size the cone (enforced by a source-scan test).
