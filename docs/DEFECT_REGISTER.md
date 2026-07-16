# RGCS v2 — QA Defect Register (Sub-Agent 08, Independent Adversarial QA)

Date: 2026-07-14. Environment: Python 3.11, `QT_QPA_PLATFORM=offscreen`, repo `/home/claude/rgcs-work/rgcs-v2`.
Severity: P0 blocker / P1 major / P2 minor / P3 cosmetic. Nothing was fixed by QA; all items are open.

## P1 — Major

### QA-D-01 (P1) Fabricated author given names in `references.bib` entry `gan2025`
- **Evidence:** `manuscript/references.bib:16` lists `Gan, Wojciech and Graef, Guilherme and Ramos, Marcelo and Vicente, Guilherme and Wang, Anzhong`. Page 1 of the actual paper (`internal-docs/reference_documents/Gan_et_al_2025_Quantum_Damping_Cosmological_Shear.pdf`, extracted with pdftotext) reads: **Wen-Cong Gan, Leila L. Graef, Rudnei O. Ramos, Gustavo S. Vicente, Anzhong Wang**. Four of five given names are invented. The wrong names appear in the compiled PDF (reference [2], p. 23).
- **Repro:** `pdftotext -f 1 -l 1 Gan_et_al_2025_... -` vs bib entry.
- **Owner:** Agent 09 (manuscript). Correct from the PDF first page; title/eprint/year are correct.

### QA-D-02 (P1) Koster reference: wrong title, wrong author initial, "and et al." author field
- **Evidence:** `references.bib:26-27`: `author = {Koster, T. and et al.}`, `title = {Spontaneous phase coherence in a parametrically pumped room-temperature magnon condensate}`. Actual paper page 1: title **"Emergence of phase coherence in a magnon Bose–Einstein condensate"**, authors **Malte Koster, Matthias R. Schweizer, Timo Noack, Vitaliy I. Vasyuchka, Dmytro A. Bozhko, Burkard Hillebrands, Mathias Weiler, Alexander A. Serga, Georg von Freymann** (Nature Physics; DOI in bib matches). Rendered ref [3] shows "T. Koster and et al." and the invented title; body text repeatedly says "Koster and et al." (grammatically broken citation form). Lee–Tsai entry checked the same way: **correct** (title, authors, PRD 114 L011701, DOI 10.1103/tsq1-bhsz all match page 1).
- **Owner:** Agent 09 (manuscript).

### QA-D-03 (P1) Figure 8 contradicts its own caption and Table 8: two different case-(d) Rayleigh statistics
- **Evidence:** Compiled PDF p. 16: figure panel title reads "Rayleigh Z_R = 0.10, p = 0.91"; the caption directly beneath and Table 8 (p. 20) and body text (`rgcs_v2.tex:894` via `\gvCaseDRayZ`) read "Z_R = 1.26, p = 0.28" — same named statistic on the same golden dataset, on the same page.
- **Root cause:** two different "per-run initial phase" estimators. `tools/make_figures.py:383-386` uses the circular mean of the first 200 samples of instantaneous phase; `tools/make_tables.py:494` uses `instantaneous_phase(z)[0]` (phase at sample 0). Both regenerate deterministically (verified byte-identical), so this is a design inconsistency, not a stale artifact.
- **Impact:** conclusion unchanged (both consistent with uniformity), but a reviewer-visible internal contradiction; violates gate 8 in spirit ("broken cross-references"/consistency).
- **Owner:** Agent 09 — pick one estimator, use it in both tools, document it.

