# Actual Sale-Crystal Triage

Status: PUBLIC_RESEARCH. SALE_LIST_ESTIMATES_NOT_MEASUREMENTS.

## Purpose

Rank real, currently purchasable crystal candidates from the sale
dataset against two frequency families, replacing the earlier
ideal-crystal comparison. Ranking uses actual sale-dataset
candidates and their estimated modes, never ideal-only calculated
lengths.

## External anchors

The scored sale dataset
(`rgcs_workbench/public_cage/actual_sale_crystal_phi_rgcs_scored_modes.json`
and `.csv`), the phi-Schumann ladder, and the RGCS frequency spine.

## RGCS operator

Two score columns per estimated mode, nothing merged:

```text
score_rgcs_4096_family      offset to the nearest 4096-multiple key
score_phi_schumann_family   offset to the nearest 7.83 * phi^n key
```

Current standings from the sale-list estimates:

```text
Best RGCS octave candidate:
  8-sided flawless Himalayan quartz, 157 mm
  axial estimate 20,098.13 Hz against 20,480 Hz (offset -1.86 percent)

Best phi-Schumann candidate:
  12-sided flawless Himalayan quartz, 125 mm
  bend mode 2 estimate 17,367.72 Hz against 17,280.81 Hz
  (offset +0.50 percent)

Best multi-hit phi candidate:
  24-sided Himalayan rutilated quartz Vogel, 138 mm
  bend mode 1 and shear f1 both within 2.2 percent of phi nodes
```

## Bench observables

Measurement first, purchase second where possible. For each
candidate: suspend lightly at nodal points, sweep 4 kHz to 55 kHz,
record with contact mic, accelerometer, or pickup, log peak modes,
bandwidth, Q, and split peaks, then compare measured peaks to both
score columns. The sale-list estimate stays separate from the
measured result forever; a measured row supersedes, it never
overwrites.

## Claim boundary

This lane claims a ranking of sale-list estimates. It does not claim
any crystal produces a physical effect, and an estimated mode is not
a measured mode. No healing or consciousness claim exists in this
lane; those remain refused.

## Next tests

1. Hold the champion selections by test against the scored dataset.
2. Reject any non-sale (ideal-only) row from the ranking by test.
3. Add measured-mode rows beside estimates when bench sweeps run,
   with the estimate retained.
