# R15 P01 — Instrument Registry

The instrument registry is the authoritative inventory of every instrument
the R15 platform could read from, and it is honest about which of those
instruments actually exist. It lives in two modules:

- `r15/instruments.py` — the typed record, the one acquisition interface,
  the four modes, the fault-injection kernels, and the registry gate.
- `r15/synthetic_instruments.py` — the nine deterministic synthetic drivers
  that sit behind a `SYNTHETIC_DEVICE`.

Nothing here is measured. The strongest class any reading reaches is
`SYNTHETIC_OBSERVATION`; a `REAL_DEVICE` acquires nothing. The module
imports `r15.claims` and is capped at the software ceiling
(`MODEL_PREDICTION`), with `measured_here = "nothing"` and
`physical_validation = "PHYSICAL_VALIDATION_NOT_CLAIMED"`.

## The typed record

`InstrumentRecord` matches `r15/schemas/instrument_record.schema.json`:

| field | meaning |
| --- | --- |
| `instrument_id` | unique id in the registry |
| `instrument_type` | e.g. `source`, `digitizer`, `microphone` |
| `mode` | one of the four modes below |
| `firmware` | firmware string |
| `clock_source` | the timebase the instrument runs on |
| `capabilities` | a frozenset of `Capability` the instrument can serve |
| `uncertainty_model` | a non-empty dict; a reading with no declared uncertainty cannot enter the evidence ladder |
| `calibration_ids` | calibration certificates the reading is bound to |
| `status` | `AVAILABLE`, `QUARANTINED`, or `BLOCKED_NO_HARDWARE` |

`Capability` is a closed vocabulary: `source`, `digitize`, `impedance`,
`acoustic`, `acceleration`, `photocurrent`, `thermal`, `magnetic`,
`timebase`. Asking an instrument for a capability it does not carry is
refused before acquisition.

## One interface, four distinct modes

Every mode sits behind the same `Instrument.acquire(...)` interface, but
the four are not interchangeable — the difference is the whole point.

- **`REAL_DEVICE`** — interface only. No laboratory hardware exists in this
  repository, so a real acquisition acquires *nothing*: `RealDevice.acquire`
  raises the typed `NoHardwareError`, and `blocked_receipt(...)` returns the
  honest `BLOCKED` state (`acquired: false`, `n_samples: 0`). This is the
  hardware-access boundary — a real read is blocked, not faked.
- **`SYNTHETIC_DEVICE`** — a deterministic driver produces a waveform under
  a numpy seed. Same seed → identical output; different seed → different
  output. The reading is a `SYNTHETIC_OBSERVATION`.
- **`REPLAY_DEVICE`** — replays a previously recorded (synthetic) artifact
  byte-for-byte. It reads back what was stored and measures nothing new.
- **`FAULT_INJECTION_DEVICE`** — wraps a synthetic device and injects the
  ordinary instrument pathologies below, deterministically under the
  acquisition seed, so the downstream error budget can be exercised against
  known faults.

## The synthetic drivers

`r15/synthetic_instruments.py` ships nine deterministic drivers, one per
instrument type. Each `generate(...)` call builds its randomness from
`numpy.random.default_rng(seed)` and adds it to a fixed closed-form signal
model — no wall-clock time, no unseeded global RNG, no external entropy.

| type | capability | signal model |
| --- | --- | --- |
| `source` | `source` | clean reference sine tone |
| `digitizer` | `digitize` | quantized (LSB-gridded) noisy sine |
| `impedance` | `impedance` | resonance magnitude sweep |
| `microphone` | `acoustic` | tone plus second harmonic |
| `accelerometer` | `acceleration` | decaying vibration |
| `photodiode` | `photocurrent` | DC bias with shot-like fluctuation |
| `thermal` | `thermal` | slow drift about a setpoint |
| `magnetic` | `magnetic` | DC field offset with ripple |
| `clock` | `timebase` | timestamps about a nominal period with jitter |

`build_synthetic_device(type, ...)` returns a ready-to-register
`SyntheticDevice`; `synthetic_record(type, ...)` builds just the record.

## Fault injection

`FaultInjectionDevice` injects every `FaultMode`, each a recognised
instrument pathology that demonstrably alters the clean reading:

- **`CLIPPING`** — symmetric soft clip of the extremes at a fraction of the
  peak.
- **`DRIFT`** — a slow linear baseline drift added across the record.
- **`SATURATION`** — a hard rail; samples beyond it flatten onto it.
- **`PACKET_LOSS`** — one contiguous packet is lost and zero-filled.
- **`MISSING_SAMPLES`** — scattered individual samples go missing (`NaN`).

Each fault draws from a per-fault stream derived from the acquisition seed
(`numpy.random.SeedSequence([seed, tag])`), so a fault-injected reading is
fully reproducible: the same seed reproduces the same faulty array.

## The refusal paths

`InstrumentRegistry` is the single gate onto acquisition. It refuses —
**before any sample is produced** —:

1. a **quarantined** instrument (`quarantine(id, reason)` sets the status;
   `acquire` then refuses);
2. an **unsupported capability** (the instrument does not carry it);
3. an **expired or missing calibration**, checked against a supplied,
   explicit `as_of` date — never the wall clock, so the refusal is
   deterministic and testable.

Only after those gates does the registry delegate to the instrument's mode.
A `REAL_DEVICE` that passes the gate still acquires nothing.

Two further refusals close the promotion path: `Acquisition` refuses to be
constructed in any measurement class (it calls
`claims.refuse_synthetic_as_physical`), and `refuse_reading_as_measurement`
refuses to let any reading here be read as a physical measurement.

## Tests

`tests/v8/test_instruments.py` (45 tests) covers: synthetic determinism
(same seed identical, different seed differs) across all nine drivers;
expired and missing calibration refusal; unsupported capability refusal;
every fault mode altering the clean reading and staying deterministic;
packet-loss zero-fill and missing-sample `NaN`; the four modes staying
distinct; a `REAL_DEVICE` read being blocked not faked; quarantine refusal;
and the no-promotion guard.

## What this does not say

It does not say any instrument measured anything. Synthetic and replay
readings are `SYNTHETIC_OBSERVATION`s produced by a seeded simulator or a
recorded synthetic artifact; a `REAL_DEVICE` acquires nothing and its read
is `BLOCKED`. A synthetic observation is never a `PHYSICAL_MEASUREMENT`.
`PHYSICAL_VALIDATION_NOT_CLAIMED`.
