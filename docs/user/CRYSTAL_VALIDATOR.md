# Crystal Validator

Enter measured crystal geometry, uncertainty, and provenance; get validation,
derived geometry, a diagram, and export paths.

## Required inputs

- specimen ID
- material family
- length (mm)
- width **or** diameter (mm)
- measurement uncertainty (mm) — **required**; there is no validation without it

Optional: facet/side count, termination angle, mass, measured node locations,
photos/diagram files, supplier, operator, source notes.

## What is derived

- aspect ratio and length/diameter ratio
- termination angle status
- volume estimate (where the geometry supports it)
- density consistency check (when mass is present)
- missing-measurement list and overall validation status

Derived values update as you type. Missing required fields block export.

## Exports

| File | Contents |
|---|---|
| `specimen_<id>.json` | schema-validated specimen receipt with SHA-256 |
| `specimen_<id>_certificate.pdf` | certification sheet ([details](CERTIFICATION_SHEETS.md)) |
| `specimen_<id>_geometry.svg` | labelled 2-D geometry diagram |
| `specimen_<id>.scad` | optional OpenSCAD model |

## Claim boundary

Validation here means *geometric and schema validation of your measurements*.
It records measured inputs, derived geometry, model estimates, and provenance.
It does not by itself validate an anomalous physical effect.
