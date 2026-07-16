# Canonical Crystal Mesh Report (Agent 05)

gmsh runs as an external SUBPROCESS (DV4-006; invoked through the venv
interpreter as a separate process, file interchange only). meshio (MIT)
reads the .msh. Deterministic: identical (geometry, clmax, gmsh 4.15.2)
-> identical node/tet SHA256 (machine-tested rebuild).

| Level | clmax (mm) | nodes | tets | min dihedral (deg) | max aspect (reg-tet=1) | volume rel err |
|---|---|---|---|---|---|---|
| coarse | 12 | 121 | 306 | 22.77 | 3.08 | 1.6e-14 |
| medium | 8 | 198 | 545 | 15.16 | 3.20 | 1.6e-14 |
| fine | 5 | 522 | 1738 | 14.92 | 3.81 | 1.6e-14 |

- Volume vs closed form (frozen polygon_area_mm2 + pyramid/frustum):
  MACHINE-EXACT at every level (planar facets -> linear tets tile the
  polyhedron exactly) -- a strong geometry-correctness check.
- Jacobian check: 0 inverted tets at all levels (hard error otherwise).
- Quality gates: min dihedral > 8 deg, max aspect < 6 (regular-tet
  normalized), enforced in tests.
- Exports shipped: .msh, .vtu, .stl, .obj (evidence/v4/agent05/);
  .glb not generated (no trimesh/gltf writer in the minimal stack;
  documented). Screenshots (real gmsh output rendered by matplotlib):
  crystal_geometry_tagged.png (facets + axes + cap/shaft tags),
  mesh_refinement_levels.png (3 levels).
