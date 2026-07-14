# RGCS v2 — Acceptance Criteria (release 2.0.0)

**Author:** Sub-Agent 09. **Date:** 2026-07-14. These are the concrete,
checkable criteria behind the nine quality gates
(`internal-docs/output_contracts/QUALITY_GATES.md`); the evidence walk is
in `RELEASE_CHECKLIST.md`.

## A. Computational correctness
- [x] AC-1 All 61 registry equations implemented in `rgcs_core` with the
      registry id in provenance metadata.
- [x] AC-2 All golden values (ledger Part E) reproduce exactly
      (`tests/golden`, 19 tests).
- [x] AC-3 Golden coherence manifest reproduces from CSVs
      (`tests/regression`, 50 tests incl. determinism).
- [x] AC-4 Corrected coupling map \|K\| = 2πg reproduces the 2g splitting
      for a degenerate pair; old map flagged
      (`tests/regression/test_qa_d04_coupling_map.py`).
- [x] AC-5 227/227 tests pass headless, twice, deterministically.

## B. Scientific integrity
- [x] AC-6 Every claim-bearing public function carries a valid
      classification label (machine-checked).
- [x] AC-7 All 14 hypotheses have observable + control + failure condition
      + uncertainty (manuscript Table 9; ROADMAP_TO_FALSIFICATION.md).
- [x] AC-8 Forbidden-vocabulary lint green over `rgcs_core` AND
      `rgcs_desktop`.
- [x] AC-9 No therapeutic/medical/cosmological/consciousness claim
      presented as established (QA claim audit + vocabulary gate).
- [x] AC-10 Bibliography verified against page 1 of all three foundation
      PDFs (gan2025, koster2026 corrected; leetsai2026 already correct).

## C. Manuscript
- [x] AC-11 `latexmk -xelatex` completes with 0 errors, 0 undefined
      references; 28 pages.
- [x] AC-12 No figure contradicts its caption/table (case-(d) estimator
      unified: Z_R = 1.26, p = 0.28 everywhere).
- [x] AC-13 All numerals generated (`\gv` macros / generated tables /
      figures); the last hand-typed derived numeral (1507.328) is now
      `\gvHalfNominal`.
- [x] AC-14 Only layout warning: one 5.2 pt overfull hbox (accepted).

## D. Desktop
- [x] AC-15 Vertical slice green: create workspace → import specimen →
      calculate modes → define experiment → run job → display results →
      export reproducibility bundle.
- [x] AC-16 Corrupt workspace db yields `WorkspaceError` (3 corruption
      modes tested), never a crash-loop; backup restore path exists and is
      tested; corrupt dbs are never archived as backups.
- [x] AC-17 Malformed CSV/JSON inputs produce actionable user-facing
      errors (7-case matrix tested); NaN/inf inputs rejected at the gate.

## E. Packaging & provenance
- [x] AC-18 `release/` contains: source zip, manuscript PDF, test results
      (junit XML + markdown), example workspace bundle, release notes,
      SHA256SUMS.txt covering every release file, PROVENANCE.json
      (input sha256s, build environment, package versions, date).
- [x] AC-19 Manuscript source bundle carries CHECKSUMS + VERSIONS metadata.
- [x] AC-20 Workbook formulas: every sampled formula ported+tested or
      explicitly marked spreadsheet-only (WB-SO-1..3 addendum,
      INCONSISTENCY_REGISTER.md).
- [x] AC-21 LICENSE (MIT), CITATION.cff, README with honest scope and
      classification-policy summary at repo root.
- [ ] AC-22 Windows binary artifact — NOT met in this environment; Linux
      build present, Windows reproducible-build instructions shipped
      (`tools/packaging/build_windows.md`). Recorded as a release-notes
      limitation, not a gate failure (gates require source + build
      instructions).
