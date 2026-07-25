# R15 P15 — Optical Measurement Lane

The optical measurement lane is the R15 acquisition lane for optical
readout of surface displacement and wave propagation — photodiode,
interferometric, speckle, and photoelastic. It is honest about what optics
can and cannot recover, and about the fact that no optical bench exists
here. It lives in one module:

- `r15/optical.py` — the typed `OpticalConfig`, the one acquisition
  interface, the four device modes, the four readout kinds, the traceable
  corrections, the synthetic signal generators and their recovery
  pipelines, the full optical error budget, the fault-injection kernels,
  and the refusal paths.

Nothing here is measured. The strongest class any reading reaches is
`SYNTHETIC_OBSERVATION`; a `REAL_DEVICE` acquires nothing and the physical
run is `PREREGISTERED_NOT_RUN`. The module imports only `r15.claims` and the
R13 authorities it extends — `r13.imaging` (reconstruction),
`r13.heterodyne` (interferometric/cavity readout), and `r13.sixangle`
(planar angular sampling) — with `measured_here = "nothing"` and
`physical_validation = "PHYSICAL_VALIDATION_NOT_CLAIMED"`.

## What every optical result is bound to

`OpticalConfig` carries the quantities every optical result must be bound
to, plus a calibration id:

| field | meaning |
| --- | --- |
| `wavelength_nm` | laser wavelength (default 632.8 nm, HeNe) |
| `bandwidth_nm` | source bandwidth |
| `power_w` | incident optical power |
| `polarization_deg` | input polarization angle |
| `incidence_deg`, `standoff_m` | geometry of the illumination |
| `geometry_passes` | 1 (single pass) or 2 (retro-reflection double pass) |
| `thermal_load_c` | thermal load on the specimen/bench |
| `visibility` | interferometric fringe contrast, in `[0, 1]` |
| `calibration_id` | the calibration the reading is bound to |

`phase_per_metre = geometry_passes · 2π/λ` is the constant that converts a
recovered fringe phase back into a surface displacement;
`unambiguous_displacement_m()` is the largest displacement whose phase stays
within ±π (before wrapping).

## One interface, four distinct modes

Every mode sits behind the same `OpticalDevice.acquire(...)` interface, but
the four are not interchangeable.

- **`REAL_DEVICE`** — interface only. No laser, interferometer,
  photodetector, polarizer, or specimen exists in this repository, so a real
  acquisition acquires *nothing*: `OpticalRealDevice.acquire` raises the
  typed `NoOpticalHardwareError`, and `blocked_receipt(...)` returns the
  honest `BLOCKED` state with `physical_run: PREREGISTERED_NOT_RUN`. This is
  the hardware-access boundary — the read is blocked, not faked.
- **`SYNTHETIC_DEVICE`** — a deterministic generator produces an optical
  signal with a *planted* displacement, retardation, or fringe under a numpy
  seed, and the pipeline recovers it. Same seed → identical trace. The
  reading is a `SYNTHETIC_OBSERVATION`, and the recovery is the POWER
  control.
- **`REPLAY_DEVICE`** — replays a previously recorded (synthetic) trace
  byte-for-byte; it measures nothing new.
- **`FAULT_INJECTION_DEVICE`** — wraps a synthetic device and injects the
  optical faults below, deterministically under the acquisition seed.

## Intensity-only vs phase-sensitive

The lane separates the two readout families, which is the load-bearing
optical distinction:

- **Phase-sensitive** (`INTERFEROMETRIC`, `PHOTOELASTIC`) — the measurand
  lives in a phase. The interferometer scans a reference-phase carrier and
  reads the fringe `I = I₀·(1 + V·cos(ψ + φ))`; the planted displacement
  sits in `φ` and is recovered by projecting the carrier tone (reusing
  `r13.heterodyne.tone_amplitude`) and dividing by `phase_per_metre`. The
  photoelastic readout reads the crossed-polarizer intensity
  `I = I₀·sin²(δ/2)` and inverts it for the retardation `δ`.
