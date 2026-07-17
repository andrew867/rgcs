# T05 — Synchrony, mentorship, fireflies, pendulums, gamma

Coverage: **C013, C023–C026, C045, C048**. Gate: **G35**.
Lane: **quarantined**.
Implementation: `kuramoto`, `kuramoto_critical_k`,
`synchrony_with_surrogates`, `phase_amplitude_coupling`,
`coherence_is_not_truth`.

## Kuramoto against its analytic limit (C025)

    theta_i' = omega_i + (K/N) sum_j sin(theta_j - theta_i)

For a Lorentzian frequency distribution of half-width γ, the mean-field
critical coupling is **K_c = 2γ** (Kuramoto). The simulation is
validated against that analytic result, not against a picture of
synchrony: sub-critical stays incoherent, super-critical locks
(`test_kuramoto_matches_analytic_critical_coupling`).

Fireflies and pendulums (C025) are the same equation with different
oscillators. The metaphor is exact here — which is precisely why it
carries no consciousness content.

## Surrogate controls are mandatory (C024, C045)

`synchrony_with_surrogates()` reports the phase-locking value **and**
its surrogate-corrected p-value.

This matters because **PLV between two slow signals is high by
construction**. Two independent 1 Hz signals will look synchronized.
Reporting a raw PLV of 0.8 without the surrogate distribution is not a
finding, it is a filter setting.

**Falsified if** measured synchrony does not exceed pseudo-pair
surrogates.

## Cross-frequency coupling (C013, C023)

`phase_amplitude_coupling()` computes a modulation index against
phase-shuffled surrogates. Tested: a genuinely coupled signal exceeds
its surrogates; noise does not.

PAC estimators return **nonzero values on pure noise**. The surrogate
null is not a refinement — without it the number means nothing.

## Gamma (C026) — `SOURCE_HYPOTHESIS`

40–160 Hz gamma correlates with conscious report. It is not thereby
consciousness.

- **Muscle artifact** contaminates the gamma band severely; EMG from
  the scalp looks like cortical gamma to an unwary analysis.
- **Volume conduction** creates apparent coherence between electrodes
  measuring the same source.
- **Stimulus locking** and **common input** synchronize without any
  coupling between the units.
- Gamma **dissociates from report** under anesthesia-graded designs.

40 / 40.96 / 41 / 42 Hz comparisons are registered so that the
*specific* number can be tested against its neighbours rather than
assumed special. **Correlation is not constitution**, and no
"universal consciousness scale" is claimed at 40 Hz or anywhere else.

## Mentorship (C045)

Borrowed structure becoming self-sustained is modelled as an
oscillator driven by a scaffold and then released — the same shape as
the ring attractor's persistence after input removal. It is a useful
formalization of a real social phenomenon and it is **not** evidence of
any field, transmission, or coupling beyond ordinary sensory contact.

## C048 — coherence is not truth (the control)

Two oscillator populations, both driven to r ≈ 1, encoding
**contradictory** states. Both are maximally coherent.

    coherence measures ORDER, not veridicality

This is implemented as an executable control (`coherence_is_not_truth`)
because it is the correction to the most seductive idea in the whole
lane: that a synchronized system is thereby a correct, conscious, or
enlightened one. A perfectly coherent population can be perfectly
wrong.

## Boundaries

- **Synchrony is not entanglement.**
- **Gamma is not a consciousness meter.**
- **Interpersonal coupling is not proof of aura** — see
  [AURA_TRANSLATION.md](AURA_TRANSLATION.md).
- No human data exists in this lane; every signal here is synthetic.
