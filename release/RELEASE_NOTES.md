# RGCS v3.0.1 / RSCS 1.0 — Release Notes

*(v3.0.1 is an archival/community patch over the v3.0.0 scientific
baseline: figure-rendering fixes D-V3-05/06, the laboratory validation
campaign, and the Zenodo/community package. No mathematical change.)*

**Date:** 2026-07-16. **License:** MIT. **Baseline:** RGCS v2.0.0 (tag
`v2.0.0`, `archive/v2.0.0/` — byte-identical, never modified).
**Repository:** https://github.com/andrew867/rgcs

## What this release is

A reproducible research framework, not an experimental result. It
contains the RSCS 1.0 typed coordinate/operator framework (17
coordinates, 23 operators, machine-checked provenance and a
conservative-extension guarantee over the frozen v2 mathematics), the
expanded crystal application (anisotropic Christoffel propagation,
optical probe layer, node menu), a synchronized coil/laser timing
architecture with a binding safety envelope, a desktop/embedded platform
tranche with cross-platform CI, four generated-number manuscripts, and a
pre-registered falsification programme (claims H-01..H-30). **No physical
hypothesis of the programme has been experimentally confirmed**, and
several directional claims are pre-registered *nulls*.

## Cross-platform evidence (hosted CI, all green)

GitHub Actions matrix on the release lineage: **ubuntu / windows / macos
× Python 3.11 / 3.13** (portable tier: 377 tests each) plus a pinned
**ubuntu reference job** (numpy/scipy pinned to the golden-generation
versions, release-builder smoke). Determinism policy (NR3-001 →
D-V3-04): golden datasets are regenerated and verified **on every
platform** by a tolerance-aware equivalence test (string cells and
headers exact; numeric cells within one unit of the printed precision);
byte-exactness of the shipped goldens is an archival property of the v2
build environment, verified at v2 release and recorded by checksum.

## Quality-gate table

| # | Gate | Verdict | Evidence |
|---|---|---|---|
| 1 | Baseline integrity | **GREEN** | archive/v2.0.0 byte-identical (verified every stage); migration map explicit |
| 2 | Notation & dimensional integrity | **GREEN** | 40 RSCS ids with units/manifolds/tests; frozen ledger; unit-suffixed identifiers |
| 3 | Claim integrity | **GREEN** | five-class labels machine-linted; firewall tests; CLAIM_AUDIT_V3 |
| 4 | Reference integrity | **GREEN** | EP-* page/equation provenance re-hashed by adversarial lint; QA-D-02 closed |
| 5 | Model integrity | **GREEN** | typed coordinates, round-trip/inverse tests, singularity handling |
| 6 | Application integrity | **GREEN** | adaptation/exclusion matrices; forbidden transfers binding; reciprocity null posture (D6-003) |
| 7 | Experiment integrity | **GREEN** | every HYP row has observable/controls/uncertainty/failure condition |
| 8 | Software integrity | **GREEN** | hosted CI matrix all green (3 OS × 2 Python + pinned reference); deterministic artifacts; portable regeneration test on every platform |
| 9 | Manuscript integrity | **GREEN** | 4× XeLaTeX clean: 0 undefined refs, 0 overfull boxes; all numbers generated |
| 10 | Release integrity | **GREEN** | source zip, manuscript bundle, sample experiments, SHA256SUMS, PROVENANCE.json, these notes |
| 11 | Safety integrity | **GREEN** | D6/D7 envelopes in schemas/firmware contract; dummy-load-first; no human exposure representable |
| 12 | Historical integrity | **GREEN** | companion preserves corpus + authors + contradictions; negative results registered |

**Overall: GREEN.**

## Known limitations (honest list)

1. **No bench data:** claims H-20..H-30 await hardware; nothing physical
   is confirmed (see the project's Honest scope).
2. **Source release only:** this release contains source and
   cross-platform-tested functionality, not packaged desktop binaries
   (the v2 Linux binary remains in the v2 archive; Windows/macOS
   packaging instructions ship as documentation).
3. **Desktop panels (T2), FEA import (T3), firmware (T4), and timing
   hardware (T5)** are contracts and tested headless services; all
   hardware is ENG until built and measured.
4. **Byte-exact golden reproduction** requires the archived v2 build
   environment (toolchain/libm-sensitive); every platform verifies
   numerical equivalence to the printed precision instead (D-V3-04).
5. The four v3 manuscripts are concise generated-number spines
   (3–5 pp.) over the fuller repository documentation.

## Artifact inventory

See `SHA256SUMS.txt` for checksums and `PROVENANCE.json` for the release
commit, environment, and test evidence.

- `rgcs-v3.0.1-source.zip` — full source at the release commit
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
