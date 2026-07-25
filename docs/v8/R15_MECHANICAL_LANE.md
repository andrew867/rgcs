# R15 P13 — Mechanical Measurement Lane

The mechanical measurement lane acquires mechanical modal data — an
accelerometer record, a microphone (acoustic proxy) record, or a ring-down
decay — and fits the modal frequencies, the quality factor `Q`, and the
damping ratio `zeta = 1/(2Q)`. It lives in one module:

- `r15/mechanical.py` — the four-mode lane interface, the deterministic
  planted-mode synthesizer, the ring-down and modal-frequency fits, the
  fixture/specimen separation, FRF and coherence, the full error budget, and
  the load-bearing refusals.

Nothing here is measured. The strongest class any fit reaches is
`SYNTHETIC_OBSERVATION` (a fit to synthetic data); a predicted modal
frequency is a `MODEL_PREDICTION`; a `REAL_DEVICE` acquires nothing. The
module imports `r15.claims` and is capped at the software ceiling
(`MODEL_PREDICTION`), with `measured_here = "nothing"` and
`physical_validation = "PHYSICAL_VALIDATION_NOT_CLAIMED"`. The physical
mechanical run is `PREREGISTERED_NOT_RUN`: the software lane is complete but
no specimen has been mounted on a calibrated fixture.

## Reuse, not duplication

The lane reuses existing R10–R13 and R11 authorities rather than building
new truth systems:

| authority | reused for |
| --- | --- |
| `r15.instruments` | the four acquisition modes, `Acquisition`, `FaultMode`, `NoHardwareError` |
| `r15.synthetic_instruments` | the `SyntheticDriver` base the planted-mode driver extends |
| `r13.qcmstack.ringdown_Q` | the ring-down `Q`/`tau` fit (envelope log-fit + spectral peak) |
| `r13.qcmstack.refuse_model_Q_as_device_Q` | the synthetic-`Q`-is-not-a-device-`Q` refusal |
| `r13.homogenize.sound_speed_from_chain` | the elastic sound speed for a modal-frequency **prediction** |
| `r11.detectors.bandwidth_ok` | the piezoelectric transducer band check |

No sibling R15 phase module is imported.

## The channels

`MechanicalChannel` maps a channel to the capability it acquires:

| channel | capability | what it is |
| --- | --- | --- |
| `ACCELEROMETER` | `acceleration` | a contact transducer record |
| `MICROPHONE` | `acoustic` | an acoustic-proxy record |
| `RINGDOWN` | `acceleration` | the free decay after the drive is cut |

## One interface, four distinct modes

Every mode sits behind the same `MechanicalLane.acquire(...)` interface, but
the four are not interchangeable.

- **`REAL_DEVICE`** (`build_real_lane`) — interface only. No accelerometer,
  microphone, shaker or vibrometer exists in this repository, so a real
  mechanical read acquires *nothing*: `acquire` raises `NoHardwareError`, and
  `blocked_receipt()` returns the honest `BLOCKED` state
  (`acquired: false`, `n_samples: 0`,
  `physical_acquisition_status: PREREGISTERED_NOT_RUN`).
- **`SYNTHETIC_DEVICE`** (`build_synthetic_lane`) — a `ModalDriver` plants
  modes `A exp(-t/tau) sin(2 pi f t + phi)` and adds seeded noise under a
  numpy seed. Same seed → identical samples; different seed → different
  samples. The reading is a `SYNTHETIC_OBSERVATION`, and the fit recovers the
  planted mode.
- **`REPLAY_DEVICE`** (`build_replay_lane`) — replays a previously recorded
  (synthetic) mechanical artifact byte-for-byte. It measures nothing new.
- **`FAULT_INJECTION_DEVICE`** (`build_fault_lane`) — wraps a synthetic
  device and injects the five instrument pathologies (clipping, drift,
  saturation, packet loss, missing samples), deterministically under the
  acquisition seed, so the fit and its diagnostics can be exercised against
  known faults.

## The fits

- **`fit_ringdown(samples, fs)`** recovers `f`, `Q`, and `zeta = 1/(2Q)` from
  a decaying record by reusing `r13.qcmstack.ringdown_Q` (a log-linear
  envelope fit for `tau` and the dominant spectral peak for `w`, so
  `Q = w tau / 2` is recovered from the data). This is the POWER path: a
  planted mode is recovered within the error budget.
