# RGCS v2 — Release Notes, version 2.0.0 (2026-07-14)

Status: **release candidate — see `docs/RELEASE_CHECKLIST.md` for the
quality-gate walk and final verdict.** MIT license, © 2026 Andrew Green.

## What this is

A complete rebuild of the Resonant Geometry Computational System:
a deterministic, tested computational core (`rgcs_core`, 61 registered
equations), a desktop research workbench (`rgcs_desktop`, 13 panels), an
experiment kit (schemas, 8 branch templates, control matrix), CAD
generators, and a 28-page manuscript whose every figure, table, and inline
numeral is generated from the core at build time. 227 automated tests pass.

## What this is NOT (no unsupported claims)

- **No RGCS hypothesis has been experimentally confirmed.** This release
  contains no measurements of real crystals. All 14 hypotheses are
  pre-registered with observables, controls, failure conditions, and
  uncertainty statements — that is the deliverable.
- No therapeutic, medical, cosmological, or consciousness claims. The
  three peer-reviewed reference papers contribute mathematical templates
  and measurement methodology only; their physical conclusions remain
  theirs (Source claims, provenance-tracked).
- Archival corpus statements (JH/Vogel) are preserved as Source claims
  with page provenance; none is endorsed.

## Fixed since the independent QA (2026-07-14, verdict YELLOW)

All five P1 defects, with regression tests:

- **QA-D-01/02** Bibliography corrected against page 1 of the source PDFs:
  gan2025 author given names (Wen-Cong Gan, Leila L. Graef, Rudnei O.
  Ramos, Gustavo S. Vicente, Anzhong Wang); koster2026 title ("Emergence
  of phase coherence in a magnon Bose–Einstein condensate") and all nine
  authors; the "Koster and et al." rendering eliminated.
- **QA-D-03** The case-(d) per-run initial-phase estimator is unified:
  φ₀ = arg z(0) mod 2π (`rgcs_core.coherence.initial_phase_estimate`),
  used identically by figures and tables. Fig. 8 and Table 8 now agree
  (Z_R = 1.26, p = 0.28); dead code removed (QA-D-19).
- **QA-D-04** The time↔frequency coupling map was **wrong** and is
  corrected: the counterpart of a frequency-domain half-splitting g (Hz)
  is the anti-Hermitian coupling K = i·2πg (rad/s), |K| = 2πg — not the
  former real-symmetric K = πg, which splits growth rates rather than
  frequencies. Fixed in `rgcs_core.coupled_modes`, RGCS-M.46 documentation,
  manuscript §10.1/Appendix B.4/Fig. 11 (erratum stated in the manuscript),
  and the pre-registered H-09 consistency gate. Regression test reproduces
  the 2g splitting numerically.
- **QA-D-05** Corrupt workspace databases now raise `WorkspaceError`
  (never raw sqlite errors), startup auto-open is guarded (no crash-loop),
  corrupt files are never archived as backups, and a backup-restore path
  exists in both the API (`Workspace.restore_latest_backup`) and the UI.

P2 hardening: CSV loader user-facing errors + NaN/inf rejection
(QA-D-06/13); manifest JSON error reporting (QA-D-07); coherence metric
edge guards (QA-D-12); vocabulary lint extended to `rgcs_desktop`
(QA-D-11); INCONSISTENCY_REGISTER D-13 sign erratum patched with trail
(QA-D-08); three workbook gaps explicitly marked spreadsheet-only with the
authoritative RGCS-M.36 definition stated (QA-D-09, WB-SO-1..3); release
checksums + version metadata added everywhere (QA-D-10). Cosmetics:
exponent formatting in Table 8 row (f), Fig. 10 title backslash, test
count updated to 227, last hand-typed manuscript numeral replaced by a
generated macro (QA-D-15/16/17/26).

## Release contents (`release/`)

- `rgcs-v2-src-2.0.0.zip` — full source (repo tree; excludes VCS/build
  caches and `release/` itself). Includes the core library, desktop app,
  tests, docs, experiment schemas/templates, sample data, SCAD models, and
  the original computational workbook
  (`tools/RGCS_v2_Computational_Workbook.xlsx`).
- `rgcs_v2.pdf` — the manuscript (28 pp.).
- `rgcs_v2_manuscript_source_bundle.zip` — manuscript source with
  CHECKSUMS.json + VERSIONS.json.
- `example_workspace_bundle.zip` — example workspace + sample coherence
  analysis, generated through the real app path, checksummed and
  tamper-evident.
- `test_results.xml`, `test_report.md`, `test_report_core.md` — test
  evidence; `QA_REPORT.md` — the independent adversarial QA report.
- `PROVENANCE.json` — input source sha256s (18/18 verified), build
  environment, package versions, date.
- `SHA256SUMS.txt` — sha256 of every file under `release/` (including the
  Linux build tree).
- `linux/rgcs-workbench/` — Linux desktop build (PyInstaller).

## Known limitations

- **No Windows/macOS binaries** in this release (built and verified on
  Linux only); reproducible Windows build instructions:
  `tools/packaging/build_windows.md`.
- SCAD `compact_mode_crystal` render mode is inert (inherited defect D-02;
  workaround in `scad/README.md`).
- Job cancellation is SIGTERM-based without SIGKILL escalation (QA-D-14,
  adversarially verified clean today; documented limitation).
- Workspace backups accumulate without rotation (QA-D-23).
- Isotropic wave speed (v_L = 6310 m/s) carries a few-percent undeclared
  systematic on ladder lengths until per-axis calibration (D-05; σ bands
  are propagated everywhere).
- No `package.json`: pure-Python stack; deviation from the expected tree
  recorded in README and RELEASE_CHECKLIST.
