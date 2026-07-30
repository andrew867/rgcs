# Aperture Ring Model


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Source-provenance geometry

- 35 physical positions;
- 33 active apertures;
- 2 omitted positions;
- occupancy \(33/35\);
- inner and outer area indices 29 and 89;
- prime denominator family 37;
- scalable geometry.

## Radial relationship

\[
\frac{R_i^2}{R_o^2}=\frac{29}{89},
\qquad
R_i=R_o\sqrt{\frac{29}{89}}.
\]

The prime-ratio construction gives candidate numerical radii:

\[
R_i\approx82.2616108\ \mathrm{units},
\qquad
R_o\approx144.1096998\ \mathrm{units}.
\]

Generator-scale candidate in millimetres:

- inner radius 82.2616 mm;
- outer radius 144.1097 mm;
- outer diameter 288.2194 mm;
- annular width 61.8481 mm.

Craft-scale candidate in metres:

- inner radius 0.822616 m;
- outer radius 1.441097 m;
- outer diameter 2.882194 m;
- annular width 0.618481 m.

## Torus equivalent

\[
R_{\mathrm{major}}=\frac{R_o+R_i}{2},
\qquad
a_{\mathrm{minor}}=\frac{R_o-R_i}{2}.
\]

## Angular lattice

\[
\Delta\theta=360^\circ/35=10.285714\ldots^\circ.
\]

Five positions give:

\[
5\Delta\theta=360^\circ/7=51.428571\ldots^\circ.
\]

## Frequency-to-geometry realization

For a 16 Hz traveling pattern:

\[
35\times16=560\ \mathrm{Hz},
\]

\[
33\times16=528\ \mathrm{Hz},
\]

\[
2\times16=32\ \mathrm{Hz}.
\]

Each position has 16 sub-bins:

- total bins: 560;
- active bins: 528;
- blank bins: 32.

## Integer master timing

A compatible exact lattice has 224000 ticks per 16 Hz revolution and a 3.584 MHz master clock. The target implementation must regenerate and verify every integer relationship rather than hard-code the values.

## Missing geometry

- exact gap indices;
- aperture diameter and shape;
- plate thickness;
- upper and lower ring offset;
- optical path;
- conductive or dielectric implementation;
- drive and sensor geometry.
