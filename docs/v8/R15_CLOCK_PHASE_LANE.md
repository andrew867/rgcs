# R15 Clock and Phase Measurement Lane (P18)

**Phase:** P18 — Clock and Phase Measurement Lane (Tranche T5, Cross-Domain Measurement)
**Module:** `r15/clock_phase.py`
**Tests:** `tests/v8/test_clock_phase.py`
**Reuses:** `r13.daq` (sampling, jitter→SNR, cross-correlation skew), `r13.quadfield` (I/Q phase demodulation), `r15.claims` (taxonomy and refusals)
**Status:** COMPLETE — software/simulation only. Physical clock run **PREREGISTERED_NOT_RUN**.

## What this is

The clock and phase lane characterises the timebase every cross-domain
experiment is measured against, and measures a tone's phase, frequency and
multi-channel synchronization — entirely from a deterministic synthetic
clock. It operates no oscillator, counter, GPSDO or phase comparator, and
acquires nothing. `measured_here = "nothing"` and
`PHYSICAL_VALIDATION_NOT_CLAIMED`.

The strongest class any reading here reaches is a `SYNTHETIC_OBSERVATION`.

## One interface, four honest modes

| Mode | Behaviour | Claim |
| --- | --- | --- |
| `REAL_DEVICE` | Interface only. No timebase hardware exists, so it acquires **nothing**: `RealClockDevice.acquire` raises `NoClockHardwareError`; `blocked_receipt()` records `PREREGISTERED_NOT_RUN`. | `BLOCKED_MISSING_INPUT` |
| `SYNTHETIC_DEVICE` | Deterministic synthetic clock (jittered, drifting tone + matching time-error series) under a numpy seed. Same seed → byte-identical output. This is the mode with power. | `SYNTHETIC_OBSERVATION` |
| `REPLAY_DEVICE` | Replays a previously recorded synthetic acquisition byte-for-byte; measures nothing new. | `SYNTHETIC_OBSERVATION` |
| `FAULT_INJECTION_DEVICE` | Injects the five ordinary DAQ faults **and** three clock-specific faults, deterministically. | `SYNTHETIC_OBSERVATION` |

The four modes are distinct and never interchangeable — that separation is
the honesty of the lane.

## What it measures (the power path)

From a `SyntheticClockSpec` and a seed, `synthesize()` produces a
`ClockAcquisition` carrying the tone waveform, the clock time-error series
`x(t)`, and the nominal edges. Planted quantities are then recovered:

| Quantity | Function | Method | Recovered |
| --- | --- | --- | --- |
| Tone phase φ | `recover_phase` | R13 I/Q demodulation (`a = I + iQ`, `arg(a) = φ`) | to ~1e-6 rad |
| Channel skew | `recover_skews` | R13 cross-correlation lag | exact for integer skew |
| Frequency drift D | `estimate_drift` | quadratic fit of `x(t)`, `D = 2·c₂` | to ~1% |
| Frequency offset f₀ | `estimate_frequency_offset` | linear term of `x(t)` | to ~1% |
| Timebase jitter | `estimate_jitter` | detrended residual std of `x(t)` | to ~10% |
| Stability | `allan_deviation` | overlapping ADEV from the phase (time-error) series | — |

Overlapping Allan deviation from time-error samples `x`:

    σ_y²(τ) = 1/(2 τ² (N−2m)) · Σ (x[i+2m] − 2 x[i+m] + x[i])²,   τ = m·τ₀.

## Synthesis error, transport delay, latency, residual phase

The lane separates the timing error into named components and combines them
in quadrature (RSS). `timing_error_budget` conforms to
`error_budget.schema.json` and tags each component with an
`R15_ERROR_BUDGET_POLICY` category (clock, instrument resolution,
environment, DSP, model residual). The four required separations —
`synthesis_error`, `transport_delay`, `latency`, `residual_phase` — are
carried explicitly under `separated`, alongside `clock_jitter`,
`reference_instability`, `frequency_drift`, `quantization`, `sync_skew` and
`demod_residual`. The combined 1σ uncertainty is expanded by a coverage
factor (k = 2 by default).

## Common-clock closure vs independent oscillators

`common_clock_closure` builds channels disciplined by **one** reference —
identical fractional frequency and drift, independent readout jitter — so
their per-channel frequencies coincide and the closure residual sits at the
jitter-noise level. `independent_oscillator_closure` gives each channel a
**distinct** fractional frequency offset, so the residual is larger by orders
of magnitude. A shared timebase closes; independent ones do not. This is the
`R15` "common-clock closure differs from independent oscillators" property.

## Negative results and refusals

- **A REAL clock acquires nothing.** No timebase hardware exists;
  `NoClockHardwareError` is raised and the physical run is
  `PREREGISTERED_NOT_RUN`.
- **Jitter is not a signal.** Clock jitter raises a tone's noise floor
  (`jitter_noise_floor`, via `r13.daq.jitter_snr`) — a `KNOWN_ORDINARY_EFFECT`.
  `refuse_jitter_as_signal` refuses reading the raised broadband floor as a
  tone or resonance (delegating to `claims.refuse_noise_as_resonance`).
- **Unknown latency stays uncertain.** Without a reference delay,
  `transport_latency` returns an **interval** with `resolved = False`: the
  absolute latency carries a cycle ambiguity.
- **Eight fault modes** — `clipping`, `drift`, `saturation`, `packet_loss`,
  `missing_samples`, `cycle_slip`, `glitch`, `holdover` — each demonstrably
  alter the clean reading and are deterministic under the seed.
- **No promotion.** A `ClockAcquisition` cannot carry a measurement class
  (`refuse_synthetic_as_physical`); `refuse_synthetic_clock_as_measured`
  refuses calling the synthetic clock measured.
- **No relativity without sensitivity.** `refuse_relativistic_interpretation`
  refuses reading a synthetic fractional frequency offset as gravitational or
  special-relativistic time dilation — the sensitivity to do so does not
  exist here.

## What this does not say

It does not say any clock was measured. Every edge, tone, jitter, drift and
skew is produced by evaluating a declared clock model under a seed; every
reading is a `SYNTHETIC_OBSERVATION` and a `REAL_DEVICE` acquires nothing. A
jitter-raised noise floor is a known ordinary effect, not a signal; an
unknown transport latency stays uncertain; and a synthetic frequency offset
is never relativistic time dilation. **Verdict:**
`CLOCK_PHASE_LANE_SYNTHETIC_NO_TIMEBASE_HARDWARE`.