### QA-D-04 (P1) Time–frequency coupling map K_nm = π·g_nm is wrong in structure and magnitude
- **Evidence (numeric):** integrating RGCS-M.46 (`rgcs_core/coupled_modes/dynamics.py`, `integrate_stuart_landau`) for two **degenerate** modes (f₀=100 Hz, g=2 Hz, K=πg, no gain/damping/saturation/noise) gives monotone exponential amplitude growth |z₁|: 1 → 2.47 → 11.28 → 53.5 → 253.8 over 1 s (≈cosh(Kt)) — no beat, no spectral splitting. Reason: the coupling term K_nm z_m is real-symmetric, so at degeneracy eigenvalues of [[iω,K],[K,iω]] are iω±K — the "splitting" lands in growth rate, not frequency. Hand integration with anti-Hermitian coupling i·2πg reproduces the expected amplitude beat and spectral peaks at f₀±g.
- **Affected:** `rgcs_core/coupled_modes/static.py:135-169` (`coupling_rate_from_g_hz`, `g_hz_from_coupling_rate`, `coupling_consistency`), `docs/MATHEMATICAL_MODEL.md` §11 M.46 term table and consistency requirement, `manuscript/rgcs_v2.tex:809,1233,1436` (§10.1, Appendix B.4, Fig. 11 box "consistency K = πg"). B.4's own derivation is muddled ("beat 2π·2g ... i.e. per-mode K = πg").
- **Impact:** the pre-registered H-09 consistency check "K_nm = πg_nm within 2σ" would flag *correct* time/frequency fit pairs as internally inconsistent. `stuart_landau_pair` (diffusive coupling) is a different, self-consistent model and unaffected.
- **Owner:** Agent 09 with math review — coupling should be anti-Hermitian, magnitude 2πg (rad/s) for a 2g Hz splitting; fix M.46, B.4, code, and the consistency gate.

### QA-D-05 (P1) Corrupt workspace DB → uncaught raw `sqlite3.DatabaseError`, startup crash-loop; recovery is manual-only
- **Evidence:** header-zeroed / truncated / garbage `workspace.db` all raise raw `sqlite3.DatabaseError` from `rgcs_desktop/workspaces/workspace.py:155` (`_migrate`); `Workspace.open()` checks only existence. No caller guards it: `app/context.py:25`, `app/main.py:56-60` (auto-reopen of `settings.last_workspace` at startup), `main_window.py:148-151`. A corrupt last-workspace crashes the app on **every launch** until the file is manually removed. Backups exist (`backups/workspace-<ts>.db` copied on open) and manual restore works, but no code path offers recovery; opening a corrupt workspace also archives a corrupt backup; backups accumulate unboundedly. Future-schema and missing-schema-row cases are, by contrast, clean `WorkspaceError`s (verified).
- **Repro:** `/tmp/qa_soft/t1_workspace.py`.
- **Owner:** Agent 09 (desktop) — wrap `_migrate` first-touch in `WorkspaceError`, guard startup auto-open, surface the backups.

## P2 — Minor

### QA-D-06 (P2) CSV ingestion raises raw internal errors and silently accepts NaN/inf
- `rgcs_desktop/jobs/workers.py:_load_timeseries_csv`: empty file → raw `StopIteration` (`next(reader)`, line 55); header-only → raw `IndexError` (line 58); binary-renamed-.csv → raw `UnicodeDecodeError`; truncated row → `ValueError` with numpy-internals message; **NaN/inf accepted silently**, failing far downstream with the misleading "need >= 2 positive samples for a log-linear fit". The job framework catches all and ships the traceback as the job error (no app crash), but the user sees `StopIteration` etc. as the diagnosis. Repro: `/tmp/qa_soft/t3_malformed.py`. Owner: 09 (desktop).

### QA-D-07 (P2) `validate_manifest_file` leaks raw `JSONDecodeError`/`UnicodeDecodeError`
- `rgcs_desktop/services/schemas.py`: malformed/binary/empty JSON files bypass the otherwise excellent schema-error formatting (which is clean and strict, incl. unknown-key rejection and major-version gate — verified). Same exposure at `services/coherence_analyzer.py:117`. Owner: 09.

### QA-D-08 (P2) D-13 sign erratum never patched in `docs/INCONSISTENCY_REGISTER.md`
- Line 64 still says "half-spacing nominal 1507.328 cycles → residue **−0.328** (−118.08°)". Code, golden test, Table 5/8 and manuscript all give **+0.328** (verified: `phase_residue_cycles(1507.328) = +0.328`). Agent 02's erratum was acknowledged elsewhere but the register itself was not corrected. Owner: 09 (docs; register owned by Agent 01).

