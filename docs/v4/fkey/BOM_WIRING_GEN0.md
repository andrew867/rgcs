# Gen-0 BOM, wiring, and fixture (Agent A20)

Status: **ENGINEERING_PROTOTYPE — nothing purchased, wired, or
powered.** Costs are indicative CAD; verify at order time.

## Budget tiers

| Tier | Contents | ~Cost |
|---|---|---|
| T0 "prove the loop" | CYD + breadboard + MOSFET + piezo disc ×2 + passives | $35–50 |
| T1 "trustworthy telemetry" | + INA219 module, DS18B20, TVS, fuse holder, op-amp front end | +$20 |
| T2 "reference check" | + USB audio interface (96 kS/s) or entry USB scope | +$60–150 |

## Core BOM (T0/T1)

- ESP32-CYD (exact variant per A14 questionnaire — buy AFTER
  identifying, or identify what arrives before wiring anything)
- Logic-level MOSFET, **verified for conduction at 3.3 V gate**
  (e.g. AO3400-class; R_DS(on) specified at V_GS ≤ 2.5 V — do not
  choose by threshold voltage alone, V_th is the turn-OFF spec)
- Gate resistor 100 Ω + 10 kΩ gate pulldown (output floats low at
  boot — belt for the FSM's braces)
- Piezo disc ×2 (one actuator, one contact pickup)
- Actuator series resistor (current limit into the capacitive load;
  size after measuring disc capacitance) + TVS across the MOSFET
- High-impedance pickup front end: MCP6002-class op-amp, 1 MΩ bias,
  input clamp diodes to rails, RC anti-alias at ~20 kHz
- DS18B20 temperature at the actuator; INA219 for **slow** supply
  telemetry (it cannot resolve a 20 kHz waveform and is never asked
  to — orchestrator prohibition)
- Fused, current-limited 5 V supply; physical output disconnect
  (remove a jumper = provably off); test points: gate, actuator,
  shunt, pickup, ground

## Wiring (per verified profile only)

```
CYD GPIO[out] --100R--> MOSFET gate (10k pulldown to GND)
5V --fuse--> actuator+ ; actuator- --> MOSFET drain ; source --> GND
TVS across drain-source ; series R in actuator+ leg
pickup piezo --> clamp --> op-amp x10 --> RC LPF --> CYD ADC[in]
DS18B20 --> 1-wire pin ; INA219 on I2C (slow telemetry only)
```

Keep the pickup wiring physically away from the switching node; star
ground at the supply; twisted pair to the actuator. Electrical
crosstalk that arrives anyway is what the sham (output-off) and
transducer-only controls exist to expose (A24).

**Never**: mains anywhere near the fixture; the specimen in an
electrical circuit; glue or permanent modification of the specimen
for first measurements.

## Fixture

Soft foam V-blocks at the model's expected displacement antinodes
(free-free: ends are motion maxima — support near ~0.224 L nodal
planes instead), actuator disc coupled through a thin elastomer pad,
pickup at the opposite end. Repeatability protocol: 8 remounts, log
the peak scatter, and refuse to interpret any shift smaller than it
(the resonator_platform rule, inherited).

## Bring-up checklist (before ANY power)

1. Continuity: no gate-drain short; pulldown present.
2. Supply current limit set; fuse installed.
3. Multimeter on the output: confirms 0 V at boot (the FSM promise,
   physically checked).
4. Smoke-test recipe into a **dummy resistive load**, scope/DMM on
   the drain — no specimen, no actuator.
5. Hearing note: near-20 kHz is audible to young ears and to
   animals. Low duty, short bursts, door closed, pets out.
