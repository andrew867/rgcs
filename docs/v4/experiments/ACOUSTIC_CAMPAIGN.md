# E01 — Acoustic and ultrasonic bench campaign

Coverage: **E001–E004, F001, F020–F023**.
Status: **`PROTOCOL_READY_HARDWARE_REQUIRED`** — not performed.
Preregistration: `PREREG-E01`. Safety: ≤85 dBA (S01).
Implementation: `rscs2_core.protocols_v4x.build_protocols()["E01"]`.

## Nothing here has been run

No sound has been played at any crystal. This is the protocol that
would do it.

## Drive plan

| Condition | Frequencies |
|---|---|
| Direct tone | 4096 Hz, contact and non-contact |
| Brushing | 3 axes × 6 facets |
| Broad sweep | 18.5–21.2 kHz |
| Focused sweep | 19.8–21.2 kHz |
| Additional bands | 10.0–12.7, 24.5–25.5 kHz |
| Candidates | 20.480, 20.800, 21.125, 20.460, 20.462, 20.6061, 20.62116 kHz |
| Harmonic targets | 32.768, 33.800 kHz |
| Source sequences | 1496/587/644; 465/787/880 (labels only, no medical claim) |
| Progressive | 10..550 sequence |
| Low-frequency | 40 / 40.96 / 41 / 42 Hz comparison |

Sources: forks vs voice-coil vs piezo, so the *transducer* is a
variable and not a constant confound.

## Channels

Microphone, contact mic, accelerometer, laser vibrometer (import),
plus **simultaneous electrical pickup** (E023) — a mechanical
resonance and an electrical artifact look identical on one channel and
different on two.

Environment logged throughout: I, V, B, T, RH, SPL.

## Controls (mandatory)

- Fixed nonmetal jig (E019); contact force logged (E027).
- Dummy rod, glass, **no-crystal**, off-resonance.
- **Neighbour frequencies** at ±0.5% and ±2% for every "special"
  number — a frequency that works no better than its neighbours is not
  special (see [TIMING_FAMILY_AUDIT.md](../TIMING_FAMILY_AUDIT.md)).
- Cheap quartz **before** precision crystals (E021).
- Randomized order, repeated days, blinded labels (E022).
- Room-mode survey before any specimen is mounted.

## Analysis (preregistered)

FFT peak → Q → ring-down via `analyze_ring_down` (validated on planted
fixtures, G29). Control subtraction against the C07 ordinary-artifact
budget. Every candidate match passes the look-elsewhere model before it
is called anything.

## Boundaries

- **A phone app is not calibrated evidence.**
- No unsafe ultrasound exposure to people.
- **Do not select only the peaks near desired numbers.** The
  progressive sweep visits 100+ frequencies; reporting the best one
  without the multiple-comparison penalty is the classic failure and
  the null model exists to prevent it.
- Room modes and transducer resonances are the expected artifacts;
  both are measured, not assumed absent.

## Blocker

Hardware: calibrated source, SPL meter, DAQ, jig, specimens. Nothing
has been procured. Human-only action.
