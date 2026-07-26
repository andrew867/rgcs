# Shell-3 zero: average land height

The bottom of shell 3 is referenced to average land height along the
gravity-defined vertical. Banned substitutes, each with a named
refusal locked by tests: mean sea level (untested), spherical Earth
radius, geometric distance from Earth's centre, WGS84 altitude, the
ellipsoid normal.

Declared land-elevation family (both retained):
{
 "CLASSIC_HYPSOGRAPHIC_840M": 840.0,
 "MODERN_DEM_797M": 797.0
}

Construction: the land-zero surface is the gravity level surface
W = W0_geoid - g_mean * h_land (W0 = 62636851.7 m^2/s^2,
g_mean = 9.7976 m/s^2), i.e. the geoid potential lifted by
the mean land elevation along gravity vertical. An untested MSL
substitution would shift the zero by the mean land elevation itself
(840.0 m) — declared, not hidden.

The reference is epoch-carried; with no declared secular land-height
rate it is epoch-constant, and that constancy is declared rather than
assumed.
