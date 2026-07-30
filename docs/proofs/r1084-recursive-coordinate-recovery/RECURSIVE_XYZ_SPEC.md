# Recursive XYZ spec (R10.8.4 §§2–5)

## Parse

Digits `d0 d1 d2 d3 ...` group into ordered levels `L_j = (X_j, Y_j, Z_j)`.
A trailing X or X,Y forms an explicit `CWPartialLevel`. No padding, no
rejection, no maximum length. (`cw_recursive_xyz.py`)

## State

`S_j = (T_j, I_j, F_j, R_j, U_j)`: surface triangle (exact Fraction chart
coords in the ordered physical face), radial interval (exact Fraction km),
frame state (family, codebook, SourceFaceID != PhysicalMeshFaceID,
vertex order), the complete route, and an uncertainty certificate.
(`cw_hedron_state.py`)

## Surface operator (Family C — see RECURSIVE_OPERATOR_INVENTORY.md)

The 10-per-edge lattice divides the current triangle into 100
sub-triangles. Digit pair (X, Y):

* `X + Y <= 9`  -> UP child at lattice (X, Y), orientation preserved;
* `X + Y >= 10` -> DOWN child at (9 - X, 9 - Y), orientation FLIPPED.

Bijective (55 UP + 45 DOWN = 100), exactly invertible
(`locate_digits`), containment-exact, and non-flattening: because DOWN
children reverse orientation, identical later digits denote different
directions depending on the fold history — the stream cannot be read as
completed decimal fractions. (`cw_surface_refinement.py`)

## Radial operator

Z selects the z-th tenth of the current radial interval (nested,
half-open). The ROOT interval is a declared profile from a finite set
(`ROOT_RADIAL_PROFILES`); no shell is ever inferred from the final digit.
(`cw_radial_refinement.py`)

## Invariants (tested)

`T_{j+1} subset T_j`, `I_{j+1} subset I_j`, hence
`Omega_{j+1} subset Omega_j`; removing final digits returns the exact
parent state; adding one complete triplet divides the surface diameter by
10 and the radial thickness by 10.

## Transformation chain

raw -> levels -> face context (codebook, §7) -> per-level surface child ->
per-level radial child -> declared compensation (§8) -> final region
(polygon + radial interval + uncertainty certificate) -> Wilkes/SAA/epoch
Earth frame -> geodetic lat/lon/height. Latitude and longitude exist only
at the final stage; the centroid is emitted solely as
`REPRESENTATIVE_CENTROID_NOT_A_MEASURED_POINT`. (`cw_recursive_decoder.py`)

## Encoder

Exact inverse for complete levels under C0 (`cw_recursive_encoder.py`);
round-trip locked by `test_encoder_round_trip_known_point` and by the
`reverse_encoding.matches_raw = true` receipts in FULL_VECTOR_TRACE.json.
