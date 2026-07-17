# T07 — Quantum cognition and the physics boundary

Coverage: **C031–C033, C035**. Gate: **G37**. Lane: **quarantined**.
Implementation: `order_effect_model`, `qq_equality`,
`classical_comparator`.

## The boundary

> **Quantum-probability models of decisions are NOT evidence of quantum
> processes in neurons.**

Quantum *probability* is a mathematical framework: non-commuting
projectors, interference in probability amplitudes, contextuality. It
can be applied to survey responses by anyone with a laptop. Applying it
successfully says something about **the algebra of the questions**, not
about the physics of the tissue.

The brain is warm, wet, and macroscopic. Nothing in a good fit to
question-order data changes that.

## C032 — order effects (`REDUCED_ORDER_VALIDATED`)

A **classical** joint-probability model requires

    P(A then B) = P(B then A)

for the same conjunction. Measured order effects violate it.
Non-commuting projectors reproduce the asymmetry naturally.
`order_effect_model()` reports whether a classical model suffices, and
its return value carries the boundary text.

## The QQ equality — a real, parameter-free prediction

    (P(A then B) + P(notA then notB))
  − (P(B then A) + P(notB then notA)) = 0

`qq_equality()` implements it. This is the strongest thing in the whole
T-lane, and it is worth being precise about why: it has **no free
parameters**. It cannot be tuned to fit. It either holds in a dataset
or it does not, and it can fail (tested — `qq_equality(0.9, 0.1, 0.9,
0.1)` is not satisfied).

A parameter-free prediction that survives is evidence *for the
model class*. It is still not evidence of quantum neurons.

## The classical comparator is mandatory

`classical_comparator()` is the parsimony control: if a plain
conditional-probability chain fits the data, **no quantum-probability
model is warranted**. The exotic model must earn its place by beating
the ordinary one, and the ordinary one is implemented so the comparison
actually happens.

## C031 — multiverse / branch selection (`SOURCE_HYPOTHESIS`, SRC)

Outside current empirical reach. Retained without endorsement. No
experiment in this programme addresses it and none could.

## C035 — path-integral language

**Metaphor unless formalized.** The schema caps the `metaphor` layer at
`SOURCE_HYPOTHESIS`. Borrowing the *phrase* "sum over paths" for
decision-making is a figure of speech; borrowing the *mathematics*
would require an action, a measure, and a propagator, none of which the
sources supply.

## The escalation ladder

    metaphor -> mathematical model -> physical experiment

Each rung requires more than the last. C032 has reached rung two. **No
item in this lane has reached rung three**, and reaching rung two is
not a licence to speak as though it had.

## Boundaries

- **Do not call quantum cognition evidence of quantum neural
  processing** (G37).
- **Do not claim consciousness collapses the wavefunction.**
- Do not present multiverse branch selection as a controllable
  mechanism.
