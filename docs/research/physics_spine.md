# RGCS Candidate Physics Spine

Status: PUBLIC_RESEARCH. NO_PHYSICAL_CLAIM_ADVANCED.

## Purpose

Describe the candidate physics spine the workbench simulates and
plans measurements for. The spine is a chain of conventional,
testable mechanisms. It is a research programme and a simulation
target, not a proven device.

```text
phase authority
-> phonon/acoustic modulation
-> time-varying boundary / impedance gate
-> 37-cell spatiotemporally modulated annular resonator
-> angular-momentum-biased synthetic rotation
-> slow-wave / surface-wave response
-> measured sidebands, nonreciprocity, delta-B, heat, vibration,
   optical phase, and particle redistribution
```

## External anchors

Every lane cites a conventional technical anchor in the patent and
paper ledger (`rgcs_workbench/public_cage/patent_paper_ledger.json`):
angular-momentum-biased ring resonators, parametrically modulated
coupled-resonator loops, tunable-loss ring modulators, microwave
time boundaries, time-variant metasurfaces, acousto-optic devices,
SAW spatiotemporal circulators, and the superconducting-circuit
dynamical Casimir experiment. Anchors support the mechanisms they
document and nothing more.

## RGCS operator

The machine-readable lane set lives in
`rgcs_workbench/public_cage/physics_spine_entries.json`. The core
ring operator is a resonator state equation, never a force equation:

```text
k in 0..36
theta_k = 2 pi k / 37
X_k(t) = X_0 + dX cos(m theta_k - Omega t + phi_0), X in {Z, C, L, R}
```

## Bench observables

First-stage observables are S-parameters, sidebands, nonreciprocity,
the near-field delta-B vector, thermal maps, vibration and phonon
maps, optical phase shift, and particle redistribution. Force or
torque is not a first-stage observable and is not accepted until
conventional nulls close and a momentum ledger closes.

## Claim boundary

RGCS models candidate physics-spine relationships and tracks
provenance and claim boundaries. RGCS does not validate anomalous
propulsion or source attribution. The positron and dynamical-Casimir
lanes are long-term analogy lanes only: no bench use, no hardware
path, bench priority zero. Forbidden public claims are enforced by
the claim firewall and its release-gated tests.

## Next tests

1. Simulate the 37-cell modulation operator and predict sideband
   orders for small m.
2. Plan the direction-agreement bench measurement: commanded bias
   direction against measured near-field delta-B direction.
3. Extend the spine entries with simulation results as they land,
   each with controls and a claim boundary.
