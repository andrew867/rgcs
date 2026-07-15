# RGCS v2 — System Specification

**Author:** Sub-Agent 09 (Integration & Release), consolidating the briefs and
handoffs of Sub-Agents 01–08. **Date:** 2026-07-14. **Version:** 2.0.0.

## 1. What RGCS v2 is

The Resonant Geometry Computational System v2 is a research instrument for
studying acoustic/mechanical resonance in engineered quartz geometries. It
consists of:

1. **`rgcs_core`** — a deterministic, typed, tested Python library
   implementing the 61 registered equations RGCS-M.1..M.61
   (`docs/model_registry.yaml`): geometry (faceted/tapered/double-terminated
   volumes, log-spiral cones), harmonic ladders, compact-coordinate mode
   spectra, resonance-offset classification, coupled-mode eigenproblems,
   Stuart–Landau amplitude–phase dynamics, coherence metrics
   (COH-M1..M14), spatial phase anisotropy, loading, and drive families.
2. **`rgcs_desktop`** — a PySide6 desktop workbench (13 panels) covering
   the full loop: workspace → source import → specimen → spectrum →
   experiment definition → analysis job → results → reproducibility bundle.
3. **Manuscript** — `manuscript/rgcs_v2.tex` (28 pp.), every figure, table,
   and inline numeral generated from `rgcs_core` at build time.
4. **Experiment kit** — JSON schemas, branch templates (8 branches),
   control matrix, golden sample data (`experiments/`).
5. **CAD** — OpenSCAD generators (`scad/`, provenance-preserved).

## 2. What RGCS v2 is NOT

- Not a claim that any RGCS hypothesis is true: all 14 hypotheses
  (H-01..H-14) are pre-registered with observables, controls, failure
  conditions, and uncertainty statements — none has been tested on hardware.
- Not a data-acquisition or instrument-control system.
- No therapeutic, medical, cosmological, or consciousness claims; see
  `docs/SCIENTIFIC_CLASSIFICATION_POLICY.md` (binding) and quality gate 7.

## 3. Normative requirements

| ID | Requirement | Verified by |
|---|---|---|
| R-01 | Every claim-bearing public core function carries a machine-checked classification label (Established / Derived / Hypothesis / Source claim) | `tests/unit/test_experiments_provenance.py` |
| R-02 | Every implemented equation references a registry id RGCS-M.x | registry `module_target` fields; provenance decorators |
| R-03 | All manuscript numerics are generated (figures, tables, `\gv` macros), never hand-copied | `tools/make_figures.py`, `tools/make_tables.py`; QA gate 2 |
| R-04 | Golden values reproduce exactly (ledger Part E; coherence manifest) | `tests/golden`, `tests/regression` |
| R-05 | Randomness is seeded and reproducible; JSON never contains NaN/inf (null instead) | property/unit tests; D-03 policy |
| R-06 | Unit conversions appear exactly once per function, commented | code review; `docs/NOTATION_AND_UNITS.md` |
| R-07 | Desktop enforces the classification policy in the UI (badges, gates, ethics block for human-loading manifests) | `tests/ui`, `tests/integration/test_vertical_slice.py` |
| R-08 | Workspaces are data-safe: atomic writes, backup-on-open, no silent overwrite, corruption surfaced as `WorkspaceError` with backup restore | `tests/unit/test_qa_hardening.py` |
| R-09 | Reproducibility bundles carry CHECKSUMS.json + VERSIONS.json and detect tampering | bundle round-trip tests |
| R-10 | Coherence is always reported as the triplet (C_w, w, b_w) | core docstrings; analyzer UI; manuscript |
| R-11 | Time-/frequency-domain coupling fits must satisfy \|K\| = 2πg (anti-Hermitian K = i·2πg; QA-D-04 erratum) | `tests/regression/test_qa_d04_coupling_map.py` |
| R-12 | Forbidden-vocabulary lint over `rgcs_core` and `rgcs_desktop` | provenance tests (QA-D-11) |

## 4. Interfaces

- Core API: `docs/CORE_API_SPEC.md` (module-by-module, units, contracts).
- Desktop: `docs/DESKTOP_PRODUCT_SPEC.md`, `docs/DESKTOP_ARCHITECTURE.md`,
  `docs/USER_GUIDE.md`.
- Data: `docs/DATA_SCHEMA.md`; JSON schemas in `experiments/schemas/`.
- Protocols: `docs/EXPERIMENT_PROTOCOL.md`,
  `docs/STATISTICAL_ANALYSIS_PLAN.md`, `docs/ROADMAP_TO_FALSIFICATION.md`.

## 5. Environments

Python ≥ 3.11; numpy ≥ 1.26, scipy ≥ 1.11, pydantic ≥ 2.5; desktop extra:
PySide6 ≥ 6.6, pyqtgraph ≥ 0.13; dev extra: pytest, hypothesis, pytest-qt.
Headless test runs use `QT_QPA_PLATFORM=offscreen`. Manuscript builds with
`latexmk -xelatex`.

## v3 Agent 08 addendum

Platform/portability spec for v3 lives in
`docs/SOFTWARE_HARDWARE_ARCHITECTURE.md` (single source of truth):
layering (rscs_core reusable library), V2-WIN-01 fix, Windows CI matrix,
persistence contracts (crystal DB, HG store, FEA export), desktop v3 view
contracts, HG Embedded OS contract (`embedded/`), quantified timing
hardware roadmap, tranche graph T1-T6.
