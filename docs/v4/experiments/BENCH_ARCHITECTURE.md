# E08 — Integrated bench, DAQ, automation, instrument control

Coverage: **E012–E017, E024, E025**.
Status: **`PROTOCOL_READY_HARDWARE_REQUIRED`**.
Implementation: `rscs2_core.protocols_v4x` (`synth_ring_down`,
`analyze_ring_down`, `blind_labels`), `rscs2_core.research_records`.

## Instrument set

Microphone, contact mic, accelerometer, vibrometer import, function
generator, oscilloscope, current probe, LCR/impedance analyzer,
magnetometer, electrometer, temperature, humidity, pH, conductivity,
flow, pressure, optional EEG/HR.

## Architecture requirements

- Timestamping and trigger alignment across channels.
- Waveform capture with declared sample rate and window.
- **Calibration expiry** — an instrument past its calibration date is
  refused, not warned about.
- **Raw-data hashing** — `raw_hash` is a required field on any `MEAS`
  record; the raw file is immutable.
- Environment logging on every run.
- Specimen and fixture IDs bound to every record.
- Automated sham and randomization.
- Operator blinding.
- Immediate safety shutdown / interlock.

## The rule that defines this agent

> **No silent fallback to fabricated data. Simulated records must be
> unmistakably marked synthetic.**

`make_record` enforces it: `synthetic: true` can never carry `MEAS` or
`EXPERIMENTALLY_MEASURED`. A DAQ that loses its instrument must fail,
not interpolate.

## Synthetic validation (G29)

The analysis pipeline is validated against planted truth **before** it
is pointed at unknown data:

```
synth_ring_down(f0=4096 Hz, Q=5000, fs=65536 Hz, noise=1%)
analyze_ring_down(...) -> f0 within ±1 Hz, Q within ±15%
```

`analyze_ring_down` recovers f₀ from the FFT peak and Q from the
envelope decay (τ fit → Q = π f τ). Its output carries
`synthetic_validated: true` and **no `MEAS` tag** — provenance is the
caller's deliberate act, never a default.

A pipeline that cannot recover a known answer has no business
reporting an unknown one.

## Failure modes exercised

Simulated instruments, dropped samples, clock drift, trigger error,
saturation, calibration expiry, missing metadata, power failure, safe
stop, cross-platform paths.

## Blocker

Hardware: the entire instrument set. Nothing procured, nothing
connected, no run executed. The DAQ exists as schemas, a validated
analysis path, and synthetic fixtures.
