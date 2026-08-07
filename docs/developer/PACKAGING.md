# Packaging

How RGCS ships: source installs, the Linux helper, frozen Windows builds, smoke
checks, checksums, and release manifests.

## Source install

```bash
python -m pip install -e ".[desktop]"
```

## Linux helper

`scripts/install_linux.sh` creates `.venv`, installs the desktop extra, runs
`rgcs-workbench --smoke-check`, writes `.rgcs-install/install_receipt.txt`, and
generates `scripts/run_rgcs_workbench.sh`. It is intended for a clean checkout.

## Windows frozen build

`tools/packaging/windows/build_windows.ps1` drives PyInstaller using the
existing spec `tools/packaging/rgcs_desktop.spec` (one spec, reused — do not
fork a second desktop spec). Output: `release/windows/rgcs-workbench/`
containing `rgcs-workbench.exe`, then the script runs `--smoke-check` against
the frozen exe and writes `SHA256SUMS.txt`.

The Inno Setup consumer installer lives at `packaging/RGCS_Workbench.iss`
(per-user, unsigned) with its own spec `packaging/RGCSWorkbench.spec`.

**Spec parity rule:** any new runtime data file the desktop reads must be added
to the `datas` of both specs and to `[tool.setuptools.package-data]`;
`tests/v4/test_v45_packaging.py` and `tests/v52/test_r10_install_parity.py`
enforce this.

## Smoke checks

- `rgcs-workbench --doctor` — dependency/environment report, no Qt required.
- `rgcs-workbench --smoke-check` — constructs the full `MainWindow` offscreen,
  counts panels, runs a real spawn job. Both the source install and every
  frozen build must pass it.

## Release manifests

Release builds write a manifest conforming to
`schemas/release/release_manifest.schema.json`: platform, commit, build
command, artifact list with SHA-256 per file, and the smoke-check status and
command. `python -m tools.packaging.release_manifest` generates one.
