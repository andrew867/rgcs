# R15 P14 — Electrical Measurement Lane

**Module:** `r15/electrical.py` · **Tests:** `tests/v8/test_electrical.py` ·
**Receipt:** `docs/v8/receipts/P14.json`

**Status:** `COMPLETE` (software lane) · physical run
`PREREGISTERED_NOT_RUN` · **claim cap:** `SYNTHETIC_OBSERVATION` ·
**verdict:** `ELECTRICAL_LANE_TYPED_NO_DEVICE_SYNTHETIC_BVD_RECOVERED`

## What this is

The electrical and impedance lane of the R15 platform. It measures nothing.
What it stands up, in software, is the full apparatus an electrical
resonator measurement would need, and it keeps a strict line between what
*could* be measured and what actually *was*, which is nothing.

- **Constitutive relations** — voltage, current, impedance `Z = V/I`,
  admittance `Y = 1/Z`, phase, charge `q = ∫ i dt`, Johnson–Nyquist thermal
  noise, and a source/load transfer function.
- **Impedance/admittance sweep + Butterworth–Van Dyke fit** — a complex
  frequency sweep of a planted BVD resonator, fit to recover the series
  resonance `f_s`, the parallel resonance `f_p`, the quality factor `Q`, and
  the motional `R, L, C` with the static `C0`. The sweep and the fit reuse
  `r13.qcmstack.synthetic_bvd_sweep` and `r13.qcmstack.fit_bvd`.
- **Fixture model** — a shunt cable capacitance and a series lead impedance,
  with two-wire, four-wire (Kelvin) and bridge topologies.
- **Open-short-load (OSL) de-embedding** — three synthetic standards remove
  the fixture parasitics so the recovered impedance is the bare device.
- **Electrical error budget** — instrument resolution, calibration, clock,
  environment, fixture repeatability, cable capacitance, lead resistance,
  DSP windowing, and model residual, combined in quadrature (k = 2).
- **Pathology detectors** — ground loops (mains-frequency pickup),
  saturation (railing), and cable capacitance (via the OSL open standard).

## One lane interface, four honest modes

Every acquisition goes through one `ElectricalLane` interface with four
distinct modes:

| Mode | Behaviour | Claim class |
|------|-----------|-------------|
| `REAL_DEVICE` | Interface only. Acquires **nothing**: raises `NoElectricalHardwareError`; `blocked_receipt()` is `PREREGISTERED_NOT_RUN`. | `BLOCKED_MISSING_INPUT` |
| `SYNTHETIC_DEVICE` | Deterministic synthetic impedance sweep from a planted BVD resonator behind a fixture, under a numpy seed. The fit recovers the planted parameters. | `SYNTHETIC_OBSERVATION` |
| `REPLAY_DEVICE` | Replays a recorded synthetic sweep point-for-point. Measures nothing new. | `SYNTHETIC_OBSERVATION` |
| `FAULT_INJECTION_DEVICE` | Wraps a synthetic device and injects clipping, drift, saturation, packet loss, and missing samples, deterministically. | `SYNTHETIC_OBSERVATION` |

## The power result

A synthetic sweep of the default resonator (`f_s ≈ 1 MHz`, `Q = 1000`) is
fit and the planted `R, L, C, C0, f_s, f_p, Q` come back to within ~1e-3
relative (and `R`/`f_s` far tighter). A parallel cable capacitance is
otherwise absorbed into `C0`; only the OSL open standard recovers the cable
capacitance and only OSL de-embedding recovers the true `C0`.

This recovery is **model self-consistency** — the fit inverts numbers this
module planted — and it is a `SYNTHETIC_OBSERVATION`, never a measured
crystal.

## The load-bearing refusals

- `RealElectricalDevice.acquire_sweep` raises `NoElectricalHardwareError` —
  no impedance analyzer, LCR bridge or crystal exists here.
- `fit_synthetic_bvd` refuses a REAL sweep (nothing to fit) and a
  fault-injection sweep (carries injected pathology).
- `OSLCalibration.correct` raises `CalibrationLimitError` for any grid it was
  not measured on — a calibration is never extrapolated.
- `refuse_synthetic_fit_as_measured_device` and `refuse_sweep_as_measurement`
  (the latter delegating to `r15.claims.refuse_synthetic_as_physical`) refuse
  to promote a synthetic observation to a measurement.
- `ElectricalSweep` refuses construction with any measurement claim class.

## What this does not say

It does not say any crystal or circuit was measured. A synthetic sweep is
simulator output and a BVD fit recovers parameters this module planted;
there is no impedance analyzer, LCR bridge or crystal in this repository, a
`REAL_DEVICE` acquires nothing, and a `SYNTHETIC_OBSERVATION` is never a
`PHYSICAL_MEASUREMENT`. The software ceiling is `MODEL_PREDICTION`.
`PHYSICAL_VALIDATION_NOT_CLAIMED`.

## Reuse (no duplicate truth systems)

`r13.qcmstack` (sweep + BVD fit), `r13.piezobridge.BVDCircuit` (equivalent
circuit), `r13.response.statespace_transfer` (transfer function), and
`r15.claims` (claim taxonomy and forbidden promotions). No sibling R15 phase
module is hard-imported.

## What would change this

A physical crystal swept on a calibrated impedance analyzer, its raw complex
sweep and OSL calibration captured with a clock binding, an environment log,
and an uncertainty budget — none of which exists in this repository.
