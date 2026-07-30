# Stonehenge containment report (R10.8.4 SS9.1)

Training equality tested as CELL CONTAINMENT (not centroid distance) for
`165876523` across every finite frame context: 4 sealed families x 20
faces x 6 vertex orders = 480 configurations, C0 (none).

* configurations whose face contains Stonehenge at level 0: 24
* configurations whose FINAL level-3 cell contains Stonehenge:
  **0**
* first-excluding-level histogram (0 = face selection):
  {"0": 456, "1": 23, "2": 1}
* attribution histogram at the first excluding level: {"FACE_SELECTION": 456, "X_AND_Y": 22, "X": 1, "Y": 1}
* best configuration: family F4_ROTATED_DIRECT_LE, mesh face 5,
  order (0, 1, 2) — excluded at level 2
  (X_AND_Y), minimum geodesic distance from Stonehenge to
  the final decoded polygon **248.04 km** (final cell
  max radius ~3.5 km).

Radial compatibility (declared profiles, Z-path 5,6,3):
{"ROOT_R0_FULL_DIAMETER": false, "ROOT_R1_BODY_INTERIOR": false, "ROOT_R2_SURFACE_BAND_10PCT": false, "ROOT_R3_ALTITUDE_0_1000KM": false}

Compensation sweep (SS8): best min-distance per profile over all frames —
```json
{
 "C0_none": {
  "contained_any": false,
  "best_min_distance_km": 248.04,
  "best_frame": {
   "family": "F4_ROTATED_DIRECT_LE",
   "face": 5,
   "order": [
    0,
    1,
    2
   ]
  }
 },
 "C1_tangential_10_9": {
  "contained_any": false,
  "best_min_distance_km": 426.4,
  "best_frame": {
   "family": "F4_ROTATED_DIRECT_LE",
   "face": 5,
   "order": [
    0,
    1,
    2
   ]
  }
 },
 "C2_radial_10_9": {
  "contained_any": false,
  "best_min_distance_km": 248.04,
  "best_frame": {
   "family": "F4_ROTATED_DIRECT_LE",
   "face": 5,
   "order": [
    0,
    1,
    2
   ]
  }
 },
 "C3_metric_10_9": {
  "contained_any": false,
  "best_min_distance_km": 426.4,
  "best_frame": {
   "family": "F4_ROTATED_DIRECT_LE",
   "face": 5,
   "order": [
    0,
    1,
    2
   ]
  }
 },
 "CTRL_tangential_9_8": {
  "contained_any": false,
  "best_min_distance_km": 491.1,
  "best_frame": {
   "family": "F4_ROTATED_DIRECT_LE",
   "face": 5,
   "order": [
    0,
    1,
    2
   ]
  }
 },
 "CTRL_tangential_81_80": {
  "contained_any": false,
  "best_min_distance_km": 206.33,
  "best_frame": {
   "family": "F4_ROTATED_DIRECT_LE",
   "face": 5,
   "order": [
    0,
    1,
    2
   ]
  }
 },
 "CTRL_tangential_55_54": {
  "contained_any": false,
  "best_min_distance_km": 191.19,
  "best_frame": {
   "family": "F4_ROTATED_DIRECT_LE",
   "face": 5,
   "order": [
    0,
    1,
    2
   ]
  }
 }
}
```

Reading: the recursive decoder was executed exactly as locked. Stonehenge
is excluded at level 2 in the best frame (attribution
X_AND_Y); no declared compensation profile achieves
containment, and controls perform comparably to 10/9. The exclusion is
attributable to the level-2 X_AND_Y
instruction under every codebook/frame combination enumerated — not to
the parser, whose structure checks all pass.

SOURCE_ORIGIN_VALIDATED: no
