# RGCS v4.5.2 — Windows Workbench clean rebuild (valid binaries)

**SOFTWARE_GREEN, PHYSICAL_UNTESTED.** A packaging-integrity patch on
[v4.5.1](https://github.com/andrew867/rgcs/releases/tag/v4.5.1). No
source logic of the science changed; no evidence class moved; all prior
tags are untouched.

## Why this release

The v4.5.0 and v4.5.1 release binaries were **invalid**. After the first
successful PyInstaller freeze, every subsequent build used
`--skip-freeze`, which only re-zips the existing `dist/` — so the shipped
executable was frozen from source that predated the first-run wizard.
The current source parses `--first-run` as a flag, but the stale exe
treated it as a positional argument, and the installer's post-install
launch (`RGCSWorkbench.exe --first-run`) created a workspace **literally
named `--first-run`**.

## Fixes

- **Clean rebuild from current source.** `build/` and `dist/` were
  deleted and the app fully re-frozen; `--skip-freeze` was not used.
- **Build provenance embedded in the executable**
  (`rgcs_desktop/build_meta.py`). At freeze time the build writes
  `_build_stamp.json` — version, git commit, and a SHA-256 over every
  packaged `.py` file — and PyInstaller bundles it. New **`--build-info`**
  prints it, so any binary can be traced to the exact source that made
  it.
- **`--skip-freeze` refuses a stale or mismatched `dist/`.** The build
  aborts (exit 2) unless the frozen tree's embedded source hash equals
  the current working tree's. The exact failure that shipped twice can
  no longer happen silently.
- **`--first-run` is structurally never a workspace path.** Startup
  selection is now a pure, unit-tested `plan_startup()`; `--first-run`
  (and any `--flag`) maps to the wizard, never to creating or opening a
  directory.

## Verified on this Windows machine

- **`--build-info` source hash matches the working tree** (proves the
  binary is built from current source, not stale).
- **Installer's exact post-install command** (`RGCSWorkbench.exe
  --first-run`) run from a scratch directory creates **no `--first-run`
  directory** — the regression is gone.
- Frozen **first-run self-test**: wizard workspace created, demo seeded,
  Master Evidence Workbook generated.
- Frozen **`--smoke-check`**: all **13 panels** constructed + a real
  background job succeeded.
- Installer **install → launch → restart → upgrade (reinstall over the
  same location) → uninstall** cycle completed; the per-user workspace
  survives uninstall.

## Still honestly gated (NOT claimed)

- **Code signing** — the installer and exe are unsigned; SmartScreen
  will warn.
- **Clean-machine proof** — the cycle above ran on a developer machine,
  not a fresh Windows VM, so this release does **not** emit the
  clean-machine verdict token.

## Verify

```bash
python -m pytest -q --deselect tests/regression/test_generator_determinism.py::test_generator_deterministic
# expect: 945 passed
python tools/v45_build_windows.py            # clean freeze + ZIP + installer + checksums
dist/RGCSWorkbench/RGCSWorkbench.exe --build-info   # version/commit/source-hash
python tools/qa_audit_v4.py --fast           # 19/19
```
