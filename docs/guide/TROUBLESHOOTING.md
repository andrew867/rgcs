# Troubleshooting

Start with the built-in diagnostic — it answers most questions in one line
each:

```bash
rgcs-workbench --doctor
```

It prints the version, Python version, platform, the resolved workspace path,
and whether **PySide6 / numpy / scipy / openpyxl** import. Anything reported
as missing points at the fix below. For build provenance:

```bash
rgcs-workbench --build-info      # version, git commit, source hash
```

## Install / import

**`rgcs-v4: command not found` (or `rgcs-workbench` not found).**
The venv isn't active, or the package isn't installed. Activate it
(`source .venv/bin/activate` on Linux; `.\.venv\Scripts\Activate.ps1` on
Windows) and re-run `pip install -e .`. You can always fall back to
`python -m rgcs_desktop` for the GUI.

**`ModuleNotFoundError: No module named 'PySide6'`.**
You installed core only. Add the desktop extra:
`pip install -e ".[desktop,workbook]"`.

**`ModuleNotFoundError: No module named 'openpyxl'`** when exporting a
workbook. Add the workbook extra: `pip install -e ".[workbook]"`.

**`Python 3.11+ required` / syntax errors on install.**
Check `python --version`. RGCS needs 3.11 or newer; install a newer Python
and recreate the venv with it.

**PowerShell won't run the venv activation script.**
Allow it once for your user:
`Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`, or use
`.\.venv\Scripts\activate.bat` from `cmd.exe`.

## Desktop app

**The GUI won't open / `qt.qpa.plugin: could not load the Qt platform
plugin`.**
You need a graphical session. On a headless Linux server there is no display;
use the CLI, or the app's headless flags (`--doctor`, `--build-info`,
`--export-workbook`, `--smoke-check`). On a desktop, ensure your distro's Qt
runtime libraries are present (most are pulled in with PySide6; on minimal
systems you may need `libxcb`/`libgl` packages).

**Quick "does the GUI build?" check without a window:**
`rgcs-workbench --smoke-check` constructs the main window headlessly and exits.

## Windows binaries

**SmartScreen: "Windows protected your PC" / unknown publisher.**
The installer and portable builds are unsigned. Choose **More info → Run
anyway** if you trust the source. To confirm integrity, compare your download
against the release's `SHA256SUMS.txt`.

**Antivirus quarantines the extracted `.exe`.**
Unsigned PyInstaller executables are commonly flagged. Restore/allow the file,
or install from source instead ([Windows → From source](INSTALL_WINDOWS.md#c-from-source-same-as-linux)).

**The portable `.exe` errors on launch.**
Make sure you **fully extracted** the ZIP (running from inside the ZIP viewer
fails). Extract to a folder you can write to, then run the `.exe`.

## CLI

**`rgcs-v4 mesh` fails / "gmsh not found".**
`mesh` needs the external **gmsh** tool on your `PATH`. Install it and retry,
or use the other subcommands, which don't need it.

**`rgcs-v4 sweep --backend opencl` fails or finds no device.**
No OpenCL runtime/device is available. Use `--backend cpu` (or `auto`, which
falls back to CPU). `rgcs-v4 devices` shows what was detected.

**A command can't write its output.**
Run from a directory you can write to, or pass `--workdir`/`--out` to a
writable path. See [Configuration → CLI output](CONFIGURATION.md#cli-output-locations).

**`verify-checksums` reports a mismatch.**
The bundle's files don't match its `SHA256SUMS.txt` — the bundle is
incomplete or altered. Regenerate it (`rgcs-v4 proof-bundle canonical-110`) or
re-download it.

## Still stuck

- Re-run `rgcs-workbench --doctor` and include its output when asking for
  help.
- Confirm your build with `rgcs-workbench --build-info`.
- Check the project's Issues page on GitHub.
