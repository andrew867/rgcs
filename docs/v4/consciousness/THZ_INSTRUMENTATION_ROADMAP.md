# T04 — THz/6G measurement and superheterodyne roadmap

Coverage: **C018, C020–C022**. Gate: **G34**. Lane: **quarantined**.
Status: `ENGINEERING_PROTOTYPE` / `PROTOCOL_READY_HARDWARE_REQUIRED`.

## The boundary, stated before anything else

> **The existence of 6G hardware at ~100 GHz–1 THz is not evidence
> that the brain receives THz.**

Engineers built radios at those frequencies because the spectrum was
available and the physics is well understood. That fact says precisely
nothing about neural tissue. C020 and C022 are marked **ANALOGY ONLY**
in the registry, and the registry entry's own failure condition says
so (G34).

## Why the analogy is weak on its own terms

**Water absorption.** Tissue is mostly water, and water is nearly
opaque at THz: penetration depth is on the order of **tens to hundreds
of micrometres**. A THz field does not reach the cortex from outside;
it barely reaches past the skin. Any "brain THz receiver" proposal must
explain this first, and none does.

**No identified mixer.** A superheterodyne receiver requires a
nonlinear mixing element, a local oscillator, and an IF stage. C022 has
none of the three identified in tissue. The analogy names a circuit
topology and leaves every component unfilled.

**Thermal confound.** At the power levels needed to penetrate, the
dominant effect is heating. A "nonthermal THz effect" must be
demonstrated against a thermal control matched to the same temperature
rise.

## What the lane is good for

C023 — **cross-frequency coupling** — is a real, measured phenomenon in
neural data at ordinary frequencies (Hz to ~200 Hz), and it *is*
implemented and tested (`phase_amplitude_coupling`, with surrogates).
Downconversion as a *mathematical* operation is well defined and does
not require any THz claim. See
[SYNCHRONY_AND_MENTORSHIP.md](SYNCHRONY_AND_MENTORSHIP.md).

## C021 — the 100 GHz–10 THz measurement lane

`PROTOCOL_READY_HARDWARE_REQUIRED`. If the hypothesis is to be tested
at all, the honest target is **material spectroscopy** (quartz,
ordered water, microtubule preparations in vitro) — not a person.

Staged requirements: THz source and detector, near-field microscopy,
pump-probe spectroscopy, electro-optic sampling, heterodyne detection,
phase-noise budget, link budget, and a noise floor that can actually
reach the claimed signal level.

**Falsified if** the instrument noise floor cannot reach the claimed
signal level — which is the first thing to compute and the reason this
is a roadmap rather than an experiment.

## Cost and access

THz time-domain spectroscopy systems are six-figure instruments, or
facility time. This is a **procurement and collaboration** blocker, and
a human-only decision.

## Boundary

Neural rhythms are used here as an **analogy for signal-processing
concepts**, never as an assumption that the brain is built like a
radio.
