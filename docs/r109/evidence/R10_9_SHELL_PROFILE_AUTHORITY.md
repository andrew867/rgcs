# R10.9 Shell Profile Authority (Phase 6)

Source-confirmed semantics (SOURCE_REPORTED, R109-SHL-01):

- `S3` is the physical shell field of the compact packet.
- **Shell 3 = finite crustal/surface band.** Sea floor, land, and
  mountains occupy VARIABLE DEPTH within it; it is not a
  zero-thickness sphere. Implemented as
  `r109.shell_semantics.CrustalBandProfile` with DECLARED (never
  fitted) topographic bounds: Terra −11..+9 km, Luna −9.1..+10.8 km —
  body-specific thickness by construction.
- **Shell 7 = orbital object class** (`OrbitClass`), not a band with
  topography.
- Shell thickness differs by planet: per-body profiles; candidate
  Earth stack profiles remain the declared engineering family in
  `cwatlas.r1085a.shell_profile` (UNIFORM_100KM_V1,
  ATMOSPHERIC_LADDER_V1, GEOMETRIC_DOUBLING_V1) — all retained.

## Marker firewall (R109-SHL-02)

Four facts are reported side by side and never collapsed
(`shell_marker_report`): the decimal terminal marker (source-reported:
3 = surface object, 7 = object in orbit), the binary S3 field
(exact arithmetic), the physical shell semantics (source-reported),
and epoch/phase closure (UNRESOLVED). `refuse_marker_collapse()`
blocks any claim that the decimal marker IS the binary S3 bits — no
transform receipt exists. Observed and preserved: V1's Montréal
transcription `168729543` has decimal terminal 3 but decoded S3 = 7 —
exactly the kind of divergence the firewall exists to keep visible.

## Radial model (R109-SHL-03)

The outer-in shell-fraction equation
(`cwatlas.r1085a.outer_in_radial`, OUTER_IN_GRAVITY_FIELD_LINE)
remains PROVISIONAL production authority, versioned, unchanged.
Outer-in vs inner-out bookkeeping verified to close under every
declared profile (test-enforced).
