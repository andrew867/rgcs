# R11 Identifiability and Red Team

**Authority:** RGCS R11 / v6.0.0 (candidate)
**Scope:** freeze-before-reveal, the six decoder families, the benchmark nulls, and the sixteen red-team attacks.
**Last verified commit:** v5.9.0 baseline (branch v590-r11)
**Prerequisites:** [R11_SPEC.md](R11_SPEC.md), [R11_SHELL_AND_CODEC_REPORT.md](R11_SHELL_AND_CODEC_REPORT.md), [R11_EARTH_FACE_AND_MAGNETIC_ZERO.md](R11_EARTH_FACE_AND_MAGNETIC_ZERO.md)
**Related code / tests:** `r11/identifiability.py`, `tests/v6/test_r11_redteam.py` (24 tests)
**Known limitations:** every input is synthetic — the output space is an abstract unit index plane with no datum and no units, and the held-out landmarks are seeded synthetic points. No geography is present anywhere in the module, so nothing it produces can be read as a place.
**Next review trigger:** a new decoder family, a change to the sixteen frozen fields, or the addition of a dedicated identifiability test module.

## Verdict

`r11.identifiability.identifiability_report()["verdict"]` returns:

> **`NO_DECODER_IDENTIFIED`**

which is a statement about *this search*, not about what is possible. It is
explicitly **not** `NO_DECODER_POSSIBLE`.

## Why no decoded-location verdict is allowed

Every other R11 module produces one *piece* of a would-be decoder: a planetary
root, a body-fixed frame, a south-up face, a gradient scalar and sign, a codec,
a header, a shell-state map, a phase alphabet, an isotope orientation, a
crystal carrier. Bolting them together in some order and reading off a place is
the obvious next move, and this module exists to make it impossible.

Count the freedom: sixteen fields, each a choice; a tolerance, a continuous
knob; and a score function that decides what "close" means. Their product is a
search space large enough that *something* lands near *somewhere* essentially
always. A place reached by picking the settings that reach it is not a decoding
— it is the search space being reported as a result. Worse, the arrival feels
like evidence: the coordinates are specific, the arithmetic is exact, and the
chain reads forward as if derived rather than selected.

`refuse_decoded_location_verdict` therefore raises **unconditionally** — not
when the fit is poor, not when the freeze is missing, always.

## The sixteen frozen fields

`planetary_body`, `body_fixed_frame`, `body_root`, `magnetic_model`,
`magnetic_epoch`, `face_orientation`, `gradient_scalar`, `gradient_sign`,
`codec`, `header`, `shell_state_map`, `phase_alphabet`,
`isotope_ratio_orientation`, `crystal_carrier`, `tolerance`, `score_function`.

