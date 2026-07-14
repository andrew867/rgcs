# RGCS v2 — Resonant Geometry Computational System

Version 2.0.0 (2026-07-14). MIT license. Author: Andrew Green.

RGCS v2 is a research instrument — a computational core, a desktop
workbench, an experiment kit, and a fully generated manuscript — for
studying acoustic/mechanical resonance and phase coherence in engineered
quartz geometries (faceted crystals, harmonic-length ladders, logarithmic
spiral cones).

## Honest scope — read this first

**No RGCS hypothesis has been experimentally confirmed.** This release
contains zero measurements of real crystals. What it contains is the
machinery to test the project's 14 pre-registered hypotheses honestly:
every hypothesis ships with an observable, a matched control, a failure
condition, and an uncertainty statement (manuscript Table 9,
`docs/ROADMAP_TO_FALSIFICATION.md`).

**Classification policy (binding, machine-checked)** — every scientific
statement in code, docs, UI, and manuscript carries one of four labels
(`docs/SCIENTIFIC_CLASSIFICATION_POLICY.md`):

- **Established** — textbook math/physics anyone can verify independently.
- **Derived** — computed within RGCS from stated inputs by stated math;
  inherits the weakest label of its inputs.
- **Hypothesis** — an RGCS conjecture that measurement could falsify;
  never presented as fact.
- **Source claim** — a statement by an external source (archival corpus or
  the three reference papers' domain conclusions), reported with
  provenance, not endorsed.

The project makes **no therapeutic, medical, cosmological, or
consciousness claims**. The three peer-reviewed reference papers (Lee &
Tsai 2026; Gan et al. 2025; Koster et al. 2026) contribute *mathematical
templates and measurement methodology only* — their physics stays in their
domains. A forbidden-vocabulary lint enforces this in the test suite.

## Repository layout

- `rgcs_core/` — deterministic, typed library implementing the 61
  registered equations (`docs/model_registry.yaml`); classification
  metadata on every claim-bearing function.
- `rgcs_desktop/` — PySide6 desktop workbench (13 panels): workspaces,
  source import with checksums, spectra, experiment builder with schema
  validation and ethics gate, background analysis jobs, reproducibility
  bundles.
- `manuscript/` — `rgcs_v2.tex` (28 pp.); every figure/table/inline value
  generated from `rgcs_core` by `tools/make_figures.py` /
  `tools/make_tables.py`.
- `experiments/` — JSON schemas, 8 experiment-branch templates, control
  matrix, golden sample data.
- `scad/` — OpenSCAD CAD generators (provenance-preserved; see
  `scad/README.md` for a known defect and workaround).
- `tests/` — 227 automated tests (unit, property, golden, regression,
  UI smoke, integration).
- `docs/` — the full specification, QA, and audit trail.
- `release/` — release artifacts, checksums, provenance manifest.

Note: `EXPECTED_TREE.md` lists a `package.json`; this project is a
pure-Python stack (no Node toolchain), so no `package.json` ships — the
deviation is recorded here and in `docs/RELEASE_CHECKLIST.md`.

## Install

```bash
python3 -m pip install .              # core library only
python3 -m pip install ".[desktop]"   # + desktop workbench
python3 -m pip install ".[desktop,dev]"  # + test tooling
```

Requires Python ≥ 3.11.

## Run

```bash
python3 -m rgcs_desktop               # desktop workbench
python3 -m rgcs_desktop --smoke-check # headless packaging self-test
QT_QPA_PLATFORM=offscreen python3 -m pytest   # full test suite (227)
```

## Build the manuscript

```bash
python3 tools/make_figures.py
python3 tools/make_tables.py
cd manuscript && latexmk -xelatex rgcs_v2.tex
```

## Build a desktop binary

Linux: `tools/packaging/build_linux.sh` (PyInstaller; output under
`release/linux/`). Windows: reproducible instructions in
`tools/packaging/build_windows.md` (no Windows artifact is included in
this release; built and tested on Linux only).

## Citing

See `CITATION.cff`. Release provenance (input checksums, build
environment, package versions): `release/PROVENANCE.json`.
