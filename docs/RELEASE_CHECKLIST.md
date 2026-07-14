# RGCS v2 — Release Checklist and Final Gate Walk

**Author:** Sub-Agent 09 (Integration, Release, and Public Package).
**Date:** 2026-07-14. **Release:** 2.0.0.
Baseline: independent QA verdict **YELLOW** (`docs/QA_REPORT.md`,
2026-07-14, 5 P1 / 9 P2 / 12 P3 defects, nothing fixed by QA).

## 1. Defect disposition (QA-D-01..26)

| Defect | Disposition |
|---|---|
| QA-D-01/02 (P1) bibliography | **FIXED** — gan2025/koster2026 corrected against source-PDF page 1; bbl regenerated; verified in compiled PDF refs [2]/[3] |
| QA-D-03 (P1) two Rayleigh values | **FIXED** — unified estimator φ₀ = arg z(0) mod 2π in `rgcs_core.coherence.initial_phase_estimate`; both tools use it; Fig. 8 = Table 8 = body (Z_R=1.26, p=0.28); estimator stated in Fig. 8 caption and Table 8 caption |
| QA-D-04 (P1) K = πg wrong | **FIXED** — anti-Hermitian K = i·2πg, \|K\| = 2πg in code (`coupled_modes/static.py`), M.46 docs (with erratum), manuscript §10.1/B.4/Fig. 11 (erratum stated); regression tests reproduce the 2g splitting and pin the old failure mode |
| QA-D-05 (P1) corrupt-workspace crash-loop | **FIXED** — integrity gate in `Workspace.open` (before backup), `WorkspaceError` wrapping, guarded startup auto-open, `restore_latest_backup` API + UI dialog; 5 tests |
| QA-D-06/07/13 (P2) loaders | **FIXED** — CSV loader 7-case friendly errors + NaN/inf gate; manifest JSON/Unicode errors reported; coherence pipeline finiteness gates; 12 tests |
| QA-D-08 (P2) D-13 sign | **FIXED** — register patched to +0.328 with erratum trail |
| QA-D-09 (P2) workbook gaps | **FIXED** — WB-SO-1..3 addendum in INCONSISTENCY_REGISTER.md; RGCS-M.36 (ℓ_3D/(2πT)) declared authoritative over WB B23/B24 |
| QA-D-10 (P2) checksums/versions | **FIXED** — release/SHA256SUMS.txt (every file incl. linux tree); manuscript source bundle carries CHECKSUMS.json + VERSIONS.json; release/PROVENANCE.json |
| QA-D-11 (P2) lint scope | **FIXED** — vocabulary lint now walks `rgcs_desktop` too (green) |
| QA-D-12 (P2) edge crashes | **PARTIALLY FIXED** — `instantaneous_frequency`/`coherence_decay_time` guarded + tested; silent-inf returns in `fit_exponential_decay`/`control_subtracted_metrics`/`anisotropy` deferred (behavior-change risk; backlog) |
| QA-D-15/16/17 (P3) | **FIXED** — `latex_sci` formatter (6.4 × 10⁻³⁵); CONTROL_MATRIX title backslash; test counts updated to 227 (manuscript §17 + ref [4]) |
| QA-D-19 (P3) dead code | **FIXED** — removed with the QA-D-03 unification |
| QA-D-26 (P3) hand-typed numeral | **FIXED** — 1507.328 now `\gvHalfNominal`, generated from `rgcs_core.drive.drive_sequence` |
| QA-D-14, 18, 20–25 | **DEFERRED with rationale** — QA-D-14 (SIGKILL escalation) verified clean adversarially, documented limitation; QA-D-18 (bare bib venues) cosmetic; QA-D-20 (default rise time), QA-D-22 (u_rel ≥ 1), QA-D-23 (backup rotation), QA-D-24 (two undocumented constants), QA-D-25 (blocking-call hygiene) are registered backlog items in `IMPLEMENTATION_PLAN.md`; none affects a quality gate |

## 2. Final gate walk (QUALITY_GATES.md 1–9)

| Gate | Status | Evidence (one line) |
|---|---|---|
| 1 Workbook parity | **PASS** | 13/16 QA-sampled formulas match to float precision or are documented replacements; remaining 3 explicitly marked spreadsheet-only (WB-SO-1..3, INCONSISTENCY_REGISTER.md addendum) with the authoritative M.36 definition stated |
| 2 Generated numerics | **PASS** | QA byte-diff regeneration verified; the single hand-typed derived numeral is now generated (`\gvHalfNominal`); figures/tables regenerated 2026-07-14 |
| 3 All suites pass | **PASS** | 227/227 (`release/test_results.xml`), unit 118 / property 17 / golden 19 / regression 50 / ui 13 / integration 10; deterministic across runs |
| 4 Claims tagged | **PASS** | QA verified on every inspected page/table/figure; machine-checked in code; unchanged by this pass |
| 5 Hypotheses complete | **PASS** | QA verified Table 9 (all 14) + roadmap rows; unchanged |
| 6 Desktop end-to-end | **PASS** | `tests/integration/test_vertical_slice.py` green; the released `example_workspace_bundle.zip` was regenerated through the same app path and verifies (`verify_bundle` ok) |
| 7 No unevidenced claims | **PASS** | Vocabulary lint green over `rgcs_core` + `rgcs_desktop`; QA manual sweep of docs/manuscript clean |
| 8 Manuscript clean | **PASS** | `latexmk -xelatex`: 0 errors, 0 undefined references, 28 pp.; Fig. 8/Table 8 contradiction resolved; refs [2]/[3] correct; malformed math and literal backslash fixed; sole remaining warning is one 5.2 pt overfull hbox (no clipping, inspected) |
| 9 Public artifacts | **PASS** | `release/`: source zip, manuscript PDF + checksummed source bundle, example bundle, test results (XML+md), QA report, PROVENANCE.json (18/18 input sha256s, build env, package versions), SHA256SUMS.txt over every release file incl. the Linux build tree |

## 3. Verdict

**GREEN — release 2.0.0.** All nine gates pass with evidence; all P1
defects fixed with regression tests; deferred items are non-gating and
registered. Honest limitations (not gate failures, disclosed in
`release/RELEASE_NOTES.md`): no Windows/macOS binaries (Linux build +
reproducible Windows instructions ship instead); SCAD D-02 inert render
mode (inherited, documented with workaround); QA-D-12 silent-inf returns
partially deferred; no hardware measurements exist — every hypothesis
remains exactly that.

## 4. Expected-tree deviations

- `package.json` — intentionally absent: pure-Python stack, no Node
  toolchain (recorded here and in README.md).
- `release/` additionally contains QA_REPORT.md, test reports, PROVENANCE,
  and SHA256SUMS beyond the minimum list.
- The source zip excludes the whole `release/` directory (not just
  `release/linux/`) to avoid self-referential archives; every release
  artifact is checksummed in SHA256SUMS.txt instead.

## 5. Release procedure (repeatable)

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest --junitxml=release/test_results.xml
python3 tools/make_figures.py && python3 tools/make_tables.py
( cd manuscript && latexmk -xelatex rgcs_v2.tex )
QT_QPA_PLATFORM=offscreen python3 tools/packaging/make_release.py
sha256sum -c release/SHA256SUMS.txt   # must be 100% OK
```
