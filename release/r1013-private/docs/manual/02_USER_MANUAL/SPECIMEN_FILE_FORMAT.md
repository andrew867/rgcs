# Specimen File Format


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


The canonical format is JSON. The schema is `schemas/crystal-specimen.schema.json`.

## Minimum record

A minimum record supports only selected quick estimates.

```json
{
  "schema_version": "rgcs.crystal-specimen/1.0",
  "specimen_id": "crystal-001",
  "name": "Six-sided quartz",
  "material": {
    "material_id": "alpha_quartz",
    "density_g_cm3": 2.65,
    "handedness": "unknown"
  },
  "geometry": {
    "length_mm": 77.8,
    "wide_diameter_mm": 30.2,
    "narrow_diameter_mm": null,
    "facets": 6,
    "female_angle_deg": null,
    "male_angle_deg": null,
    "diameter_mode": "across_vertices",
    "angle_mode": "face_slope"
  },
  "orientation": {
    "status": "unknown"
  },
  "measurements": {
    "mass_g": 68.0
  }
}
```

## Complete regular-faceted record

```json
{
  "schema_version": "rgcs.crystal-specimen/1.0",
  "specimen_id": "crystal-001",
  "name": "Measured six-sided quartz",
  "description": "Double-terminated tapered specimen",
  "material": {
    "material_id": "alpha_quartz",
    "density_g_cm3": 2.65,
    "handedness": "unknown",
    "material_record_version": "alpha-quartz-default"
  },
  "geometry": {
    "length_mm": 77.8,
    "wide_diameter_mm": 30.2,
    "narrow_diameter_mm": 24.0,
    "facets": 6,
    "female_angle_deg": 51.843,
    "male_angle_deg": 60.0,
    "diameter_mode": "across_vertices",
    "angle_mode": "face_slope"
  },
  "orientation": {
    "status": "assumed",
    "c_axis_body_axis": "+Z",
    "euler_zxz_deg": [0.0, 0.0, 0.0],
    "uncertainty_deg": [0.0, 10.0, 360.0]
  },
  "measurements": {
    "mass_g": 68.0,
    "length_uncertainty_mm": 0.1,
    "diameter_uncertainty_mm": 0.2,
    "angle_uncertainty_deg": 1.0,
    "mass_uncertainty_g": 0.1,
    "temperature_c": 22.0
  },
  "provenance": {
    "operator": "local-user",
    "measurement_date": "2026-07-28",
    "source_type": "operator_measurement",
    "notes": "Replace example values with actual measurements."
  }
}
```

## Null and unknown

Use null when a value was not measured. Use `unknown` for a categorical state. Do not use zero for missing data.

## Source claim versus measured value

A marketplace listing or handwritten note belongs under `source_claims`. A caliper measurement belongs under `measurements`. Preserve both when they differ.

## Custom mesh

An irregular specimen may add:

```json
{
  "mesh_source": {
    "type": "stl",
    "path": "specimens/crystal-001.stl",
    "units": "mm",
    "sha256": "..."
  }
}
```

The mesh must have a declared scale and closed-volume audit.
