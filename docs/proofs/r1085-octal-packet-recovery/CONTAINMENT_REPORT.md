# Stonehenge containment — octal packet decode (R10.8.5)

Word `165876523` = `F5|Q22|S3` -> source face 4, quaternary path
(3,3,0,1,2,0,2,1,2,1,1), shell 3 (body-relative surface shell by the
locked semantics — NOT inferred from any decimal digit). Cell geometry:
R12 frozen midpoint 4-way subdivision (`r12.icosarefine.cell_triangle`),
level-11 cell edge ~ 3.44 km. Face context: source-face 4
mapped through the five declared codebooks; Earth orientation: sealed
CALFREEZE per-family rotations. 20 finite contexts.

* contained in the final level-11 cell: **False**
  (0 of
  20 contexts)
* best context: codebook D_CW_DUAL_SPIRAL, family
  F1_CANONICAL_DIRECT_BE, mesh face 6,
  first excluding level 1,
  approx. min distance 2683.03 km
* full rows in PACKET_RECEIPT-adjacent JSON below.

```json
[
 {
  "family": "F4_ROTATED_DIRECT_LE",
  "codebook": "A_BFS_RINGS_CW_FROM_SAA",
  "source_face": 4,
  "mesh_face": 2,
  "root_face": 12,
  "contained": false,
  "first_excluding_level": 0,
  "cell_centroid_latlon": [
   -31.402512147321087,
   -15.885915137647904
  ],
  "approx_min_distance_km": 9283.23
 },
 {
  "family": "F4_ROTATED_DIRECT_LE",
  "codebook": "B_ANTIPODAL_PAIRS",
  "source_face": 4,
  "mesh_face": 16,
  "root_face": 12,
  "contained": false,
  "first_excluding_level": 0,
  "cell_centroid_latlon": [
   -36.69772501946944,
   159.08280211761712
  ],
  "approx_min_distance_km": 17806.63
 },
 {
  "family": "F4_ROTATED_DIRECT_LE",
  "codebook": "C_XYZ_NORMAL_ORDER",
  "source_face": 4,
  "mesh_face": 15,
  "root_face": 12,
  "contained": false,
  "first_excluding_level": 0,
  "cell_centroid_latlon": [
   37.547545208330426,
   69.63819178843953
  ],
  "approx_min_distance_km": 5640.01
 },
 {
  "family": "F4_ROTATED_DIRECT_LE",
  "codebook": "D_CW_DUAL_SPIRAL",
  "source_face": 4,
  "mesh_face": 0,
  "root_face": 12,
  "contained": false,
  "first_excluding_level": 0,
  "cell_centroid_latlon": [
   -3.760255298429756,
   -41.54001256769721
  ],
  "approx_min_distance_km": 7173.68
 },
 {
  "family": "F4_ROTATED_DIRECT_LE",
  "codebook": "E_VERTEX_TRIPLE_CANONICAL",
  "source_face": 4,
  "mesh_face": 4,
  "root_face": 12,
  "contained": false,
  "first_excluding_level": 0,
  "cell_centroid_latlon": [
   -69.75487759715452,
   -50.52237578240601
  ],
  "approx_min_distance_km": 14008.96
 },
 {
  "family": "F2_REVERSED_DIRECT_BE",
  "codebook": "A_BFS_RINGS_CW_FROM_SAA",
  "source_face": 4,
  "mesh_face": 3,
  "root_face": 12,
  "contained": false,
  "first_excluding_level": 0,
  "cell_centroid_latlon": [
   -34.67270639937732,
   -27.1942827929195
  ],
  "approx_min_distance_km": 9861.58
 },
 {
  "family": "F2_REVERSED_DIRECT_BE",
  "codebook": "B_ANTIPODAL_PAIRS",
  "source_face": 4,
  "mesh_face": 13,
  "root_face": 12,
  "contained": false,
  "first_excluding_level": 0,
  "cell_centroid_latlon": [
   -38.840940869675684,
   146.19470780451246
  ],
  "approx_min_distance_km": 17180.78
 },
 {
  "family": "F2_REVERSED_DIRECT_BE",
  "codebook": "C_XYZ_NORMAL_ORDER",
  "source_face": 4,
  "mesh_face": 15,
  "root_face": 12,
  "contained": false,
  "first_excluding_level": 0,
  "cell_centroid_latlon": [
   37.547545208330426,
   144.19866678296876
  ],
  "approx_min_distance_km": 9606.08
 },
 {
  "family": "F2_REVERSED_DIRECT_BE",
  "codebook": "D_CW_DUAL_SPIRAL",
  "source_face": 4,
  "mesh_face": 0,
  "root_face": 12,
  "contained": false,
  "first_excluding_level": 0,
  "cell_centroid_latlon": [
   -3.760255298429756,
   33.02046242683203
  ],
  "approx_min_distance_km": 6943.54
 },
 {
  "family": "F2_REVERSED_DIRECT_BE",
  "codebook": "E_VERTEX_TRIPLE_CANONICAL",
  "source_face": 4,
  "mesh_face": 4,
  "root_face": 12,
  "contained": false,
  "first_excluding_level": 0,
  "cell_centroid_latlon": [
   -69.75487759715452,
   24.03809921212324
  ],
  "approx_min_distance_km": 13607.55
 },
 {
  "family": "F1_CANONICAL_DIRECT_BE",
  "codebook": "A_BFS_RINGS_CW_FROM_SAA",
  "source_face": 4,
  "mesh_face": 3,
  "root_face": 12,
  "contained": false,
  "first_excluding_level": 0,
  "cell_centroid_latlon": [
   -34.67270639937732,
   -15.352076537790976
  ],
  "approx_min_distance_km": 9635.58
 },
 {
  "family": "F1_CANONICAL_DIRECT_BE",
  "codebook": "B_ANTIPODAL_PAIRS",
  "source_face": 4,
  "mesh_face": 13,
  "root_face": 12,
  "contained": false,
  "first_excluding_level": 0,
  "cell_centroid_latlon": [
   -38.840940869675684,
   158.03691405964096
  ],
  "approx_min_distance_km": 17930.49
 },
 {
  "family": "F1_CANONICAL_DIRECT_BE",
  "codebook": "C_XYZ_NORMAL_ORDER",
  "source_face": 4,
  "mesh_face": 15,
  "root_face": 12,
  "contained": false,
  "first_excluding_level": 0,
  "cell_centroid_latlon": [
   37.547545208330426,
   156.0408730380973
  ],
  "approx_min_distance_km": 9913.71
 },
 {
  "family": "F1_CANONICAL_DIRECT_BE",
  "codebook": "D_CW_DUAL_SPIRAL",
  "source_face": 4,
  "mesh_face": 6,
  "root_face": 12,
  "contained": false,
  "first_excluding_level": 1,
  "cell_centroid_latlon": [
   31.402512147321087,
   -20.605960052311865
  ],
  "approx_min_distance_km": 2683.03
 },
 {
  "family": "F1_CANONICAL_DIRECT_BE",
  "codebook": "E_VERTEX_TRIPLE_CANONICAL",
  "source_face": 4,
  "mesh_face": 4,
  "root_face": 12,
  "contained": false,
  "first_excluding_level": 0,
  "cell_centroid_latlon": [
   -69.75487759715452,
   35.88030546725176
  ],
  "approx_min_distance_km": 13787.14
 },
 {
  "family": "F3_CANONICAL_ROOTREL_BE",
  "codebook": "A_BFS_RINGS_CW_FROM_SAA",
  "source_face": 4,
  "mesh_face": 3,
  "root_face": 12,
  "contained": false,
  "first_excluding_level": 0,
  "cell_centroid_latlon": [
   -34.67270639937732,
   -15.352076537790976
  ],
  "approx_min_distance_km": 9635.58
 },
 {
  "family": "F3_CANONICAL_ROOTREL_BE",
  "codebook": "B_ANTIPODAL_PAIRS",
  "source_face": 4,
  "mesh_face": 13,
  "root_face": 12,
  "contained": false,
  "first_excluding_level": 0,
  "cell_centroid_latlon": [
   -38.840940869675684,
   158.03691405964096
  ],
  "approx_min_distance_km": 17930.49
 },
 {
  "family": "F3_CANONICAL_ROOTREL_BE",
  "codebook": "C_XYZ_NORMAL_ORDER",
  "source_face": 4,
  "mesh_face": 15,
  "root_face": 12,
  "contained": false,
  "first_excluding_level": 0,
  "cell_centroid_latlon": [
   37.547545208330426,
   156.0408730380973
  ],
  "approx_min_distance_km": 9913.71
 },
 {
  "family": "F3_CANONICAL_ROOTREL_BE",
  "codebook": "D_CW_DUAL_SPIRAL",
  "source_face": 4,
  "mesh_face": 6,
  "root_face": 12,
  "contained": false,
  "first_excluding_level": 1,
  "cell_centroid_latlon": [
   31.402512147321087,
   -20.605960052311865
  ],
  "approx_min_distance_km": 2683.03
 },
 {
  "family": "F3_CANONICAL_ROOTREL_BE",
  "codebook": "E_VERTEX_TRIPLE_CANONICAL",
  "source_face": 4,
  "mesh_face": 4,
  "root_face": 12,
  "contained": false,
  "first_excluding_level": 0,
  "cell_centroid_latlon": [
   -69.75487759715452,
   35.88030546725176
  ],
  "approx_min_distance_km": 13787.14
 }
]
```

Shell 3 declares surface compatibility, so the radial lane is consistent
by construction under this candidate.

SOURCE_ORIGIN_VALIDATED: no
