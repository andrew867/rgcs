# R15 P17 — Magnetic and RF Measurement Lane

**Module:** `r15/magnetic_rf.py`
**Tests:** `tests/v8/test_magnetic_rf.py` (35 tests)
**Status:** COMPLETE (software lane); physical run **PREREGISTERED_NOT_RUN**
**Claim cap:** `SYNTHETIC_OBSERVATION` — nothing here is measured.

## What this lane is

Two coupled instruments and their shared trap:

- a **magnetometer** — a Hall plate or a fluxgate — reporting a DC/AC
  magnetic flux density trace (tesla);
- an **RF front end** — a spectrum analyser fed by a near-field probe or a
  shielded loop antenna — reporting power against frequency (dBm/linear);
- a **magnetic-field-dependent frequency shift** binding them: a spectral
  line whose centre moves linearly with the applied field,
  `f_line = f0 + gyro * B` (`line_freq_from_field` / `field_from_line_freq`).

The lane recovers a planted RF line and a planted field shift (POWER) and
refuses to promote the things that only *look* like a signal.

## The four device modes

| Mode | Class | Behaviour |
|------|-------|-----------|
| `REAL_DEVICE` | `RealMagneticRFDevice` | Interface only. `acquire()` raises `NoHardwareError`; physical run **PREREGISTERED_NOT_RUN**. Acquires nothing. |
| `SYNTHETIC_DEVICE` | `SyntheticMagneticRFDevice` | Deterministic B-field trace and RF spectrum from a closed-form model plus seeded noise under `numpy.random.default_rng(seed)`. Output is a `SYNTHETIC_OBSERVATION`. |
| `REPLAY_DEVICE` | `ReplayMagneticRFDevice` | Replays a recorded synthetic artifact byte-for-byte. |
| `FAULT_INJECTION_DEVICE` | `FaultInjectionMagneticRFDevice` | Plants one named defect deterministically. |

No magnetometer, near-field probe, antenna or spectrum analyser exists in
this repository. Only physical acquisition is blocked; all software,
simulation, protocol, tests and docs are complete.

## Fault modes

Time-domain (corrupt the magnetometer trace): `CLIPPING`, `DRIFT`,
`SATURATION`, `PACKET_LOSS`, `MISSING_SAMPLES`.

Spectral (add an ordinary RF pathology): `EMI_INGRESS`, `INTERMOD`, `SPUR`.
Each spectral fault is an *ordinary* effect, not a signal.

## The error budget

`MagneticRFBudget` decomposes the combined uncertainty (root-sum-square)
over: `magnetometer_noise`, `rf_background`, `calibration`, `clock`,
`quantization`, `shielding_leakage`. The **ambient `rf_background`** term is
**required** — it is the `KNOWN_ORDINARY_EFFECT` floor a candidate line must
clear before it is even a candidate. `to_record()` conforms to
`error_budget.schema.json`.

## The ordinary-explanation firewall for RF

`classify_feature` types a spectral line, trying ordinary explanations first
in fixed precedence: **mains pickup** (a multiple of 60 Hz), then a **drive
harmonic**, then an **intermodulation product** (`m·f1 ± n·f2`); only a line
with no ordinary match is a `SIGNAL_CANDIDATE`. `localize_interference`
pins a feature to a named known source. `refuse_emi_as_signal` always
raises: an RF spur, a mains harmonic, or the ambient RF background is a
`KNOWN_ORDINARY_EFFECT`, never a signal. A line that does not clear the
expanded uncertainty is noise, not a resonance
(`recover_field_shift` calls `claims.refuse_noise_as_resonance`).

## Controls

- **Reversal** — `coil_reversal_demodulate` separates the field-linear
  response (odd part, `(forward − reverse)/2`) from pickup (even part,
  `(forward + reverse)/2`). Reversal signs propagate: the recovered sign
  follows the drive polarity (labelled with the R13 helicity sense).
- **Dummy load** — `dummy_load_control` compares a specimen run to a
  dummy-load run; any line surviving in the dummy is pickup, exposed.

## Antenna geometry, clock and bandwidth binding

`AntennaGeometry` tracks probe type, loop area, turns, orientation and
shielding; `orientation_reference` reuses the R13 IGRF orientation reference,
so an antenna attitude from one field vector is fixed only up to the turn
about the field axis (2 DOF recovered, 1 undetermined). `RFBand` binds a band
to a resolution bandwidth; `ClockBinding` binds a trace to a timebase and its
Nyquist limit; the magnetometer bandwidth reuses the R11 Hall detector band.

## Reused authorities (no duplicate truth systems)

- `r11.detectors` — Hall magnetometer capability and bandwidth.
- `r13.magroot` — antenna orientation reference and its alias limits.
- `r13.chiral` — reversal-sign (helicity) sense.
- `r15.claims` — claim taxonomy and forbidden promotions.

No sibling R15 phase module is imported.

## Negative results

- A `REAL_DEVICE` acquisition raises and acquires nothing;
  **PREREGISTERED_NOT_RUN**.
- A mains harmonic, a drive harmonic, and an intermodulation product are each
  `KNOWN_ORDINARY_EFFECT`, not a `SIGNAL_CANDIDATE`.
- A spectral line that does not exceed the expanded uncertainty is refused as
  noise, not a resonance.
- `refuse_emi_as_signal` and `refuse_synthetic_as_physical` always raise;
  an observation may not carry a measurement claim class.
- No physical measurement was performed: `measured_here` is `nothing`,
  `PHYSICAL_VALIDATION_NOT_CLAIMED`.

## Reopening test

Reopen this lane if: a synthetic trace is ever labelled a
`PHYSICAL_MEASUREMENT`; an RF spur, mains harmonic or ambient background is
classified as a `SIGNAL_CANDIDATE`; a line below the combined uncertainty is
called a resonance; a coil reversal fails to flip the sign of the
field-linear response; a dummy-load run fails to expose a shared pickup line;
or a `REAL_DEVICE` acquisition returns data. Physical acquisition is
reopened only when real magnetometer/probe/antenna/analyser artifacts —
instrument, calibration, specimen, fixture, protocol, clock, environment and
raw traces — are supplied.

## Verdict

`MAGNETIC_RF_LANE_FOUR_MODES_NO_PROMOTION`
