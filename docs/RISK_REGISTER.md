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

## v3 Agent 08 additions

| ID | Risk | Mitigation |
|---|---|---|
| R-08-1 | ESP32 internal crystal drift (10-40 ppm) invalidates phase claims | TCXO reference mandatory (architecture section 7); H-29 gate blocks phase claims without calibration |
| R-08-2 | SD-card config could loosen safety limits | limits compile into firmware; config may only tighten (HG OS contract section 2) |
| R-08-3 | Schema migration hook missing on future version bump | migrate() fails loudly; CI runs the migration tests |
| R-08-4 | Desktop panels drift from headless services | panels are thin views over tested services (T2 rule); services carry the tests |
| R-08-5 | CPLD dead-time logic is safety-relevant | classified ENG until measured; interlock loop is hardware and independent of it |

## RGCS v4 additions (planning; full table docs/plans-v4/V4_RISK_REGISTER.md)

| id | Risk | Mitigation |
|---|---|---|
| RV4-02 | Gmsh GPL contaminates MIT | Gmsh as external subprocess only; meshio (MIT) bridge (DV4-006) |
| RV4-03 | No GPU hardware -> acceleration unverifiable | four-status ladder; ship experimental; CPU stays authority (DV4-007) |
| RV4-04 | Eye diagnostics over-interpreted as physical | SRC/DER/HYP only; robustness battery; NULL verdict; exclusion lint (DV4-010) |
| RV4-08 | Conservative-extension anchor fails -> v4 diverges from v3 | V.6/V.9 hard gates at M4/M8; halt, never loosen tolerance |
| RV4-14 | Frozen v3/v2 modified | CI frozen-path diff gate; anchors read frozen modules read-only |
