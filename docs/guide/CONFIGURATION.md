# Configuration

RGCS runs with working defaults and needs **no configuration to start**. This
page documents the few things you can adjust: the workspace, output
locations, compute backends, and how to read build provenance.

## The workspace

The desktop app stores per-user data (settings, generated workbooks,
run outputs) in a single **workspace** directory. Its default location:

| Platform | Default workspace |
|---|---|
| Windows | `%USERPROFILE%\Documents\RGCS Workspace` |
| Linux / macOS | `~/RGCS Workspace` |

On first launch the app's **first-run wizard** creates this folder. You can
confirm the resolved path at any time:

```bash
rgcs-workbench --doctor        # prints "default workspace: <path>"
```

The workspace is created on demand and is safe to delete when the app is
closed; the app recreates it on next launch. Nothing outside the workspace is
modified by normal use.

## CLI output locations

The `rgcs-v4` CLI writes into the **current directory** unless you tell it
otherwise:

- Solvers that produce intermediate files take `--workdir` (default
  `cli_work`), e.g. `rgcs-v4 modes ideal_n7 --workdir /tmp/run1`.
- `rgcs-v4 proof-bundle canonical-110 --out mybundle` writes the bundle to
  `mybundle/` (default `proof_bundle_110mm/`).
- `rgcs-workbook path/to/out.xlsx` writes the workbook where you name it.

Run the CLI from a directory you can write to.

## Compute backend

The Christoffel anisotropy sweep can use different backends:

```bash
rgcs-v4 sweep --backend auto      # default: OpenCL if available, else CPU
rgcs-v4 sweep --backend cpu       # force CPU (no extra dependencies)
rgcs-v4 sweep --backend opencl    # requires an OpenCL runtime + device
rgcs-v4 devices                   # list detected CPU/OpenCL devices (JSON)
```

`--backend cpu` always works. `--backend opencl` needs a working OpenCL
runtime and device; `rgcs-v4 devices` shows what was detected. `auto` falls
back to CPU when OpenCL is unavailable, so it is always safe.

## Optional external tools

| Tool | Needed for | Notes |
|---|---|---|
| **gmsh** | `rgcs-v4 mesh` (mesh generation) | must be on `PATH` |
| **OpenCL runtime** | `rgcs-v4 sweep --backend opencl` | vendor ICD + device |
| **openpyxl** (Python extra) | `.xlsx` workbook export | installed via the `workbook` extra |
| **PySide6, pyqtgraph** (extras) | the desktop workbench | installed via the `desktop` extra |

## Private vs public data

Some tools accept a `--private` flag (`rgcs-workbook --private`,
`rgcs-workbench --export-workbook --private`). RGCS is built with a strict
**public/private firewall**: public builds, tests, logs, and releases never
contain private inputs. Leave `--private` **off** unless you are the operator
working with a local private corpus that lives outside the repository; it is
never required for normal use and never affects released artifacts.

## Build provenance

Every install can report exactly what it was built from:

```bash
rgcs-workbench --build-info
```

This prints a JSON stamp with the **version**, **git commit**, and a
**source hash** over every packaged Python file. For a frozen Windows binary
the stamp is embedded at build time; from a source checkout it is computed
live. Use it to confirm which build you are running.

## Environment

- **Python**: source installs require 3.11+. A frozen binary bundles its own
  interpreter — the system Python is irrelevant to it.
- RGCS does **not** require any environment variables to run. It reads
  `USERPROFILE` (Windows) only to locate the default workspace.
- No network access is required for any command documented here;
  `--doctor` and `--build-info` are explicitly offline and side-effect-free.
