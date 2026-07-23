# Frequency and Phase System

**Authority:** RGCS R10.10 / v5.9.0 (candidate)
**Scope:** The frozen 4096 / 925 / 20.48 phase frames, exact multi-frequency gcd closures with 13 MHz, the SI time/frequency standards, and the 13 MHz quartz microcrystal as a circuit model.
**Last verified commit:** v5.8.0 baseline (branch v580-r10-10)
**Prerequisites:** [COORDINATE_SPACE.md](COORDINATE_SPACE.md) (epochs bind to frames); helpful: [CRYSTAL_SPECIMEN_PROGRAM.md](CRYSTAL_SPECIMEN_PROGRAM.md)
**Related code / tests / schemas:** [../../r10/phaseframes.py](../../r10/phaseframes.py), [../../r10/multiframe.py](../../r10/multiframe.py), [../../r10/timebase.py](../../r10/timebase.py), [../../r10/microcrystal.py](../../r10/microcrystal.py); tests/v52/test_r10_phaseframes.py, tests/v52/test_r10_multiframe.py, tests/v52/test_r10_timebase.py, tests/v52/test_r10_microcrystal.py
**Known limitations:** Frozen frequencies are **hypotheses** from the source delta, not measured signals. Closures are arithmetic, not physics. No frequency is generated, no crystal is driven, nothing is measured. Live timing data is **BLOCKED**. Hardware is deferred.
**Next review trigger:** A measured frequency or Allan deviation, a change to the frozen-frequency set, or any attempt to admit live data.

## Frozen phase frames (`phaseframes.py`)

A small set of ratios is frozen in the source delta and kept as exact
rational arithmetic (`Fraction`) so nothing rounds at a claim boundary.
Honesty is load-bearing at the "ratio match": the delta notes that

    q⁻¹ = 4096 / 925 = 4.428108…

is *close* to `8300 / 1876 = 4.424307…`. The module computes the residual
exactly — `1649/433825`, about **0.086%** — and refuses to report the two
as equal. A coincidence at the 1-in-1000 level is a coincidence, not an
identity.

## Exact multi-frequency closures (`multiframe.py`)

Four integer frequencies sit together in the source delta: **13 MHz**
(13 000 000 Hz), **4096 Hz**, **925 Hz**, and a **20.48 Hz** timebase that
is itself exactly `512/25 Hz`. The module computes, with exact
integer/rational arithmetic, *when* pairs and triples return to a common
phase:

    gcd(13 000 000, 4096) = 64  → the pair closes every 1/64 s = 15.625 ms
    gcd(13 000 000,  925) = 25  → the pair closes every 1/25 s = 40 ms
    gcd(13 000 000, 4096, 925) = 1 → all three close every 1 s exactly

The closure period is `Fraction(1, gcd(...))` seconds, never a rounded
decimal. These gcd closures earn verdict `PHASE_FRAME_EXACT`: they are
pure number theory saying integer frequencies share a beat period —
**nothing about physics.** A mixer sum/difference product is a weaker,
clearly-labelled claim, not an identity.

## SI standards (`timebase.py`)

The standards are quoted from their **primary definitions** (BIPM and the
national metrology institutes) precisely so they cannot be misread as
measurements this project made:

- Since 1967 the SI second is *defined* by the cesium-133 ground-state
  hyperfine transition at exactly **9 192 631 770 Hz**. That integer has
  **zero uncertainty by definition** — it is not a measured value with an
  error bar. A clock *realises* it; the realisation (a cesium fountain, or
  an optical standard) is where uncertainty lives.
- With `c` fixed at exactly 299 792 458 m/s, `λ = c/f` is exact **in
  vacuum**; a wavelength *in matter* is not free and is not computed as if
  it were.
- **Allan deviation** is the correct stability statistic for a clock, and
  the module models it — but **live data is BLOCKED**: no external timing
  feed is admitted.

## 13 MHz microcrystal (`microcrystal.py`)

The source material wants a "13 MHz crystal" to *mean* a distance, a
wavelength in the stone, or a resonance to point an antenna at. The module
refuses that leap and does the defensible thing: it writes down the
**Butterworth-Van Dyke (BVD)** equivalent circuit of a quartz
microcrystal resonator and works with it as a circuit model only. A
resonator's electrical resonance is not a coordinate and not a wavelength
in matter.

## Bottom line

Frozen frequencies are hypotheses; closures are arithmetic. The exact
periods above are number theory about a hypothesised set — not evidence
that any such signal exists or was observed. Epochs used here bind to
frames per [COORDINATE_SPACE.md](COORDINATE_SPACE.md).

PHYSICAL_VALIDATION_NOT_CLAIMED
