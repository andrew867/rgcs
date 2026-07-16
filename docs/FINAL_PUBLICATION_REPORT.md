# Final Publication Report (Agent 15)

**Date:** 2026-07-16. The closing assessment of the publication
programme, written after a fresh external-researcher review pass.

## 1. Repository state

- **Public**: https://github.com/andrew867/rgcs — MIT detected,
  CITATION.cff detected, 13 topics, issues on, branch protection with
  7 required checks, latest CI **green** (ubuntu/windows/macos ×
  Python 3.11/3.13 + pinned reference).
- **Tags**: `v2.0.0` (frozen baseline, immutable), `v3.0.0-rc1`,
  `v3.0.0` (release, at a fully green commit). No tag ever rewritten.
- **Release v3.0.0**: 9 assets, published, sizes verified byte-equal
  after upload, checksums in `SHA256SUMS.txt`, one documented asset
  refresh (figure-rendering fix D-V3-05/06) noted in the release body;
  source zip byte-identical to the tag throughout.

## 2. Verification results (this pass)

| Check | Result |
|---|---|
| Release assets present/final (not draft/pre) | ✅ 9 assets |
| README (badges, honest scope, quick start, figures) | ✅ renders; images render; math legends fixed and verified |
| Contributor docs | ✅ 7 root docs + `docs/README.md` index + `CONTRIBUTOR_ROADMAP.md` (new) |
| Citations | ✅ CITATION.cff v3.0.0; manuscripts 0 undefined refs; QA-D-02 closed |
| Manuscripts | ✅ 4 PDFs + sources + per-manuscript checksums; 0 overfull; generated numbers only |
| Release notes | ✅ final wording, 12-gate table all GREEN, honest limitations |
| DOI readiness | ✅ `.zenodo.json` (machine) + `docs/ZENODO_METADATA.md` (human) + `DOI_RELEASE_GUIDE.md`; **no DOI invented** |
| Reproducibility | ✅ suite 378 tests (377 portable everywhere + archived-env byte test); regeneration byte-stable; PROVENANCE.json |
| Build instructions | ✅ README quick start + per-manuscript BUILD.md + CI as executable documentation |

## 3. Completeness assessments

**Documentation: complete** for its stage — orientation (README/FAQ),
discipline (DESIGN_PHILOSOPHY, CONTRIBUTING), history
(RESEARCH_HISTORY, Historical Companion), operations (lab/calibration/
protocol/pipeline/validation set), governance (registers), publication
(communication kit, Zenodo metadata, roadmaps).

**Software maturity: stable research framework.** Frozen mathematics;
append-only registries; conservative-extension guarantee machine-tested;
three-OS CI; deterministic artifacts. Not shipped by design: desktop
panels (T2), FEM import (T3), firmware (T4/T5) — contracts published,
tests waiting.

**Remaining engineering work** (tracked, non-blocking):
T2–T5 tranches; GPU/inference tiers per `MODELLING_ROADMAP.md`;
platform packaging. All governed by the §0 invariants (CPU oracle,
reproducibility, typed I/O, classification).

**Remaining scientific work** (the actual frontier): execute the bench
campaign — Phase 0 gates (H-29/H-30) first, then Phases I–IV per
`VALIDATION_PLAN.md`; independent replication; dataset contributions.
Nothing physical is confirmed today, several rows are pre-registered
nulls, and the campaign's honesty criterion is on the record.

## 4. Community-release package (this commit)

`.zenodo.json` · `docs/ZENODO_METADATA.md` · `docs/community/`
(press summary, community announcement, forum post, reddit post,
LinkedIn post, email announcement, release FAQ) ·
`docs/CONTRIBUTOR_ROADMAP.md` · `docs/MODELLING_ROADMAP.md` · this
report. Every piece states, in its own register's voice: what RGCS is,
what it is not, the current evidence, the current limitations, and how
to contribute — with negative results as first-class contributions.

## 5. Blockers

None. The single outstanding *manual* action is external to the
repository: publish/verify the Zenodo record for the v3.0.0 release
(integration is enabled; metadata is staged in `.zenodo.json`), then
make the post-DOI follow-up commit per the checklist in
`ZENODO_METADATA.md`. Publication itself is not gated on it.

## 6. Recommendation

**PUBLISH COMPLETE**
