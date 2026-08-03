# Sensor Feedback Report

**Status:** `PASS_REFERENCE_IMPLEMENTATION_PHYSICAL_CALIBRATION_PENDING`

## Topology

The stationary encoder has 37 sector-resolved complex pickup channels, eight
coarse compass channels, a fixture-mounted center reference, four optional
above-plane locations, and four optional below-plane locations. The imported
R10.73 plan contains exactly 54 probes and locks carrier/reference acquisition
to 1,683,456 Hz and 4096 Hz.

The estimator subtracts the declared center reference, removes ring common
mode, and evaluates the normalized first spatial harmonic. It returns a
complex `DeltaB`, magnitude, direction, common mode, and sample count. A
separate eight-channel estimator provides a coarse cross-check. Per-channel
complex gain calibration must be nonzero and is applied before estimation.

## Transform controls

- Rotating a table by `k` cells advances direction by `360*k/37`.
- Mirroring conjugates the effective asymmetry and negates direction.
- Reversing lag negates offset around the amplitude-only axis while preserving magnitude.
- Eight randomized controls preserve the exact amplitude multiset.

All transforms are exercised against the imported R10.73 tables, not locally
invented seed values.

## Physical work still required

Board A must be calibrated against a traceable known field. Sector/compass
gain tables, remount repeatability, center-probe registration, probe-position
uncertainty, environmental background, thermal, vibration, and electrostatic
channels require measured receipts. Until then this report validates only the
reference estimator and geometry.
