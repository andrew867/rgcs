# Measuring Your Crystal


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Tools

A basic record can use:

- digital calipers;
- a scale with suitable resolution;
- a flat background and camera;
- a protractor or angle gauge;
- a rotating polarizer or polarized display for orientation work;
- soft gloves or clean hands;
- a specimen identifier label that does not touch the crystal during a solve.

## Measurement order

1. Photograph the untouched specimen.
2. Assign a specimen ID.
3. Measure mass.
4. Measure tip-to-tip length.
5. Count shaft facets.
6. Measure the widest cross-section.
7. Measure the narrow cross-section.
8. Record whether each diameter is across vertices or across flats.
9. Measure both termination angles and record the angle convention.
10. Inspect chips, inclusions, repairs, coatings, glue, and asymmetric facets.
11. Estimate orientation and uncertainty.
12. Repeat each dimension at least three times.

## Length

Measure from one apex to the other. Do not measure only the shaft. Record the tool resolution and repeated readings.

Example:

```json
{
  "length_mm": 77.80,
  "length_uncertainty_mm": 0.10
}
```

## Diameters

A tapered crystal needs two diameters.

- Wide diameter: the larger shaft cross-section near the wide termination.
- Narrow diameter: the smaller shaft cross-section near the narrow termination.

Measure at a defined axial station. Photograph the station.

## Mass and density

Mass helps detect an inconsistent geometry or assumed density. It does not determine a unique mode spectrum by itself.

For alpha quartz, a nominal density may be used as a material default. A measured density or supplier certificate should replace it when available.

## Termination angles

Do not copy 51.843 degrees and 60 degrees unless they describe your specimen. Those values are defaults and source claims for a particular geometry family.

When the angle is unknown, enter null and choose a model that can operate without it. A full geometry solve must refuse or use an explicit uncertainty ensemble.

## Facet irregularity

The regular-polygon model assumes equal facets. If the specimen is irregular, capture each vertex or use a mesh imported from photographs or scanning. Do not average severe asymmetry into a false regular crystal.

## Defects

Record defects because they may change local stiffness, mass, damping, optical response, and measured Q.

Use neutral descriptions:

- chip at male apex;
- internal inclusion at 0.42L;
- repaired fracture;
- surface coating;
- glued holder residue.

## Orientation

A visual shaft axis is not automatically the crystallographic C-axis. Store orientation confidence separately from geometry confidence.

## Measurement worksheet

Use `examples/crystal_measurement_worksheet.csv` or the desktop wizard. Keep the raw readings. Do not keep only the average.
