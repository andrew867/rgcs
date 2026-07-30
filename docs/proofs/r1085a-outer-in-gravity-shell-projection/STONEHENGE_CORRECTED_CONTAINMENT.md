# Stonehenge under the corrected projection

Training equality: `165876523` = Stonehenge
(51.1789, -1.8262). Packet (frozen):
face 4, path (3,3,0,1,2,0,2,1,2,1,1), shell 3, octree X=83 Y=80 Z=461.

## Lateral lane — equality HOLDS under the trained frame

* terminal level-11 cell contains Stonehenge: **True**
* forward-projection surface residual across all 48
  declared configurations: **1.654..5.15 km** (cell edge
  ~3.44 km). The residual varies with the declared stack height: the
  inward gravity-field line bends away from the cell-centroid ray, so
  taller stacks land farther from the centroid (that drift is the
  physics the layer exists to carry, reported per-config in
  SWEEP_ROWS.json). The best configs are within quantization; cell
  CONTAINMENT above is the primary lateral criterion.
* every sealed R10.8.2 context still misses (freeze not retuned):
  {"BASE": true, "F4_ROTATED_DIRECT_LE": true, "F2_REVERSED_DIRECT_BE": true, "F1_CANONICAL_DIRECT_BE": true, "F3_CANONICAL_ROOTREL_BE": true}

This satisfies the R10.8.5A instruction: the 2,683 km miss recorded at
e5864a5 was produced under the older projection assumptions; under the
corrected outer-in transform with the declared training alignment the
equality holds. **It is calibration.** The word trained the frame
(2 of 3 rotational DOF; roll undetermined), so this containment cannot
validate anything — and is labelled accordingly.

## Radial lane — honest misfit, reported not hidden

The decoded height above the land-zero surface (shell 3, zeta from
octree Z or midband) vs the site's physical height
(~102.0 m ASL, i.e. below the average-land zero):

{
 "ATMOSPHERIC_LADDER_V1|ZETA_FROM_OCTREE_Z_V1|CLASSIC_HYPSOGRAPHIC_840M": 11.5544,
 "ATMOSPHERIC_LADDER_V1|ZETA_FROM_OCTREE_Z_V1|MODERN_DEM_797M": 11.5114,
 "ATMOSPHERIC_LADDER_V1|ZETA_MIDBAND_V1|CLASSIC_HYPSOGRAPHIC_840M": 6.738,
 "ATMOSPHERIC_LADDER_V1|ZETA_MIDBAND_V1|MODERN_DEM_797M": 6.695,
 "GEOMETRIC_DOUBLING_V1|ZETA_FROM_OCTREE_Z_V1|CLASSIC_HYPSOGRAPHIC_840M": 23.2722,
 "GEOMETRIC_DOUBLING_V1|ZETA_FROM_OCTREE_Z_V1|MODERN_DEM_797M": 23.2292,
 "GEOMETRIC_DOUBLING_V1|ZETA_MIDBAND_V1|CLASSIC_HYPSOGRAPHIC_840M": 13.238,
 "GEOMETRIC_DOUBLING_V1|ZETA_MIDBAND_V1|MODERN_DEM_797M": 13.195,
 "UNIFORM_100KM_V1|ZETA_FROM_OCTREE_Z_V1|CLASSIC_HYPSOGRAPHIC_840M": 90.8747,
 "UNIFORM_100KM_V1|ZETA_FROM_OCTREE_Z_V1|MODERN_DEM_797M": 90.8317,
 "UNIFORM_100KM_V1|ZETA_MIDBAND_V1|CLASSIC_HYPSOGRAPHIC_840M": 50.738,
 "UNIFORM_100KM_V1|ZETA_MIDBAND_V1|MODERN_DEM_797M": 50.695
}

Best declared configuration still differs by ~6.695 km. No
declared profile places shell-3/zeta at the monument's physical
elevation; this is retained as an open structural misfit of the radial
lane (no parameter was added to force it — that would be overfitting a
training point).

SOURCE_ORIGIN_VALIDATED: no
Verdict: `RGCS_R10_8_5A_YELLOW_PACKET_AUTHORITY_HELD_PROJECTION_UNDERDETERMINED`
