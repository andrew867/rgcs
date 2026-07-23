# R11 Findings, Limitations and Non-Claims

**Authority:** RGCS R11 / v6.0.0 (candidate)
**Scope:** the consolidated R11 result, every module verdict, the honest limitations, and the standing non-claims.
**Last verified commit:** v5.9.0 baseline (branch v590-r11)
**Prerequisites:** [R11_SPEC.md](R11_SPEC.md) — the other seven R11 documents expand individual rows of the table below.
**Related code / tests:** `r11/` (twelve modules), `tests/v6/` (thirteen test modules, 577 tests)
**Known limitations:** nothing in R11 is measured; no apparatus exists; hosted CI is unavailable, so the local suite is the verification of record.
**Next review trigger:** any measured dataset, any hardware, any change to a module verdict string, or the v6.0.0 release gate.

## The R11 final verdict

> **`R11_GREEN_MODELS_IMPLEMENTED_DECODER_NOT_IDENTIFIED`**

Green means the models are implemented and tested and the discipline held. It
does **not** mean anything was found. The two stronger-sounding alternatives are
defined and were not reached:
`R11_YELLOW_CANDIDATE_SURVIVES_HOLDOUT_NOT_PHYSICALLY_VALIDATED` (no candidate
survived a holdout) and `R11_RED_PRIVACY_IDENTIFIABILITY_OR_REGRESSION_FAILURE`
(no such failure occurred).

## Every verdict, as returned by the code

| Module | Verdict |
|---|---|
| `sources` | `SOURCES_REGISTERED_PRIVACY_RESIDUAL_DECLARED` |
| `planetroot` | `PLANETARY_ROOT_FRAMEWORK_SPECIFIABLE` |
| `earthface` | `EARTH_FACE_LOCAL_ZERO_SPECIFIABLE_WITH_ALIASES` |
| `shelladdr` | `MOVING_SHELL_SEQUENCE_RETAINED_WITHOUT_KINEMATICS` |
| `phasealpha` | `FRACTIONAL_PHASE_ALPHABET_SPECIFIABLE` |
| `carrier` | `CRYSTAL_CARRIER_CANDIDATE_ARITHMETIC_ONLY` |
| `isotope` | `CESIUM_BARIUM_EPOCH_STILL_NON_UNIQUE` |
| `dynboundary` | `TRUNCATED_PHOTON_IS_MULTIMODE_EM_STATE_NOT_NEW_PARTICLE` |
| `atomicarch` | `ATOMIC_ARCHITECTURE_MODEL_ONLY` |
| `orbitalscaling` | `ORBITAL_ATOMIC_SCALING_UNESTABLISHED` |
| `numcorpus` | `NUMERIC_CORPUS_AUDITED_NO_DECODER_IDENTIFIED` |
| `identifiability` | `NO_DECODER_IDENTIFIED` |

Not one of them asserts a positive physical finding. Six are explicitly
negative or null.

## Consolidated findings

**Positive findings (about the software and the arithmetic, not the world).**

- The nine-stage Earth-face pipeline is implementable end to end, and the
  South-Up view `diag(1, −1, −1)` is a **proper** rotation (det = +1), not a
  mirror — so handedness is preserved through the chain.
- The 42-bit envelope over the twelve-digit address round-trips exactly at 14
  octal digits, and the mixed-radix seven-field layout round-trips exactly. Both
  demonstrate the *frames* are faithful.
- The carrier chain reproduces exactly in rational arithmetic:
  13772.28 × 2/3 = 9181.52; residual to 9192 is 10.48; 63/6 = 10.5 exactly;
  9192 × 3/2 = 13788 exactly.
- Both benchmarks that could have been blind demonstrably are not: the carrier
  search recovers a planted expression at zero residual, and the decoder
  benchmark recovers planted labels at hit rate 1.0.
- All 21 corpus rows are retained with layout preserved and content-addressed;
  5 rows that refuse to parse are kept visible rather than dropped.

**Negative and null findings.**

- **A single quadratic channel cannot carry the four-symbol alphabet.** 240° and
  300° both map to cos² = 0.25; four symbols in, three values out.
  `SINGLE_QUADRATIC_CHANNEL_INSUFFICIENT`.
- **The crystal carrier is no better than chance.** Look-elsewhere p = 0.3455
  over a 2160-expression grid.
- **The source pack figure is wrong.** 13788 − 13772.28 = 15.72 Hz *above* the
  computed mode, not 0.03 Hz below — wrong in sign and by ~500× in magnitude.
  The code's value is adopted; the pack's is not.
- **No unique epoch.** Two ratio orientations give ages 10.92 y and 65.12 y, a
  54.2-year spread, and a second coherent carrier reduces the Cs-133 alias count
  from ~1.6e19 to ~1.7e10 without reaching one. `ALIASES_REDUCED_NOT_RESOLVED`.
