# RGCS Earth Alignment Solve

**Date:** 2026-07-26  
**Status:** `CALIBRATED_CANDIDATE_NOT_VALIDATED`  
**Publication:** `HOLD`

## 1. What changed

The earlier manuscript package must not be released as a geographic-coordinate paper. It described a correct structural codec while the physical Earth projection was still unresolved.

This run performs the missing alignment calculation. It does not simply rotate the regular icosahedron until Stonehenge fits. The regular rigid model was first tested and excluded. A finite face-codebook translation was then selected, followed by a smooth, globally continuous nonlinear spherical registration.

The resulting candidate maps the supplied calibration locations exactly, preserves the Wilkes and SAA frame locks, makes the Erie-Montréal-Toronto hierarchy exactly equilateral under the declared tree metric, and enforces the orange triplet as one body-centred great-circle plane. It has **zero detected orientation reversals over an 81,920-triangle level-6 verification mesh**.

It remains calibrated rather than prospectively validated.

## 2. Locked inputs used

- Earth centre of mass.
- Mean rotation axis.
- South-Up as the proper rotation `diag(1,-1,-1)`.
- Clockwise-positive orientation viewed externally above Antarctica.
- Twenty icosahedral faces and dodecahedral-dual adjacency.
- Wilkes Land root at 70°S, 120°E.
- 2025 surface magnetic minimum at 26.22°S, 60.03°W as the SAA phase target.
- `165876523 = Stonehenge` as a training equality.
- Erie, Montréal, and Toronto as municipality-level calibration regions.
- Node/state 23 as source-reported operator guidance.
- The orange packet triplet as an ordered body-centred plane constraint.

## 3. Exact transport bridge

The variable-length pair shares candidate decimal transport header `16`:

```text
16 | 43789253    variable Stonehenge
16 | 72875493    variable Toronto
```

The least positive odd affine multiplier in the searched family that:

1. maps variable Stonehenge to fixed Stonehenge;
2. maps Toronto to face 5 and shell 3;
3. gives Toronto a third quaternary branch distinct from Erie and Montréal;
4. makes all three pairwise longest-common-prefix depths equal to two;

is:

```text
y = (923 x + 550585316) mod 2^30
```

with inverse:

```text
x = 953920147 (y - 550585316) mod 2^30
```

Exact outputs:

```text
43789253 -> 165876523
72875493 -> 168930443
```

Toronto's canonical candidate is therefore:

```text
168930443
octal: 1204326213
face: 5
path: 0,0,2,0,3,1,1,2,1,0,1
shell: 3
```

The coefficient relation `923 = 40×23 + 3` is logged as retrospective arithmetic only. It was not used as a proof.

## 4. Exact equilateral hierarchy

The canonical paths are:

```text
Erie:     0,0,0,0,2,1,1,3,0,1,2
Montréal: 0,0,1,3,1,0,3,1,3,2,0
Toronto:  0,0,2,0,3,1,1,2,1,0,1
```

Each pair shares exactly the first two symbols and diverges at the third:

```text
LCP(E,M) = LCP(M,T) = LCP(T,E) = 2
```

Using the declared tree distance:

```text
d(a,b) = 2 × (11 - LCP(a,b))
```

gives:

```text
d(E,M) = d(M,T) = d(T,E) = 18
```

The equilateral statement is therefore exact in the transformed hierarchical metric. It is not a claim that the three municipalities form an equilateral geodesic triangle on ordinary Earth.

## 5. Node 23 and the face codebook

Stonehenge's original top-six-bit state is 9. The source-reported node is 23:

```text
23 - 9 = 14
```

An exhaustive test of all twenty cyclic translations of the declared Option-A root-relative breadth-first codebook selected the same magnitude:

```text
source_face = (packet_F5 + 14) mod 20
```

Top finite results:

| Offset | Packet face 4 becomes | Packet face 5 becomes | Rigid RMS | Maximum residual |
|---:|---:|---:|---:|---:|
| 14 | 18 | 19 | 13.959109° | 16.620328° |
| 13 | 17 | 18 | 15.336696° | 18.801190° |
| 12 | 16 | 17 | 23.299943° | 27.568466° |
| 11 | 15 | 16 | 26.742705° | 47.679312° |
| 10 | 14 | 15 | 29.142939° | 35.617511° |
| 5 | 9 | 10 | 45.485625° | 82.753702° |

Offset 14 is the unique minimum in this family. It gives:

```text
packet F5 4 -> source face 18 -> physical mesh face 12
packet F5 5 -> source face 19 -> physical mesh face 19
```

