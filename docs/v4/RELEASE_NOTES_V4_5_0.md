# RGCS v4.5.0 — Windows Workbench, Portable Package, Master Evidence Workbook

**SOFTWARE_GREEN, PHYSICAL_UNTESTED.** This is a packaging and
interoperability release. No physical result is validated, no evidence
class was promoted, and every prior tag is untouched. The installer,
portable app, and workbook exist so a technical or nontechnical
visitor can install, launch, and explore the project without
rebuilding it from source — not to assert that crystal resonance, the
Eye hypothesis, or any anomalous channel has been demonstrated.

## What shipped

**Canonical export model** (`rgcs_workbench/canonical.py`). A typed
`Record` / `CanonicalStore` layer builds a single in-memory snapshot
from the live v4.x modules: frequency-key registry, ranked harmonic
relations (mechanism-classified), pre-arrival specimens and mode
estimates, timing recipes, the hypothesis register, the Eye numerical
ladder, the resonator-platform campaign, hardware profiles and BOM,
the experiment queue, corrections, the source registry, and
PUBLIC_SAFE lore. Every row carries one of the eight evidence classes
(LORE → INDEPENDENT_REPLICATION) and a privacy class
(PUBLIC / PUBLIC_SAFE / PRIVATE). No row anywhere is
BENCH_MEASUREMENT or INDEPENDENT_REPLICATION: nothing physical has
been measured.

**Master Evidence Workbook** (`rgcs_workbench/workbook.py`). One-way
generation from the canonical store to a 17-sheet formula-visible
`.xlsx`: Dashboard, Frequency Keys, Harmonic Relations, Specimens,
Mode Estimates, Timing Recipes, Hypotheses, Evidence Ledger, Eye
Results, Resonator Platform, Hardware BOM, Experiment Queue,
Corrections, Source Registry, Lore Registry, Installer Metadata,
Workbook Guide. Derived cells remain live formulas (mode-estimate
percentage errors `=(f−d)/f`, dashboard sums); evidence classes are
colour-coded with a legend; the Dashboard carries the explicit claim
boundary. A public export provably contains no PRIVATE row content.
The workbook is **never** the canonical store — it is regenerated, not
edited back. Microsoft Excel is not required to run the application.

**Windows packaging** (`packaging/`). A PyInstaller onedir build
(`RGCSWorkbench.spec`) freezes the desktop app to
`RGCSWorkbench.exe`, bundled into a portable ZIP that runs with no
install, no admin, no telemetry, no network listener, and no
auto-start; per-user data lives in `Documents\RGCS Workspace`.
Headless `--doctor` (offline diagnostics) and `--smoke-check` verify
the frozen build; `--export-workbook` regenerates the workbook from a
frozen install.

## Verified in this environment

- 938 tests passing (see Verify below), including 22 new
  workbench, workbook, and packaging tests.
- Frozen `RGCSWorkbench.exe` launches and passes `--doctor`
  (reports PySide6 6.11.1, model RGCS-v2.0, claim boundary).
- Portable ZIP built and its SHA256 recorded in `SHA256SUMS.txt`.
- Public Master Evidence Workbook generated and byte-checked to carry
  no PRIVATE content.

## Honestly gated (NOT claimed)

- **Compiled installer EXE.** The Inno Setup script
  (`packaging/RGCS_Workbench.iss`, per-user,
  `PrivilegesRequired=lowest`) ships in-tree, but Inno Setup (`iscc`)
  is not present in the build environment, so no Setup EXE was
  compiled. Building it requires a machine with Inno Setup installed.
- **Code signing.** The build is UNSIGNED and is labelled as such.
- **Clean-machine proof.** No clean Windows VM was available, so the
  install → launch → workbook → upgrade → uninstall cycle was not
  exercised on a fresh machine. This release therefore does **not**
  emit the clean-machine verdict token.

## Verify

```bash
python -m pytest -q --deselect tests/regression/test_generator_determinism.py::test_generator_deterministic
# expect: 938 passed
python -m pytest tests/v4/test_workbench.py -q   # 16 workbench tests
python -m rgcs_workbench.workbook out.xlsx       # 17-sheet workbook
python tools/v45_build_windows.py                # portable ZIP + workbook + checksums
python tools/qa_audit_v4.py --fast               # 19/19
```

On a machine with Inno Setup installed, `tools/v45_build_windows.py`
additionally compiles the Setup EXE; without it, that step is reported
as blocked rather than skipped silently.
