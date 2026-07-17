# RGCS v4.4.0 — release notes

**Frequency-Key Harmonic Excitation and ESP32-CYD Instrument.**

All prior tags (v2.0.0 … v4.3.0) are untouched.

## Claim boundary, first

**SOFTWARE_GREEN, PHYSICAL_UNTESTED.** The specimen is an eBay
listing (`SP-EBAY-137330949270-PREARRIVAL` — seller dimensions are
not measurements). No CYD board has been powered, no MOSFET wired, no
sound produced, no crystal measured. All six preregistered hypotheses
are `UNTESTED`. Every run artifact in this lane is SYNTHETIC and
carries the marker in its id, filename, manifest, and banner text.

## What ships

- **Exact relation engine** — `fractions.Fraction` arithmetic (floats
  refused), one primary mechanism class per relation, the frozen seed
  corpus classified as the pack requires: 4096×5 is a low-order
  HARMONIC; 8×2560 / 20.48×1000 / 40.96×500 are exact but
  PHASE_CLOSURE_ONLY; the mixed sums are ARITHMETIC_COINCIDENCE
  (orders 33 and 21) — a weighted sum of tones is not an emitted
  frequency in a linear system.
- **The key comparison, proven twice** — an ideal 4096 Hz sine has a
  zero fifth harmonic; an ideal 50% square carries one at exactly
  1/5 Fourier amplitude. Verified analytically AND by independent
  FFT; duty error measurably resurrects even harmonics.
- **Pre-arrival specimen model** — quarter-wave 20278.959 Hz /
  half-wave 40557.918 Hz from seller claims + an assumed isotropic
  velocity; correction FK-CORR-001 (the two target errors are ONE
  v/L ratio); a search band, never a magic frequency; arrival
  measurements create a new revision, the old one is immutable.
- **Mechanism-first optimizer** — arithmetic coincidences and
  sine-"harmonics" score zero expected amplitude by construction;
  the Pareto frontier spans the hypothesis register (a sham is not a
  substitute for a resonance tone); randomized blinded campaigns
  with the decisive matched-target-component control
  (H-EQUIV-SPECTRUM-01) and a declared no-post-hoc-frequency rule.
- **Fail-off instrument twin** — strict JSON contracts (a segment
  without an explicit amplitude is REFUSED); safety FSM with fresh
  single-use expiring arm leases, no auto-arm, 14 latching fault
  causes, reset-lands-output-off; hash-chained logs; pin-conflict
  detection; UNKNOWN board ⇒ OUTPUT_DISABLED; LEDC/RMT/DDS realized
  frequencies as exact rationals with `measured: None` until a real
  measurement exists.
- **Firmware source** (`firmware/fkey_cyd/`, PlatformIO) mirroring
  the tested twin — **NOT compiled in this repository** (no
  toolchain, no hardware); board envs default to output-disabled
  until a human verifies the A14 self-test.
- **Six demos**, all simulator, all SYNTHETIC
  ([report](fkey/SYNTHETIC_demo_report.md)); **46 FK coverage
  requirements** with bidirectional orphan checks; the A24 red-team
  attacks as executable regressions.

## Blockers (human-only)

Board purchase + variant verification (A14 questionnaire), Gen-0 BOM
procurement and bring-up (multimeter before power), specimen arrival
measurement, and any physical campaign. The near-20 kHz band is
audible to young ears and animals: first runs are low-duty, short,
conservative, and not near anyone's head.

## Verify

```bash
python -m pytest -q --deselect tests/regression/test_generator_determinism.py::test_generator_deterministic
# expect: 916 passed
python tools/v44_coverage.py         # 46 FK requirements
python tools/v44_demo_campaigns.py   # six SYNTHETIC demos
python tools/qa_audit_v4.py --fast   # 19/19
```
