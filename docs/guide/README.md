# RGCS — User Documentation

This is the user documentation set for installing, configuring, and running
RGCS (Resonant Geometry Computational System) on **Linux** and **Windows**.

RGCS is an open, evidence-governed **research and computation** framework. It
is software: it computes, records, and refuses claims. It operates no
hardware and reports no physical measurement. Read
[SCIENTIFIC_BOUNDARIES.md](../../SCIENTIFIC_BOUNDARIES.md) and
[NON_CLAIMS.md](../../NON_CLAIMS.md) for what the project does and does not
establish.

## What you get when you install

| Command | Kind | What it is |
|---|---|---|
| `rgcs-v4` | console | the RSCS 2.0 multiphysics CLI (geometry, mesh, modal/piezo/optical solves, proof bundles) |
| `rgcs-workbook` | console | writes the Master Evidence Workbook (`.xlsx`) |
| `rgcs-workbench` | desktop GUI | the PySide6 workbench (also `python -m rgcs_desktop`) |

The research packages (`r10`–`r15`, `rgcs_core`, `rscs2_core`, …) are also
importable Python APIs — see [Using the Python API](USING_THE_PYTHON_API.md).

## Pick your path

| You are on… | Start here |
|---|---|
| **Linux** (any distro) | [Install on Linux](INSTALL_LINUX.md) |
| **Windows**, a release with an installer `.exe` | [Install on Windows → Installer](INSTALL_WINDOWS.md#a-installer-recommended) |
| **Windows**, a release with only a portable `.zip` | [Install on Windows → Portable](INSTALL_WINDOWS.md#b-portable-zip) |
| **Windows**, no release binary at all | [Install on Windows → From source](INSTALL_WINDOWS.md#c-from-source-same-as-linux) |

## Then

1. [Configuration](CONFIGURATION.md) — workspace, environment variables,
   compute backends, provenance.
2. [Using the CLI](USING_THE_CLI.md) — every `rgcs-v4` subcommand with
   examples.
3. [Using the desktop app](USING_THE_DESKTOP_APP.md) — the workbench, the
   evidence workbook, first-run.
4. [Using the Python API](USING_THE_PYTHON_API.md) — importing the research
   packages.
5. [Troubleshooting](TROUBLESHOOTING.md) — `--doctor`, common errors.

## Requirements at a glance

- **Python 3.11 or newer** (source installs).
- Core: `numpy`, `scipy`, `pydantic`, `pyyaml` (installed automatically).
- Optional extras: `desktop` (PySide6 + pyqtgraph), `workbook` (openpyxl for
  `.xlsx`), `dev` (test suite), `packaging` (PyInstaller, to build binaries).
- Optional external tools: **gmsh** (only for `rgcs-v4 mesh`), an **OpenCL**
  runtime (only for `rgcs-v4 sweep --backend opencl`).

> A Windows installer or portable build bundles its own Python and
> dependencies — you do **not** need to install Python separately to run a
> release binary.
