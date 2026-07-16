# Bench Hardware (Agent 14) — ENG

Physical bench for the RGCS measurement campaign. **Class: ENG
throughout** — nothing here is a claim; every operating point is inside
the binding D7-003 envelope (≤ 30 V, ≤ 3 A peak, ≤ 5 mJ/pulse, laser
class ≤ 3R at ≤ 5 mW with interlock, specimen ΔT stop at 5 °C,
dummy-load-first, no human exposure). Costs are indicative classes:
€ (< 100), €€ (100–1000), €€€ (1000–5000).

## 1. Bench layout

```
 ┌────────────────────────────────────────────────────────────────┐
 │  optical rail (breadboard, 600×300)   │  instrument rack        │
 │  laser→mod→pol→[specimen]→pol→PD      │  scope · AWG · DMM      │
 │───────────────────────────────────────│  timing box (TCXO/DDS)  │
 │  isolation platform:                  │  PSU (current-limited)  │
 │   granite slab on sorbothane          │  interlock chain        │
 │   ├ fixture + specimen                │─────────────────────────│
 │   ├ coil pair (A/B) on micrometer rails                        │
 │   └ sensors: accel / contact mic / Hall probe on 3-axis stage  │
 └────────────────────────────────────────────────────────────────┘
```

Rules: one mains phase for the whole bench (ground loops); drive
electronics ≥ 50 cm from sensor preamps; all cables measured and
labelled with length + velocity factor (they enter the phase budget);
the optical rail is mechanically decoupled from the acoustic platform.

## 2. Equipment list

| # | Item | Minimum spec | Feeds | Cost |
|---|---|---|---|---|
| 1 | 2-ch AWG / function generator | 2 phase-locked outputs, ext-ref input, burst mode, ≤ 10 Vpp | all drive branches; `function_generator_presets()` | €€ |
| 2 | Timing box: 32.768 kHz TCXO (≤ 2 ppm) + DDS (AD9833-class) + divider | jitter ≤ 100 ns rms at outputs | master clock; non-integer channels (1496/644/587/20/21 Hz) | €€ |
| 3 | 4-ch oscilloscope | ≥ 100 MHz, ≥ 1 GS/s, ext trigger, ≥ 8 Mpt | H-29 latency cal; waveform fidelity | €€€ |
| 4 | Data acquisition | ≥ 4 ch, ≥ 200 kS/s simultaneous, 16-bit, ext clock input | all time-series capture (fs ≥ 100 kHz for 20.48 kHz work) | €€€ |
| 5 | Current probe (DC–1 MHz) + 0.1 Ω 4-wire shunt | 1 % | coil current *at the load* | €€ |
| 6 | Hall/fluxgate probe | mT range, DC–100 kHz | field at the interaction coordinate | €€ |
| 7 | Accelerometer (≤ 1 g, ≥ 50 kHz BW) + charge amp; contact microphone | calibrated pair | acoustic response; two-sensor parity phase (H-03) | €€ |
| 8 | Laser: HeNe 632.8 nm or stabilized diode, **≤ 5 mW, class ≤ 3R** | power-monitored | optical branch (H-20..H-23) | €€ |
| 9 | Optical: 2 polarizers + λ/4 plate, AO/EO or chopper modulator, biased Si photodiode ≥ 1 MHz, ND filters | — | intensity/polarization modulation; detection | €€ |
| 10 | Interferometry option (H-20): Michelson kit around the specimen path, PZT reference mirror | λ/100 resolution class | photoelastic ΔΦ ~ 3×10⁻² rad target | €€€ |
| 11 | Impedance analysis: scope + shunt + swept AWG (or LCR meter) | 20 Hz–100 kHz | electrical node scan (H-24), coil model | €–€€€ |
| 12 | Thermometry: 2× Pt100/thermistor (specimen + ambient), logging | 0.1 °C | thermal control + 5 °C stop | € |
| 13 | Environment: RH sensor, barometer, SPL meter | logging | environment record schema | € |
| 14 | Current-limited PSU | CC/CV, limits latched ≤ 30 V / ≤ 3 A | coil driver supply | €€ |
| 15 | Instrumented dummy load | 8 Ω power resistor + coil-equivalent RL network on heatsink, thermocouple | dummy-load-first rule | € |
| 16 | Interlock chain | series loop: enclosure switch, laser shutter, coil overcurrent trip, thermal cutoff → output-enable relay | hardware safety | € |
| 17 | Specimens | ≥ 2 quartz crystals (one with measured crystallographic orientation, X-ray or polariscope service), BK7/borosilicate glass blank (matched size), dummy (PLA/aluminium), spiral-cone + matched control (v2 SCAD) | all branches | €€ |