The equality between the selected codebook offset and `|23-9|` is a real arithmetic convergence. It remains a calibrated interpretation of the node instruction, not an externally verified semantic fact.

## 6. Why a rigid icosahedron was rejected

With the Wilkes root fixed, the physical Wilkes-to-Stonehenge central angle is about 147.69°. The greatest compatible root-to-terminal-cell angle found in the regular midpoint-refined model was about 140.87°, leaving a gap of roughly 6.82° before the remaining city constraints were even imposed.

Under the declared codebook without a face translation, the best rigid four-anchor RMS was about 82.06°. Offset 14 reduced it to 13.96°, but a rigid rotation still could not satisfy all anchors.

This is the numerical reason the final projection must be nonlinear and face-dependent.

## 7. Nonlinear global projection

The calibrated angular map is a composition of small Gaussian radial-basis deformations on the unit sphere:

```text
x_(k+1) = normalize(x_k + K_sigma(x_k, C_k) W_k)
```

Each step interpolates the current landmark motion. The deformation was integrated in small increments so every intermediate mesh remained orientation-preserving.

Frozen parameters:

```text
primary kernel sigma: 0.09 chord units
primary steps:        542
orange-plane steps:    85
total steps:          627
```

The candidate was chosen from the recorded sigma sweep by minimum RMS log-area distortion among the tested exact, no-flip solutions.

The operator is stored in `operator/WARP_STEPS.json.gz`.

## 8. Numerical verification

Level-6 mesh:

```text
vertices:  40962
triangles: 81920
```

Selected final model:

```text
detected flipped triangles: 0
minimum area-proxy ratio:    0.038403667
maximum area-proxy ratio:    5.860407373
1st percentile ratio:        0.389897759
99th percentile ratio:       1.266241755
RMS log-area proxy:          0.223049791
```

All six calibration landmarks have zero floating-point angular residual after the final composition:

- Wilkes root;
- SAA phase point;
- Stonehenge;
- Erie;
- Montréal;
- Toronto.

Numerical inverse checks:

```text
calibration-anchor inverse residual: 0°
random 200-point mean residual:       0.000024138°
random 200-point maximum residual:    0.002595807°
random 200-point 99th percentile:     0.000479612°
```

“No detected flips” is a dense numerical verification, not a continuum proof.

## 9. Orange-slice result

After the exact anchor solve, the orange triplet was projected to its least-displacement common great-circle plane and re-registered while holding every geographic anchor fixed.

Final candidate representatives:

```text
165892743 -> 49.87628265°, -2.69555526°
165892763 -> 49.86190931°, -2.74351030°
165892783 -> 49.81001006°, -2.91590219°
```

The middle point's residual from the endpoint-defined body-centred plane is approximately:

```text
0.000001049°
```

These are not labelled geographic predictions. Their absolute placement remains model-dependent because the supplied constraint fixes a plane and ordering, not one known longitude.

## 10. Shell handling

This solve establishes the **angular** Earth alignment. Wire S3 values are preserved exactly.

Montreal has wire S3 = 7 despite its municipality label. Therefore this run does not silently rewrite S3 to surface shell 3. It records:

```text
wire state:       exact packet value
physical anchor:  municipality angular region
radial semantics: unresolved transport/shell/epoch split
```

The orange authority likewise preserves its active shell interpretation separately from raw extraction.

A public physical-coordinate claim remains blocked until that radial semantic bridge is frozen.

## 11. Current verdict

```text
EARTH_ANGULAR_ALIGNMENT:
CALIBRATED_CANDIDATE_SOLVED

RIGID_REGULAR_ICOSAHEDRON:
EXCLUDED

FACE_CODEBOOK:
OPTION_A_WITH_OFFSET_14_SELECTED

NODE23_RELATION:
OFFSET_MAGNITUDE_MATCHES_23_MINUS_9

VARIABLE_STONEHENGE_BRIDGE:
EXACT_REVERSIBLE_AFFINE_CANDIDATE

ERIE_MONTREAL_TORONTO:
EXACT_EQUILATERAL_TREE_METRIC

GLOBAL_WARP:
ZERO_DETECTED_FLIPS_AT_LEVEL_6

ORANGE_SLICE:
BODY_CENTRED_PLANE_ENFORCED

RADIAL_SHELL_SEMANTICS:
UNDERDETERMINED

INDEPENDENT_HOLDOUT:
NOT_YET_RUN

PUBLICATION:
HOLD
```

This is now a real candidate globe alignment rather than an unprojected structural packet. It must remain private until a sealed holdout vector is decoded without moving any parameter.
