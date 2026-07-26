# Outer operational boundary

The outer boundary of shell 8: land-zero radius along the decoded
direction plus the profile's stack height, then deformed onto the
declared level surface Sigma_8(t) = {x : W(x,t) + kappa*M(x,t) =
C_8(t)} (level constant set at the nominal radius on the dipole axis,
the declared reference azimuth).

The inward calculation starts HERE — not at the geometric centre. The
physical core may be offset relative to the magnetic structure and the
ellipsoidal figure, so the outer-shell geometry is the reference
authority.

Boundary deformation from the nominal sphere at the training-word
direction (land ref CLASSIC_HYPSOGRAPHIC_840M, zeta
ZETA_FROM_OCTREE_Z_V1) — includes the gravity-equipotential (ellipticity) part;
the purely magnetic part is the difference from the GRAVITY_ONLY row:

[
 {
  "magnetic": "GRAVITY_ONLY",
  "profile": "UNIFORM_100KM_V1",
  "boundary_deformation_m": 9223.1
 },
 {
  "magnetic": "DIPOLE_B_MAGNITUDE",
  "profile": "UNIFORM_100KM_V1",
  "boundary_deformation_m": 9058.8
 },
 {
  "magnetic": "DIPOLE_SCALAR_POTENTIAL",
  "profile": "UNIFORM_100KM_V1",
  "boundary_deformation_m": 9223.1
 },
 {
  "magnetic": "DIPOLE_INCLINATION",
  "profile": "UNIFORM_100KM_V1",
  "boundary_deformation_m": 9484.4
 },
 {
  "magnetic": "GRAVITY_ONLY",
  "profile": "ATMOSPHERIC_LADDER_V1",
  "boundary_deformation_m": 10476.8
 },
 {
  "magnetic": "DIPOLE_B_MAGNITUDE",
  "profile": "ATMOSPHERIC_LADDER_V1",
  "boundary_deformation_m": 10321.0
 },
 {
  "magnetic": "DIPOLE_SCALAR_POTENTIAL",
  "profile": "ATMOSPHERIC_LADDER_V1",
  "boundary_deformation_m": 10476.8
 },
 {
  "magnetic": "DIPOLE_INCLINATION",
  "profile": "ATMOSPHERIC_LADDER_V1",
  "boundary_deformation_m": 10769.1
 },
 {
  "magnetic": "GRAVITY_ONLY",
  "profile": "GEOMETRIC_DOUBLING_V1",
  "boundary_deformation_m": 12768.9
 },
 {
  "magnetic": "DIPOLE_B_MAGNITUDE",
  "profile": "GEOMETRIC_DOUBLING_V1",
  "boundary_deformation_m": 12623.8
 },
 {
  "magnetic": "DIPOLE_SCALAR_POTENTIAL",
  "profile": "GEOMETRIC_DOUBLING_V1",
  "boundary_deformation_m": 12768.8
 },
 {
  "magnetic": "DIPOLE_INCLINATION",
  "profile": "GEOMETRIC_DOUBLING_V1",
  "boundary_deformation_m": 13108.9
 }
]

Outer-in vs inner-out invariant: checked on every decode
(`OuterInRadialResult.invariant_residual_km`, refused above 1e-9 km).