### QA-D-09 (P2) Quality-gate-1 gaps: three workbook formulas neither ported nor marked spreadsheet-only
- (a) Spiral 4D WB `B23/B24`: workbook R_χ = ℓ_3D/2π = 60.986 mm vs core `compact_radius_prior_mm` = ℓ_3D/(2πT) = 15.280 mm — a 4× (=turns) discrepancy on identical inputs; D-09/RG-09 discuss the closed form but no document states WB B23 omits ÷turns and is superseded. (b) 4096 Ladder cols E–H (power-of-2 detector, ratio-vs-N=5, Long/Primary/Short labels): no implementation, no marking. (c) Loading Calibration B17–B19 (target/predicted-free/required-shift): derivable but not produced, not marked. 13 of 16 sampled formulas match to full float precision or are documented replacements (D-06, D-09, D-12, D-13, D-22). Owner: 09 (docs — mark or port).

### QA-D-10 (P2) Release artifacts and manuscript source bundle lack checksums/version metadata (gate 9 partial)
- `release/linux/rgcs-workbench/` (21.7 MB binary tree) has no checksum manifest at all. `manuscript/rgcs_v2_manuscript_source_bundle.zip` (28 files, verified contents) contains no CHECKSUMS/VERSIONS file. Contrast: workspace bundle export writes and verifies CHECKSUMS.json + VERSIONS.json (verified round-trip incl. tamper detection), and `docs/PROVENANCE_REGISTER.csv` verifies 18/18 — but the register covers **inputs only**, not the project's own public artifacts. Owner: 09 (packaging).

### QA-D-11 (P2) Forbidden-vocabulary lint covers `rgcs_core` only
- `tests/unit/test_experiments_provenance.py:179-194` walks only the `rgcs_core` package. `rgcs_desktop` strings, `docs/`, and manuscript are unlinted. QA ran the checker manually over `rgcs_desktop` and `docs/USER_GUIDE.md`: **clean today** (the tex hits 'BEC'/'dark matter' only in legitimate source-domain contexts). Process gap, not a live violation. Owner: 09 (extend the test with a context-aware allowlist).

### QA-D-12 (P2) Unguarded crashes and silent `inf` in core edge cases
- `rgcs_core/coherence/metrics.py:78` `instantaneous_frequency` on a single sample → raw numpy gradient error; `metrics.py:257` `coherence_decay_time` on empty arrays → raw `argmax of an empty sequence`. Silent non-JSON `inf` returns: `models.py` `fit_exponential_decay` on constant data (tau_s=inf), `experiments/__init__.py:120-122` `control_subtracted_metrics` degenerate samples (d_c/G_c=inf), `anisotropy.py:117` — all conflict with the project's own D-03 "null, never NaN" JSON policy. None have test coverage. Owner: 09 (core).

### QA-D-13 (P2) `rgcs_core.coherence` silently propagates NaN/inf inputs
- All-NaN signal → all-NaN C(w) with no error; a single inf sample → NaN coherence in affected windows, silently. No `isfinite` gate anywhere in `coherence/metrics.py` (contrast `control_subtracted_metrics`, which rejects non-finite input cleanly). Owner: 09 (core).

### QA-D-14 (P2) Job cancellation is SIGTERM hard-kill with residual risks
- Verified clean today (state `cancelled`, no orphans, db integrity ok, no partial artifacts, idempotent — `/tmp/qa_soft/t2_jobs.py`). Risks: one `multiprocessing.Queue` shared across all jobs (`jobs/manager.py:72`) — terminating a job mid-`put` can theoretically wedge other jobs' messages; no SIGKILL escalation if `proc.join(timeout=5.0)` expires (record marked cancelled even if process survived). Matches the desktop's honest limitations list. Owner: 09 (desktop, low priority).

## P3 — Cosmetic

