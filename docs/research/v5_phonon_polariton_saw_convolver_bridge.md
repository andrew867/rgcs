# V5 Phonon-Polariton and SAW Convolver Bridge

Status: PUBLIC_RESEARCH. SOURCE_BOUND_OPERATORS. NO_PHYSICAL_CLAIM_ADVANCED.

## Purpose

Extend the longitudinal-mode bridge with four source-bound lanes:
the alpha-quartz anisotropic phonon-polariton lane, the US3833867
SAW convolver operator, the US4023124 SAW geometry guard, and the
hBN hyperbolic benchmark. Patents and papers are anchors and
geometry, never validation.

## External anchors

Ledger rows P020 through P027
(`rgcs_workbench/public_cage/v5_reference_ledger.json`): Falge,
Otto, Sohler 1974 ATR dispersion on alpha-quartz; US3833867 Sperry
Rand convolver; US4023124 Philips SAW geometry; direct s-SNOM SPhP
observation on quartz; monoisotopic hBN polariton lifetimes; Scott
and Ushioda polariton intensities; Rubano 2019 THz Hyper-Raman.

## RGCS operator

```text
k_p = (omega/c) sqrt((eps_x eps_z - eps_z)/(eps_x eps_z - 1))
s(x) = A exp(-x/L_p) sin(2 pi x / d - phi)
k_p' = 2 pi / d - k0 cos(theta_in)
omega_3 = omega_1 + omega_2, k_3 = k_1 - k_2
lambda_saw = v_saw / f_saw; q4 = lambda/4; q8 = lambda/8
```

Optic-axis orientation selects which tensor components enter the
polariton branch; parallel and perpendicular geometries never share
components. The convolver is bidirectional by construction, its
bias field is attenuation control and carrier drift, and the model
refuses net gain as an operating target. Geometry features must be
tied to a material velocity and frequency; correction strips sit at
odd multiples of lambda/4 outside the overlap envelope; aperture
modes never mix.

## Bench observables

ATR spectra against gap and layer thickness; near-field fringe
periods converted to wavevectors; convolver sum-frequency output;
sideband spectra; hBN-style wide-scan fringe analysis where the
scan must be at least as wide as the claimed propagation length.

## Claim boundary

The 1974 sources prove SAW convolution and quartz polariton
dispersion in their own systems. Nothing here validates RGCS
hardware, craft behavior, or any anomalous effect. hBN is a
benchmark material, not a replacement for quartz. Crop residue
remains a dielectric witness-layer hypothesis, not causal proof.

## Next tests

1. Fit measured quartz constants into the medium fields when a
   bench spectrometer run exists.
2. Model the convolver overlap region against the ring sector pitch.
3. Compare witness-layer ATR sensitivity to the SSPP thin-layer
   sensitivity for the same film.
