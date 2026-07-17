# T01 — Resonant state change, subjective time, phase coherence

Coverage: **C001–C006, C012, C014, C034–C036, C040, C046, C047**.
Lane: **quarantined** — no record here is evidence in quartz
computation.
Implementation: `consciousness_lane.reduced_models`.

## The seed

The programme's original seed phrase concerns consciousness as a
*decaying resonance of state change*, and awareness of time as the
*current velocity* of that change. This document turns that into
mathematics with observables and failure conditions — and marks
honestly where it could not.

## C001 — decaying resonance (`REDUCED_ORDER_VALIDATED`)

    x'' + 2 zeta w x' + w^2 x = f(t)          tau = 1/(zeta w)

An abstract state coordinate `x` (dimensionless), t in seconds, ω in
Hz. `state_change_response()` integrates it and returns τ.

This is a damped harmonic oscillator. Calling the coordinate "state
change" does not make it a theory of consciousness — it makes it a
declared operationalization that can be fitted and can lose.

**Falsified if** no damped-oscillator fit to an operationalized
state-change series outperforms an AR(1) null.

## C002 — awareness as velocity (`REDUCED_ORDER_VALIDATED`)

The awareness proxy is |dx/dt|. **Falsified if** reported time-rate is
uncorrelated with |d(state)/dt| proxies across participants.

## C003 — subjective time (`REDUCED_ORDER_VALIDATED`)

    D_hat = sum_t (w_n * novelty_t + w_a * arousal_t) * dt

A linear accumulator — the standard reduced form of change/attentional-
gate models of duration. `subjective_time()` returns the perceived/clock
ratio. More novelty and arousal → longer perceived duration (tested).

**Falsified if** duration judgements are unaffected by novelty and
arousal manipulations under preregistered analysis.

## Downgraded by the v4.2.1 audit (`SOURCE_HYPOTHESIS`)

These were marked `REDUCED_ORDER_VALIDATED` in v4.2.0 **with no model
behind them**. The audit downgraded them and recorded why:

| ID | Claim | Why it is not validated |
|---|---|---|
| C006 | two/three linked temporal phases | no phase-count model; no comparison against a one-phase null |
| C034 | manifestation as affordance selection | no affordance-selection model implemented |
| C036 | active inference and affordances | no free-energy model, no reactive-policy null |
| C040 | the layer map | a documentation instrument, not a validated model |
| C046 | flow as subsystem coherence | no flow model, no coherence index |
| C047 | raising consciousness as coordination | no coordination index against a group outcome |

Each retains its falsification condition, so each is a real hypothesis
awaiting a model — not a deleted idea.

## C012 — the space-to-time operator (`SOURCE_HYPOTHESIS`)

No operator definition reproduces the claimed mapping with declared
units. Retained; not implemented.

## Metaphor boundary (C004, C005, C035)

Block-universe wavefronts, observer frames, 4th-dimension language, and
path-integral phrasing are **metaphors**. The schema caps the
`metaphor` layer at `SOURCE_HYPOTHESIS` — a metaphor cannot be promoted
by restating it precisely.

## Boundary

**Do not claim consciousness changes external time or selects physical
realities without evidence.** Nothing in this document does. Every
model here is mathematics about an abstract state variable, with no
human data of any kind in this lane.
