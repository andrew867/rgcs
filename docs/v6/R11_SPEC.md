# R11 Specification — What the R11 Modules Implement

**Authority:** RGCS R11 / v6.0.0 (candidate)
**Scope:** the per-module scope of the R11 layer, its verdict strings, and what each module refuses.
**Last verified commit:** v5.9.0 baseline (branch v590-r11)
**Prerequisites:** [R11_GATE_ZERO.md](R11_GATE_ZERO.md) — the start-state receipt this layer was built on.
**Related code / tests:** `r11/` (all twelve modules), `tests/v6/` (thirteen test modules, 577 tests)
**Known limitations:** every module is arithmetic, literature values and software. Nothing in R11 measures anything, and no apparatus exists.
**Next review trigger:** a new R11 module, a changed verdict string, or the arrival of any measured dataset.

## What R11 is

R11 is a layer of twelve Python modules under `r11/`, each of which takes one
strand of the incoming material, implements it honestly, and then states in a
typed verdict what the implementation does **not** license. The layer's own
standing result is:

> **`R11_GREEN_MODELS_IMPLEMENTED_DECODER_NOT_IDENTIFIED`**

Models are implemented and tested; no decoder is identified. That is the
strongest sentence R11 is permitted to emit.

## Module map, with the verdict each one actually returns

Verdict strings below were read from the running code on the `v590-r11`
branch, not transcribed from a plan.

| Module | Docstring tag | Verdict string returned by its `*_report()` |
|---|---|---|
| `r11/sources.py` | A01 | `SOURCES_REGISTERED_PRIVACY_RESIDUAL_DECLARED` |
| `r11/planetroot.py` | P02 | `PLANETARY_ROOT_FRAMEWORK_SPECIFIABLE` |
| `r11/earthface.py` | P03 | `EARTH_FACE_LOCAL_ZERO_SPECIFIABLE_WITH_ALIASES` |
| `r11/shelladdr.py` | R11 | `MOVING_SHELL_SEQUENCE_RETAINED_WITHOUT_KINEMATICS` |
| `r11/phasealpha.py` | P01 | `FRACTIONAL_PHASE_ALPHABET_SPECIFIABLE` |
| `r11/carrier.py` | P06 | `CRYSTAL_CARRIER_CANDIDATE_ARITHMETIC_ONLY` |
| `r11/isotope.py` | P06 | `CESIUM_BARIUM_EPOCH_STILL_NON_UNIQUE` |
| `r11/dynboundary.py` | P08 | `TRUNCATED_PHOTON_IS_MULTIMODE_EM_STATE_NOT_NEW_PARTICLE` |
| `r11/atomicarch.py` | P09 | `ATOMIC_ARCHITECTURE_MODEL_ONLY` |
| `r11/orbitalscaling.py` | R11 | `ORBITAL_ATOMIC_SCALING_UNESTABLISHED` |
| `r11/numcorpus.py` | P0N | `NUMERIC_CORPUS_AUDITED_NO_DECODER_IDENTIFIED` |
| `r11/identifiability.py` | R11 | `NO_DECODER_IDENTIFIED` |

`r11/dynboundary.py` exposes three report functions — `dynboundary_report()`,
`divergence_report()` and `observables_report()`. The other modules expose one
each, named `<module>_report()`.

## Per-module scope, in one line each

- **`sources`** — 14 registered sources, 13 traced equations, one `BLOCKED_MISSING_DATA`
  source (`SRC_TRUNCPHOTON`), a privacy scan over the public tree, and one
  `DECLARED_RESIDUAL_EXPOSURE` that is declared rather than quietly excluded.
- **`planetroot`** — six bodies across five field classes, seven competing root
  constructions (one a magnetism-free null control), a preregistered circularity
  test, and an epoch requirement. `PLANETARY_ROOT_CANDIDATE_A`.
- **`earthface`** — the geodetic → ITRF → ECEF → South-Up → city-ray →
  frozen-icosahedron-face → local-frame → gradient-zero pipeline, whose honest
  output is an alias set. `SEDONA_FACE_CONTROL` is the control site.
