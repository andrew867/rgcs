# T06a — Dream-Wake Constraint Theory

Coverage: **C027, C041, C042, C030**. Lane: **quarantined**.
Implementation: `consciousness_lane.reduced_models.dream_wake_constraint`.

## The model

A constraint budget on a generative world-model:

    C = k_sensory + k_int + k_ext

| Term | Meaning |
|---|---|
| `k_sensory` | constraint from sensory input |
| `k_int` | internal/self-consistency constraint |
| `k_ext` | **quarantined** external-field constraint |

**Wake** is the high-`k_sensory` regime: the world model is
continuously corrected by sensory data and is therefore stable, shared,
and predictive.

**Dream** is the low-`k_sensory` regime: the same generative machinery
runs with the correction term removed, which is why dreams are
internally compelling and externally incoherent.

This is a reduced-order restatement of a mainstream view (dreaming as
generative modelling with reduced sensory precision). Its value here is
that it makes the dream/wake difference a **parameter** rather than a
mystery.

## K_ext is quarantined, and that is the whole point

`k_ext` is the external-consciousness-field term (C030/C042). The
module's default is `k_ext = 0` — the null.

    k_ext = 0     -> "the default null (no external field)"
    k_ext != 0    -> "a HYPOTHESIS under test, not an assumption;
                      falsified if fits return k_ext ~ 0"

The layer exists **so the hypothesis is testable and separable, not so
it is assumed**. A theory that bakes the external field into its
structure can never discover that it is zero. This one can, and the
expected outcome is that it is.

**Falsified if** `k_ext` is identically zero in every fit — which would
be a clean, publishable null (G48).

## C027 — dream vs wake permanence

**Falsified if** no measurable constraint difference exists between
dream and wake states under the declared operationalization. Testable
in principle via dream reports vs wake reports with matched
elicitation; no data exists in this lane.

## Distinguishing ordinary from field claims

The experiment matrix that would separate them:

| Observation | Ordinary explanation | Field claim needs |
|---|---|---|
| dream content matches an event | coincidence, memory reconstruction, post-hoc matching | preregistered content prediction |
| shared dream themes | shared culture, shared stimuli | isolation of participants |
| "sensed" presence | sensory leakage, expectation | shielded vs unshielded difference |

Shielded-versus-unshielded is the discriminating design, and it is the
one that has never been run here.

## Boundaries

- **Do not claim dreams prove an afterlife.**
- Do not treat a compelling subjective experience as an external
  measurement.
- `k_ext` may be *fitted*. It may not be *assumed*.
