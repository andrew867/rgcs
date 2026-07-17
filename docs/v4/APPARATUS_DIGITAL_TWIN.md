# Apparatus digital twin (Agent C07)

Coverage: **A16, E008–E027** (hardware side). Gate: **G14** (ordinary
artifact model). Status: `REDUCED_ORDER_VALIDATED`.
Implementation: [`rscs2_core/apparatus.py`](../../rscs2_core/apparatus.py).

## Why this exists

**A residual may not be called exotic until the ordinary channels are
bounded.** That is the C07 boundary, and it is the most load-bearing
rule in the experimental programme. Every function here exists so an
ordinary channel has a *number* instead of an adjective.

If a coil buzzes, warms, and pulls a resonance by 0.4 Hz, and the
"effect" is 0.3 Hz, there is no effect — there is a coil. This module
is how that gets decided in advance rather than argued afterwards.

## Coil model

`coil_model()` returns, for a declared winding:

| Quantity | Model |
|---|---|
| resistance | ρ(T)·L/A with the copper temperature coefficient |
| inductance | Wheeler single-layer solenoid (~1% for l > 0.8r) |
| reactance | 2πfL |
| centre field | μ₀ N I / 2r |
| power | I²R |
| skin depth | sqrt(ρ/(π f μ₀)) with a negligibility flag |

For the 40-turn, 0.33 mm, 30 mm-radius coil at 0.5 A: R = 1.48 Ω,
L = 1.21e-4 H, B₀ = 4.19e-4 T, P = 0.37 W, and the skin depth exceeds
the wire radius at 4 kHz — so the DC resistance is the right model,
and the flag says so rather than leaving it assumed.

## Independent cross-check

`coil_field_map()` computes the 3-axis field with the **validated
Biot-Savart integrator** (the same one the frozen v4 projections module
uses). At the coil centre it agrees with the analytic loop formula to
**1 part in 10⁴**:

    Biot-Savart |B| = 4.1890e-04 T
    analytic   |B|  = 4.1888e-04 T     ratio 1.0001

Two independent routes to the same number. That is what makes the
field prediction usable as a control rather than a hope.

## Thermal

`thermal_rise_c()`: T = T_amb + P·R_th, with a declared 60 °C limit.
Above it, hardware enable is blocked pending an interlock (S01). A
warm coil moves every resonance through thermal expansion — an
ordinary channel that masquerades as drift.

## Contact and fixture

`contact_load_model()` uses Hertzian contact stiffness k = 2E*a in
parallel with the modal stiffness; the frequency pulls as
sqrt(1 + k_c/k_m).

This is the **E06 subtraction model**: a hand on a crystal changes its
frequency by ordinary mechanics. The note in the return value says so
explicitly — `NOT an operator effect`. Any operator-state claim must
survive subtraction of this first.

## Instrument chain

- `transducer_transfer()` — second-order response; every measured
  spectrum is the product of the specimen and the instrument, and
  failing to divide it out **manufactures peaks**.
- `cable_loading()` — f_3dB = 1/(2πRC); measurements above it are
  attenuated by the cable, not by the specimen.
- `electrode_capacitance_f()` — parallel-plate ideal, declared as a
  **lower bound** because fringing only increases it.

## Crossed coils

`crossed_coil_coupling()` computes the mutual coupling of two
orthogonal coils numerically: the symmetry null holds to < 1e-9. A
nonzero reading on the orthogonal pickup is misalignment or
capacitive crosstalk, not a new field.

## Ordinary artifact budget (G14)

`ordinary_artifact_model()` assembles the expected artifact
contributions so any campaign can subtract them before discussing a
residual. The E-lane protocols reference it as a precondition.

## Boundary

Do not authorize hardware operation above validated limits: ≤30 V,
≤3 A, ≤5 mJ electrical; ≤85 dBA acoustic; 60 °C coil. Nothing in this
module has been operated — it makes **predictions** for controls, and
every one of them is currently unmeasured.
