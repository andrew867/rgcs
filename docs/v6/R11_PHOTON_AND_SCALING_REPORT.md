# R11 Photon and Scaling Report

**Authority:** RGCS R11 / v6.0.0 (candidate)
**Scope:** the dynamical-boundary (Bogoliubov) result for `TRUNCATED_PHOTON_REFERENCE_A`, and the orbital-versus-atomic scaling nulls.
**Last verified commit:** v5.9.0 baseline (branch v590-r11)
**Prerequisites:** [R11_SPEC.md](R11_SPEC.md)
**Related code / tests:** `r11/dynboundary.py`, `r11/orbitalscaling.py`, `tests/v6/test_r11_dynboundary.py` (40 tests), `tests/v6/test_r11_orbitalscaling.py` (50 tests), `tests/v6/test_r11_redteam.py`
**Known limitations:** no apparatus has been built; all eight required observables are `UNMEASURED`. The scaling work uses published semi-major axes and body radii and does nothing to them but arithmetic. A formation-informed model is `BLOCKED_MISSING_DATA`.
**Next review trigger:** any bench measurement of a switched-boundary observable, or the arrival of formation-model data for the scaling comparison.

## Verdicts

- `r11.dynboundary.dynboundary_report()["verdict"]` →
  **`TRUNCATED_PHOTON_IS_MULTIMODE_EM_STATE_NOT_NEW_PARTICLE`**
- `r11.orbitalscaling.orbitalscaling_report()["verdict"]` →
  **`ORBITAL_ATOMIC_SCALING_UNESTABLISHED`**

## Part 1 — the dynamical boundary

### What the source picture claims, and what the field theory says

The source picture, carried under the neutral alias
`TRUNCATED_PHOTON_REFERENCE_A`, is a photon meeting a mirror that vanishes
mid-flight, so the photon is "cut" and the truncated piece is something new.

The module's actual result, under the candidate label
`DYNAMIC_BOUNDARY_MULTIMODE_STATE_CANDIDATE`, is that a boundary condition
changing in time applies a **Bogoliubov transformation**:

```
a_out = alpha * a_in + beta * conj(a_in_dagger),      |alpha|² - |beta|² == 1
```

That mixing is the whole story. There is no operator taking a one-photon state
to a state of 0.6 photons; the number operator still has integer eigenvalues.
What the transformation produces is a **multimode state** whose photon-number
sectors run from zero upward — with vacuum input, a multimode squeezed vacuum
with mean occupation `<n> = |beta|² = sinh(r)²` per mode, i.e. real photons
appearing in pairs. This is the dynamical Casimir effect, which has been
observed in superconducting-circuit analogues.

**This is not a broken photon, and it is not a new particle.** An
electromagnetic field state is not a new particle species.

### The divergence is an unphysical idealization

Instantaneous removal of a perfect boundary has no spectral cutoff, excites
arbitrarily high frequencies, and gives a divergent expected photon number.
Give the switching a finite time τ and the spectrum acquires a smooth cutoff.
The module's scaling is `<N> = coupling / (4 * tau**2)`, and its ladder:

| τ (s) | expected photons |
|---|---|
| 1e-06 | 2.5e+11 |
| 1e-05 | 2.5e+09 |
| 1e-04 | 2.5e+07 |
| 1e-03 | 2.5e+05 |

`instantaneous_limit: DIVERGENT`, `finite_switching_limit: FINITE`, verdict
**`INSTANTANEOUS_LIMIT_IS_UNPHYSICAL_IDEALIZATION`**. Slower switching means
fewer photons. `expected_photon_number(0.0)` raises rather than return a number
(red-team attack 14).

### Where the energy comes from

The created photons are **paid for by work done on the boundary** by whatever
switches it. `refuse_energy_from_nothing` and `refuse_infinite_free_energy` both
raise. The τ → 0 divergence is a statement about an impossible boundary, not a
supply of free energy.

### The five firewalls

1. a photon is not divided into a fractional photon;
2. static destructive interference redistributes energy and leaves no exotic
   remainder;
3. the instantaneous-switching divergence is an unphysical idealization, not
   usable infinite free energy;
4. created photons are paid for by work on the boundary;
5. an electromagnetic field state is not a new particle species.

### Eight competing mechanisms, all still live

`STATIC_MIRROR_OR_BEAMSPLITTER`, `ORDINARY_DESTRUCTIVE_INTERFERENCE`,
`PULSE_GATING`, `TIME_DEPENDENT_DIELECTRIC`, `DYNAMICAL_CASIMIR`,
`WAVEPACKET_TRUNCATION`, `CLASSICAL_SPECTRAL_BROADENING`, `DETECTOR_ARTIFACT`.
All eight produce "the light changed" and are not the same claim. Every
conventional one must be nulled before any exotic reading is on the table.

