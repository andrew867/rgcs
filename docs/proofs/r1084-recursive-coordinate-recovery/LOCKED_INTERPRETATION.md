# Locked interpretation (R10.8.4 §1)

Permanently locked (operator, 2026-07-25): CW source-vector digits group
into **ordered XYZ triplets**, each triplet one hierarchical refinement
instruction through the triangular surface hierarchy (X, Y) and the radial
shell hierarchy (Z):

```
165876523  ->  L1 (1,6,5)  ->  L2 (8,7,6)  ->  L3 (5,2,3)
165877623  ->  L1 (1,6,5)  ->  L2 (8,7,7)  ->  L3 (6,2,3)

165892743  ->  (1,6,5) -> (8,9,2) -> (7,4,3)
165892763  ->  (1,6,5) -> (8,9,2) -> (7,6,3)
165892783  ->  (1,6,5) -> (8,9,2) -> (7,8,3)
```

The orange-slice triplet shares the first two complete levels and differs
only in the level-3 Y instruction (4 -> 6 -> 8), with level-3 X (7) and Z
(3) fixed. Vectors may end after X or Y inside the final level (explicit
partial level, axis-specific uncertainty, digits append in X, Y, Z order).

## Superseded and regression-locked as REJECTED

* five independent base-100 semantic tokens (fold / mod-20 face rule);
* three contiguous XYZ blocks;
* three completed decimal fractions (column flattening);
* one Cartesian unit vector;
* direct latitude/longitude input;
* fixed-resolution nine-digit address;
* shell inferred from the final decimal digit.

Registry: `cwatlas/r1084/cw_recursive_xyz.py::REJECTED_MODELS`; tests:
`tests/cwatlas/r1084/test_r1084_recursive.py::test_rejected_models_registry`.

Consequence for prior numbers: the 1,830 km direct-global residual, the
218 km BARY_DIGIT residual, and the 260.5 km flattened-fraction residual
are all results for rejected models (`WRONG_MODEL_TESTED`) and carry no
weight for or against the recursive codec. The recursive codec's own
placement results live in `STONEHENGE_CONTAINMENT_REPORT.md`.

Implementation: `cwatlas/r1084/` (parser, typed state, surface lattice
refinement with folding, radial nesting, gravity gradient, codebooks,
decoder, encoder, trace).

SOURCE_ORIGIN_VALIDATED: no