- **QA-D-15** Table 8 row (f) renders "$p = 6.4e-35$" as malformed math ("6.4e − 35"); source `manuscript/tables/tab_coherence_golden.tex:17` (generated by `make_tables.py` — fix the formatter to `\times 10^{-35}`). Fig. 8 caption formats the same number correctly.
- **QA-D-16** Figure 10 title renders a literal backslash: "(CONTROL\\_MATRIX v1.0.0)" (PDF p. 19; escape bug in `make_figures.py` title string).
- **QA-D-17** Reference [4] self-citation claims "180 automated tests"; actual suite is **203** (97 unit + 17 property + 19 golden + 47 regression + 13 UI smoke + 10 integration). §17 (tex:1307) lists the 180 core-side counts without noting the 23 UI/integration tests exist.
- **QA-D-18** Bib entries [8], [23], [24], [25] lack journal/venue metadata (bare author+title); [2] is arXiv-only (fine) but see QA-D-01.
- **QA-D-19** `tools/make_figures.py:374-386`: `first_phases` computed once then immediately overwritten by a different estimator — dead code that obscures QA-D-03.
- **QA-D-20** `micro_pulse_metrics` default `rise_time_us=1.0` (`rgcs_core/drive/__init__.py:155`) differs from the archival operating point 1.3 µs used by golden G-13 and the manuscript; silent misuse risk for callers relying on defaults.
- **QA-D-21** One overfull hbox (5.2 pt, `rgcs_v2.log`, tab lines 12–28). Only layout warning in the log.
- **QA-D-22** `rgcs_core/uncertainty.py:41-42`: `UncertainValue` raises for u_rel ≥ 1 — a fit with ≥100% relative uncertainty crashes rather than reporting.
- **QA-D-23** Workspace backups accumulate unboundedly and corrupt DBs get archived as backups (see QA-D-05 caveats).
- **QA-D-24** `DEFAULT_WAVE_SPEED_M_S`/`DEFAULT_WAVE_SPEED_U_REL` are public, used by a desktop viewer, in `__all__`, but absent from `docs/CORE_API_SPEC.md`.
- **QA-D-25** `run_analysis(wait=True)` branch inside a widget method blocks up to 120 s if ever wired to UI (currently only tests use it); several viewers call fast core functions synchronously in event handlers — `avoided_crossing_sweep` is the one most likely to grow into a stall.
- **QA-D-26** `rgcs_v2.tex:1019` hand-types the nominal count "1507.328" (also present in generated Table 5); the only hand-typed derived numeral found — all other manuscript numerics route through the 63 `\gv` macro uses (66 defined) or generated tables.

### Agent 08 addendum (2026-07-15)

- **V2-WIN-01 FIXED** in `rgcs_desktop/services/bundle.py` (POSIX arcnames
  via `as_posix()`); regression guard `test_bundle_arcnames_posix`;
  `test_step_7_reproducibility_bundle` passes on Windows.
- **"Specimen-listing Windows defect" RE-DIAGNOSED:** the step-4/4b
  vertical-slice failures were missing-`jsonschema` import errors, not a
  listing defect; with the dependency declared (pyproject dev extra) the
  tests pass unmodified. The frozen V2_BASELINE_AUDIT.md wording is
  superseded by this addendum (audit file itself untouched).
- **D-02 (SCAD compact-mode rings inert) FIXED in v7**
  (`scad/vogel_parametric_crystal_models_v7_RGCS_v3.scad`); v6 retained
  verbatim; diff summary in `scad/README.md`.
- QA-D-02 (Koster citation) remains OPEN, owner Agent 09.

### Agent 09 addendum (2026-07-15)