## 3. Fixture design

- **Base:** granite or cast plate on sorbothane feet (≥ 20 dB isolation
  above 50 Hz — verify in commissioning).
- **Specimen cradle:** 3-point kinematic support with PTFE/cork pads at
  adjustable axial stations, so support points can be placed at
  *predicted node* vs *off-node* stations (H-07/H-24 sweeps need the
  support NOT to define the answer: repeat key runs at two support
  configurations).
- **Sensor stage:** 3-axis manual micrometer stage, 10 µm resolution,
  position logged in `position_mm` fields (crystal-axis frame).
- **Coil rails:** the opposed pair on a common rail, coaxial with the
  specimen axis; gap and axial station micrometer-set and logged.
- Every fixture part gets a `fixture_id`; fixture resonances are
  characterized in commissioning (tap test) and registered as artifact
  channels.

## 4. Crystal mounting

1. Handle with gloves (skin oils change surface loading, H-08 family).
2. Photograph + measure per the specimen schema (length, diameters,
   facet count, mass to 0.01 g); record orientation state
   (`orientation_known` true/false — this selects anisotropic vs scalar
   model, crystal application §7).
3. Mount free-free for modal work: cradle pads at the FEA/1D-predicted
   displacement nodes of the target mode; verify insensitivity by a
   deliberate ±5 mm pad shift (frequency shift must stay < the H-01
   tolerance band, else register a fixture systematic).
4. Torque/clamp forces: gravity + pads only. No adhesives on specimens.
5. ΔT sensor taped (kapton) to the non-measured end.

## 5. Coil construction (signal-level, D7-003)

- Two identical air-core solenoids ("A"/"B"): ~200 turns AWG 24–26
  enamelled copper on 40–60 mm ID formers, L ≈ 100–500 µH, R ≈ 1–5 Ω.
  Measure L, R, and distributed C per coil (`coil_impedance`,
  `self_resonance_hz` — self-resonance must be ≥ 10× the 4096 Hz
  carrier; expect ≥ 100 kHz).
- Drive: AWG → audio-class amplifier or MOSFET half-bridge fed from the
  current-limited PSU; series shunt for the current probe. **Peak
  current hard-limited ≤ 3 A**; pulse energy ½LI² ≤ 5 mJ verified by
  `safe_drive_check` before every new operating point, **on the dummy
  load first**, always.
- Opposed (complementary) geometry: coils coaxial, specimen between;
  180° relationship commanded and *verified at the load* each session
  (H-29 procedure in the calibration guide).
- Mutual inductance measured (drive A, read B open-circuit) and logged
  (`mutual_inductance_h` model check).

## 6. Optical setup (class ≤ 3R only)

Rail order: laser → power monitor pick-off → modulator (chopper/AOM/EO)
→ polarizer → specimen (entry facet per `optical_probe` record, path
from `rgcs_core.optics.ray_to_target`) → analyzer → photodiode.
- Beam fully enclosed in tube/box segments; interlock on the box lid;
  beam height constant; no specular path exits the enclosure.
- Crossed-polarizer configuration for birefringence modulation (H-20
  mechanism 2); Michelson insert for direct phase (mechanism 1);
  matched-power off-node path for the heating control (H-22).
- σ⁺/σ⁻ prepared with the λ/4 plate; flip = 90° plate rotation, logged
  (H-23).
- Forward/backward = swap source and detector ends WITHOUT touching the
  specimen mount (rail carriages), per reversal-pair schema (H-21).

## 7. Timing architecture (hardware realization of Agent 07 §9)

```
TCXO 32.768 kHz ──÷8──► 4096 Hz carrier ──► coil A drive ─┐ verified
              └──► DDS ► 1496/644/587/20/21 Hz channels    ├ 180° at
              └──► ÷N  ► 20.48 / 40.96 Hz exact channels   ┘ the load
              └──────► DAQ external sample clock (phase-locked)
              └──────► isolated (opto) trigger: laser mod, scope
```
- ONE reference; every instrument that can take an external
  reference/clock takes this one.
- All triggers opto- or transformer-isolated; no ground path between
  drive and sense sides except the single star point.
- Per-channel latency measured at the connector (calibration guide §3)
  and stored in the `timing_program` record; a null calibration renders
  the channel phase-invalid (H-29 gate) — the analysis pipeline
  enforces this.
