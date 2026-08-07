# Angular-Momentum-Biased Resonator Rings

Status: PUBLIC_RESEARCH. NO_PHYSICAL_CLAIM_ADVANCED.

## Purpose

Anchor the 37-cell annular resonator in the established physics of
angular-momentum-biased rings: stationary structures whose cell
parameters are modulated as a traveling wave, producing a synthetic
rotation bias and measurable nonreciprocity without magnets and
without mechanical rotation.

## External anchors

US9405136B2 (magnetic-free nonreciprocal devices through angular
momentum biasing), Nature Physics nphys3134 (parametrically
modulated coupled-resonator loops), ACS Photonics ph400058y
(angular-momentum-biased nanorings), and US7561759B2 (tunable-loss
ring resonator modulator) document the mechanism family. They
support nonreciprocity and spatiotemporal modulation only.

## RGCS operator

```text
k in 0..36
theta_k = 2 pi k / 37
Z_k(t) = Z_0 + dZ cos(m theta_k - Omega t + phi_0)
```

Locked geometry for the bench profile: 37 cells, 288 mm outer and
188 mm inner diameter (the ratio reduces exactly to 47/72), running
occupancy 35 of 37, steering state 33 active, no mechanical
rotation, external resonance 4096 x 411 = 1,683,456 Hz. The
field-scale comparison profile uses metres and is a separate
profile; code must never mix the two
(RGCS_RING_PROFILE_BENCH_MM vs RGCS_RING_PROFILE_FIELD_M).

## Bench observables

The first validation is direction agreement, not any mechanical
quantity: commanded_direction = arg(d_eff) of the cell weighting,
measured_direction = arg(delta-B measured), pass when the wrapped
difference is inside tolerance. Secondary observables: S11/S21
modulation products, sidebands at carrier plus and minus n Omega,
thermal symmetry map, vibration response, near-field B phase around
the ring.

## Claim boundary

This lane claims that a stationary, modulated ring can carry a
synthetic angular-momentum bias with measurable nonreciprocity,
which the anchors already demonstrate in other bands. It does not
claim thrust, lift, or craft behavior; forbidden claims are listed
per entry in the spine registry and enforced by the firewall.

## Next tests

1. Verify the 37-cell theta table and mask counts by test (done in
   tests/release_cage).
2. Simulate small-m modulation and predict the sideband ladder.
3. Bench: all-active mask, mirrored mask, and reversed phase
   progression nulls before any steering run.
