# Install on Linux

RGCS runs from source on any modern Linux distribution. There is no Linux
binary release; you install into a Python virtual environment. This takes a
few minutes.

## 1. Prerequisites

- **Python 3.11+** and the `venv` module.
- **git** (to clone) — or download a source tarball from the Releases page
  and extract it.
- A C toolchain is **not** required for the core install; `numpy`/`scipy`
  ship prebuilt wheels for common Linux platforms.

Install the prerequisites (examples):

```bash
# Debian / Ubuntu
sudo apt update && sudo apt install -y python3 python3-venv python3-pip git

# Fedora / RHEL
sudo dnf install -y python3 python3-pip git

# Arch
sudo pacman -S --needed python python-pip git
```

Check your Python version (must be 3.11 or newer):

```bash
python3 --version
```

## 2. Get the source

Clone the repository:

```bash
git clone https://github.com/andrew867/rgcs.git
cd rgcs
```

Or, if you downloaded a source archive from the Releases page, extract it and
`cd` into the extracted folder:

```bash
tar xf rgcs-<version>-source.tar.gz
cd rgcs-<version>
```

## 3. Create and activate a virtual environment

Keeping RGCS in its own venv avoids clashing with system packages:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Your shell prompt should now be prefixed with `(.venv)`. Upgrade pip:

```bash
python -m pip install --upgrade pip
```

## 4. Install RGCS

Choose the install that matches what you want to run:

```bash
# Core only — the rgcs-v4 CLI and the importable research packages
pip install -e .

# + desktop workbench (PySide6 GUI) and .xlsx workbook export
pip install -e ".[desktop,workbook]"

# + the full test suite (for contributors / verification)
pip install -e ".[desktop,workbook,dev]"
```

`-e` (editable) is recommended so `git pull` updates your install in place.
Drop `-e` for a plain install.

### Optional external tools

- **gmsh** — required only for `rgcs-v4 mesh` (mesh generation). Install from
  your distro (`sudo apt install gmsh`) or from gmsh.info, and ensure `gmsh`
  is on your `PATH`.
- **OpenCL runtime** — required only for `rgcs-v4 sweep --backend opencl`. The
  CPU backend (`--backend cpu`, the default `auto` falls back to CPU) needs
  nothing extra.

## 5. Verify the install

```bash
# CLI is on PATH and reports its subcommands
rgcs-v4 --help

# Compute-device capability report (JSON) — proves numpy/scipy import
rgcs-v4 devices

# Desktop app self-diagnostics (only if you installed the desktop extra)
rgcs-workbench --doctor
```

`rgcs-workbench --doctor` prints the version, Python, platform, the default
workspace path, and whether PySide6 / numpy / scipy / openpyxl import. All
should say OK.

To see build provenance (version, git commit, source hash):

```bash
rgcs-workbench --build-info
```

## 6. Run it

- **CLI:** see [Using the CLI](USING_THE_CLI.md), e.g.
  `rgcs-v4 material` or `rgcs-v4 proof-bundle canonical-110 --fast`.
- **Desktop workbench:** `rgcs-workbench` (or `python -m rgcs_desktop`). See
  [Using the desktop app](USING_THE_DESKTOP_APP.md).
- **Evidence workbook:** `rgcs-workbook out.xlsx`. See
  [Using the desktop app → Evidence workbook](USING_THE_DESKTOP_APP.md#the-evidence-workbook).

The desktop app needs a graphical session (X11 or Wayland). On a headless
server, use the CLI, or run the GUI's non-interactive commands
(`--doctor`, `--build-info`, `--export-workbook`, `--smoke-check`).

## 7. Configure (optional)

See [Configuration](CONFIGURATION.md) for the workspace location, environment
variables, and compute-backend selection. RGCS runs with sensible defaults
and needs no configuration to start.

## Upgrading

```bash
cd rgcs
git pull
source .venv/bin/activate
pip install -e ".[desktop,workbook]"   # picks up any new dependencies
```

## Uninstalling

Delete the checkout and its venv:

```bash
deactivate 2>/dev/null || true
rm -rf /path/to/rgcs
```

RGCS writes user data only under the workspace directory (default
`~/RGCS Workspace`, see [Configuration](CONFIGURATION.md)); remove that too if
you want a clean slate.
