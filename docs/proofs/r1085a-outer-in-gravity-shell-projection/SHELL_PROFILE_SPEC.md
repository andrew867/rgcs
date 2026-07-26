# ShellProfile specification

Operational stack: shells [3, 4, 5, 6, 7, 8], inner to
outer. Shell 3's inner boundary is the land-zero surface; shell 8's
outer boundary is the outermost operational boundary. Shells 0..2 lie
below the land-zero surface and carry no declared thickness (refused).

Bounded candidate family (declared before projection; all retained;
`refuse_fitted_thickness` bans any member fitted to a source vector):

[
 {
  "profile_id": "UNIFORM_100KM_V1",
  "thickness_km_at_2025": {
   "3": 100.0,
   "4": 100.0,
   "5": 100.0,
   "6": 100.0,
   "7": 100.0,
   "8": 100.0
  },
  "stack_height_km_2025": 600.0,
  "provenance": "engineering candidate: six equal 100 km bands, no epoch rate; the maximum-ignorance member of the family."
 },
 {
  "profile_id": "ATMOSPHERIC_LADDER_V1",
  "thickness_km_at_2025": {
   "3": 12.0,
   "4": 38.0,
   "5": 35.0,
   "6": 215.0,
   "7": 300.0,
   "8": 400.0
  },
  "stack_height_km_2025": 1000.0,
  "provenance": "engineering candidate: bands echo conventional atmospheric layering above the land-zero surface (troposphere ~12 km, stratosphere ~38 km, mesosphere ~35 km, lower/upper thermosphere ~515 km split, exosphere band 400 km). Thermosphere band carries a small negative rate as a stand-in for solar-cycle/secular contraction (declared, not fitted). SOURCE_ESTABLISHED_PHYSICS for the layer altitudes; the shell mapping is a candidate only."
 },
 {
  "profile_id": "GEOMETRIC_DOUBLING_V1",
  "thickness_km_at_2025": {
   "3": 25.0,
   "4": 50.0,
   "5": 100.0,
   "6": 200.0,
   "7": 400.0,
   "8": 800.0
  },
  "stack_height_km_2025": 1575.0,
  "provenance": "engineering candidate: thickness doubles per shell from 25 km (25, 50, 100, 200, 400, 800), no epoch rate; the geometric member, echoing r12.shells8.SpacingLaw.GEOMETRIC."
 }
]

Epoch dependence is linear per band (`ShellBand.rate_km_per_year`);
non-positive thickness under the linear model is refused, not clamped.
No corpus value fixes these thicknesses: the physical shell structure
remains PHYSICAL_VALIDATION_NOT_CLAIMED.
