# Apparatus Architecture — Modeled Designs Only

**Authority:** RGCS R10.10 / v5.9.0 (candidate)
**Scope:** The *modeled* apparatus and experiment designs. No apparatus exists.
**Last verified commit:** v5.8.0 baseline (branch v580-r10-10)
**Prerequisites:** [ARCHITECTURE.md](ARCHITECTURE.md), [../../SCIENTIFIC_BOUNDARIES.md](../../SCIENTIFIC_BOUNDARIES.md)
**Related code / tests / schemas:** `r10/handshake.py`, `r10/emisurvey.py`, `r10/microcrystal.py`, `r10/pcemi.py`, `r10/txline.py`, `r10/timebase.py`
**Known limitations:** Everything here is software and paper. Every hardware step is BLOCKED or deferred.
**Next review trigger:** Acquisition of any physical specimen, instrument, or measured dataset.

## Read this first

**No apparatus has been built.** This document describes only the *designs that
have been modeled in software*. To be unambiguous:

- **No coil has been wound.**
- **No crystal has been driven, aligned, or excited.**
- **No signal has been emitted** on any RF, optical, acoustic, or electrical path.
- **No human has been stimulated or exposed** in any way.

## Modeled designs (all software / paper)

- **Natural-vs-synthetic quartz bench** — a matched-specimen protocol comparing
  natural and synthetic quartz. Synthetic quartz is the **mandatory control**.
  Specimens do not exist; the design is **BLOCKED_NO_SPECIMENS**. See
  [NATURAL_VS_SYNTHETIC_QUARTZ.md](NATURAL_VS_SYNTHETIC_QUARTZ.md).
- **EMI survey** (`r10/emisurvey.py`) — a blinded ABAB electromagnetic-interference
  survey. Measured spectra are **blocked**; only the analysis harness exists.
- **Handshake protocol** (`r10/handshake.py`) — a 925 Hz handshake modeled in
  software only, with **no pineal, brain, subliminal, RF, optical, acoustic, or
  electrical path** to any person.
- **13 MHz microcrystal model** (`r10/microcrystal.py`) — a Butterworth–Van Dyke
  equivalent-circuit model; refuses to invent a free-space wavelength in quartz.
- **Phase-conjugate return under EMI** (`r10/pcemi.py`) — ordinary DSP; refocus
  degrades monotonically under interference (a null, shown with power).
- **Transmission-line / grounding** (`r10/txline.py`) — grounding never overrides
  electrical safety.
- **Atomic-time / timebase** (`r10/timebase.py`) — the cesium definition and Allan
  deviation; **live atomic-time data is blocked**.

## Receipts

Every hardware-dependent step carries an explicit blocked/deferred receipt
(`BLOCKED_NO_SPECIMENS`, `BLOCKED_NO_DATA_SOURCE`, deferred hardware). None of
these is faked or filled with synthetic data presented as real. See the findings
records indexed in [DECISION_LOG_INDEX.md](DECISION_LOG_INDEX.md).

## Human-safety stance

Human exposure is **prohibited throughout**. The claim firewall
(`r10/claimfirewall.py`) refuses any group-targeted biological or medical
inference, and financial cues are paper-trading only.

PHYSICAL_VALIDATION_NOT_CLAIMED
