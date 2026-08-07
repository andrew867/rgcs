# Design Studio inventory (Phase 00)

Date: 2026-08-07 · Branch: `research/workbench-design-studio-v1` · Base commit: `a78a32e`

Scope: repo reconnaissance before implementing the RGCS Design Studio release pack
(`internal-docs/plans-v7/RGCS_Enterprise_UX_Docs_Installer_Workbench_Spec_Tests_Plans_v0_2_2026-08-07`).
No app code was modified in this phase.

## Entry points

- `pyproject.toml` (v8.3.0, Python >=3.11). Scripts: `rgcs-v4`, `rgcs-workbook`,
  `rgcs-coordinate`, `rgcs-lab`, `rgcs`. GUI script: `rgcs-workbench = rgcs_desktop.app.main:main`.
- Optional groups: `desktop` (PySide6, pyqtgraph), `workbook`, `fem`, `packaging`
  (pyinstaller), `workbench` (fastapi/uvicorn/httpx), `archive`, `dev` (pytest,
  hypothesis, pytest-qt, jsonschema, referencing, ...).
- Root `README.md` documents the research lanes and the map workbench quickstart; the
  desktop workbench appears only as one row in the Applications table. No task-first
  user path exists yet — that is the gap Design Studio fills.

## Docs index

- `docs/README.md` is the index (Start here / Governance / Engineering / QA / Releases).
- `docs/user/` and `docs/developer/` exist but only contain `rgcs_lab` guides.
- Desktop docs: `docs/DESKTOP_ARCHITECTURE.md`, `docs/DESKTOP_PRODUCT_SPEC.md`,
  `docs/workbench/{INSTALLATION,QUICKSTART,CONCEPTS_AND_CLAIM_BOUNDARIES,RGCS_LAB_CLI}.md`.
- `docs/reports/` did not exist before this file.

## Desktop app architecture

- Package `rgcs_desktop` (`__version__ = "3.0.1"`, disagrees with dist 8.3.0 — see skew note).
- `app/main.py` → `main()`: headless subcommands (`--doctor`, `--build-info`,
  `--print-startup-plan`, `--export-workbook`, `--first-run-selftest`, `--smoke-check`)
  then Qt app. `--smoke-check` constructs the full `MainWindow` and runs a real job.
- `app/main_window.py`: `MainWindow(QMainWindow)` — central `QTabWidget`, left Navigator
  dock, right Inspector dock, bottom Jobs/Logs/Warnings dock. Panels come from a
  module-level `PANEL_CLASSES` list literal (14 panels, eagerly constructed, keyed by
  `cls.TITLE`). Command palette (Ctrl+K) auto-generates "Open panel: {title}" commands.
- Panel contract: `viewers/base.py` — `TITLE`, signals `inspector_changed` /
  `status_message`, `inspector_info()` returning `properties/classification/units/provenance`,
  `refresh()`. Smallest example: `viewers/settings_panel.py`. Best generate/export donor:
  `viewers/report_panel.py`. Closest existing Design-Studio-like panel:
  `viewers/pulse_designer.py` (exact-cycle families, 4096 Hz default carrier).

## Services

- `services/formatting.py` — classification colors/labels (Established/Derived/Hypothesis/Source claim).
- `services/schemas.py` — loads `experiments/schemas/validate.py` by path; Draft 2020-12 +
  `referencing`; refuses schema major != 1.
- `services/report.py` — markdown report generation with atomic write + `record_export`.
- `services/bundle.py` — deterministic zip bundle + `CHECKSUMS.json` + `verify_bundle`.
- `services/manifests.py`, `services/gates.py`, `services/registry.py`,
  `services/scad.py` (crystal/spiral SCAD text), `services/provenance_graph.py` and
  `services/waveform_preview.py` (both currently unconsumed by any viewer).
- Hash primitives: `rgcs_core.provenance` (`sha256_file`, `sha256_of_jsonable`, `json_dumps`).

## Reusable calculation code

