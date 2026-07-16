# V4 Geometry & Mesh Spec — `rscs2_core.mesh` (RSCS2-G.*)

**Status:** PLANNING. **Licensing (DV4-006):** Gmsh is an external tool
invoked by subprocess/file interchange (GPL kept out of the MIT
codebase); **meshio (MIT)** bridges formats. CPU-only; no GPU here.

## 1. Geometry import (RSCS2-G.1)

| Source | Path | Notes |
|---|---|---|
| OpenSCAD crystal models (v2 lineage) | SCAD → STL export (OpenSCAD CLI subprocess) → import | reuses `scad/` v7; parameters carried as provenance |
| STL / OBJ | meshio / trimesh (optional) | surface only; needs volume meshing |
| STEP / BREP | Gmsh subprocess (OCC kernel) → `.msh` → meshio | "where feasible"; degrades to documented-unsupported |
| Gmsh-native `.geo`/`.msh` | meshio read | first-class |

Every import produces a **RSCS2-G.1 geometry source record**: source
file sha256, format, unit + coordinate-frame declaration (mm, crystal-
axis frame per `NOTATION_AND_UNITS`), and — for the crystal — the
crystallographic orientation (Euler z-x-z) that selects the anisotropic
vs scalar material path (mirrors `fea_export` `orientation_known`).

## 2. Meshing (RSCS2-G.2/G.3)

- Volume: tetrahedral (Gmsh subprocess; element order 1 and 2). Surface
  mesh (RSCS2-G.3) for optical facets and BC tagging.
- **Deterministic:** fixed Gmsh algorithm + seed + size field recorded;
  the manifest pins element counts and a mesh sha256. Re-meshing from
  the same manifest reproduces the same element counts (tolerance-aware
  on node coordinates per D-V3-04 — never byte-equality across Gmsh
  builds; the manifest records the Gmsh version).
- Staged/adaptive refinement (RSCS2-S.7-driven): uniform refinement
  levels ℓ=0..N for convergence; optional error-indicator adaptivity as
  a later phase.

## 3. Tags (RSCS2-G.4) — the multiphysics hooks

Named tag sets carried on the mesh and validated against the physics
that consumes them:
- **material regions** → constitutive tensor (single-region for the
  crystal; multi-region for composite fixtures);
- **boundary surfaces** → RSCS2-B.* operators (free/fixed/elastic/mass);
- **electrodes** → piezoelectric Dirichlet potential surfaces (L3);
- **coil footprint / source region** → EM drive projection (L5);
- **optical-entry facets** → ray entry/exit (L5), linked to
  `optical_probe` records;
- **fixture contacts** → mass/elastic-support (L4, hand-loading-equiv).

Tag provenance: which import feature or coordinate box defined each tag,
so a tag is never an unexplained region.

## 4. Mesh-quality diagnostics (RSCS2-G.5, DER)

Aspect ratio, min dihedral angle, scaled Jacobian, edge-length
histogram, sliver count. A mesh below a declared quality floor is
**flagged**, not silently used (fail-loud, extends v3 policy); the
solver records the mesh-quality summary in every result.

## 5. Deterministic mesh manifest (RSCS2-G.6)

JSON: geometry source sha256 + record, Gmsh version + algorithm + seed +
size field, element counts per order, node/element sha256, coordinate
frame, tag inventory with provenance, quality summary. **A mesh without
a valid manifest does not exist for the solver** (extends the v2 run-
manifest rule).

## 6. Tests (feed V4_TEST_PLAN)

- round-trip import→mesh→manifest→re-load (serialization);
- deterministic element counts from a fixed manifest (cross-platform,
  tolerance-aware on coordinates);
- tag-coverage completeness (every physics consumer's required tags
  present or an explicit "absent+reason");
- malformed-input adversarial (non-manifold STL, zero-volume, NaN
  coords, missing tags) → loud failure;
- quality-floor enforcement (a deliberately bad mesh is flagged);
- convergence-mesh generation for RSCS2-V.8.

## 7. Dependencies

Required: numpy, scipy, meshio (MIT). External tools (subprocess,
optional): OpenSCAD, Gmsh. Optional Python: trimesh (surface ops),
pyvista (3D view — reporting spec). CPU-only install never needs Gmsh
to *read* an existing `.msh`; it needs Gmsh only to *generate* one.
