# Independent Adversarial QA Report — RGCS v3 / RSCS 1.0 (Agent 10)

**Date:** 2026-07-15. **Scope:** everything Agents 01–09 produced, plus
all remaining v2/v3 register defects. Method: fresh execution of every
machine gate + adversarial spot checks; defects documented BEFORE fixes
(fixes belong to Agent 11). The v2 report (`QA_REPORT.md`) is retained
unchanged as the v2 record.

## 1. Verdict summary

**Recommendation: YELLOW → GREEN after Agent 11 fixes D-V3-01..03.**
No mathematical, provenance, or safety defect was found. The three new
defects are editorial/reproducibility-of-metadata issues, all
mechanically fixable. One inherited platform limitation remains
documented (NR3-001), and one honest gap is recorded (Linux CI defined
but not yet executed).

## 2. Review dimensions and results

| Dimension | Method | Result |
|---|---|---|
| Equation correctness | full suite (376 pass) incl. closed-form checks: Christoffel axis speeds = √(c/ρ); dispersion derivative; critical-coupling zero; beating length; closures 512/187 | PASS |
| Units | unit-suffixed identifiers; siunitx in manuscripts; M2 formula validated against fused-silica literature value (±5 %) | PASS |
| Sign conventions / anti-Hermitian coupling | source scan: no real-symmetric `π·g` in libraries; K†=−K asserted; forbidden-convention growth contrast test present | PASS |
| Conservative-extension compliance | live `run_all_cep()` → all_ok True; regression battery in suite | PASS |
| Source-page/equation verification | adversarial lint (6 tests) re-hashes PDFs and verifies EP locations | PASS |
| Bibliography | v3 builds: 0 undefined citations; QA-D-02 (Koster) verified fixed in the v2 bib; handbook entries checked (Bechmann 1958 PhysRev 110:1060 correct) | PASS |
| Claim classification | every `rgcs_core` public fn carries `@classified` (suite gate); rscs firewall tests pass; manuscripts tag every physics statement | PASS |
| Source-to-claim firewall | `assert_no_src_upgrade` tests; H-2x rows all carry failure conditions; historical companion keeps authorship | PASS |
| Registry completeness | fresh script: 40 ids (17 C + 23 O), no dupes, every module resolves, every entry has tests, OPERATORS/COORDINATE_TYPES complete, ledger↔registry id sets consistent | PASS |
| Code/document agreement | generated-number discipline; **D-V3-01 found** (see §3) | 1 DEFECT |
| Generated-number reproducibility | regenerate → tables/macros byte-stable; comparison table `--check` OK; **figure PDFs differ by embedded CreationDate (D-V3-02)** | 1 DEFECT |
| Manuscript layout | fresh log scan: 4 manuscripts, 0 undefined refs, 0 overfull boxes; landscape ledger renders | PASS |
| Cross-platform behavior | Windows/Py3.13: 376/377 pass (NR3-001 only, documented); vertical slice 10/10; Linux: CI matrix defined, **not yet executed** (gap, §4) | PASS w/ gap |
| Corrupted inputs / malformed workspaces | fuzz: garbage JSON, unknown schema versions, missing versions → all raise loudly (crystal DB, HG store); v2 workspace tests in suite | PASS |
| Experiment-schema validation | `validate.py`: 12 targets OK incl. optical probe + timing programme examples | PASS |
| Packaging | deps declared (pyyaml, jsonschema, referencing); registry yaml in package-data; **CITATION.cff still v2.0.0 (D-V3-03)** | 1 DEFECT |
| Safety language | D6/D7 envelopes present in schemas/docs/manuscripts; no human-exposure protocol representable; forbidden-vocabulary scan: all hits are prohibition statements | PASS |
| Licensing | MIT LICENSE present; all adapted math cites sources; no bundled third-party code | PASS |
| Unsupported claim detection | overclaim scan ("proves/confirms/demonstrates that quartz", therapeutic, healing): clean; null postures pre-registered | PASS |
| Historical-companion fidelity | authors retained; original terminology preserved; exclusions stated without ridicule; evidence boundary explicit | PASS |
| README portfolio/public claims | honest-scope retained; Lessons Learned accurate; **coordinate count wrong (part of D-V3-01)** | 1 DEFECT (shared) |
| Remaining v2/v3 register defects | D-02 (SCAD) fixed v7; QA-D-02 closed; V2-WIN-01 fixed+guarded; QA-D-19 (dead code in v2 make_figures) remains open-not-blocking (v2 tooling, frozen behavior) | PASS |

## 3. New defects (documented before fix; owner Agent 11)

- **D-V3-01 (P2, editorial/agreement).** The generated macro
  `\gvNumCoords` = 18 and README says "18 coordinates". Truth: 17
  RSCS-C ids (C.1–C.17). Cause: `tools/make_v3_artifacts.py` adds `+1`
  for C.15, but C.15 is already a registry row. Fix: drop the `+1`,
  regenerate, rebuild foundations manuscript, correct README.
- **D-V3-02 (P3, reproducibility).** Manuscript figure PDFs are not
  byte-reproducible: matplotlib embeds CreationDate. Fix: set
  `SOURCE_DATE_EPOCH` in `make_v3_artifacts.py` before importing
  matplotlib; regenerate; confirm regen-clean.
- **D-V3-03 (P2, packaging).** `CITATION.cff` still describes v2.0.0.
  Fix at release: title/version/date for 3.0.0.

## 4. Honest gaps (not defects)

- **Linux execution:** the CI matrix exists but no Linux run has executed
  in this environment; NR3-001's "passes on Linux reference platform"
  status is inherited from the v2 record, not re-verified today.
- **Manuscript depth:** the four manuscripts are concise generated-number
  spines (3–5 pp each) over the fuller repository docs — appropriate for
  this stage, stated in LAYOUT_QA_REPORT_V3.
- **Bench work:** all H-2x rows await hardware; nothing physical is
  confirmed (this is the programme's own stated status).

## 5. Gate recommendation

Proceed to Agent 11. Release may go GREEN only after D-V3-01..03 are
fixed and the full suite + regeneration checks re-run clean.
