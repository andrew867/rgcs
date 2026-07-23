# RGCS v5.8.0 — Release Notes

**Status:** `SOFTWARE_VERIFIED_PHYSICAL_UNTESTED`
**Baseline:** v5.7.0
**Licence:** MIT, unchanged. No relicensing.

R10.8: a handshake protocol, an EMI survey, a 13 MHz microcrystal model,
atomic-time standards, and the 1604/1644 numeric cues — all from a
private source session, all defaulting to a refusal or a null.

Everything here is arithmetic, conventional engineering, and software.
**No physical measurement was performed by this project.**

---

## The firewalls come first

The private session contained claims that would be dangerous if acted on:
alleged differential viral effects on hidden human groups, hidden hybrid
or genetically-modified populations, medical predictions, and investment
tips. [`r10/claimfirewall.py`](R10_8_FINDINGS.md) preserves each **as a
source record** and refuses to do anything more: it never classifies a
real person as nonhuman/hybrid/genetic, never infers biology from race/
geography/appearance/group, never produces pathogen or group-targeted
medical analysis, never gives medical advice, never accuses, and never
issues a financial action. Every quarantined claim is `UNSUPPORTED` and
promotion to any evidentiary status is refused.

Human exposure is prohibited throughout: the 925 Hz handshake
(`r10/handshake.py`) is a software state machine with **no** pineal,
brain, subliminal, RF, optical, acoustic, magnetic, or electrical
human-stimulation path. Grounding never overrides electrical safety
(`r10/txline.py`). Financial cues are validated only by blinded paper
trading with frozen rules and retained failures (`r10/prospective.py`).

## What R10.8 adds

Eighteen new `r10` modules (261 new tests):

- **Provenance:** `session` (append-only, source vs operator separation,
  raw text never public), `nolookahead` (self-report only), `numcue`
  (preregistered transforms/budget).
- **Cues:** `cue1604` — `1604 ≈ 925·√3` is **`APPROXIMATE_NOT_EXACT`**
  (~0.116% residual) and **`NO_BETTER_THAN_CHANCE`** under a look-elsewhere
  null (p ≈ 1.0); `1644 − 1604 = 40` with no meaning assigned.
- **Handshake:** `handshake` (925 Hz, ordered transitions, replay guard,
  timeout, checksum; opening key never in clear).
- **Engineering:** `microcrystal` (13 MHz BVD; refuses free-space
  wavelength in quartz), `multiframe` (exact closures **15.625 ms /
  40 ms / 1 s**), `timebase` (cesium **9 192 631 770 Hz** by definition,
  Allan deviation; live data blocked), `emisurvey` (blinded ABAB, three
  separate outcomes, measured data blocked), `txline` (reflection/SWR +
  protective-earth safety), `envlog` (stream sync; refuses unsynchronized
  correlation), `pcemi` (phase-conjugate refocus degrades monotonically
  under EMI).
- **Binding & comparison:** `routebind` (no retrofit), `memhandshake`
  (ordered/destructive read over the fading crystal), `extcompare`
  (publication-time discipline), `skycorr`
  (`UNIDENTIFIED_CORRELATION_ONLY`), `prospective` (preregistered
  holdouts, failures retained, paper-trading only).

## Verification

```bash
git clone https://github.com/andrew867/rgcs && cd rgcs
pip install -e ".[dev]"
pytest -q --deselect tests/regression/test_generator_determinism.py::test_generator_deterministic
# expect: 3340 passed
```

The deselected node is a byte-equality test requiring the archived v2.0.0
build environment (policy D-V3-04).

> **CI note.** The project's free-tier GitHub Actions minutes are
> exhausted, so this release was not built by hosted CI. The verification
> of record is the full local suite measured on the exact release commit
> (see `docs/v4/RELEASE_METADATA.json`); the clone-and-test recipe above
> reproduces it.

## What this release does not claim

- No apparatus, no emitted signal, no measured EMI, no opened channel, no
  human stimulation, no trade placed.
- No external communication source, hidden-species identity, medical
  effect, or financial signal is identified — none has prospective,
  discriminating evidence.
- The 1604/1644 cues carry no location, distance, route index, or
  meaning.
- No named person, session text, opening-key word, or CW vector digit
  enters the public tree; the session archive and quarantined claims are
  private and every quarantined claim is `UNSUPPORTED`.

## Not executed (deferred / blocked)

Measured EMI spectra and environmental captures, live atomic-time data,
apparatus/bench/mechanical source, prospective outcomes (nothing has
resolved), and real external-corpus ingestion — all deferred or
`BLOCKED_NO_DATA_SOURCE`.

See [R10_8_FINDINGS.md](R10_8_FINDINGS.md) for the full analysis.
