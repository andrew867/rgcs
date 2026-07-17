# Frequency-Key Harmonic Excitation and ESP32-CYD Instrument
(v4.4 pack, Agents A00–A26)

Package: [`fkey_instrument/`](../../../fkey_instrument/) ·
Firmware: [`firmware/fkey_cyd/`](../../../firmware/fkey_cyd/) ·
Tests: `tests/v4/test_fkey_instrument.py`,
`tests/v4/test_fkey_device_redteam.py` ·
Demos: [`SYNTHETIC_demo_report.md`](SYNTHETIC_demo_report.md)

> Lore proposes. Mathematics translates. Software attacks.
> Evidence decides. Provenance remembers.

**Nothing physical exists.** No CYD board has been powered, no MOSFET
wired, no crystal measured — the specimen is an eBay listing. Every
run in this lane is SYNTHETIC and says so. All six preregistered
hypotheses are `UNTESTED`.

## The relation engine (A04) — exact, classified, honest

All frequency arithmetic is `fractions.Fraction`; floats are refused
at the parse boundary. Every relation carries exactly one primary
mechanism class, and the class controls the language:

| Frozen seed case | Class | Why |
|---|---|---|
| 4096 × 5 = 20480 | **HARMONIC** (order 5) | a square/pulse drive at 4096 Hz physically carries a 5th-harmonic line at 1/5 Fourier amplitude |
| 8 × 2560 = 20480 | PHASE_CLOSURE_ONLY | exact, but order 2560 is not a generation mechanism |
| 20.48 × 1000 / 40.96 × 500 | PHASE_CLOSURE_ONLY | same: timing closure, not spectrum |
| 1496 + 32×587 = 20280 | ARITHMETIC_COINCIDENCE (order 33) | a weighted sum of tones is not an emitted frequency in a linear system |
| 3·644+4·787+9·880+5·1496 = 20480 | ARITHMETIC_COINCIDENCE (order 21) | same |
| 8 × 2535 = 20280 | PHASE_CLOSURE_ONLY | exact, ~1.041 Hz above the nominal specimen model |

The A06 engine proves the key comparison rather than asserting it: an
ideal sine has a **zero** fifth harmonic; an ideal 50% square carries
one at exactly **1/5** — verified analytically AND by independent FFT
(A22 cross-check). Duty error resurrects even harmonics (tested).

## The specimen (A07) — a listing, not a crystal

`SP-EBAY-137330949270-PREARRIVAL`, revision 1, immutable. Seller
claims: 77.8 mm, 6 facets, "Himalayan quartz". The screening model
(1-D rod, isotropic v = 6310.812116 m/s — an assumption for an
unoriented specimen) gives quarter-wave 20278.959 Hz and half-wave
40557.918 Hz. **Correction record FK-CORR-001**: those two targets'
percentage errors are the SAME number by construction (both ∝ v/L) —
one piece of evidence, never two.

The model licenses a **search band** (~±1 kHz around nominal under
declared length/velocity/support uncertainty), not a magic frequency.
Arrival measurements create revision 2 with instrument provenance;
revision 1 is never edited (tested; the A24 seller-promotion attack
is refused in code).

## Plant + identification (A08, A09)

2-DOF actuator+specimen model: perturb the specimen parameter and see
which peak moves — identity by response-to-perturbation, so a
transducer resonance cannot masquerade as a crystal resonance.
Nonlinearity is opt-in: a linear plant returns an EMPTY
intermodulation list, so the high-order arithmetic sums have nowhere
to hide. Fits refuse under-sampled linewidths and saturated peaks;
bootstrap gives Q intervals, not points.

## Optimizer (A10) — mechanism first, frontier not winner

Expected target amplitude comes from the A06 engine through the
plant, so `clock_sine_4096` (no 5th harmonic) and `highorder_mix`
(coincidence) score **zero** expected amplitude by construction — the
gate "a high-order arithmetic match cannot outrank a low-order
physically generated component" holds because arithmetic never enters
the amplitude at all. Pareto dominance runs within a hypothesis
(candidates answering different questions are not substitutes), so
the frontier spans the register: resonance-locked drives, the
4096-derived square, controls, and the null tests — with
`H-EQUIV-SPECTRUM-01`'s **matched target-component comparison** as
the decisive ordinary-physics control.

## Contracts + device + safety (A12, A19, A15-sim)

Recipes validate against a strict schema (jsonschema): out-of-profile
frequency, duty > 0.5, duration > limit, non-finite numbers, unknown
schema versions, and **missing amplitude** are refused — a segment
without an explicit amplitude would otherwise default to something,
and any default is the wrong answer on an actuation instrument.
Invalid JSON never reaches the output driver; it faults the device at
load.

The safety FSM: `BOOT_SAFE → SELF_TEST → SAFE_OFF → RECIPE_VALID →
ARMED → RUNNING → COOLDOWN`, with `FAULT_LATCHED` reachable from
everywhere and output legal ONLY in RUNNING. Arm leases are fresh,
single-use, expiring; there is no auto-arm; faults latch until
acknowledged while off; reset/watchdog/brownout lands output-off with
no authority resumed. All tested, including the sabotaged-recipe
mid-run timeout.

## Boards + backends (A14, A16)

"ESP32 CYD" is not a pin map: profiles for the 2432S028R and
2432S024C are registered as **candidates (verified=False)** from
community documentation, with boot-strap, input-only, and peripheral
pins mapped and a static conflict checker. UNKNOWN board ⇒
OUTPUT_DISABLED. Backends report requested vs **calculated realized**
frequency as exact rationals (LEDC Q10.8 divider, RMT ticks, DDS
phase increment) with `measured_realized_hz: None` until a real
measurement exists — the setpoint is never called exact.

## Firmware (A15)

`firmware/fkey_cyd/`: PlatformIO tree whose safety FSM mirrors the
tested Python twin line for line, with the board-profile gate at
compile time (`BOARD_VERIFIED` must be set by a human after the A14
self-test). **Status: FIRMWARE_SOURCE_PROVIDED / NOT_COMPILED — no
toolchain ran in this repository and no hardware exists.** The
simulator stub target documents the host-side check.

## Demos (A23)

Six demos, all simulator, all SYNTHETIC-labelled: relation census,
waveform distinction, nominal sweep + Q, optimizer + 4 compiled
recipes, full device cycle with intact hash-chained logs, and fault
refusal (overtemp / expired arm / pin conflict all fail off).

## Claim boundary (A25)

`SOFTWARE_GREEN, PHYSICAL_UNTESTED.` This lane ships mathematics,
schemas, a simulator, firmware source, and protocols. It does not
ship evidence that 4096 Hz does anything to a crystal, that the
specimen resonates at any particular frequency, or that any frequency
key has physical meaning. The near-20 kHz band is at the edge of
human hearing and within animal hearing: first bench runs use low
duty, short bursts, conservative amplitude, and nobody's ears next to
the fixture.

## First build sequence (when hardware exists — all human-only)

1. Complete the A14 questionnaire; run the self-test; verify a board
   profile.
2. Multimeter checks before power (A20 bring-up list); smoke-test
   recipe into a dummy load.
3. Campaigns C1–C2 (instrument + actuator characterization, no
   crystal).
4. On specimen arrival: measure, create revision 2, THEN campaigns
   C3–C4 (coarse/fine sweep) over the model's band.
5. C5: the decisive matched-component comparison (direct vs
   4096-derived).
