# RGCS v2 Desktop Research Workbench — Product Specification

**Author:** Sub-Agent 05 (Desktop Research Workbench)
**Date:** 2026-07-14
**Status:** Implemented in `rgcs_desktop/` (PySide6 + pyqtgraph); entry point
`python -m rgcs_desktop`. This spec maps every user-facing feature to its
implementation and to the quality gates it satisfies.

## 1. Product intent

A single desktop environment for the whole RGCS v2 research loop: register
sources, define specimens, compute model predictions, plan experiments,
analyze measured time series, compare model vs measurement, and export
reproducible reports and bundles — with the scientific-classification
policy enforced *in the UI*, not just in the docs.

Non-goals: data acquisition/instrument control (manifests reference data
files; the workbench never talks to hardware), statistical claim
adjudication (STATISTICAL_ANALYSIS_PLAN.md governs that), and cloud sync.

## 2. Scientific-integrity rules enforced by the UI (binding)

| Rule | Where enforced |
|---|---|
| Every claim-bearing display carries a classification badge (Established / Derived / Hypothesis / Source claim) | `widgets/badges.py`; all panels; right inspector |
| Ladder/compact frequencies are `UncertainValue`s — rendered as `mean ± σ [lo, hi] (1σ)`, never bare points | `services/formatting.format_uncertain`; spectrum plot draws 1σ bands (`plots/uncertainty.py`) |
| `measured_node_mm` may be `None` → displayed "not measured", never NaN | `services/formatting.format_node_mm`; specimen editor |
| `classify_resonance` requires `u_eps`; the UI supplies it (model σ ⊕ measurement u) | comparison view (`viewers/comparison_view.py`) |
| merit-score / resonance-class outputs carry "not evidence" notes → surfaced as badges/labels | comparison view badge; coherence analyzer classification |
| `pulses_per_period` exposed as an explicit control (RG-14) | pulse designer |
| Source presets render under Source-claim banners | pulse designer, source library (`SourceClaimBanner`) |
| Coherence-claim workflows gated on `post_drive_ratio >= 2.5` AND `n_runs >= 100` | `services/gates.coherence_claim_gate`; coherence analyzer claim button |
| human_loading manifests require the ethics block (hard gate) | `services/gates.ethics_gate`; experiment builder treats failures as errors |
| Unknown major `schema_version` is refused | `services/schemas.check_schema_version` |

## 3. Features by panel

1. **Workspace browser** — object registry (id/kind/name/sha256), imported
   files with checksums, export history.
2. **Source library** — import any file (copied under its sha256, checksum
   recorded), citation registration, provenance JSON view, drive source
   presets under a Source-claim banner.
3. **Specimen/geometry editor** — crystal form (L, D_w, D_n, N_f, angles,
   density, diameter/angle modes, measured node, measured mass) and spiral
   form (q, T, R_0, H, p_z, Ω_s); derived mass/volume/node positions/axial
   half-wave (interval); 2D projection preview (pyqtgraph); OpenSCAD export
   preview (text); save to workspace.
4. **Model editor/browser** — all 61 `docs/model_registry.yaml` entries with
   classification badges, filter, YAML detail, inspector shows equation,
   input units and sources.
5. **Compact-mode spectrum** — `compact_mode_spectrum` with f_b, u(f_b),
   v_chi (+u_rel), R_chi, n_max, parity, zero-mode toggle; 1σ bands;
   Hypothesis badge; κ_χ interval; save-as-artifact.
6. **Avoided-crossing explorer** — interactive g slider (0–50 Hz), hybrid
   branches vs uncoupled lines, 2g splitting and strong-coupling ratio R_g.
7. **Phase/coherence analyzer** — CSV loader (I/Q or real column), window/hop
   controls (defaults = golden analysis parameters), background-process job,
   C_w plot **with baseline** (C, w, baseline reported together), amplitude
   and phase plots, Rayleigh test, onset/decay times; claim gate (above).
8. **Pulse timing designer** — exact-cycle families 2261/1508/1131
   (standard / half_spacing / double_rate), exact ms timings, phase residue
   (cycle counts only, D-13), micro-pulse metrics with `pulses_per_period`,
   source presets under a Source-claim banner.
9. **Experiment builder** — full run-manifest form (branch, hypotheses,
   control role, specimen from workspace, drive, acquisition incl. n_runs
   and post-drive coverage, ethics block, data CSV with auto sha256);
   validates against the JSON-schema set using the same registry as
   `experiments/schemas/validate.py`; live gate display; atomic save to
   `manifests/` + workspace object.
10. **Results/artifact browser** — content-addressed artifacts with JSON
    viewer; error artifacts appear here too.
11. **Comparison view** — model spectrum (1σ bands) vs measured peaks
    (entered list), per-peak ε, u(ε) and resonance class with the
    "engineering heuristic - not evidence" note.
12. **Report generator / bundle export** — markdown workspace report;
    reproducibility zip (workspace.db, sources, artifacts, manifests,
    reports, CHECKSUMS.json, VERSIONS.json) with post-export verification.
13. **Settings** — display units, default workspace path (QSettings).

Shell: left navigator (workspaces/specimens/models/experiments/sources/
results), central tabs, right inspector (properties/classification/units/
provenance), bottom jobs+logs+warnings dock, command palette (Ctrl+K, 19
actions), layout persisted via QSettings.

## 4. Quality-gate mapping

| Gate | Evidence |
|---|---|
| Vertical slice (gate 6): workspace → specimen → spectrum → validated experiment → background coherence job on sample data → results → repro bundle | `tests/integration/test_vertical_slice.py` (10 tests, offscreen, real app objects) |
| UI smoke: window opens, panels construct, palette lists actions, job queue processes trivial job, cancellation works | `tests/ui/test_smoke.py` (13 tests) |
| Data safety: atomic saves, backup-on-open, schema_version + migration hook, no silent overwrite, deterministic artifact ids, import checksums | `workspaces/workspace.py`; asserted in vertical-slice tests |
| Background jobs: process-based, progress/cancel/logs, immutable versioned inputs/outputs, errors preserved as artifacts, UI thread never computes | `jobs/manager.py`, `jobs/workers.py`; smoke tests |
| Packaging | `tools/packaging/` (Linux build verified incl. frozen job smoke check; Windows documented, unverified) |

## 5. Out of scope / known gaps (honest)

- 3D preview is a 2D projection (profile / plan view), not a rotatable 3D
  scene; SCAD text preview is provided instead of rendered SCAD.
- Notebook-style calculation history from the original brief is **not
  implemented** (results/artifact browser + job log is the closest analog).
- Experiment-control **matrix** editor is not a dedicated panel; control
  roles are set per manifest in the experiment builder.
- Comparison view takes measured peaks as a typed list, not from a fitted
  peak-picker.
- Report generator emits markdown only (no PDF).
