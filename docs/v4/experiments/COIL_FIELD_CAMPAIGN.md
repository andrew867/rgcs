# E03 — Copper/silver coil and field-proxy mapping

Coverage: **E008–E011**. Status: **`PROTOCOL_READY_HARDWARE_REQUIRED`**.
Preregistration: `PREREG-E03`. Safety: ≤24 V, ≤1 A, 60 °C interlock.
Implementation: `protocols_v4x.build_protocols()["E03"]`,
`apparatus.coil_model`, `apparatus.coil_field_map`.

## Predictions exist before the measurements do

This is the campaign where the digital twin earns its place. Before any
coil is energized, [APPARATUS_DIGITAL_TWIN.md](../APPARATUS_DIGITAL_TWIN.md)
predicts, for the 40-turn 0.33 mm coil at 0.5 A:

    R = 1.48 Ω    L = 1.21e-4 H    B_centre = 4.19e-4 T    P = 0.37 W

with the Biot-Savart integrator and the analytic formula agreeing to
1 part in 10⁴. A measured field that disagrees with that means the
build is wrong, the probe is uncalibrated, or the current is not what
the supply says — **not** that something new is happening.

## Builds

- 40-turn, 0.33 mm wire coil.
- 90° crossed copper/silver coils (mutual coupling null < 1e-9 by
  symmetry — `crossed_coil_coupling`).
- Seven-turn one-litre historical coil (ORPHAN-015).

## Controls

Single coil, **dummy coil**, resistor, no-crystal, rotated crystal,
metal bracket, nonmetal jig. Field reversal. Cable-loop geometry
varied (ground loops make beautiful signals).

## Channels

3-axis B-field maps, high-impedance E-field, current, voltage,
heating, vibration, acoustic leakage (coils buzz — that is a real
acoustic drive nobody intended), geographic orientation and north
logging (E026), inter-coil phase.

## The "torsion" translation

The source claims a torsion field. **This programme does not measure
torsion**, because no operational definition with units exists in the
sources (ORPHAN-001 keeps the term at SRC).

What it does instead: translate the claim into **measurable residual
channels**. After subtracting the predicted B field, thermal drift,
acoustic coupling, and fixture modes, is there anything left above the
noise floor? That residual is a number. Whether to call it "torsion" is
not a measurement question, and the answer here is no.

**Do not label unexplained residuals torsion fields.** An unexplained
residual is an unexplained residual, and the first hypothesis is
always the apparatus.

## Boundaries

- No high-power coil operation without thermal and current interlocks.
- Residuals are discussed only after the twin's predictions are
  subtracted (G14).
- Geomagnetic orientation is logged because a 3-axis magnetometer
  measures the Earth first and everything else second.

## Blocker

Hardware: coils, current source, 3-axis magnetometer, electrometer.
Nothing procured. Human-only action.
