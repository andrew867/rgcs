# Phyrll Generator Designer

Generate custom-fit printable holder templates from a validated crystal
specimen.

## Inputs

- source specimen (dimensions are inherited automatically)
- holder style, clearance (mm), wall thickness (mm), base thickness (mm)
- material, optional coil channel (width/depth), mounting holes, label text

## Geometry rules

- cavity length = specimen length + 2 × clearance
- cavity width = specimen width/diameter + 2 × clearance
- outer walls derived from cavity + wall thickness
- coil channel depth must fit inside the wall thickness — invalid combinations
  are refused with an explanation, not silently clamped

## Exports

| File | Contents |
|---|---|
| SCAD | deterministic OpenSCAD source for the holder |
| STL | generated only when OpenSCAD is installed; otherwise marked unavailable |
| build sheet PDF | dimensions, print settings, claim boundary, receipt hash |
| JSON receipt | design record with input/output hashes |

## Claim boundary

The build sheet is an engineering plan and reproducibility record. Predictions
are model outputs. Measurements decide.
