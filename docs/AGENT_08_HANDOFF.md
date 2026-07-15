# Agent 08 Handoff — Software, Hardware, CAD, Platform, Portability

**Date:** 2026-07-15. **Status: COMPLETE (tranche T1), GREEN.** Consumers:
Agent 09 (manuscripts — esp. the Software & Hardware Architecture
manuscript), Agent 10 (QA), Agent 11 (release).

## Headlines

1. **The Windows portability debt is paid.** V2-WIN-01 fixed
   (`bundle.py` POSIX arcnames); the "specimen-listing defect" was
   re-diagnosed as a missing-`jsonschema` dependency (now declared); the
   vertical slice runs 10/10 on Windows. The only remaining inherited
   failure is NR3-001 (byte-equality of Linux-generated goldens —
   platform-documented, deselected in Windows CI).
2. **Windows CI exists:** `.github/workflows/ci.yml`, Linux+Windows ×
   Py3.11/3.13, with schema validation and generated-doc freshness gates.
3. **Persistence layer landed:** crystal DB (schema-versioned, migration
   hooks, uncertainty-aware), HG memory store (H-15/H-17/H-19 now
   machine-tested-pass), FEA export contract (sha256-verified material
   card from Agent 05 constants).
4. **Desktop v3 data layer:** provenance-graph and waveform/timing/
   phase-budget services are headless, deterministic, and tested; Qt
   panels are tranche T2 thin views.
5. **CAD:** SCAD v7 closes D-02 (inert compact-mode rings) with exactly
   one functional change; v6 retained verbatim; provenance in
   `scad/README.md`.
6. **Embedded:** HG Embedded OS contract + app-manifest schema published
   (ENG); quantified timing-hardware roadmap — TCXO reference mandatory,
   DDS for non-integer channels, CPLD justified for the complementary
   pair/dead-time safety function, **FPGA explicitly not justified**.
7. **Registry repair:** RSCS-C.16/C.17 rows were sitting in the operators
   list (Agent 06 YAML placement slip); moved to coordinates, content
   unchanged, pinned by the graph test (17 coordinates / 23 operators).

## For Agent 09 (next)

- The Software & Hardware Architecture manuscript should be built from
  `SOFTWARE_HARDWARE_ARCHITECTURE.md` + `HG_EMBEDDED_OS_CONTRACT.md` +
  the tranche graph; all hardware is ENG until measured.
- Open editorial defect QA-D-02 (Koster citation title/authors) is YOURS.
- Generated tables available: `docs/generated/OPTICAL_MECHANISM_COMPARISON.md`
  (+ regenerate check), provenance-graph counts
  (`build_provenance_graph()["counts"]`).
- Lessons-learned inputs now include: the QA-D-04 coupling correction, the
  conservative-extension discipline, AND the V2-WIN-01/jsonschema
  re-diagnosis (cross-platform lesson: declared deps + CI matrix).

## Test state after Agent 08

Full suite: **375 passed, 1 failed** — only NR3-001 remains (inherited,
documented, Windows-only byte-equality). Zero new regressions; 11 new
tests. Schema validation green (12 targets). Frozen paths verified
untouched.