`DecoderSpec` freezes all sixteen; `freeze()` returns a sha256 commitment over
them; `refuse_unfrozen_evaluation` blocks scoring an uncommitted decoder; and
`refuse_spec_change_after_reveal` blocks the quiet edit ("the epoch was
obviously 2020", "the sign must be negative") that turns a failed decoder into
a successful one once holdout labels are visible.

## The six decoder families

`DIRECT_GEOGRAPHIC`, `SOUTH_POLAR`, `HEDRON_LOCAL`, `ENVELOPE_42BIT`,
`ENVELOPE_36BIT`, `MIXED_RADIX` — with 2, 2, 6, 4, 8 and 3 admissible branches
respectively. All six default decoders are frozen (`all_defaults_frozen:
true`).

## The two deliverables that are not answers

**An ALIAS SET.** `alias_set()` never returns a unique answer. The worked
example: `DECODER_ENVELOPE_36BIT` at tolerance 0.05 admits **126** candidates
across all eight branches. The report's stated reason is that the 36-bit
envelope truncates three high bits of a 39-bit address, so eight inputs share
every surviving code — *"this ambiguity is a property of the frame, not of the
reader's indecision."* Freezing the rest of the spec cannot restore erased bits.

**A DESCRIPTION LENGTH.** A field frozen in advance costs only its commitment
(1 bit); a field left free costs its whole search width, because it will be
chosen after the data are in view. Measured: a tightly frozen decoder costs
**16 bits**; the same decoder with many free choices costs **81 bits**.
`free_costs_more: true`. A match found by a decoder with many free choices is
worth correspondingly less.

## The benchmark: power control and four nulls

Defaults: 160 trials, seed 20260723, tolerance 0.02, better-than-chance margin
0.15, alias tolerance 0.05.

**Power control (PLANTED).** Vectors from a known generator in the
`DIRECT_GEOGRAPHIC` family. `DECODER_DIRECT_GEOGRAPHIC` recovers them at hit
rate **1.0** while the worst null stays at **0.0**;
`other_families_better_than_chance` is empty; `detected: true`. The benchmark
has the power to detect a decoder that is really present.

**Four nulls** — `random_coordinates`, `random_digit_strings`,
`shuffled_labels`, `heldout_landmarks` (eight synthetic
`HOLDOUT_REFERENCE_nn` points on an abstract unit index plane). On every one of
them, `better_than_chance` is **empty** and `any_decoder_beat_chance` is
**false**. Observed hit rates on the nulls sit at 0.0 to 0.00625, i.e. at or
below one hit in 160.

That the benchmark detects nothing outside the planted case is a finding, not
blindness — the power control is what makes that sentence sayable.

## The sixteen red-team attacks

Each attack is executed against the real module API, not merely described. A
refusal that is only a docstring is not a refusal. All 24 collected tests in
`tests/v6/test_r11_redteam.py` pass.

| # | Attack | Fails with |
|---|---|---|
| 1 | rotate the frozen solid after seeing targets | `EarthFaceError` (`refuse_rotate_after_load`) |
| 2 | choose the magnetic scalar target-by-target | `EarthFaceError` + `PlanetRootError` (`refuse_target_dependent_selection`) |
| 3 | reverse the gradient sign target-by-target | `EarthFaceError`; also asserts >1 alias survives |
| 4 | read decimal digits as octal | `ShellAddrError` (`refuse_decimal_digits_as_octal`) |
| 5 | present a lossy envelope as lossless | `ShellAddrError` (`refuse_lossy_as_lossless`) |
| 6 | reorder the shell observations | `ShellAddrError` (`refuse_reordering`) |
| 7 | invent timestamps, then speed / orbit / ETA | `ShellAddrError` ×3 (`refuse_speed`, `refuse_orbit`, `refuse_eta`) |
| 8 | pick the isotope orientation that yields a nicer year | `IsotopeError` (`refuse_orientation_chosen_from_desired_year`) |
| 9 | select the crystal mode after seeing 9192 | `CarrierError` (`refuse_carrier_selected_after_target`) |
| 10 | add an arbitrary correction to force closure | `CarrierError`; also asserts `target_fitted is True` |
| 11 | equate degrees, hertz, microtesla or miles by number alone | `PhaseAlphaError` (`refuse_unit_confusion`); same-unit comparison still allowed |
| 12 | treat nuclear spin 7/2 as the phase fraction 7/2 | `PhaseAlphaError` + `IsotopeError` |
| 13 | call destructive interference a broken photon | `DynBoundaryError` ×3 (interference, fractional photon, new particle) |
| 14 | call the instantaneous divergence free infinite energy | `DynBoundaryError` ×3, including `expected_photon_number(0.0)` |
| 15 | use an Earth dynamo root on a body without one | `PlanetRootError` for MARS, MOON, VENUS; plus 15b, no surface on a gas giant |
| 16 | leak private provenance into the public tree or history | `SourceError` ×2 (`refuse_private_delta_read`, `refuse_new_identity_exposure`) |

Attack 16b additionally runs `sources.privacy_scan` over the public tree and
asserts `committed_clean`, an empty `history_serious` list, and that the
residual is reported as `DECLARED_RESIDUAL_EXPOSURE` rather than silently
excluded.

### Cross-cutting standing refusals

Four further tests sit outside the numbered attacks: no decoded-location verdict
anywhere (`IdentifiabilityError`); retired sequences cannot return
(`CorpusError`); a storage bulb is not an oscillator and two coils are not a
state selector (`AtomicArchError` ×2); and nothing in R11 claims a measurement —
asserted across ten modules by checking `measured_here == "nothing"` and
`physical_validation == "PHYSICAL_VALIDATION_NOT_CLAIMED"`.

## Verification of record

Hosted CI is **unavailable**: the free-tier GitHub Actions minutes for this
account are exhausted, so `.github/workflows/ci.yml` does not run for the
`v590-r11` branch. The local full-suite run on the exact commit —
**577 passed** across `tests/v6` — is therefore the verification of record.

## Non-claims

No decoder is identified. No location is decoded, named, computed, or implied.
No ship, no external transmission, no new particle, no unique epoch, no
planetary terraforming system, and no physical crystal effect. The R11 final
verdict is **`R11_GREEN_MODELS_IMPLEMENTED_DECODER_NOT_IDENTIFIED`**.

PHYSICAL_VALIDATION_NOT_CLAIMED
