# R15 P11 — Ordinary Explanation Engine

**Tranche:** T4 Evidence Engine · **Module:** `r15/ordinary_explanations.py` ·
**Verdict:** `ORDINARY_EXPLANATION_FIREWALL_IMPLEMENTED`

**Measured here: nothing. `PHYSICAL_VALIDATION_NOT_CLAIMED`.**

## What this is

The ordinary-explanation firewall, as code. Before any apparent anomaly may
be called an `UNEXPLAINED_INSTRUMENT_RESIDUAL`, it has to survive a battery
of eleven *ordinary-explanation attacks*. Each attack is a detector for one
mundane mechanism that routinely masquerades as a discovery. A residual
with **any** ordinary explanation is not unexplained; a residual below the
combined uncertainty budget is not anomalous at all; and a residual that
survives every attack reaches only the `UNEXPLAINED_INSTRUMENT_RESIDUAL`
ceiling — never new physics.

## The eleven attacks

Each attack is a pure function `(signal, context) -> AttackResult`. An
attack that lacks the context it needs is *not applicable* and does not
fire, but is still recorded, so no failed attempt is discarded.

| Attack | Detects | Fires when | Ordinary claim class |
|---|---|---|---|
| `raw_data_defect` | NaN/inf, zero-filled dropout | non-finite samples or a long constant run | `KNOWN_ORDINARY_EFFECT` |
| `clock_error` | timebase jitter | sample instants wander off the ideal grid beyond a fraction of a sample period | `KNOWN_ORDINARY_EFFECT` |
| `calibration_drift` | slow gain trend | end/start RMS gain change exceeds tolerance | `CALIBRATION_ERROR` |
| `clipping` | flat-topping on a rail | a fraction of samples pile up exactly on the peak/trough | `KNOWN_ORDINARY_EFFECT` |
| `aliasing` | out-of-band fold | an above-Nyquist source lands at the observed tone (`r13.daq.alias_frequency`) | `KNOWN_ORDINARY_EFFECT` |
| `spectral_leakage` | off-bin smearing | boxcar sidelobes are high and collapse under a Hann window | `KNOWN_ORDINARY_EFFECT` |
| `environmental_coupling` | tracks an environment monitor | \|Pearson r\| with the environment channel exceeds threshold | `KNOWN_ORDINARY_EFFECT` |
| `fixture_effect` | present in a blank fixture | \|Pearson r\| with the no-specimen record exceeds threshold | `FIXTURE_EFFECT` |
| `cross_talk` | neighbouring-channel leak | \|Pearson r\| with the aggressor channel exceeds threshold | `KNOWN_ORDINARY_EFFECT` |
| `specimen_mismatch` | wrong specimen mounted | dominant feature falls outside the declared specimen band | `KNOWN_ORDINARY_EFFECT` |
| `model_inadequacy` | too-simple model | an augmented model (polynomial baseline + missing harmonics) captures the residual variance | `MODEL_ERROR` |

The aliasing and specimen attacks read frequencies back through the
existing R13 DAQ authority (`r13.daq.alias_frequency`,
`dominant_frequency`); the engine does not fork a second copy of that
truth.

## The firewall verdict

`classify_residual(signal, context)` decides, in order:

1. **Within budget → not anomalous.** If the residual's peak amplitude is
   within the combined-uncertainty coverage (`k·u`), it is
   `NOISE_WITHIN_UNCERTAINTY`. The attacks are still recorded.
2. **Any attack fires → explained.** If any ordinary-explanation attack
   fires, it is `ORDINARY_EXPLANATION_FOUND` — not unexplained. The verdict
   is a **union**: no attack has exclusive authority.
3. **Survives everything, above budget → the ceiling.** Only then is it an
   `UNEXPLAINED_INSTRUMENT_RESIDUAL`, and it is never promoted past that.
   `refuse_residual_before_attacks` refuses the label before the battery
   has run; `refuse_residual_as_new_physics` refuses to read the ceiling as
   a discovery.

The result serialises to a record conforming to
`r15/schemas/residual_record.schema.json` via `as_record()`, carrying every
attack attempt (firing, non-firing, and inapplicable), the combined
uncertainty budget, the classification, and a reopening test.

## The firewall is not vacuous

The load-bearing power test is symmetric:

* **Planted artifacts are caught.** An injected NaN, a jittered timebase, a
  gain ramp, a clipped rail, a 3700 Hz tone aliased to 396 Hz at
  `fs = 4096`, an off-bin 640.5-cycle tone, an environment-coupled signal,
  a cross-talk leak, a blank-fixture signature, a wrong-band feature, and a
  missing model harmonic are each caught by their own attack.
* **A clean residual passes everything.** A deterministic, on-bin,
  stationary, uncoupled tone above the uncertainty budget — offered the
  *full* context so every attack is applicable — fires **zero** attacks and
  reaches the `UNEXPLAINED_INSTRUMENT_RESIDUAL` ceiling. If the firewall
  flagged everything, it would prove nothing.

## Negative results and refusals

- A residual within the uncertainty budget is classified
  `NOISE_WITHIN_UNCERTAINTY`, never anomalous.
- Inapplicable attacks are recorded (marked `applicable: false`), not
  dropped — failed explanations are preserved.
- `refuse_residual_before_attacks([])` / `(None)` raises
  `OrdinaryExplanationError`.
- `refuse_residual_as_new_physics()` raises `ClaimError` (via the R15
  governance core).
- An empty or too-short signal is refused.

## What this does not say

It measures nothing and detects no new physics. Every fixture is a seeded
synthetic waveform. The strongest class the module reaches is
`SOFTWARE_IMPLEMENTED`; the strongest label any residual reaches is
`UNEXPLAINED_INSTRUMENT_RESIDUAL`, the ceiling for an unreplicated residual
that survived the ordinary-explanation attacks — not a resonance, not a
particle, not a new energy. `PHYSICAL_VALIDATION_NOT_CLAIMED`.

## Tests

`tests/v8/test_ordinary_explanations.py` — 24 tests: power (each planted
artifact caught; clean residual survives all), coexisting faults, no
exclusive authority, preserved failed/inapplicable explanations, the
within-budget negative, both refusals, the empty-signal guard, determinism,
and schema conformance.
