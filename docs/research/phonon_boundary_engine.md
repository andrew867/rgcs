# Phonon Boundary Engine

Status: PUBLIC_RESEARCH. NO_PHYSICAL_CLAIM_ADVANCED.

## Purpose

Treat the crystal subsystem as a phonon-addressed phase grating: a
coherent acoustic or elastic wavepacket in quartz or a plate, whose
boundary conditions change while the packet is interacting.

## External anchors

US7894125B2 (acousto-optic devices), WO2021069873A1 (selectable
acoustic transducer beam deflection), and the SAW spatiotemporal
magnet-free circulator literature (arXiv:1905.13252) anchor
phonon-to-optical modulation and acoustic nonreciprocity. Quartz is
an established acousto-optic material.

## RGCS operator

```text
u(x,t) = sum_n q_n(t) psi_n(x)
B(t) in {open, shorted, capacitive, resistive, driven, lossy,
         clamped, released}
omega_out = omega_in +/- m Omega_phonon
k_out = k_in +/- m K_phonon
```

## Energy and momentum accounting

Boundary switching work supplies or removes energy; the drive and
switch electronics are the only energy sources in the model.
Sidebands and frequency translation are the observables.
A momentum ledger is required before any force reading is accepted
from this lane.
DCE is an analogy, not a power claim, and it stays out of the phonon
bench plan entirely.

## Bench observables

1. Ring-down response before and after a boundary switch.
2. Sideband spectrum around the drive frequency.
3. Acoustic-to-optical phase modulation with a laser probe.
4. Fixture reversal to eliminate clamp asymmetry.
5. Sensor reversal to eliminate measurement asymmetry.
6. Heating control with identical electrical power and randomized
   phase.

## Claim boundary

This lane claims conventional acousto-elastic mode conversion and
modulation. It does not claim anomalous energy, communication, or
propulsion effects. Bench measurement remains pending.

## Next tests

1. Wire the phonon lane entries to the Phyrll measurement-lane
   schema (voltage, current, temperature, magnetometer channels,
   dummy controls per sweep).
2. Predict the sideband ladder for the 20.48 kHz burst control on a
   quartz specimen.
3. Add the randomized-phase heating null to the sweep plan template.
