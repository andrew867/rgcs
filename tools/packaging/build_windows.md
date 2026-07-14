# Building the RGCS v2 Desktop Workbench for Windows

**Status note (honest):** this repository was developed and packaged on
Linux. PyInstaller does **not** cross-compile, so no Windows artifact could
be produced or tested here. The steps below use the same spec file that
builds successfully on Linux (`tools/packaging/rgcs_desktop.spec`); they are
precise but **unverified on Windows** until someone runs them there.

## Prerequisites (on the Windows build machine)

1. Windows 10/11 x64.
2. Python 3.11 or 3.12 (64-bit) from python.org. Check `py -3.11 --version`.
3. Git checkout of this repository, e.g. `C:\src\rgcs-v2`.
4. From a terminal in the repo root:

   ```bat
   py -3.11 -m venv .venv
   .venv\Scripts\activate
   pip install --upgrade pip
   pip install .[desktop]        rem numpy, scipy, pydantic, PySide6, pyqtgraph
   pip install jsonschema referencing pyyaml
   pip install pyinstaller
   ```

## Build

From the repo root, with the venv active:

```bat
pyinstaller tools\packaging\rgcs_desktop.spec --noconfirm ^
    --distpath release\windows --workpath build\pyinstaller-windows
```

Output: `release\windows\rgcs-workbench\rgcs-workbench.exe` (one-dir
layout; ship the whole `rgcs-workbench` folder, or zip it).

## Verify

```bat
release\windows\rgcs-workbench\rgcs-workbench.exe --smoke-check
```

must print `rgcs_desktop 2.0.0 (rgcs_core model version …); 13 panels
constructed OK` and exit 0. Then launch normally and run through
workflow 1 of `docs/USER_GUIDE.md` (create workspace, save specimen,
compute spectrum, run the demo job from the command palette).

## Windows-specific notes

- **Multiprocessing:** background jobs use the `spawn` start method and
  `multiprocessing.freeze_support()` is called first thing in
  `rgcs_desktop.app.main.main()` — both are required for frozen Windows
  executables. Do not remove either.
- **Console window:** the spec sets `console=False`. If the app fails to
  start silently, rebuild with `console=True` in the spec to see the
  traceback.
- **Antivirus/SmartScreen:** unsigned PyInstaller executables commonly
  trigger SmartScreen. For distribution, sign `rgcs-workbench.exe` with a
  code-signing certificate (`signtool sign /fd SHA256 /a ...`).
- **Qt plugins:** PySide6's PyInstaller hooks bundle the `windows` platform
  plugin automatically; no `QT_QPA_PLATFORM` setting is needed on Windows.
- **Paths:** workspaces default under `%USERPROFILE%\rgcs_workspaces`;
  settings persist via QSettings in the registry
  (`HKCU\Software\RGCS\rgcs_desktop`).

## Known limitations

- Not built or smoke-tested on Windows in this environment (Linux
  container). The Linux build from the same spec is verified by
  `tools/packaging/build_linux.sh`.
- macOS packaging is not provided (out of scope for this pass); the spec is
  expected to work with minor changes (app bundle/codesign) but is untested.
