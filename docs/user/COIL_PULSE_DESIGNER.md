# Coil and Pulse Designer

Estimate wire and coil parameters, generate pulse tables, compute modulation
sidebands, and export build sheets for a selected generator assembly.

## Inputs

- assembly ID, wire gauge and material, coil radius/height, turn count,
  number of coils
- pulse base frequency (4096 Hz remains the explicit default carrier),
  modulation key, modulation mode, duty cycle, phase mode, voltage/current
  limits

## Pulse modes

`base_4096`, `am_key`, `pwm_key`, `timing_fm_key`, `phase_dither_key`,
`quadrature_key`. Unsupported keys are allowed only as *custom* entries and are
labelled with a warning.

## Outputs

- wire length and resistance estimates (model estimates, labelled as such)
- sideband table — e.g. carrier 4096 Hz with key 925 Hz gives 3171 and 5021 Hz
- pulse timing table and phase/quadrature diagram
- PDF build sheet and JSON receipt

## Claim boundary

Wire, resistance, and sideband values are model outputs from declared formulas.
The build sheet is an engineering plan and reproducibility record — it is not a
measurement, and it does not by itself validate any anomalous physical effect.
