# Design Studio v1 — final report (Phase 08 gate)

## Branch

`research/workbench-design-studio-v1` (merged to `main` for release v8.4.0)

## Base commit

Branched from `a78a32e` (physics-spine research tip; `main` was an ancestor,
so the release merge carries the physics-spine pack and RC2 workbench state).

## Summary

The desktop workbench gained a guided, task-first **Design Studio** mode
layered over the existing Advanced Scientific Workbench (all fourteen research
panels preserved and untouched in behaviour). Six new panels (home + five
workflows) route through nine new Qt-free services with four new JSON schemas,
export receipts, checksummed bundles, and a dependency-free PDF writer. Docs,
installers, demo artifacts, screenshot proofs, and ~200 new tests ship with it.

## Changed files (grouped)

- **docs**: `README.md` (Design Studio section, entry-point row, release
  status), `docs/README.md` (Design Studio index section), `INSTALL.md`,
  `docs/user/{DESIGN_STUDIO, CRYSTAL_VALIDATOR, CERTIFICATION_SHEETS,
  PHYRLL_GENERATOR_DESIGNER, COIL_PULSE_DESIGNER, ANNULAR_RING_DESIGNER,
  FREQUENCY_KEYS, ADVANCED_MODE}.md`, `docs/developer/PACKAGING.md`,
  `docs/reports/DESIGN_STUDIO_INVENTORY.md`, this report, `CHANGELOG.md`,
  `CITATION.cff`.
- **UX**: `rgcs_desktop/viewers/{design_studio_home, design_studio_common,
  crystal_validator_panel, phyrll_generator_panel, coil_pulse_panel,
  annular_ring_panel, frequency_keys_panel}.py`,
  `rgcs_desktop/app/main_window.py` (panel registration + navigate signal,
  window title).
- **services**: `rgcs_desktop/services/{design_studio, crystal_validator,
  certification, phyrll_generator, coil_pulse, annular_ring,
  frequency_keys_lib, export_receipts, pdf_sheets}.py`;
  `services/formatting.py` (deliberate MODEL_OUTPUT/EST/DER/HYP/SRC/ENG →
  badge-label mapping; "Model output" badge color).
- **schemas**: `experiments/schemas/{crystal_specimen, phyrll_generator_design,
  coil_pulse_design, annular_ring_design}.schema.json` + registration in
  `experiments/schemas/validate.py` + four example templates;
  `schemas/release/release_manifest.schema.json`.
- **data**: `rgcs_desktop/data/frequency_keys.json` (17 keys; packaged via
  `[tool.setuptools.package-data]` and both PyInstaller specs).
- **tests**: `tests/unit/test_{design_studio_schemas, crystal_validator,
  phyrll_generator, coil_pulse_designer, annular_ring_designer}.py`,
  `tests/integration/test_design_studio_exports.py`,
  `tests/ui/test_design_studio_navigation.py`, `tests/ui/test_smoke.py`
  (expected panel set), `tests/docs/test_design_studio_docs_links.py`,
  `tests/release/test_design_studio_packaging.py`,
  `tests/v4/test_v4x_release_metadata.py` + `test_v4c_docs_closeout.py`
  (version pins → 8.4.0); `tests/docs` and `tests/release` added to
  `testpaths`.
- **packaging**: `scripts/install_linux.sh`, `scripts/run_rgcs_workbench.sh`,
  `tools/packaging/windows/build_windows.ps1` (reuses
  `tools/packaging/rgcs_desktop.spec` — one spec, not forked),
  `tools/packaging/release_manifest.py`, both PyInstaller specs bundle
  `rgcs_desktop/data`, `.gitattributes` (LF for `*.sh`),
  `tools/design_studio_demo.py`, `tools/design_studio_screenshots.py`.

## Tests run

```text
python -m pytest -q --deselect tests/regression/test_generator_determinism.py::test_generator_deterministic
  -> 8362 passed, 9 skipped, 1 deselected, exit 0  (1456.96 s)

focused suites (all green):
  tests/unit/test_design_studio_schemas.py .......... 8
  tests/unit/test_crystal_validator.py .............. 8
  tests/unit/test_phyrll_generator.py ............... 6
  tests/unit/test_coil_pulse_designer.py ............ 11
  tests/unit/test_annular_ring_designer.py .......... 9
  tests/integration/test_design_studio_exports.py ... 7
  tests/ui (smoke + navigation) ..................... 28
  tests/docs/test_design_studio_docs_links.py ....... 5
  tests/release/test_design_studio_packaging.py ..... 7

UI smoke: QT_QPA_PLATFORM=offscreen python -m rgcs_desktop --smoke-check
  -> 20 panels constructed OK; background job succeeded
```

