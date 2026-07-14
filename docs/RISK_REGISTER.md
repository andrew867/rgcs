# RGCS v2 — Risk Register

**Author:** Sub-Agent 09. **Date:** 2026-07-14. Severity: H/M/L ×
likelihood: H/M/L. Status reflects release 2.0.0.

| ID | Risk | Sev/Lik | Mitigation | Status |
|---|---|---|---|---|
| R-01 | **Numerology / post-hoc pattern mining** — the 4096 ladder and compact spectrum invite coincidence-hunting | H/H | Pre-registered statistics with look-elsewhere controls (`STATISTICAL_ANALYSIS_PLAN.md`); scrambled-label controls; D-22 warning on the "nearest 4096 N" column | Mitigated, permanent vigilance |
| R-02 | **Misreading Hypothesis outputs as validated physics** | H/M | Binding classification policy; machine-checked labels; UI badges; forbidden-vocabulary lint over core + desktop (QA-D-11 closed) | Mitigated |
| R-03 | **Human-loading branch harms or overclaims** | H/L | Ethics gate (hard, schema-level) on human-loading manifests; explicit human-loading boundary in manuscript; `SAFETY_AND_ARTIFACT_CHECKLIST.md` | Mitigated |
| R-04 | **Equation-level error ships in a pre-registered gate** (realized once: QA-D-04, K = πg wrong) | H/M | Independent adversarial QA with numeric re-implementation caught it; corrected to \|K\| = 2πg (anti-Hermitian) with regression tests; erratum trail in MATHEMATICAL_MODEL.md, CORE_API_SPEC.md, manuscript B.4 | Closed for M.46; residual risk on untested equations low (14/14 QA-checked correct otherwise) |
| R-05 | **Reference misquotation undermines source-audit credibility** (realized: QA-D-01/02) | M/M | Bibliography now verified against page 1 of each source PDF; fixed gan2025/koster2026 | Closed |
| R-06 | **Workspace data loss** | H/L | Atomic writes, backup-on-open, integrity gate before backup, `WorkspaceError` + restore path (QA-D-05 closed); residual: unbounded backup growth (QA-D-23) | Largely mitigated |
| R-07 | **Isotropic wave-speed systematic** (D-05: single v_L=6310 m/s for trigonal quartz) | M/H | UncertainValue σ bands on all ladder outputs; anisotropy module for measurement; calibration campaign required before any length claim tighter than a few percent | Open, documented |
| R-08 | **Archival corpus errors propagate** | M/M | Source claims never feed computations without a Derived re-derivation; corpus arithmetic errors corrected as worked examples | Mitigated |
| R-09 | **Manuscript/code drift** | M/M | All numerics generated at build time; regeneration byte-diff in QA; hand-typed numeral eliminated (QA-D-26 closed via `\gvHalfNominal`) | Mitigated |
| R-10 | **Job-cancellation edge cases** (QA-D-14: SIGTERM only, shared queue) | L/L | Adversarially tested clean today; documented limitation; backlog item | Accepted |
| R-11 | **Windows build unverified** — release built/tested on Linux only | M/M | Reproducible-build instructions (`tools/packaging/build_windows.md`); PyInstaller spec is OS-agnostic; smoke-check flag (`--smoke-check`) for post-build verification | Open, documented in RELEASE_NOTES |
| R-12 | **Dependency drift** (numpy/scipy/pydantic majors) | M/M | Version floors in pyproject; exact build-environment versions recorded in `release/PROVENANCE.json` | Mitigated |
| R-13 | **SCAD compact-mode defect misleads CAD users** (D-02, inert flag) | L/M | Shipped unmodified for provenance with a prominent warning + workaround in `scad/README.md` | Accepted, documented |
