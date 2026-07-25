# R15 P16 — Thermal Measurement Lane

**Tranche:** T5 Cross-Domain Measurement · **Module:** `r15/thermal.py` ·
**Tests:** `tests/v8/test_thermal.py` · **Receipt:** `docs/v8/receipts/P16.json`

**Verdict:** `R15_THERMAL_LANE_SYNTHETIC_NO_MEASUREMENT` ·
`measured_here = "nothing"` · `PHYSICAL_VALIDATION_NOT_CLAIMED`

## What this lane is

Temperature is the quietest way an experiment lies to itself: a resonator's
frequency drifts a few parts per million per kelvin, a delay line's phase
walks as its path expands, and a thermometer warms itself with its own bias
current and reads high. None of that is the specimen, and all of it looks
like a slow, clean signal. The thermal lane reads temperature honestly and
then uses it to **explain away** the frequency and phase drift it causes —
the opposite of discovering something.

Nothing here is measured. Every temperature is a deterministic
`SYNTHETIC_OBSERVATION` from `numpy.random.default_rng(seed)` on a supplied
clock; a hand-entered note is a `SOURCE_CLAIM`; and a temperature-induced
frequency or phase shift is a `KNOWN_ORDINARY_EFFECT`. The strongest class the
lane reaches is a synthetic observation, and a synthetic observation is not a
`PHYSICAL_MEASUREMENT`.

## Inputs and transducer models

Five inputs, three electrical conversion models (readout → kelvin). Each
conversion constant is a `CONVENTIONAL_LITERATURE` figure for a *class* of
sensor, not a calibration of any device.

| Input | Model | Function |
|---|---|---|
| Thermistor | Beta/Steinhart: `1/T = 1/T0 + ln(R/R0)/B` | `thermistor_temperature` |
| RTD | Linear Callendar: `R = R0(1 + α(T−T0))` | `rtd_temperature` |
| Thermocouple | Linear Seebeck: `V = S(T−T_ref)` (cold-junction compensated) | `thermocouple_temperature` |
| IR | Replay of a recorded trace | `ReplayThermalDevice` |
| Manual | A declared note — `SOURCE_CLAIM`, not a reading | `refuse_manual_as_sensor` |
| Synthetic | Deterministic simulator under a seed | `SyntheticThermalDevice` |

## Sensors bound to a place and a lag

A `ThermalSensor` carries a **location** and a first-order **response time**
`τ`: a sensor is not a point probe of the specimen, it is a low-pass filter
watching the ambient from somewhere nearby.

- `apply_sensor_response(ambient, dt, τ)` models the first-order lag.
- `estimate_sensor_lag_samples(ambient, sensor)` recovers it by
  cross-correlation, reusing `r13.daq.cross_correlation_lag`. A pure integer
  delay is recovered exactly; a first-order lag grows monotonically with `τ`.

## Two artifacts corrected, not measured

- **Self-heating.** A sensor dissipates its own bias power and warms itself,
  `ΔT = R_θ · P` (`ThermalSensor.self_heating_offset_K`). `correct_self_heating`
  removes it. Self-heating is a property of the *sensor*, never the specimen's
  output — `refuse_self_heating_as_specimen` refuses that confusion.
- **Ambient drift.** `fit_ambient_drift` recovers a slow linear ramp (K/s);
  `correct_ambient_drift` detrends it.

## Thermal explanation of frequency and phase

A mode's frequency drifts with temperature through the **thermal coefficient
of frequency (TCf)**. The underlying mechanism — the crystal expanding — is
read from `r13.crystalframe`: the alpha-quartz lattice constants expand by
their `CONVENTIONAL_LITERATURE` coefficients
(`QUARTZ_ALPHA_A_PER_K = 13.2e-6`, `QUARTZ_ALPHA_C_PER_K = 7.1e-6`), so a
governing dimension grows and a thickness-governed mode's frequency falls
(`df/f = −α·ΔT`, via `expansion_frequency_coefficient`).

- `frequency_from_temperature(T; f0, T_ref, a1, a2)` — the forward TCf model.
- `fit_thermal_coefficient(T, f; f0, T_ref)` — recovers a **planted** `a1`
  (and quadratic `a2`) from a `(T, f)` record. This is the lane's **power
  check**: a known thermal drift is reproduced and recovered.
- `thermal_phase_shift(φ0, ΔT; α)` — turns a fractional thermal expansion into
  a phase walk `dφ = φ0·α·ΔT`.

A temperature-induced shift is a `KNOWN_ORDINARY_EFFECT`.
`refuse_thermal_drift_as_signal` refuses to read it as a discovery and — via
`r11.detectors` — names it as the thermal-expansion artifact a transducer
produces when read outside its domain (`thermal_coupling_is_an_artifact`: a
thermometer does not couple to the specimen's mechanical/strain mode).

## Four device modes, kept distinct

| Mode | Behaviour | Claim |
|---|---|---|
| `REAL_DEVICE` | Acquires nothing; raises `NoThermalHardwareError` | `PREREGISTERED_NOT_RUN` |
| `SYNTHETIC_DEVICE` | Deterministic `T(t)` (+ co-drifting `f(t)`) under a seed | `SYNTHETIC_OBSERVATION` |
| `REPLAY_DEVICE` | Replays a recorded trace byte-for-byte | `SYNTHETIC_OBSERVATION` |
| `FAULT_INJECTION_DEVICE` | Injects clipping, drift, saturation, packet loss, missing samples, **self-heating** | `SYNTHETIC_OBSERVATION` |

The physical run is fully specified but **not run**: no thermistor, RTD,
thermocouple, IR camera, oven or reference bath was operated.

## Thermal error budget

`ThermalBudgetComponent` decomposes a thermal result into sensor resolution,
calibration, self-heating, ambient drift, sensor lag, thermal gradient,
radiation, lead resistance, reference junction, numerical method, and model
residual. `build_thermal_error_budget` combines the one-sigma lines in
quadrature (`quadrature_sum_rss`) and conforms to `error_budget.schema.json`.
The budget is a `MODEL_PREDICTION`; a residual within combined uncertainty is
not anomalous (`is_within_budget`).

## Refusals (the forbidden promotions)

| Name | Refuses |
|---|---|
| `thermal_drift_to_signal` | A temperature-driven frequency/phase shift read as a signal |
| `self_heating_to_specimen` | Sensor self-heating read as the specimen's output |
| `synthetic_thermal_to_measured` | Synthetic thermal data read as a measurement |
| `manual_to_sensor` | A manual note read as a transduced sensor trace |

## Reuse (no duplicate truth systems)

- `r15.claims` — claim taxonomy, evidence ladder, and the load-bearing
  `refuse_synthetic_as_physical` wired into `ThermalAcquisition`.
- `r13.daq.cross_correlation_lag` — sensor-lag estimation.
- `r13.crystalframe` — alpha-quartz lattice frame; thermal expansion drives
  the frequency/phase explanation.
- `r11.detectors` — the thermal-expansion artifact principle behind
  `refuse_thermal_drift_as_signal`.

No sibling R15 phase module is imported.

## What this lane does not say

It does not measure any temperature. Every reading is a deterministic
synthetic observation; the REAL-mode read is `PREREGISTERED_NOT_RUN`; a
temperature-induced frequency or phase shift is a `KNOWN_ORDINARY_EFFECT`, not
a signal; and sensor self-heating is a sensor artifact, never the specimen's
output. `PHYSICAL_VALIDATION_NOT_CLAIMED`.
