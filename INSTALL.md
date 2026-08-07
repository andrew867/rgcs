# Install RGCS

RGCS is a local-first Python application. Python 3.11+ is required.

## Source install (all platforms)

```bash
python -m pip install -e ".[desktop]"
rgcs-workbench
```

The `desktop` extra installs PySide6 and pyqtgraph. For development add the
`dev` extra:

```bash
python -m pip install -e ".[desktop,dev]"
```

## Linux helper

A scripted install that creates a virtual environment, installs the desktop
extra, runs a smoke check, and writes an install receipt:

```bash
./scripts/install_linux.sh
./scripts/run_rgcs_workbench.sh
```

## Windows

Build a frozen app with PyInstaller:

```powershell
tools\packaging\windows\build_windows.ps1
```

The build produces `release/windows/rgcs-workbench/rgcs-workbench.exe`, runs its
smoke check, and writes SHA-256 checksums beside it. See
[docs/developer/PACKAGING.md](docs/developer/PACKAGING.md) for details and for
the Inno Setup installer path (`packaging/RGCS_Workbench.iss`).

## Verify an install

```bash
rgcs-workbench --doctor       # environment + dependency report
rgcs-workbench --smoke-check  # constructs the full UI offscreen and runs a job
```

## First launch

`rgcs-workbench` opens the **Design Studio** home — task cards for crystal
validation, certification sheets, Phyrll generator design, coil/pulse design,
and annular ring design. The **Advanced Scientific Workbench** (the full
research workbench) is one click away. See
[docs/user/DESIGN_STUDIO.md](docs/user/DESIGN_STUDIO.md).
