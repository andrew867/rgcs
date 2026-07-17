# RGCS v4.5.1 — Windows Workbench launch fix + compiled installer

**SOFTWARE_GREEN, PHYSICAL_UNTESTED.** A packaging patch on
[v4.5.0](https://github.com/andrew867/rgcs/releases/tag/v4.5.0). No
source logic, no evidence class, and no scientific claim changed; every
prior tag is untouched.

## Why this release

The v4.5.0 portable build launched to a crash: the model-browser panel
reads `docs/model_registry.yaml` (and the provenance graph reads
`references/` and `experiments/schemas/`), but the PyInstaller spec
only bundled the two `registry/` trees, so the frozen app raised
`FileNotFoundError` on `_internal\docs\model_registry.yaml` while
constructing its panels. The `--doctor` smoke test used to verify the
build returns before any panel is built, so it never caught this.

## Fixes

- **Bundle every runtime data tree the desktop reads**
  (`packaging/RGCSWorkbench.spec`): `docs/model_registry.yaml`,
  `references/`, and `experiments/schemas/` are now shipped alongside
  the existing `rscs_core/registry` and `rscs2_core/registry`. A new
  regression test (`tests/v4/test_v45_packaging.py`) fails the build if
  the spec ever drops one.
- **Verify with `--smoke-check`, not just `--doctor`**
  (`tools/v45_build_windows.py`): the build now launches the frozen exe
  with `--smoke-check`, which constructs all 13 panels and runs a real
  background job — the exact path that crashed — so a missing data file
  is caught at build time.

## New in this release

- **Compiled Windows installer EXE**
  (`RGCS-Workbench-4.5.1-Windows-x64-Setup.exe`). Per-user, no admin
  (Inno Setup, `PrivilegesRequired=lowest`); creates Start-Menu
  shortcuts, offers an optional desktop shortcut, and leaves the
  per-user workspace in place on uninstall. **UNSIGNED** — Windows
  SmartScreen will warn; this is expected and disclosed.

## Verified on this Windows machine

- Frozen build: **13 panels constructed OK** under `--smoke-check`.
- Installer: silent per-user **install → launch (13 panels) →
  uninstall (clean removal)** cycle completed.
- Portable ZIP now contains the `docs/`, `references/`, and
  `experiments/schemas/` data under `_internal/`.

## Still honestly gated (NOT claimed)

- **Code signing** — the installer and exe are unsigned.
- **Clean-machine proof** — the install/uninstall cycle above ran on a
  developer machine, not a fresh Windows VM, so this release still does
  **not** emit the clean-machine verdict token.

## Verify

```bash
python -m pytest -q --deselect tests/regression/test_generator_determinism.py::test_generator_deterministic
# expect: 939 passed
python tools/v45_build_windows.py      # portable ZIP + workbook + installer + checksums
python tools/qa_audit_v4.py --fast     # 19/19
```
