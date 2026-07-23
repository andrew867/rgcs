# Nonlinear Optics in Quartz

**Authority:** RGCS R10.10 / v5.9.0 (candidate)
**Scope:** Second-harmonic generation (SHG) in quartz, and why bulk quartz cannot be phase-matched for it.
**Last verified commit:** v5.8.0 baseline (branch v580-r10-10)
**Prerequisites:** [CRYSTAL_SPECIMEN_PROGRAM.md](CRYSTAL_SPECIMEN_PROGRAM.md), [FREQUENCY_AND_PHASE_SYSTEM.md](FREQUENCY_AND_PHASE_SYSTEM.md)
**Related code / tests / schemas:** [../../r10/nlo.py](../../r10/nlo.py); tests/v52/test_r10_nlo.py
**Known limitations:** No optical measurement exists in this repository — no laser, no crystal on a bench, no photodiode. Every number here is book physics or closed-form arithmetic. Hardware is deferred.
**Next review trigger:** A measured SHG efficiency, a phase-matching scheme other than birefringent bulk (e.g. quasi-phase-matching), or any change to the coefficient constants in `nlo.py`.

## What is real

Quartz is trigonal, crystal class **32** (point group `D3`), and it is
**non-centrosymmetric**. That symmetry is the exact precondition for a
non-vanishing second-order susceptibility, so quartz genuinely has one.
It was the first material in which optical SHG was observed (Franken,
Hill, Peters and Weinreich, *Phys. Rev. Lett.* **7**, 118, 1961 — a ruby
laser doubled through a quartz plate). SHG in quartz is real and old.
The module does not dispute any of this.

The dominant coefficient is `d11 ≈ 0.3 pm/V` — roughly an order of
magnitude below KDP and two below common engineered doublers. Quartz has
a nonlinearity; it is a weak one.

## The honest negative

SHG is efficient only when the fundamental and the second harmonic stay
in step, i.e. when the phase mismatch

    Δk = (4π/λ)·(n(2ω) − n(ω))

is driven to zero. Normal dispersion makes `n(2ω) > n(ω)`, so `Δk ≠ 0`.
Birefringent phase matching cancels dispersion by playing polarizations
against the birefringence — but quartz's birefringence (~0.009) is far
too small to offset its dispersion over the relevant band. The verdict
the module returns is therefore:

    NOT_PHASE_MATCHABLE_IN_BULK_QUARTZ

Without phase matching, useful conversion is bounded by the **coherence
length**

    L_c = λ / (4·|n(2ω) − n(ω)|)

beyond which the harmonic dephases and back-converts. The module reports
`L_c` and refuses any claim of efficient bulk SHG in quartz.

## What the module refuses

- No claim that bulk quartz is a *useful* frequency doubler.
- No efficiency figure — nothing was measured.
- No leap from "quartz has a d-coefficient" to "quartz doubles light well."

This bounds a specimen-level optical expectation only; it does not license
any coordinate, frequency, or memory claim elsewhere in R10.

See also: [FREQUENCY_AND_PHASE_SYSTEM.md](FREQUENCY_AND_PHASE_SYSTEM.md)
for the frozen frequencies these optical questions are sometimes attached
to, and [INVERSE_PROBLEMS.md](INVERSE_PROBLEMS.md) for how a fitted
optical constant can look precise yet be non-identifiable.

PHYSICAL_VALIDATION_NOT_CLAIMED
