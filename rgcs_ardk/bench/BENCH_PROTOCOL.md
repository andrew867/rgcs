# Bench protocol RevA

## Aim

Measure whether the annular board produces controllable field asymmetry, not force.

## Primary measurements

- 37 sector complex pickups.
- 8 compass pickups.
- center reference.
- optional above/below probes.
- carrier lock-in at 1,683,456 Hz.
- envelope/reference lock-in at 4096 Hz.
- temperature, vibration, environmental magnetic/acoustic background.

## Commissioning order

1. Visual inspection.
2. Continuity and isolation tests.
3. Board A passive pickup calibration with known external source.
4. Fixture remount repeatability test.
5. Dummy load electronics run.
6. Board B unpowered pickup baseline.
7. Board B low-power active test.
8. All-active symmetric control.
9. R10.73 constrained recipe.
10. Null controls.
11. Rotation/mirror/reverse-lag transform controls.
12. Report generation.

## Refusal gates

The bench report must raise if:

- angular uncertainty undeclared;
- amplitude uncertainty undeclared;
- raw data hashes missing;
- calibration IDs missing;
- any required control missing;
- primary observable is force/thrust;
- result language exceeds field-asymmetry claim.

## PASS criterion

A field-asymmetry PASS requires:

- `arg(DeltaB)` tracks command within uncertainty;
- `|DeltaB|` exceeds equal-resource null distribution;
- rotated table transforms by `360*k/37`;
- mirrored table negates offset;
- reversed lag negates offset and preserves magnitude within uncertainty;
- thermal/vibration/electrostatic artifacts bounded.