## Installer status

- **Linux script**: executed end-to-end on a clean checkout (fresh git
  worktree): venv creation, `pip install -e ".[desktop]"` (fresh PySide6
  6.11.1), `--smoke-check` passed (20 panels), install receipt written,
  launcher generated. Host was Windows Git Bash; true-Linux execution is
  covered by the ubuntu CI matrix (offscreen Qt with system EGL). A WSL
  run was attempted and blocked: the Debian image lacks libEGL and sudo
  requires a password, so Qt cannot load there without operator action.
- **Windows**: `tools/packaging/windows/build_windows.ps1` present and
  guard-tested (reuses the existing spec; smoke + SHA-256 + release
  manifest). A full frozen build was not run in this session.

## Demo artifacts (`docs/assets/design-studio/demo/`)

crystal_certificate_demo.pdf · crystal_geometry_demo.svg ·
phyrll_generator_demo.scad · phyrll_generator_build_sheet_demo.pdf ·
coil_pulse_build_sheet_demo.pdf · annular_ring_demo.svg ·
annular_ring_engineering_sheet_demo.pdf · export_bundle_demo.zip
(bundle MANIFEST.json + CHECKSUMS.json verified by
`tests/integration/test_design_studio_exports.py`). SHA-256 per artifact
is recorded in the export bundle's CHECKSUMS.json.

## Screenshot proofs (`docs/assets/design-studio/screenshots/`)

Eight rendered captures of the real application walking the golden path
(01 home → 02 validated example specimen → 03 derived holder → 04 coil/pulse
with 3171/5021 sidebands → 05 37-cell ring → 06 key library with 925
selected → 07 Advanced Mode → 08 reports/exports). The run exported real
artifacts and recorded 10 rows in the workspace export ledger.

## Acceptance matrix

| id | gate | status |
|---|---|---|
| A01 | README start-by-task table | PASS (`tests/docs`) |
| A02 | docs index Design Studio section | PASS (`tests/docs`) |
| A03 | INSTALL.md | PASS |
| A04 | Design Studio home navigates | PASS (`tests/ui/test_design_studio_navigation.py`) |
| A05 | Advanced Mode preserved | PASS (navigation test + old smoke set intact) |
| A06 | Crystal Validator exports JSON/PDF/SVG | PASS (unit + integration + UI) |
| A07 | Phyrll SCAD/STL-path/build PDF | PASS (STL = stated-unavailable without OpenSCAD) |
| A08 | 925 and 1337 sidebands exact | PASS (unit fixtures) |
| A09 | 37-cell ring diagram/receipt | PASS (unit + UI + demo) |
| A10 | Linux installer tested | PASS with platform caveat above |
| A11 | Windows packaging present | PASS (script + spec, guard-tested) |
| A12 | full suite passes | PASS — 8362/0 failures |
| A13 | claim boundaries in PDFs | PASS (pypdf text-extraction tests) |

## Remaining blockers / honest list

- Windows frozen build (`build_windows.ps1`) is guard-tested but was not
  executed this session; run it before shipping a binary installer.
- True-Linux (non-WSL) installer execution not performed locally; relies
  on CI ubuntu matrix for the Linux desktop stack.
- STL export requires an external OpenSCAD install; without it the app
  reports "unavailable" by design.
- Version skew noted in the inventory remains: `rgcs_desktop.__version__`
  is 3.0.1 (desktop package version) vs distribution 8.4.0, and
  `services/manifests.py` stamps "2.0.0" into run manifests. Left
  unchanged deliberately — several guards pin these; reconciling them is
  a separate change.
- Local-only historical tags v8.1.0/v8.2.0 remain unpushed (deliberate
  LOCAL-ONLY decisions from earlier sessions; not changed here).

## Deliberately not implemented (plan stretch scope)

Live 3D preview, photo-assisted dimension extraction, LM Studio vision
integration, measured peak import, hardware acquisition, DXF flat-template
export (SCAD/SVG cover the printable path).

## Claim boundary

Everything above is software and test evidence. Design Studio artifacts are
engineering plans, model outputs, and reproducibility records; none of them
validates an anomalous physical effect. Measurements decide.
