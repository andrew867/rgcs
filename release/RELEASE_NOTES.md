# RGCS v3.0.0-rc1 / RSCS 1.0 — Release Notes

**Date:** 2026-07-15. **License:** MIT. **Baseline:** RGCS v2.0.0 (tag
`v2.0.0`, `archive/v2.0.0/` — byte-identical, never modified).

## What this release is

A reproducible research framework, not an experimental result. It
contains the RSCS 1.0 typed coordinate/operator framework (17
coordinates, 23 operators, machine-checked provenance and a
conservative-extension guarantee over the frozen v2 mathematics), the
expanded crystal application (anisotropic Christoffel propagation,
optical probe layer, node menu), a synchronized coil/laser timing
architecture with a binding safety envelope, a desktop/embedded platform
tranche with Windows portability fixes and two-OS CI, four
generated-number manuscripts, and a pre-registered falsification
programme (claims H-01..H-30). **No physical hypothesis of the programme
has been experimentally confirmed**, and several directional claims are
pre-registered *nulls*.

## Quality-gate table

| # | Gate | Verdict | Evidence |
|---|---|---|---|
| 1 | Baseline integrity | **GREEN** | archive/v2.0.0 byte-identical (verified every agent); migration map explicit |
| 2 | Notation & dimensional integrity | **GREEN** | 40 RSCS ids with units/manifolds/tests; frozen ledger; unit-suffixed identifiers |
| 3 | Claim integrity | **GREEN** | five-class labels machine-linted; firewall tests; CLAIM_AUDIT_V3 |
| 4 | Reference integrity | **GREEN** | EP-* page/equation provenance re-hashed by adversarial lint; QA-D-02 closed |
| 5 | Model integrity | **GREEN** | typed coordinates, round-trip/inverse tests, singularity handling (D3-009/013) |
| 6 | Application integrity | **GREEN** | adaptation/exclusion matrices; forbidden transfers binding; reciprocity null posture (D6-003) |
| 7 | Experiment integrity | **GREEN** | every HYP row has observable/controls/uncertainty/failure condition |
| 8 | Software integrity | **GREEN\*** | 376 passed / 1 documented inherited failure (NR3-001); deterministic artifacts verified. \*Linux CI legs defined but not yet executed (limitation 2) |
| 9 | Manuscript integrity | **GREEN** | 4× XeLaTeX clean: 0 undefined refs, 0 overfull boxes; all numbers generated |
| 10 | Release integrity | **GREEN** | source zip, manuscript bundle, sample experiments, SHA256SUMS, PROVENANCE.json, these notes |
| 11 | Safety integrity | **GREEN** | D6/D7 envelopes in schemas/firmware contract; dummy-load-first; no human exposure representable |
| 12 | Historical integrity | **GREEN** | companion preserves corpus + authors + contradictions; negative results registered |

**Overall: GREEN for a release candidate.** Final `3.0.0` is gated on
limitation 2 (a green Linux CI run) and requires no other known work.

## Known limitations (honest list)

1. **NR3-001 (inherited):** one golden CSV is byte-exact only on the
   Linux reference platform; semantics are tolerance-checked everywhere
   (deselected in Windows CI with documented justification).
2. **Linux execution gap:** the CI matrix (Linux+Windows × Py3.11/3.13)
   is defined but this release was verified on Windows; the Linux legs
   have not yet run.
3. **Desktop panels (T2), FEA import scripts (T3), firmware (T4), and
   timing hardware (T5)** are contracts and tested headless services,
   not shipped UI/firmware/hardware; all hardware is ENG until measured.
4. **No bench data:** claims H-20..H-30 await hardware; the v2 negative
   results and calibrations remain the only measurement record.
5. **Manuscripts are concise generated-number spines** (3–5 pp each)
   over the fuller repository documentation, by design at this stage.
6. `latexmk` requires perl (absent on the build machine); BUILD.md
   documents the direct xelatex/bibtex sequence.

## Artifact inventory

See `SHA256SUMS.txt` for checksums and `PROVENANCE.json` for the release
commit, environment, and test evidence.

- `rgcs-v3.0.0-rc1-source.zip` — full source at the release commit
- `rgcs_v3_manuscripts.zip` — 4 PDFs + TeX + generated tables/figures +
  per-manuscript checksums/build docs
- `rgcs_v3_sample_experiments.zip` — 13 JSON schemas + validated example
  manifests (incl. optical probe + timing programme) + sample data
- `PROVENANCE.json`, `SHA256SUMS.txt`, `RELEASE_NOTES.md`

## Recommended public wording

> RGCS v3 / RSCS 1.0 is a reproducible modelling, experiment-design, and
> falsification framework for resonance studies in engineered quartz
> geometries. It provides typed, provenance-checked mathematics; tested
> conservative extensions of its frozen v2 baseline; safety-bounded
> experiment schemas; and four fully generated manuscripts. It makes no
> confirmed physical claims: every hypothesis ships with an observable,
> controls, and a pre-registered failure condition — several as expected
> nulls. The strongest result of the project so far is methodological:
> a demonstration that unconventional source material can be preserved
> faithfully and tested honestly without becoming evidence by repetition.
