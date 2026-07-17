# E05 — Water, fluid, coil, and acoustic exposure programme

Coverage: **W001–W017, E010**.
Status: **`PROTOCOL_READY_HARDWARE_REQUIRED`**.
Preregistration: `PREREG-E05`. Safety gate: `no_ingestion_ack` required.

## Binding constraints, stated first

- **Treated water is research-only and is not ingested. No
  exceptions.**
- **No claim of healing, memory, structuring, or benefit.** None is
  made anywhere in this programme.
- The `no_ingestion_ack` flag is a hard condition of the safety gate: a
  water protocol without it does not reach protocol-ready (G26).

## Design

| Element | Specification |
|---|---|
| Vessels | matched, blind-labelled (W001) |
| Sham | full sham exposure (W002) |
| Controls | no crystal (W010), raw quartz (W011), polymer + glass (W012), reversed orientation (W013) |
| Exposure | 4096 Hz acoustic; selected frequency controls |
| Apparatus | seven-turn one-litre 70 °F historical coil (ORPHAN-015) |
| Flow | 1–7 passes in a flow loop; rate and pressure logged |
| Chemistry | pH, conductivity, temperature, dissolved gas, mass balance |
| Optical | UV-Vis, IR where available |
| Physical | acoustic pressure and coil field logged |
| Procedure | randomized labels, repeated days, cleaning and calibration between runs |

## Why pH drift is the trap

pH and conductivity are **exquisitely sensitive to things that are not
the experiment**: dissolved CO₂ from the room, a 1 °C temperature
change, a fingerprint on the vessel, the previous sample. A treated
sample will differ from a control. It will differ from *itself* an hour
later.

**pH/conductivity drift alone is not evidence of molecular
reprogramming.** It is evidence that water is a good solvent in a room
with air in it. This is why sham exposure, mass balance, dissolved-gas
logging, and blinded analysis are not optional garnish — they are the
only things separating a result from an artifact.

## Analysis

Preregistered primary outcome; multiple-comparison handling across the
chemistry panel (measuring 6 quantities and reporting the one that
moved is a look-elsewhere error). **Analysis is locked before
unblinding.**

## Validation before hardware

Randomization, blind decoding, contamination spikes, vessel effects,
temperature confounding, sensor drift, and sham equivalence are all
exercised against synthetic fixtures.

## Failure conditions

- Sham and treated are indistinguishable → registered null (G48), and
  a null here is a real result.
- Contamination spike detected → run void, not "interesting".
- Blind broken before analysis lock → data unusable.

## Blocker

Hardware: vessels, flow loop, pH/conductivity meters, spectrometer,
coil. Nothing procured. **No water has been exposed to anything.**
