# Using the desktop app (RGCS Workbench)

The Workbench is the graphical front end (PySide6). Launch it however you
installed it:

- **Windows installer** — Start Menu → **RGCS Workbench**.
- **Windows portable** — run `RGCS-Workbench.exe` from the extracted folder.
- **From source (any OS)** — activate your venv, then `rgcs-workbench`
  (equivalently `python -m rgcs_desktop`). Requires the `desktop` extra
  (`pip install -e ".[desktop,workbook]"`) and a graphical session.

## First run

On first launch a **first-run wizard** creates your workspace (see
[Configuration → workspace](CONFIGURATION.md#the-workspace)):

- Windows: `%USERPROFILE%\Documents\RGCS Workspace`
- Linux/macOS: `~/RGCS Workspace`

You can trigger the wizard explicitly with `rgcs-workbench --first-run`.

## Command-line flags (no window)

The Workbench also runs headless utility commands that print and exit — handy
for scripting, CI, or a quick check without opening the GUI:

| Flag | What it does |
|---|---|
| `--doctor` | offline diagnostics: version, Python, platform, workspace path, and whether PySide6 / numpy / scipy / openpyxl import |
| `--build-info` | print the build provenance stamp (version, git commit, source hash) as JSON |
| `--first-run` | run the first-run workspace wizard |
| `--export-workbook [--private]` | write the evidence workbook without opening the GUI |
| `--smoke-check` | construct the main window headlessly and exit (a fast "does the GUI import and build?" check) |
| `--print-startup-plan` | print what startup would do, without doing it |

Examples:

```bash
rgcs-workbench --doctor
rgcs-workbench --build-info
rgcs-workbench --export-workbook          # writes the workbook to the workspace
```

Run `rgcs-workbench` with no flags to open the graphical Workbench.

## The evidence workbook

RGCS's headline artifact is the **Master Evidence Workbook** — a multi-sheet
`.xlsx` summarizing the canonical evidence records across every programme
generation, each labelled by claim class. Two ways to generate it:

```bash
# standalone console tool
rgcs-workbook out.xlsx           # PUBLIC workbook
rgcs-workbook out.xlsx --private # operator-only; never used in releases

# or via the desktop app, headless
rgcs-workbench --export-workbook
```

Generating the workbook needs the `workbook` extra (openpyxl); it is included
in the Windows binaries and installed by `pip install -e ".[workbook]"`. The
public workbook contains no private data. Open the `.xlsx` in LibreOffice
Calc, Excel, or any spreadsheet reader — Excel is **not** required to produce
it.

## What the Workbench is for

The Workbench presents the framework's records, geometry, and diagnostics for
inspection. Like the CLI, it computes and reports; it does not operate
hardware and reports no physical measurement. The evidence distribution it
shows is, by design, mostly refusals and unmeasured results — see
[SCIENTIFIC_BOUNDARIES.md](../../SCIENTIFIC_BOUNDARIES.md).

If the GUI won't start, run `rgcs-workbench --doctor` first and see
[Troubleshooting](TROUBLESHOOTING.md).
