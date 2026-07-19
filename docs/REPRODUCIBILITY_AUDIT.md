# RGCS v2 — Reproducibility Audit (Sub-Agent 08)

Date: 2026-07-14. All commands run in a clean shell from `<BUILD_ROOT>/rgcs-work/rgcs-v2` (Python 3.11, TeX Live latexmk/xelatex, `QT_QPA_PLATFORM=offscreen`). Nothing in the repo was modified by these checks except the four QA-owned docs.

## 1. Test suite

| Command | Result |
|---|---|
| `QT_QPA_PLATFORM=offscreen python3 -m pytest -q` (run 1) | **203 passed** in 11.32 s |
| same (run 2, determinism) | **203 passed** in 11.20 s — identical count, no flakes |
| `pytest -q -m slow` | 1 passed, 202 deselected (the slow test is inside the 203) |

Per-directory collection: unit 97, property 17, golden 19, regression 47, ui 13, integration 10 (= 203). The handoff claim "203 tests green" is **verified**. Note: manuscript ref [4] says "180 automated tests" — the core-only subtotal (QA-D-17).

## 2. Manuscript number regeneration (gate 2)

1. Copied committed `manuscript/figures` and `manuscript/tables` aside.
2. Ran `python3 tools/make_figures.py` and `python3 tools/make_tables.py` in a clean shell.
3. `diff -r` on tables: **byte-identical** (all 9 `.tex` files including `generated_values.tex`).
4. Deep JSON compare of `figures/fig_values.json`: **identical** (every key, full float precision).

Conclusion: figure/table values are fully deterministic and regenerable from `rgcs_core` — no stale committed artifacts. Grep of `rgcs_v2.tex` for hand-typed derived numerals found exactly one (`1507.328`, tex:1019; QA-D-26); all other inline numerics are `\gv` macros (63 uses of 66 defined) or generated tables.

**Caveat:** deterministic regeneration does not imply internal consistency — Fig 8 (from `fig_values.json`, Z_R=0.10) and Table 8 / caption (from `generated_values.tex`, Z_R=1.26) reproducibly disagree because the two tools use different initial-phase estimators (QA-D-03).

## 3. Manuscript compilation (gate 8)

`latexmk -xelatex -interaction=nonstopmode rgcs_v2.tex`: completed; **0 errors** (`grep -c '^!' rgcs_v2.log` = 0), **0 undefined references/citations**, 0 multiply-defined; exactly **1 overfull hbox (5.2 pt)**; `pdfinfo`: **28 pages** as claimed. All 28 pages visually inspected (see QA_REPORT §4): no clipped figures, no overflowing tables; cosmetic issues QA-D-15/16 only.

## 4. Checksums and provenance (gate 9)

- `docs/PROVENANCE_REGISTER.csv`: **18/18 rows verified** — sha256 and size_bytes both match the actual files (reference PDFs, prior-project sources, workbook dumps, corpus files).
- Workspace reproducibility bundle (`rgcs_desktop/services/bundle.py`): export → `verify_bundle` → ok; independent re-hash of every member against the bundle's `CHECKSUMS.json`: 0 mismatches; **tamper test** (one flipped byte) correctly detected; export recorded in `export_history` with the zip's own sha256. VERSIONS.json present.
- **Gaps:** `release/linux/rgcs-workbench/` has **no checksum manifest**; `manuscript/rgcs_v2_manuscript_source_bundle.zip` (28 files: tex, bib, generated tables/figures, both tools, layout report — contents verified) contains **no checksums or version metadata** (QA-D-10).

## 5. Determinism of analysis artifacts

- Two full pytest runs identical (above); `tests/integration/test_vertical_slice.py::test_deterministic_artifact_ids` passes.
- Golden coherence datasets are seeded; regeneration path exercised via the `-m slow` test (passed).
- Job worker runs in a spawned process; results returned over a queue; artifact writes are atomic (temp + `os.replace`; no stray `.tmp` after cancellation test).

## 6. Robustness reproductions (scripts under /tmp/qa_soft, repo untouched)

- **Workspace corruption:** 3 corruption modes → raw `sqlite3.DatabaseError` (QA-D-05); future-schema 999 and missing-schema-row → clean `WorkspaceError`; manual restore from `backups/` works.
- **Job cancel mid-run:** status `cancelled` in 0.013 s, worker pid gone (SIGTERM, exit −15), `PRAGMA integrity_check: ok`, no partial artifacts, idempotent second cancel (QA-D-14 for residual risks).
- **Malformed imports:** JSON schema validator — clean, precise messages for missing keys, wrong types, unknown keys (strict), future major version, non-object roots. CSV loader — raw `StopIteration`/`IndexError`/`UnicodeDecodeError` and silent NaN/inf acceptance (QA-D-06); malformed JSON files leak `JSONDecodeError` (QA-D-07).

## 7. Verdict on reproducibility

Core reproducibility is **excellent**: tests deterministic, every manuscript number regenerates byte-identically, provenance register fully verified, workspace bundles checksum-verified with tamper detection. Open reproducibility items: checksums/version metadata for `release/` and the manuscript source bundle (QA-D-10), and the reproducible-but-inconsistent case-(d) Rayleigh statistic (QA-D-03).
