# Phryll v2 CAD engine (developer)

Package: `rgcs_desktop/services/phryll_v2/`

- `crystal_profile.py` — schema-validated normalization (major 2,
  local validator in `schemas.py`, deliberately outside the major-1
  experiments registry), linear radius envelope, Eye validation.
- `cone_generator.py` — `r_inner(z) = r_crystal(z) + clearance`,
  `r_outer = r_inner + wall`; per-station fit check; refusals for
  unusable clearance/wall.
- `coil_sleeve.py` — source spacing rules (gap ≥ 2·wire Ø enforced,
  pitch = 3·wire Ø), standoff report, crossed helix parameters phased
  onto the Eye.
- `eye_alignment.py` — residual report, `solve_helix_phase_for_eye`
  (phase = −s·2πz_eye/pitch puts both helices at angle 0 on the Eye
  plane), crossing ladder spaced pitch/2.
- `reference_assets.py` — packaged registry (12 CC-SA assets +
  M2_TEXT/M2_MESH kept separate + mesh-decode seed data), direct
  binary/ASCII STL bounds + radial cone-profile measurement, advisory
  reference-vs-custom comparison.
- `mesh_backend.py` — watertight frustum-shell tessellation from the
  generated profiles → binary STL + minimal 3MF (no external CAD).
- `openscad_export.py` — deterministic SCAD module set (no `import()`
  or mesh scaling — tested); optional OpenSCAD CLI STL.
- `flat_templates.py` — SVG axial section/top template, R12 ASCII DXF
  winding template (developed at the band's mean outer radius).
- `pdf_exports.py` — compatibility + build sheets (shared pure-Python
  PDF writer).
- `bundle_export.py` / `pipeline.py` — the bundle layout
  (inputs/cad/flat/pdf/receipts/logs + MANIFEST + CHECKSUMS.sha256)
  and the end-to-end orchestrator used by panel, demo, and tests.

Schemas + registry ride `rgcs_desktop/data/phryll_v2_*.json` (existing
`data/*.json` package-data glob and PyInstaller `datas` cover them).
