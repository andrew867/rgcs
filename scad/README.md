# SCAD models (provenance-preserved project CAD artifacts)

Both files are copied verbatim from the v2 prototype package
(`internal-docs/existing_project/scad/`; provenance rows in
`docs/PROVENANCE_REGISTER.csv`). They are **design artifacts**, not
validated physics: geometry parameters mirror `rgcs_core.geometry`, but the
authoritative numeric definitions (spiral path length, compact radius
R_chi per RGCS-M.36, node positions) live in the tested core library.

## Files

- `vogel_parametric_crystal_models_v6_RGCS_v2.scad` — OpenSCAD Customizer
  generator for faceted/tapered/double-terminated crystal models
  (citation entry `greenscad2026`).
- `rgcs_v2_compact_spiral_resonator.scad` — contracting logarithmic
  spiral cone and matched control geometries (citation entry
  `greenspiralscad2026`).

## Known defect (open, inherited): D-02 — inert compact-mode render mode

`vogel_parametric_crystal_models_v6_RGCS_v2.scad` lines 465–468 assign
`show_compact_mode_rings = true;` *inside* the dispatch `if`-block. OpenSCAD
scoping means the `vogel_wand` module still sees the top-level
`show_compact_mode_rings = false`, so the dedicated `compact_mode_crystal`
render mode **draws no rings** — the v6 headline feature is inert.

Workaround: set the `show_compact_mode_rings` customizer variable to `true`
directly instead of relying on the render-mode dispatch.

This defect is tracked as D-02 (S1) in `docs/INCONSISTENCY_REGISTER.md`.
The files are shipped unmodified to preserve provenance; the fix belongs to
a future CAD revision.