- **QA-D-02 (Koster citation) VERIFIED FIXED:** `manuscript/references.bib`
  (v2, shipped) already carries the corrected entry ("Emergence of phase
  coherence in a magnon Bose-Einstein condensate", full nine-author list);
  the v3 manuscripts do not cite Koster. Closing as fixed-in-v2-final.
- v3 manuscript layout: all four builds show 0 undefined references and
  0 overfull boxes (see docs/LAYOUT_QA_REPORT_V3.md).

### Agent 10 addendum (2026-07-15) — v3 adversarial QA findings

- **D-V3-01 (P2, OPEN -> Agent 11):** generated coordinate count wrong
  (18 vs true 17): make_v3_artifacts.py adds +1 for RSCS-C.15 which is
  already a registry row; propagates to the RSCS Foundations abstract and
  README. Fix: drop +1, regenerate, rebuild, correct README.
- **D-V3-02 (P3, OPEN -> Agent 11):** manuscript figure PDFs not
  byte-reproducible (matplotlib CreationDate metadata). Fix:
  SOURCE_DATE_EPOCH before matplotlib import; verify regen-clean.
- **D-V3-03 (P2, OPEN -> Agent 11):** CITATION.cff still v2.0.0.
- QA-D-19 (v2 make_figures dead code) remains OPEN, non-blocking (frozen
  v2 tooling behavior; disposition: document, do not patch v2).

### Agent 13 addendum (2026-07-15) — hosted CI findings

- **D-V3-04 (P3, environment):** NR3-001 byte-equality fails on hosted
  ubuntu-latest even with numpy pinned to the golden version 2.4.4
  (case_a_white_noise.csv drifts; the Windows drift was case_e). The
  golden CSVs record their full generation environment
  (archive/v2.0.0/release/PROVENANCE.json: Python 3.11.15 GCC 13.3.0,
  numpy 2.4.4, scipy 1.17.1). Repair sequence: (1) pin scipy==1.17.1 in
  the CI reference job; (2) if byte-equality still drifts, adopt the
  documented fallback: the byte-exactness guarantee is scoped to the
  ARCHIVED v2 build environment (where it was verified at v2 release,
  with recorded checksums); hosted CI verifies tolerance-aware numerical
  equivalence on every platform and deselects only that exact node id.
  Either endpoint keeps determinism tests strong everywhere else.
- **D-V3-04 CLOSED (2026-07-15):** resolved via the pre-registered
  fallback endpoint. New portable test
  test_generator_numerically_equivalent regenerates the goldens on EVERY
  platform (string cells/headers exact; numeric cells within one printed
  unit, 2e-8; manifest floats within max(2e-8, 1e-9 rel) with per-field
  mismatch reporting); byte-equality test scoped to the archived v2 build
  environment and deselected by exact node id in all hosted CI jobs.
  Hosted matrix green: ubuntu/windows/macos x 3.11/3.13 + pinned
  reference.

### Post-release figure-rendering audit (2026-07-15, user report)

- **D-V3-05 (P3, FIXED):** README PNG `docs/images/anisotropy_sweep.png`
  showed raw mathtext (`\{qL}(\theta)$`) — the one-off shell generation
  escaped the `$` characters. Fix: permanent generator
  `tools/make_readme_images.py` with correct raw-string labels; PNGs
  regenerated and visually verified.
- **D-V3-06 (P3, FIXED):** generated macros gvPelDn/gvMTwo rendered
  scientific notation as ASCII ("-2.95e-08") in the Crystal Application
  manuscript. Fix: macros now emit siunitx `\num{}`; manuscript rebuilt
  (0 undefined / 0 overfull) and visually verified as -2.95 x 10^-8 and
  7.01 x 10^-16.
- Full-figure audit performed: all three v3 manuscript figure PDFs, all
  four manuscript PDFs (TikZ + captions + equations), README PNGs, and
  v2 spot-checks render correctly. Known-accepted: frozen v2
  fig_epsilon_map title uses the ASCII style ("1.125e-03") — v2 shipped
  record, not modified; registry-verbatim ASCII strings (E^3, g^(2)) in
  generated tables are data faithfulness, not rendering defects.

### RGCS v4 (v4-dev branch) — Agent 00 finding (2026-07-16)

- **V4-D-001 (P1, OPEN):** CPU FEM eigensolver does not reproduce the
  analytic cantilever eigenfrequency (RSCS2-V.2): computed first flexural
  mode ~4-22x too low and *decreasing* with mesh refinement, across
  ElementHex1 and ElementVector(ElementTetP2()) on init_tensor meshes.
  Ruled out: BC application, matrix symmetry (~1e-16), mesh geometry
  (bbox exact), material (c correct); dense eigh cross-check confirms the
  assembled (K,M) pair is mesh-dependently wrong. Fix path: single-element
  patch tests, gmsh-generated well-shaped tet beam, per-element Jacobian
  verification, static-deflection patch test. BLOCKS the M3 gate and any
  v4 release. Documented before fix (QA discipline).
