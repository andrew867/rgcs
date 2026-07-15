# RGCS — Resonant Geometry Computational System

Version 3 programme (RSCS 1.0) in progress; frozen baseline v2.0.0
(2026-07-14, tag `v2.0.0` / `archive/v2.0.0/`). MIT license.
Author: Andrew Green.

**What v3 adds** (all tested, all conservative extensions of the frozen
v2 mathematics): the typed RSCS coordinate/operator framework
(`rscs_core`, 18 coordinates + 23 operators with machine-checked
provenance), anisotropic Christoffel propagation resolving the v2 scalar
wave-speed hypothesis, an optical probe layer with pre-registered null
expectations, a synchronized coil/laser timing architecture with a
binding safety envelope, Windows portability fixes + two-OS CI, and four
generated-number manuscripts (`manuscripts/`). Programme ledger:
`docs/PROGRAMME_PROGRESS.md`.

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

## Lessons Learned

- Independent QA is most valuable when it is allowed to overturn the
  project's own mathematics. A v2 review found an incorrect time-domain
  coupling map; fixing it (anti-Hermitian `K = i·2πg`) changed the
  physical interpretation and produced a permanent regression test.
- Provenance and classification matter as much as equations. Separating
  Established, Derived, Hypothesis, Source, and Engineering claims
  allowed historical material to inspire tests without becoming evidence
  by repetition — and a machine-enforced firewall keeps it that way.
- Historical or unconventional claims can often be translated into
  measurable variables without presuming they are true: "the eye" became
  an eight-definition node menu with failure conditions; "a single
  crystal tone" became a scalar wave speed that anisotropic modelling
  then explained.
- A resonant system cannot be characterized by geometry and nominal
  frequency alone. Boundary conditions, anisotropy, mode overlap, phase,
  delay, damping, loading, uncertainty, and measurement fidelity all
  matter — the v3 phase-at-coordinate model exists because commanded
  phase is never the phase at the crystal.
- Cross-platform numerical reproducibility requires pinned reference
  environments plus tolerance-aware portability tests. Two of our
  "Windows defects" turned out to be an undeclared dependency; the third
  was a real path-separator bug. Declared environments and a two-OS CI
  matrix caught what code review had not.
- Frozen registries and conservative-extension tests made it possible to
  expand the framework without silently rewriting earlier results: v3
  provably reproduces v2 wherever it overlaps.
- Software and mathematical modelling advanced faster than the physical
  measurement programme. The project's strongest current output is a
  reproducible framework and falsification plan, not experimental
  confirmation — and every claim-bearing surface says so.
- Independent review, negative results, and explicit failure conditions
  strengthened rather than weakened the project.

A fuller engineering version lives in
`docs/SOFTWARE_HARDWARE_ARCHITECTURE.md` and the Software & Hardware
manuscript.

## Citing

See `CITATION.cff`. Release provenance (input checksums, build
environment, package versions): `release/PROVENANCE.json`.
