# RGCS report for My crystal (my-crystal-001)

This report contains computed candidate frequencies. A computed frequency is not a measured resonance.

## Specimen
- material: alpha_quartz
- length: 77.8 mm
- wide diameter: 30.2 mm (across_vertices)
- narrow diameter: 24.0 mm
- validation: PASS, 1 warning(s)
- specimen hash: 05aed5a559bc3cd72a3105d6101fc958b1087260d01fca34db623d06c89d57b4
  - warning: Orientation is not measured; anisotropic results will carry an orientation-unknown warning and an ensemble spread instead of a single line.

## result
- evidence class: NUMERICAL_SIMULATION

| mode | frequency |
|---|---|
| 1 | 31.743 kHz |
| 2 | 31.745 kHz |
- warning: orientation not measured: frequencies assume C-axis along body +Z; expect shifts for the real cut

## result
- evidence class: None

## Reproduction
The specimen file, results, and hashes in this folder let another RGCS install reproduce every number. Verify with: rgcs bundle verify FOLDER