### Eight required observables, all UNMEASURED

photon-number distribution; squeezing correlations; sideband spectrum;
forward/backward correlations; switching energy input; transition-region energy
density; dependence on switching time; and nulls with static boundaries and
classical pulses. `any_measured` is **false**. `hardware_status` is
`DEFERRED — no apparatus has been built`.

### Accessibility, and why it proves nothing

The module states both halves and requires both (`both_statements_are_required:
true`). The dynamic-boundary lane *is* far more accessible than neutrino work —
optical and microwave frequencies, bench or dilution refrigerator, existing
photon counters and homodyne detection. But accessibility says nothing about
what the test will show. It makes the claim cheap to falsify, not more likely to
be true.

## Part 2 — orbital versus atomic scaling

### Why the analogy is not free

A hydrogenic radius scales as `n²/Z` because a Coulomb eigenvalue problem forces
it: discreteness is *compelled*, intermediate `n` do not exist, and the electron
has no track. A semi-major axis is a continuous constant of motion set by
accretion, migration, resonance capture and survival. Nothing quantises it.
There is no established universal mapping between them.

### The trap, and the test

Family, parameters, index offset, normalising length and which bodies count are
all free, so a handful of sorted radii fit *something* almost always. The only
quantity that can be evidence is a residual smaller than randomly drawn sorted
radii achieve under the **same** search.

Five families are compared — `hydrogenic`, `geometric`, `power_law`,
`titius_bode`, `resonance_chain` — against a `random_order_statistic` control.
A `formation_informed` model is declared `BLOCKED_MISSING_DATA`.

### The eight-planet result

In-sample rms log error: titius_bode **0.1741** (best), resonance_chain 0.1571
(the report names `titius_bode` as `solar_best_model` under its own selection
rule), geometric 0.2004, power_law 0.5468, hydrogenic 0.5544.

Against the random control (120 trials, endpoints pinned): null median
**0.3025**, null 10th percentile 0.1115, **p = 0.157**, `null_competitive:
true`. Verdict: **`NO_BETTER_THAN_CHANCE`**.

### Per system

| system | best model | rms log err | null median | p | verdict |
|---|---|---|---|---|---|
| solar_planets | titius_bode | 0.1741 | 0.3025 | 0.157 | `NO_BETTER_THAN_CHANCE` |
| jovian_galilean | resonance_chain | 0.00312 | 0.0359 | **0.0331** | **`TIGHTER_THAN_CHANCE`** |
| saturnian_major | resonance_chain | 0.0465 | 0.0940 | 0.248 | `NO_BETTER_THAN_CHANCE` |

**One system does beat its control**, and this document states it rather than
rounding it away. The reason is known and mundane: Io, Europa and Ganymede sit
in an established Laplace resonance — gravitational dynamics with a mechanism,
not shell structure. It is also the smallest set here (4 bodies).

### Look-elsewhere correction

5 models × 3 systems = **15 effective trials**. Raw p **0.0331** → Bonferroni
corrected p **0.4959** against corrected alpha 0.00333.
`significant_after_correction: **false**`. The module notes the correction is a
*lower bound* on the penalty owed, since normalisation choice, index offset and
which bodies count are further looks not even counted here.

### Out-of-sample transfer

Fit on solar_planets, evaluate on jovian_galilean, both normalised by their own
declared `PRIMARY_BODY_RADIUS` scale so the comparison is dimensionless on both
sides. Selected model titius_bode: in-sample **0.1741**, out-of-sample
**2.7452** — a **degradation factor of 15.77**. Every one of the five families
degrades comparably. Verdict: **`NO_UNIVERSAL_MAPPING`**.

The shape-only number (0.0669) comes out *below* the in-sample number, and the
module warns explicitly that this is not transfer succeeding — it is a reminder
that a four-point fit is easy, the same warning the random control gives.

### No universal exponent

Fitted exponents: solar **2.139**, jovian **1.034**, saturnian **1.271**,
spread **1.104**, `universal: false`. A hydrogenic mapping predicts p = 2
everywhere. The fitted exponents disagree with each other by more than they
disagree with 2, so there is no single exponent to call universal.

`refuse_per_target_normalization` and `refuse_shared_physics_from_fit` both
raise.

## Non-claims

No new particle. No broken or fractional photon. No free energy. No apparatus,
no photon counted, no squeezing or sideband observed. Planetary orbits are not
quantised, planets do not occupy shells, no principal quantum number applies to
celestial mechanics, and no fitted exponent is a law. No ship, no transmission,
no decoded location, no terraforming system.

PHYSICAL_VALIDATION_NOT_CLAIMED
