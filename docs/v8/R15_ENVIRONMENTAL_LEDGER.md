# R15 P03 — Environmental Ledger

**Tranche:** T1 Instrument Authority · **Module:** `r15/environment.py` ·
**Tests:** `tests/v8/test_environment.py` · **Receipt:**
`docs/v8/receipts/P03.json`

**Verdict:** `R15_ENVIRONMENTAL_LEDGER_SYNTHETIC_NO_MEASUREMENT`
**Measured here:** nothing · **Physical validation:**
`PHYSICAL_VALIDATION_NOT_CLAIMED`

## What this is

Every measurement happens in a room, and the room moves. Temperature drifts,
the mains sags, a truck goes past and the bench rings, an unshielded supply
sprays RF across the band of interest. None of that is the specimen, and all
of it lands in the data. The **environmental ledger** is the record that lets
a later analysis tell the two apart: for every run it carries, per channel,
the ambient condition as a **time-series** with units, a one-sigma
uncertainty, and a content hash, aligned to the experiment clock.

Nothing here is measured. Every channel this module builds is a deterministic
`SYNTHETIC_OBSERVATION` produced from a seeded generator on a supplied clock.
No sensor is operated, and the `REAL`-mode ledger is `BLOCKED_MISSING_INPUT`.

## The nine nuisance channels

| Channel | Units | | Channel | Units |
|---|---|---|---|---|
| temperature | K | | line voltage (mains) | V |
| humidity | %RH | | EMI/RF background | V/m |
| pressure | Pa | | magnetic field | T |
| vibration | m/s² | | operator action | event |
| acoustic background | Pa | | | |

Each is an `EnvChannel`: a kind, a source, a timestamp vector (**passed in**,
never read from the wall clock), a value vector, its units, a one-sigma
uncertainty, and a SHA-256 content hash so a trace cannot be silently edited
(`verify_hash()` recomputes and compares).

## Four modes, kept distinct

- `REAL` — live sensor acquisition. **Blocked here** (`real_mode_status()`
  returns `BLOCKED_MISSING_INPUT`): no sensor was operated.
- `REPLAY` — a recorded trace re-played.
- `SYNTHETIC` — a deterministic simulator (the only mode this repo produces).
- `FAULT_INJECTION` — a deliberately corrupted trace, for exercising guards.

## Four sources, ranked by authority

A live `SENSOR` trace (rank 3) outranks a `REPLAY` (2), which outranks a
`SYNTHETIC` trace (1), which outranks a `MANUAL` declaration (0). A manual note
("the lab was about 21 °C") is a `SOURCE_CLAIM`, not a measurement;
`EnvironmentLedger.authoritative(kind)` returns the highest-authority channel
for a kind, and `refuse_manual_as_sensor()` refuses to let a hand-entered note
stand in for a sensor trace.

## Clock alignment

- `clock_offset_seconds(channel, expected_t0)` — signed offset of a trace's
  origin from the experiment clock.
- `is_clock_aligned(channel, expected_t0, tol_s)` — within tolerance?
- `trace_lag_samples(reference, channel)` — reuses
  `r13.daq.cross_correlation_lag` to recover the relative lag between two
  traces; a nonzero lag on traces that should share the clock is a detected
  misalignment.
- `realign_to_clock(channel, expected_t0)` — returns a copy shifted onto the
  experiment clock and rehashed, so the correction is explicit, not silent.

## Missing-data policy by protocol

A protocol declares its `required_kinds` (default: the seven core measurement
nuisances). `check_completeness(ledger, policy)` applies one of three
policies:

- `INVALIDATE` — a missing required channel voids the run; evidence drops to
  `E0`.
- `DEGRADE` — the run proceeds but evidence is capped to `E1`.
- `ALLOW_MANUAL` — a manual declaration for a missing kind counts as a
  substitution (at its lower authority); a kind with neither trace nor note
  still invalidates.

A complete synthetic ledger tops out at `E2` (a deterministic synthetic
observation) — **never a physical measurement**, because no calibration,
specimen, or raw artifact exists (`r15.claims.evidence_cap`).

## Drift and nuisance-correlation diagnostics

- `drift_rate(channel)` — least-squares linear drift in units per second. An
  injected drift appears in the output (a `+0.5 K/s` ramp reads back as
  `0.5 K/s`).
- `nuisance_correlation(channel, signal)` — Pearson correlation between an env
  channel and a candidate signal. A feature that tracks a nuisance channel is
  a nuisance suspect, not an intrinsic effect.

## The error budget

`build_error_budget(budget_id, quantity, components, coverage_factor=2.0)`
assembles an error budget conforming to `r15/schemas/error_budget.schema.json`.
Every quantitative result decomposes uncertainty into **eleven components**:

instrument resolution · calibration · clock · environment · fixture
repeatability · specimen geometry · orientation · numerical method · DSP ·
operator · model residual

The components combine in **quadrature** (`combine_quadrature`, root-sum-
square), and the environmental channels feed the `environment` component via
`environment_component(ledger)`. The budget is a `MODEL_PREDICTION`: no
coupling coefficient here was measured.

### A residual below the combined uncertainty is not anomalous

- `is_within_budget(residual, combined_sigma)` — `True` when
  `|residual| ≤ combined_sigma`. The residual is consistent with the eleven
  known error sources; it is **not** a signal.
- `refuse_subbudget_as_anomaly(residual, combined_sigma)` — **always raises.**
  Calling a within-budget residual an anomaly is a promotion this guard
  blocks. (This is the P03 face of `r15.claims.refuse_noise_as_resonance`.)

## Load-bearing refusals

| Name | Refuses |
|---|---|
| `refuse_subbudget_as_anomaly` | a within-budget residual being called an anomaly |
| `refuse_manual_as_sensor` | a manual declaration standing in for a sensor trace |
| `refuse_synthetic_env_as_measured` | synthetic channels being called measurements |

Indexed for the red team in `FORBIDDEN_PROMOTIONS`.

## Negative results

- Synthetic environmental channels are **not** measurements; the `REAL`-mode
  ledger is `BLOCKED_MISSING_INPUT`. No ambient condition was measured.
- A residual within the combined quadrature uncertainty is **not** anomalous
  and does not advance any physical claim.
- A manual declaration cannot acquire sensor authority.
- A run missing a required environmental channel is invalidated (or degraded),
  and its evidence never reaches `E4` (physical measurement).

## Determinism

All synthetic channels are deterministic under a seed: the same `seed` and the
same passed-in timestamp vector reproduce the trace byte-for-byte and
therefore the same hash (`synthetic_channel`, `synthetic_ledger`). Timestamps
are always supplied by the caller; the module never reads the wall clock.

## Reuse (no duplicate truth systems)

- `r15.claims` — claim taxonomy, evidence ladder, and `evidence_cap`.
- `r13.daq.cross_correlation_lag` — trace-to-trace lag for misalignment.

No sibling R15 phase module is imported.

## Reopening test

Re-run `pytest tests/v8/test_environment.py`. The phase reopens if any of the
following becomes true: a synthetic channel stops being deterministic under
its seed; a within-budget residual is reported as anomalous; a manual
declaration gains authority over a sensor trace; a missing required channel no
longer invalidates the run; the error budget stops combining in quadrature or
drifts out of conformance with `error_budget.schema.json`; or any channel
claims a class stronger than `SYNTHETIC_OBSERVATION` without real artifacts.
