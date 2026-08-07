# Longitudinal Mode Bridge and Dielectric Witness Layer

Status: PUBLIC_RESEARCH. SIMULATION_SURROGATE. NO_PHYSICAL_CLAIM_ADVANCED.

## Purpose

Translate the source phrase "coherent longitudinal EMF" into a
conventional modeling lane, and extend it (V4B) with a
residue-sensitive dielectric witness layer. Free-space far-field
waves are transverse; longitudinal electric components are physical
in plasmas, metals, near fields, piezoelectric surfaces, and
surface-bound polariton modes, which is where this model stays.

## External anchors

The uploaded SPP source (archive record ARC-0005, hash-pinned):
surface plasmon polaritons as bounded interface modes; Raman modes
as molecular fingerprints with reported enhancements near 10^2 to
10^3 and plasmonic amplification near 10^5 to 10^6; and the
observation that surrounding media contaminated by observed
molecules shift the dielectric function enough to force numerical
treatment. The angular-momentum ring and time-varying boundary
anchors from the physics-spine ledger carry the rest of the chain.

## RGCS operator

```text
div(E) = rho / epsilon
omega_p = sqrt(n e^2 / (epsilon_0 m_eff))
epsilon(omega) = eps_inf - omega_p^2 / (omega^2 + i gamma omega)
k_spp = (omega/c) sqrt(eps_m eps_d / (eps_m + eps_d))
X_k(t) = X_0 + dX cos(m theta_k - Omega t + phi_0)
k_surface = k_incident + G_grating +/- K_phonon
```

The dielectric witness layer supplies eps_d and loss terms: a
formation event may leave transient molecules, aerosols, mineral
particles, oxidized residues, or water films; those shift the local
dielectric function; the shifted response is measurable. The residue
layer is a field-history witness hypothesis, never causal proof.

## Bench observables

Raman spectrum; SERS response where metal or mineral nanoparticles
are present; FTIR fingerprints; dielectric constant and loss
tangent; surface conductivity; particulate analysis; time-decay
retests; off-formation controls. The surrogate's outputs are the
SPP factor, predicted sidebands, and a damping status, each labeled
ESTIMATE, SIMULATION, MEASURED, or SOURCE_REPORTED.

## SSPP corrugated-waveguide lane

Conventional anchor: Erementchouk, Joy, Mazumder 2016 (spoof surface
plasmon polaritons on corrugated conductors; ledger row P018).
The 37-cell ring read as a corrugated waveguide:

```text
period d = pi * OD / 37   (24.4535 mm at 288 mm)
beta_max = pi / d
f_p = c / (4 h sqrt(eps_g))
well_formed when h > d / 2
```

The groove fill (eps_g), ambient medium (eps_a), and a thin witness
film (t_layer) form the lane's dielectric layer. A non-default layer
sets sensitivity_status to WITNESS_SENSITIVE, which is a measurement
expectation. The thin-layer mode is a hypothesis to be measured,
never causal proof.

## One-variable-at-a-time runs

RUN_DWL_0001 through RUN_DWL_0006 change exactly one input each:
baseline without a layer, then epsilon_d, loss tangent, mineral
flag, water film, and decay-retest interval. Changing only
epsilon_d changes the SPP factor and its residual against the air
baseline; changing only the loss tangent changes the damping
status. Held by test.

## Claim boundary

This lane claims conventional SPP arithmetic and a measurement
design for residue samples. It does not claim formation causality,
craft behavior, or any anomalous effect, and a witness layer can
never carry a validation status; the validator refuses one. Sale,
source, simulation, and measured labels never mix.

## Next tests

1. Wire witness-layer sample rows to the archive schema when real
   samples exist, with off-formation controls first.
2. Extend the surrogate with the grating and phonon wavevector
   inputs against measured S-parameters when a bench exists.
3. Keep the residue block honest: unknowns stay unknown until a
   measurement replaces them.
