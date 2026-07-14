# RGCS v2 — Independent Adversarial QA Report (Sub-Agent 08)

Date: 2026-07-14. Reviewer stance: independent; failures documented first; **nothing fixed by QA**. Companion documents: `DEFECT_REGISTER.md` (QA-D-01..26), `CLAIM_AUDIT.md`, `REPRODUCIBILITY_AUDIT.md`.

## VERDICT: **YELLOW**

All nine gates were exercised with evidence; none is unverified. Six pass outright; gates 1, 8, and 9 have documented, bounded failures; five P1 defects (no P0) block a GREEN. No result invalidates the scientific framework's core discipline — but the manuscript misquotes two of its three foundation references, contradicts itself on one statistic, and publishes one demonstrably wrong equation-level requirement.

## 1. Methodology

- Full test suite run twice (`QT_QPA_PLATFORM=offscreen python3 -m pytest`), plus `-m slow`, plus per-directory collection counts.
- Clean-shell regeneration of every figure/table with byte-level diff against committed artifacts.
- Full `latexmk -xelatex` recompile; log audit; visual inspection of **all 28 PDF pages**.
- Bibliography verified against page 1 of the three reference PDFs on disk (pdftotext).
- 16 workbook formulas traced to `rgcs_core` with numeric execution (gate 1); 14 equations RGCS-M.x re-implemented independently and compared numerically; 2×2 coupled eigenproblem verified by hand against `numpy.linalg.eigh`.
- Adversarial software tests (scripted, `/tmp/qa_soft`): workspace corruption ×3 + future-schema + restore; mid-run job cancellation with process/db/artifact audit; malformed-import matrix (7 CSV/JSON cases); checksum verification (provenance register 18/18, bundle export round-trip + tamper test); AST-level architecture-leakage scan; edge-case/singularity probing of every coherence metric.
- Claim audit: 24 sampled claims + all scientific-review dimensions (see CLAIM_AUDIT.md).

## 2. Gate-by-gate assessment

| Gate | Requirement | Status | Evidence |
|---|---|---|---|
| 1 | Workbook formulas ported or marked spreadsheet-only | **PARTIAL** | 13/16 sampled match to full float precision or are documented replacements; 3 unmarked gaps, worst: Spiral WB B23/B24 R_χ differs 4× from core with no marking (QA-D-09) |
| 2 | Manuscript numbers generated, not hand-copied | **PASS** | Regeneration byte-identical; one hand-typed derived numeral (1507.328, also in a generated table; QA-D-26) |
| 3 | Unit/property/golden/integration/UI tests pass | **PASS** | 203/203, twice, deterministic; 97+17+19+47+13+10 |
| 4 | Claims tagged EST/DER/HYP/SRC | **PASS** | Verified on every inspected page, table, figure, notation row, traceability matrix |
| 5 | Every hypothesis: observable, control, failure condition, uncertainty | **PASS** | Table 9 (all 14) + ROADMAP_TO_FALSIFICATION rows sampled (H-05, H-10) |
| 6 | Desktop end-to-end workflow | **PASS** | `tests/integration/test_vertical_slice.py` steps 1–7 (workspace→import→spectrum→experiment→job→results→bundle) all pass; ethics gate verified |
| 7 | No unevidenced therapeutic/medical/cosmological/consciousness claims | **PASS** | None found in manuscript, docs, or UI strings; human-loading boundary explicit; vocab checker run manually over desktop+docs: clean (lint-scope gap QA-D-11) |
| 8 | Manuscript compiles clean; no clipped figures/overflow/broken refs | **PARTIAL** | 0 errors, 0 undefined refs, 28pp, one 5.2pt overfull, no clipping — but Fig 8 contradicts its own caption/Table 8 (QA-D-03), malformed `6.4e-35` math (QA-D-15), literal `CONTROL\_MATRIX` in Fig 10 (QA-D-16) |
| 9 | Public artifacts: source, checksums, version metadata, provenance | **PARTIAL** | Provenance register 18/18 verified; workspace bundles exemplary (checksums+versions+tamper detection) — but `release/` has no checksums and the manuscript source bundle carries none (QA-D-10) |

## 3. Headline findings (detail in DEFECT_REGISTER.md)