- Sidebands: `fkey_instrument/relations.py::am_sidebands` (exact `Fraction` arithmetic),
  plus `r13/heterodyne.py` mixing helpers.
- Pulse/envelope: `rgcs_core.drive` (`DRIVE_PRESETS`, `drive_sequence`,
  `micro_pulse_metrics`), `rgcs_core.timing`, `services/waveform_preview.py`.
- Frequency keys: `rscs2_core/frequency_keys.py` (F001–F052 registry with
  `ARITHMETIC_ONLY_NOTE` auto-disclaimer) and `fkey_instrument/relations.py::SEED_KEYS`.
  925 Hz lives in the `r10` lane (`Fraction(925, 4096)` phase-frame work; 925 = 5^2 * 37).
  963 and 1337 are not registered keys anywhere in the repo today.

## Export capability gaps

- No PDF writer anywhere (report output is markdown; `pypdf` is CI-only, read-only).
  Design Studio adds Qt-based PDF rendering (`QPdfWriter`/`QTextDocument`) — no new deps.
- No SVG generation anywhere. Design Studio adds plain-XML SVG writers.
- No desktop STL service; `r1015a/scad.py` explicitly refuses in-process STL and requires
  external OpenSCAD. Design Studio follows the same refusal pattern when OpenSCAD is absent.

## Tests and CI

- 474 test files / ~8.1k tests. UI tests: `tests/ui/` (pytest-qt, offscreen platform set in
  `tests/ui/conftest.py`; fixtures `app_context`, `main_window`).
- CI (`.github/workflows/ci.yml`): 3-OS matrix, installs `[desktop,dev,workbook,workbench]`
  + pypdf; runs `python -m pytest -q` with one deselect; schema lint via
  `python experiments/schemas/validate.py`.

## Packaging

- `tools/packaging/rgcs_desktop.spec` (onedir `rgcs-workbench`) + `build_linux.sh` +
  `make_release.py`; `packaging/RGCSWorkbench.spec` + `RGCS_Workbench.iss` (Inno Setup).
- The two specs bundle different `datas` sets; `tests/v4/test_v45_packaging.py`
  polices spec/runtime-data parity.

## Guard-rails that constrain this work (blocker list)

1. `tests/ui/test_smoke.py` asserts the panel-title set with exact equality — must be
   updated in the same change that adds panels.
2. `PANEL_CLASSES` is a hand-maintained list; panels are eagerly constructed, so a panel
   that raises in `__init__` breaks startup and `--smoke-check`. Use the
   `evidence_ledger_panel.py` try/except pattern for optional data.
3. Panel titles are simultaneously captions, dict keys, and command names; hard-coded in
   several places.
4. `SIDEBAR_SECTIONS` string surgery (`section.lower().rstrip("s")`) constrains new
   sidebar sections.
5. `restoreState()` requires unique dock objectNames.
6. Any new runtime data file must be added to both PyInstaller specs and
   `[tool.setuptools.package-data]` (`tests/v52/test_r10_install_parity.py`,
   `tests/v4/test_v45_packaging.py` enforce this).
7. Claim firewall scans all tracked markdown (`rgcs_workbench/public_cage/claim_firewall.py`
   via `tests/release_cage/`). All new docs must keep claim-boundary discipline.
8. Desktop classification labels (4) differ from repo-wide claim vocabulary
   (EST/DER/HYP/SRC/ENG, `MODEL_OUTPUT`); `classification_label()` silently maps unknown
   labels to "Derived" — mapping must be made deliberate before Design Studio emits
   classifications.
9. Version skew: dist 8.3.0 vs `rgcs_desktop.__version__` 3.0.1 vs a hard-coded
   `"2.0.0"` in `services/manifests.py`.
10. `services/schemas.py` pins schema major 1; new Design Studio schemas stay on 1.x.

## Claim boundary

Design Studio records measurements, derived geometry, and model outputs. It does not
claim any anomalous physical effect; no row of this inventory is a measurement.