- **`shelladdr`** — three range readings of `MOVING_SHELL_SEQUENCE_A` with
  timestamps explicitly missing, plus lossless and lossy envelopes over one
  twelve-digit address.
- **`phasealpha`** — the four-fraction alphabet `PHASE_ALPHABET_A`, exact
  rational arithmetic, the spin-versus-phase distinction, and a negative result
  about single-quadratic-channel readout.
- **`carrier`** — the `CRYSTAL_CARRIER_CANDIDATE_A` audit, its target-fitting
  flag, a look-elsewhere null, a power control, and a discrepancy found in the
  source pack.
- **`isotope`** — Cs-133 (a frequency **definition**) and Cs-137 (a decay
  **statistic**) typed apart, a coarse-age model with seven mandatory
  declarations, and `ISOTOPE_RATIO_CANDIDATE_A` audited in both orientations.
- **`dynboundary`** — a Bogoliubov treatment of a time-dependent boundary,
  under the alias `TRUNCATED_PHOTON_REFERENCE_A` and the candidate label
  `DYNAMIC_BOUNDARY_MULTIMODE_STATE_CANDIDATE`.
- **`atomicarch`** — the atomic frequency standard as a typed ten-stage chain,
  Rabi and Ramsey physics, a hydrogen-maser error budget, and a two-channel
  analogy with six stated failure boundaries.
- **`orbitalscaling`** — five scaling families plus a random order-statistic
  control across three systems, with out-of-sample transfer and a Bonferroni
  correction.
- **`numcorpus`** — 21 corpus rows retained as strings with the layout
  preserved and content-addressed (`corpus_hash` =
  `cc870d6baed08e6e6b6ca31aed108f7a1a94f94567babeb2480a7331f7337306`),
  5 rows retained unparsed.
- **`identifiability`** — freeze-before-reveal over 16 fields, six decoder
  families, five controls, alias sets and description lengths, and an
  unconditional refusal of any decoded-location verdict.

## The invariants every module holds

Each report carries `measured_here: "nothing"` and
`physical_validation: "PHYSICAL_VALIDATION_NOT_CLAIMED"`;
`tests/v6/test_r11_redteam.py::test_nothing_in_r11_claims_a_measurement`
asserts both across ten of the modules. Each module also exposes at least one
named refusal function that raises a typed error rather than returning a
plausible number.

## Verification of record

`.venv/Scripts/python.exe -m pytest tests/v6 -q` on the `v590-r11` branch:
**577 passed** (~85 s). Distribution: identifiability 120, planetroot 62,
orbitalscaling 50, shelladdr 45, earthface 44, dynboundary 40,
atomicarch 38, isotope 38, phasealpha 37, numcorpus 35, carrier 29,
redteam 24, sources 15 — thirteen test modules, summing to 577.

Hosted CI is **unavailable** — the free-tier GitHub Actions minutes for this
account are exhausted, so `.github/workflows/ci.yml` does not run for this
branch. The local full-suite run on the exact commit is therefore the
verification of record, and this document says so rather than implying a green
badge that does not exist.

## Known discrepancies against the R11 plan

1. Gate Zero condition 5 (no alleged-communicator identity in the tree **or
   Git history**) could not be satisfied: the strings sit in immutable
   history back to the frozen v2.0.0 baseline. It is **waived and declared**
   as a `DECLARED_RESIDUAL_EXPOSURE`, not dropped, and R11 adds no new
   identity strings. See `R11_GATE_ZERO.md`.
2. `r11/carrier.py` reports that the source pack's "0.03 Hz below" figure is
   wrong in sign and by a factor of about 500; the code's value of 15.72 Hz is
   the one adopted. See `R11_CARRIER_AND_ISOTOPE_REPORT.md`.
3. `r11/orbitalscaling.py` is not a uniform null: one of three systems returns
   `TIGHTER_THAN_CHANCE` before the look-elsewhere correction. See
   `R11_PHOTON_AND_SCALING_REPORT.md`.

## Standing non-claims

No ship. No external transmission. No new particle. No decoded location. No
unique epoch. No planetary terraforming system. No physical crystal effect.

PHYSICAL_VALIDATION_NOT_CLAIMED
