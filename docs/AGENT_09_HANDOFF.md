# Agent 09 Handoff — Manuscripts and Public Documentation

**Date:** 2026-07-15. **Status: COMPLETE, GREEN.** Consumers: Agent 10
(QA — including manuscript layout re-check), Agent 11 (release
regeneration + bundles).

## Deliverables

- **Four manuscripts** under `manuscripts/` (PDF + TeX + generated
  tables/figures + CHECKSUMS.json + VERSIONS.json + BUILD.md each):
  1. `rscs_foundations` (5 pp): typed framework, architecture diagram,
     full registry tables, CEP battery, anti-Hermitian keystone with
     golden numbers, ATS figure.
  2. `rgcs_crystal_application` (3 pp): forward-hierarchy diagram,
     Christoffel resolution of scalar v_L with sweep figure inside the
     v2 band, node menu, optical layer with null posture, model-selection
     rules.
  3. `software_hardware_plan` (3 pp): layering, timing architecture with
     generated closure tables, macro-envelope figure, safety envelope,
     HG Embedded OS, quantified hardware roadmap, engineering lessons.
  4. `historical_source_companion` (5 pp): source corpus in its own
     words with authors retained, NHT/HAL and photonics adaptations,
     landscape adaptation ledger (19 EP rows with forbidden transfers),
     evidence boundaries stated without ridicule.
- **Generation pipeline:** `tools/make_v3_artifacts.py` (all numbers) +
  `tools/package_manuscripts.py` (checksums/versions/build docs).
  Build: `xelatex → bibtex → xelatex ×2` (latexmk needs perl, absent on
  this machine — documented in BUILD.md).
- **Shared assets:** `manuscripts/common/rgcs_v3_preamble.tex`
  (filename-loaded fonts — builds without OS font registration; ENG tag
  added; math-safe classification tags), `manuscripts/common/handbooks.bib`
  (Bechmann/Auld/Hecht/Narasimhamurty).
- **README:** v3 header + public **Lessons Learned** section (fuller
  engineering version in `SOFTWARE_HARDWARE_ARCHITECTURE.md` and the
  software manuscript).
- **Layout QA:** `docs/LAYOUT_QA_REPORT_V3.md` — all four: 0 undefined
  references, 0 overfull boxes; three layout fixes documented.
- **QA-D-02 closed:** the v2 `manuscript/references.bib` Koster entry was
  verified correct against the paper (full author list, real title);
  defect register addendum records the closure.

## Decisions / deviations

- v2 `manuscript/` stays in place (NOT moved into `archive/v2.0.0/` —
  moving would dirty the frozen-path check); it remains the shipped v2
  artifact. Agent 11 should note this in the release notes.
- The manuscripts are concise generated-number spines over the fuller
  repository docs, not exhaustive rewrites; each section cites its
  source document. Growing them later can only add generated content.

## For Agent 10

- Re-verify: builds reproduce (regenerate artifacts → rebuild → compare
  CHECKSUMS for tex/tables; PDF bytes will differ by timestamps), layout
  counts, citation-vs-PDF spot checks, README public claims, companion
  fidelity (no ridicule, authors retained), classification tags on every
  physics statement.
- Note: `latexmk` unavailable (no perl); use the BUILD.md sequence.

## Test state after Agent 09

Full suite unchanged by this agent's code (generation tools only):
**376 passed, 1 inherited failure (NR3-001)**. Frozen paths verified
untouched.