- **`fit_modal_frequencies(samples, fs, n_modes=...)`** identifies modal
  peaks in the windowed magnitude spectrum. Each peak's frequency is refined
  by a 3-point parabola and its `Q` by the half-power (-3 dB) bandwidth.
  Window side-lobes within `min_separation_hz` of an accepted peak are
  merged, and a peak whose prominence (peak magnitude over the spectral
  median) does not clear `MODE_PROMINENCE_MIN` is **not returned** — a
  feature within noise is not a mode.

## Mode identification: drive, fixture, specimen

`separate_fixture_specimen(modes, fixture_band)` attributes any mode falling
in the known fixture resonance band to the **fixture**, not the specimen.
Fixture motion is never assigned to specimen motion.

## Fault diagnostics

- **Aliasing** — `synthesize_modal_record` and `ModalDriver.generate` refuse
  a planted mode at or above the Nyquist frequency *before any sample is
  produced*; a folded artifact is never returned as a mode.
  `aliasing_risk(f, fs)` flags an under-sampled frequency.
- **Clipping / saturation** — `clipping_fraction(samples)` reports the
  fraction of samples pinned on the rail (NaN-aware), and `is_clipped`
  flags a suspicious fraction. A clean decaying record touches its peak only
  briefly; a clipped or saturated record pins many samples.
- **Missing samples** — a record carrying NaN (a fault-injection
  missing-samples reading) is refused for fitting; a gapped record is not
  silently fitted.

## The error budget

`MechanicalErrorBudget` carries the full component set required by the error
budget policy, as relative fractions combined in quadrature:

`instrument_resolution`, `calibration`, `clock`, `environment`,
`fixture_repeatability`, `specimen_geometry`, `dsp_window_leakage`,
`numerical`, `model_residual`.

`combined_relative` is the root-sum-square; `expanded_relative` applies the
coverage factor; `within_budget(true, est)` tests agreement inside the
expanded uncertainty. `to_error_budget_record()` conforms to
`r15/schemas/error_budget.schema.json`. A residual below the combined
uncertainty is not a mode.

## Placeholders

Per the phase's required work, the lane also carries `frf` and `coherence`
(single-input H1 estimator and ordinary coherence over synthetic signals),
`to_velocity`/`to_displacement` (spectral integration with a high-pass to
suppress integration drift), a `ModeShapeField` placeholder
(`mode_shape_placeholder`), and `predicted_rod_mode_hz` (a modal frequency
predicted from an elastic sound speed — a `MODEL_PREDICTION`).

## The refusal paths

- `MechanicalLane` over a `REAL_DEVICE` raises `NoHardwareError` — it
  acquires nothing.
- A mode at/above Nyquist is refused (aliasing) before any sample.
- A record with missing samples (NaN) is refused for fitting.
- `assert_mode_above_noise` calls `claims.refuse_noise_as_resonance` for a
  within-noise feature.
- `FittedMode` refuses to be constructed in any measurement class (it calls
  `claims.refuse_synthetic_as_physical`).
- `refuse_fit_as_measurement` — a synthetic modal fit is not a measurement.
- `refuse_synthetic_Q_as_device_Q` — delegates to
  `r13.qcmstack.refuse_model_Q_as_device_Q`.
- `refuse_prediction_as_measurement` — a `MODEL_PREDICTION` is not a
  measurement.

## Tests

`tests/v8/test_mechanical.py` (42 tests) covers: the planted mode recovered
within budget on the ring-down fit and via the synthetic lane;
`zeta = 1/(2Q)`; two-mode identification and fixture/specimen separation;
aliasing refusal and `aliasing_risk`; clipping/saturation detection and a
clean reading not flagged; the `REAL_DEVICE` lane acquiring nothing and its
`PREREGISTERED_NOT_RUN` blocked receipt; every fault mode altering the
reading, missing-samples refusing a fit, packet-loss zero-filling; a fit
within noise not being a mode; replay; the four modes staying distinct;
determinism (same seed identical, different seed differs, deterministic fault
injection); no promotion to a measurement class and every refusal; the model
prediction being a `MODEL_PREDICTION`; FRF/coherence/integration
placeholders; and schema conformance of the error budget, observation and
phase-receipt records.

## What this does not say

It does not say any specimen was measured. `fit_ringdown` and
`fit_modal_frequencies` recover modes **planted** in a synthetic record;
there is no accelerometer, microphone, shaker or vibrometer in this
repository. A fitted `f`, `Q` or `zeta` is a `SYNTHETIC_OBSERVATION`, and a
predicted modal frequency is a `MODEL_PREDICTION`; neither is a
`PHYSICAL_MEASUREMENT`. The physical acquisition is `PREREGISTERED_NOT_RUN`.
`PHYSICAL_VALIDATION_NOT_CLAIMED`.
