# RGCS v2 — Implementation Plan (as executed)

**Author:** Sub-Agent 09. **Date:** 2026-07-14. This records the plan the
project actually followed (nine sequential sub-agent work packages), each
with its binding deliverables; it is retained so a future revision can
follow the same discipline.

| # | Work package | Deliverables (all in-repo) |
|---|---|---|
| 01 | Source ingestion & evidence ledger | `SOURCE_EVIDENCE_LEDGER.md`, `SOURCE_DELTA_REPORT.md`, `INCONSISTENCY_REGISTER.md` (D-01..D-24 + WB-SO addendum), `SCIENTIFIC_CLASSIFICATION_POLICY.md`, `PROVENANCE_REGISTER.csv` |
| 02 | Mathematical foundations | `MATHEMATICAL_MODEL.md` (RGCS-M.1..M.61), `model_registry.yaml`, `NOTATION_AND_UNITS.md`, `DIMENSIONAL_ANALYSIS.md`, `MODEL_ASSUMPTIONS.md` |
| 03 | Coherence & dynamics spec | `COHERENCE_METRICS.md` (COH-M1..M14), `DYNAMIC_COHERENCE_SPEC.md`, `COHERENCE_TEST_MATRIX.md`, normative generator `tools/generate_golden_coherence.py`, golden datasets + manifest |
| 04 | Computational core | `rgcs_core/` (11 packages), `CORE_API_SPEC.md`, core test suites, `archive/v2.0.0/release/test_report_core.md` |
| 05 | Desktop workbench | `rgcs_desktop/` (13 panels), `DESKTOP_PRODUCT_SPEC.md`, `DESKTOP_ARCHITECTURE.md`, `USER_GUIDE.md`, UI/integration tests, packaging specs |
| 06 | Experiment kit | `experiments/` schemas, 8 branch templates, `CONTROL_MATRIX`, `EXPERIMENT_PROTOCOL.md`, `STATISTICAL_ANALYSIS_PLAN.md`, `ROADMAP_TO_FALSIFICATION.md`, `SAFETY_AND_ARTIFACT_CHECKLIST.md` |
| 07 | Manuscript | `manuscript/rgcs_v2.tex` + generated figures/tables/macros via `tools/make_figures.py`, `tools/make_tables.py`; `LAYOUT_QA_REPORT.md` |
| 08 | Independent adversarial QA | `QA_REPORT.md` (verdict YELLOW), `DEFECT_REGISTER.md` (QA-D-01..26), `CLAIM_AUDIT.md`, `REPRODUCIBILITY_AUDIT.md` — nothing fixed by QA |
| 09 | Integration & release (this package) | All P1 defects fixed + P2 hardening; docs completion; `release/` artifacts (test results, example bundle, source zip, manuscript PDF, SHA256SUMS, PROVENANCE.json, RELEASE_NOTES); `RELEASE_CHECKLIST.md` gate walk |

## Sequencing rules that made this work

1. **Contract before code**: the model registry and coherence spec were
   frozen before `rgcs_core` was written; the golden generator is the
   normative implementation and the core is an exact port.
2. **Core before UI**: the desktop consumes only the public core API.
3. **Adversarial QA before release**, with a strict "QA fixes nothing"
   rule so defects are documented, prioritized, and fixed under
   integration control (this package) with regression tests.

## Post-2.0.0 backlog (not release-blocking)

- QA-D-14 SIGKILL escalation for stuck cancelled jobs; per-job queues.
- QA-D-20 `micro_pulse_metrics` default rise time 1.0 → 1.3 µs review.
- QA-D-22 `UncertainValue` u_rel ≥ 1 handling (report, don't raise).
- QA-D-23 backup rotation policy.
- D-02 SCAD compact-mode rings fix (see `scad/README.md`).
- Windows binary build (documented path, not yet produced in this
  Linux-only environment).

## v3 Agent 08 addendum

Tranches T1-T6 with dependency graph in
`docs/SOFTWARE_HARDWARE_ARCHITECTURE.md` section 8. T1 (fixes, CI,
persistence, FEA, headless services, embedded contracts) is COMPLETE in
this commit; T2 desktop panels consume the tested headless services; T4/T5
firmware/hardware are ENG until built and measured.
