# Gravity field-line integration

Vertical: GRAVITY_VERTICAL, v_g = -grad U / |grad U| (internally the
geodetic W = V + centrifugal with g = +grad W; one sign convention,
stated once). Potential model: GM/r truncation with J2(t) (linear
secular rate -2.6e-11/yr) and centrifugal term —
SOURCE_ESTABLISHED_PHYSICS as a model; nothing is measured.

Integration: RK4 on dx/ds = gravity_down(x), step 5000.0 m,
accumulating true path distance from the outer operational boundary
inward (D_in). The straight geocentric radial endpoint is computed
alongside on every run; the lateral deviation between the two is
receipted per projection, never asserted.

Training-word deviations by profile (m, over each profile's D_in):

[
 {
  "profile": "ATMOSPHERIC_LADDER_V1",
  "field_line_deviation_m": 3226.5
 },
 {
  "profile": "ATMOSPHERIC_LADDER_V1",
  "field_line_deviation_m": 3226.6
 },
 {
  "profile": "ATMOSPHERIC_LADDER_V1",
  "field_line_deviation_m": 3226.8
 },
 {
  "profile": "ATMOSPHERIC_LADDER_V1",
  "field_line_deviation_m": 3239.9
 },
 {
  "profile": "ATMOSPHERIC_LADDER_V1",
  "field_line_deviation_m": 3240.0
 },
 {
  "profile": "ATMOSPHERIC_LADDER_V1",
  "field_line_deviation_m": 3240.2
 },
 {
  "profile": "GEOMETRIC_DOUBLING_V1",
  "field_line_deviation_m": 5140.7
 },
 {
  "profile": "GEOMETRIC_DOUBLING_V1",
  "field_line_deviation_m": 5140.8
 },
 {
  "profile": "GEOMETRIC_DOUBLING_V1",
  "field_line_deviation_m": 5140.9
 },
 {
  "profile": "GEOMETRIC_DOUBLING_V1",
  "field_line_deviation_m": 5141.2
 },
 {
  "profile": "GEOMETRIC_DOUBLING_V1",
  "field_line_deviation_m": 5165.7
 },
 {
  "profile": "GEOMETRIC_DOUBLING_V1",
  "field_line_deviation_m": 5165.8
 },
 {
  "profile": "GEOMETRIC_DOUBLING_V1",
  "field_line_deviation_m": 5166.1
 },
 {
  "profile": "GEOMETRIC_DOUBLING_V1",
  "field_line_deviation_m": 5166.2
 },
 {
  "profile": "UNIFORM_100KM_V1",
  "field_line_deviation_m": 1678.1
 },
 {
  "profile": "UNIFORM_100KM_V1",
  "field_line_deviation_m": 1678.2
 },
 {
  "profile": "UNIFORM_100KM_V1",
  "field_line_deviation_m": 1800.1
 },
 {
  "profile": "UNIFORM_100KM_V1",
  "field_line_deviation_m": 1800.2
 }
]

Locked behaviour: deviation > 0 at mid-latitude, ~0 on the equator and
spin axis (symmetry) — the gravity path differs from the geometric
radial exactly where the model predicts it should.