- **No universal orbital mapping.** Out-of-sample error degrades 15.8×; fitted
  exponents span 1.03–2.14; the one system that beats its control
  (jovian_galilean, raw p = 0.0331) is an established Laplace resonance and
  fails Bonferroni correction (corrected p = 0.496).
- **No decoder.** On four matched nulls, no decoder family beats chance.
- **No universal anomaly circle.** Carried as `UNSUPPORTED` on every body.
- **No kinematics from the shell readings.** Timestamps are missing, so speed,
  orbit and ETA do not exist to be estimated.

## Limitations, stated honestly

1. **Nothing is measured.** Every R11 report carries
   `measured_here: "nothing"`. No magnetometer, no photon counter, no sample, no
   spectrum, no clock comparison, no site visit.
2. **No apparatus exists.** `dynboundary` reports
   `hardware_status: DEFERRED — no apparatus has been built`, and all eight of
   its required observables are `UNMEASURED`.
3. **Blocked data.** Published spherical-harmonic coefficient sets and crustal
   anomaly maps are `BLOCKED_MISSING_DATA`, so every planetary field grid is
   synthetic. The referenced 2026 photon paper (`SRC_TRUNCPHOTON`) is also
   `BLOCKED_MISSING_DATA` — it was **not** read or verified here. A
   formation-informed orbital model is likewise blocked.
4. **Toy field model.** The Earth-face field is a declared tilted-centred dipole
   in dimensionless model units, not a field value.
5. **Declared layouts, not decoded ones.** The mixed-radix field names and
   radices are the module's own invention. An exact round-trip says nothing
   about whether the address is organised that way.
6. **A declared privacy residual.** Identity strings for the alleged
   communicators exist in the public tree and in immutable history back to the
   frozen v2.0.0 baseline. Removal would require rewriting published history and
   re-cutting released tags, which release policy forbids. This is recorded as
   `DECLARED_RESIDUAL_EXPOSURE` by category — never by repeating the strings —
   and assessed LOW-MODERATE: no credential, location, medical or financial data
   is exposed. R11 adds no new identity strings; public modules use the neutral
   aliases only. A clean tree with the residual quietly excluded would not be an
   honest pass. See [R11_GATE_ZERO.md](R11_GATE_ZERO.md) for the start-state
   receipt in which condition 5 was waived and declared rather than dropped.
7. **The identifiability nulls are software controls, not field data.** No
   decoder beat chance on any null (random 12-digit strings, shuffled labels,
   random coordinates, held-out landmarks), and the power control fires
   cleanly on planted data — but every input is synthetic. The output space
   is an abstract unit index plane with no datum and no units, so nothing it
   produces can be read as a place.
8. **Hosted CI is unavailable.** Free-tier GitHub Actions minutes for this
   account are exhausted, so `.github/workflows/ci.yml` does not run for
   `v590-r11`. The local full-suite run on the exact commit — **577 passed** in
   ~104 s — is the verification of record. This is a real gap in independent
   reproduction, not a formality.

## NON-CLAIMS

Stated once, plainly, and binding on every R11 document:

- **No ship.** Nothing in R11 identifies, locates, characterises or implies a
  vehicle of any kind. The three shell readings are reported ranges with no
  clock.
- **No external transmission.** Nothing was sent or received. No channel was
  built. No symbol was ever read out.
- **No new particle.** A time-dependent boundary yields an electromagnetic
  quantum-field state. A photon is not divided into a fraction, and a field
  state is not a new particle species.
- **No decoded location.** No place is named, computed, or implied anywhere. The
  control site is a control; the held-out landmarks are abstract synthetic
  points on a unit index plane.
- **No unique epoch.** A phase is ambiguous modulo one cycle; a second carrier
  reduces the alias set without collapsing it. A six-digit year is forbidden.
- **No planetary terraforming system.** No root is located on any body, no
  universal anomaly circle is supported, and no mechanism of any kind is
  proposed for altering a planet.
- **No physical crystal effect.** No crystal carries, generates or locks to any
  frequency. No crystal, material, device or specimen is measured, identified or
  implicated. The two-channel model is `ANALOGY_ONLY_NO_MECHANISM_CLAIMED`.
- **No free energy.** The τ → 0 divergence is an unphysical idealization;
  created photons are paid for by work on the boundary.
- **No measurement, anywhere.** `PHYSICAL_VALIDATION_NOT_CLAIMED` on every
  module.

## What would change any of this

An independently computed mode a rational was not selected on; a look-elsewhere
p that survives the full grid; a physical mechanism that predicts a residual
instead of absorbing it; a real published magnetic-model coefficient set; a
timestamp on any shell reading; a signed, phase-sensitive readout channel that
actually exists; a bench measurement of any switched-boundary observable; and
restored hosted CI so that the suite is reproduced by someone other than the
author.

PHYSICAL_VALIDATION_NOT_CLAIMED
