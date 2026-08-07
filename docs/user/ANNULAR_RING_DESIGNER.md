# Annular Ring Designer

Design annular ring prototypes: geometry, active/blanked cell masks, probe
layouts, diagrams, and engineering sheets.

## Inputs

- outer diameter (mm), inner diameter (mm), cell count
- active mask (must match the cell count exactly) and blanked cells
- probe plan, drive mode, modulation key, material assumptions

## Default RGCS fixture

OD 288 mm · ID 188 mm · 37 cells · 35/37 running · 33 active steering ·
4 blanked · base 4096 Hz · keys 925, 963.026, 1337.

## Outputs

- ring diagram SVG with labelled sectors
- phase map CSV and active mask CSV
- probe layout SVG
- SCAD geometry
- engineering PDF and JSON receipt

Cell geometry closes exactly: 37 cells span the full ring with no residual gap.

## Claim boundary

This design records geometry, masks, phase tables, probe layouts, and model
outputs. It is not evidence of physical performance until measured.
