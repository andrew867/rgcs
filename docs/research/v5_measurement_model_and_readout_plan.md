# V5 Measurement Model and Readout Plan

Status: PUBLIC_RESEARCH. MEASUREMENT_PLAN. NO_PHYSICAL_CLAIM_ADVANCED.

## Purpose

Define the V5 readout and run discipline: THYR as the future quartz
readout lane, the extended dielectric witness layer, and the
one-variable-at-a-time run chain.

## External anchors

Rubano et al. 2019 THz Hyper-Raman (ledger P026) and the V4B
witness-layer sources. THYR mixes an intense sub-picosecond THz
pulse with a femtosecond optical pulse in alpha-SiO2; sidebands
appear at 2 omega_L minus and plus omega_T around the optical second
harmonic; the time-domain trace Fourier-transforms into the
excitation spectrum.

## RGCS operator

THYR is a readout lane, not a drive lane, and not a claim of RGCS
success. The source resonance list is preserved as data: 2.0, 5.2,
7.0, 13.4, 14.3, and 16.3 THz, with the 9 to 10 THz moving
polariton-like feature recorded as unresolved in the source; its
resolution requires new measurement, not interpretation.

The V5 witness layer adds ATR, THYR, s-SNOM, PTIR, and FTIR
availability flags, layer type, thickness, and surface gap on top
of the V4B contract. The V4B rule stands: a witness layer can never
carry a validation status.

## One-variable-at-a-time runs

Every run row names its parent run; the parent is the control; the
changed variable is named; the claim status is SIMULATION_ESTIMATE.
The V5 chain steps through witness epsilon, witness loss, surface
gap, quartz optic-axis orientation, and SAW bias field, one at a
time, held by test.

## Claim boundary

This lane claims a measurement design and a run discipline. It does
not claim device performance, and no run row can carry a measured
status until a bench measurement exists to back it.

## Next tests

1. Wire run rows to bench data files when the first sweep runs.
2. Add measured columns beside estimates, never replacing them.
3. Keep the unresolved THYR feature unresolved until a measurement
   resolves it.