**P1-01/02 — Bibliography misrepresents two of the three foundation papers.** Gan et al.: four of five author given names fabricated. Koster et al.: wrong title and "Koster, T. and et al." author field; actual title is "Emergence of phase coherence in a magnon Bose–Einstein condensate" (first author Malte Koster; nine authors, all on page 1 of the PDF sitting in the repo's reference directory). Lee–Tsai verified correct. For a project whose identity is source-audit discipline, these are the most damaging defects found.

**P1-03 — The case-(d) Rayleigh statistic is published with two values.** Fig 8's panel says Z_R=0.10, p=0.91; its caption, Table 8, and the body say Z_R=1.26, p=0.28. Root cause: `make_figures.py` and `make_tables.py` implement different "initial phase" estimators. Both regenerate deterministically; the pipeline is honest, the definition is not unified.

**P1-04 — K_nm = πg_nm is wrong.** Numerically demonstrated: with the documented real-symmetric coupling, two degenerate modes grow as cosh(Kt) with no frequency splitting; the frequency-domain model corresponds to anti-Hermitian coupling of magnitude 2πg. The pre-registered H-09 consistency requirement would flag correct data as inconsistent. Affects MATHEMATICAL_MODEL M.46, manuscript §10.1/B.4/Fig 11, `coupled_modes/static.py:135-169`.

**P1-05 — Corrupt workspace = startup crash-loop.** Raw `sqlite3.DatabaseError` escapes `Workspace.open()`; `main.py` auto-reopens the last workspace unguarded. Backups exist but no recovery path is surfaced.

**What held up under attack:** all 14 checked equations and every golden value reproduce exactly; the 2×2 eigenproblem matches analytic values to 1e-11 Hz; unit discipline is airtight (every conversion single, commented, documented); no architecture leakage in either direction; job cancellation leaves a clean state; JSON schema validation is strict and user-friendly; checksummed bundle export detects tampering; the classification-label system is real, machine-checked, and consistently applied; numerology containment and null models are genuinely pre-registered.

## 4. PDF visual inspection

All 28 pages read. No clipped figures, no overflowing tables, no broken cross-references, headers/footers consistent, notation matches Appendix A / NOTATION_AND_UNITS.md throughout (spot checks: κ_χ, ε_R^(f), C_w, r_φ, k̃_H vs k_H distinction maintained). Issues found: p.16 Fig 8 contradiction (QA-D-03), p.20 malformed exponent (QA-D-15), p.19 literal backslash (QA-D-16), p.23-24 reference defects (QA-D-01/02/18), ref [4] test-count claim (QA-D-17). Landscape Fig 11 (p.21) renders correctly but repeats the wrong "consistency K = πg" (QA-D-04).

## 5. Reasoning for YELLOW (not GREEN, not RED)

- **Not GREEN:** gates 1, 8, 9 have concrete failures; five P1 defects exist; QUALITY_GATES.md requires all gates for GREEN.
- **Not RED:** every gate was verified with evidence and none fails wholesale. The computational core is sound (203/203 twice; all equations except M.46's consistency map verified correct; byte-identical regeneration). All P1s have small, well-localized fixes: two bib entries (source PDFs are on disk), one estimator unification, one coupling-map correction, one exception wrapper + startup guard.

## 6. Required before release (Agent 09)

1. Fix `references.bib` gan2025 and koster2026 from the PDFs' first pages; fix "Koster and et al." phrasing throughout the tex; rebuild (QA-D-01/02).
2. Unify the case-(d) initial-phase estimator between `make_figures.py` and `make_tables.py`; regenerate; state the estimator in the caption (QA-D-03; delete the dead code QA-D-19).
3. Correct the K_nm↔g_nm map (anti-Hermitian, 2πg) in MATHEMATICAL_MODEL M.46, manuscript §10.1/B.4/Fig 11, and `coupled_modes/static.py`; add a regression test that the corrected map reproduces the 2g splitting (QA-D-04).
4. Wrap workspace-open corruption in `WorkspaceError`; guard the startup auto-open; surface backup restore (QA-D-05).
5. Patch INCONSISTENCY_REGISTER D-13 sign (QA-D-08); mark or port the three workbook gaps (QA-D-09); add checksums+versions to `release/` and the manuscript source bundle (QA-D-10).
6. P2 hardening as time allows: CSV loader error messages + finiteness gate (QA-D-06/13), manifest JSON error wrapping (QA-D-07), core edge-case guards (QA-D-12), vocab-lint scope (QA-D-11).