- **Intensity-only** (`PHOTODIODE`) — reads optical power and is phase-blind.
  A pure displacement is a phase shift that does not change the power, so it
  is **not recoverable** from a photodiode trace. `refuse_intensity_as_phase`
  raises on any attempt to read a displacement from an intensity-only
  readout.

The speckle readout builds a fully-developed synthetic speckle intensity
field (a random-phasor sum); `speckle_correlation` and `decorrelate_speckle`
model how the field decorrelates as the surface moves.

## Traceable corrections

Dark, flat, reference, and drift corrections each return both the corrected
trace and a `Correction` record of exactly what was removed, so the chain is
auditable back to the raw trace:

- **dark** — subtract a dark-frame offset (records the level).
- **flat** — divide out a flat-field gain (records the gain; zero gain
  refused).
- **reference** — subtract a reference-arm baseline (records its mean).
- **drift** — fit and remove a slow linear baseline (records the slope).

## The optical error budget

`build_error_budget(config)` decomposes the displacement uncertainty into
the R15-policy components — instrument resolution, calibration, clock,
environment, fixture repeatability, specimen geometry, orientation,
numerical method, DSP, operator action, model residual — **plus** the
optical-specific terms (wavelength, bandwidth, optical power, polarization).
Thermal load is kept as its own component, distinct from the general
environment term, as the policy requires. Components are combined in
quadrature (`root_sum_square`) and scaled by a coverage factor. The result
conforms to `r15/schemas/error_budget.schema.json`; every
`OpticalObservation` serializes to `observation_record.schema.json` and is
bound to its geometry and calibration.

## Fault injection

`OpticalFaultInjectionDevice` injects every `OpticalFault`, each a
recognised pathology that demonstrably alters the clean trace:

- **`CLIPPING`**, **`DRIFT`**, **`SATURATION`**, **`PACKET_LOSS`**,
  **`MISSING_SAMPLES`** — the five generic instrument faults.
- **`FRINGE_WASHOUT`** — collapses the fringe modulation onto its DC level;
  the interferometric visibility washes out.
- **`SPECKLE_DECORRELATION`** — mixes in an independent speckle realisation,
  dropping the correlation with the original field.

Each fault draws from a per-fault stream derived from the acquisition seed
(`numpy.random.SeedSequence([seed, tag])`), so a fault-injected reading is
fully reproducible.

## The refusal paths

- `OpticalRealDevice.acquire` raises `NoOpticalHardwareError` — a real read
  acquires nothing, physical run `PREREGISTERED_NOT_RUN`.
- `refuse_intensity_as_phase` — a photodiode cannot yield a displacement.
- `refuse_reconstruction_as_measured` — delegates to
  `r13.imaging.refuse_reconstruction_as_measured`: a reconstruction of a
  synthetic phantom or fringe is a `SYNTHETIC_OBSERVATION`, not an image of a
  real source.
- `refuse_synthetic_as_physical` — delegates to the governance core; no
  trace here is a physical measurement.
- `OpticalObservation` refuses to be constructed in any measurement class,
  and its evidence is capped at `E3` (a calibrated self-test) because the
  specimen, fixture, and raw physical artifact bindings are absent.

## Tests

`tests/v8/test_optical.py` (39 tests) covers: the POWER controls (a planted
displacement, retardation, and fringe are recovered, and the phantom
reconstruction round trip); the photodiode being phase-blind and the
intensity/phase refusal; the four modes staying distinct; the replay reading
back a recorded trace; every one of the seven fault modes altering the trace
(fringe wash-out collapsing visibility, speckle decorrelation dropping
correlation); dark/flat/reference/drift corrections being traceable; the
error budget combining in quadrature with thermal load a distinct component;
schema conformance of the observation record and the error budget; the
evidence cap below a physical measurement; and determinism (same seed
identical, different seed differs, fault injection reproducible).

## What this does not say

It does not say any optical signal was transduced from a specimen. Every
trace is simulator output under a seed; a photodiode is phase-blind and
cannot yield displacement; a reconstructed fringe is a
`SYNTHETIC_OBSERVATION`, not an image of a real source. A synthetic
observation is never a `PHYSICAL_MEASUREMENT`. `PHYSICAL_VALIDATION_NOT_CLAIMED`.
