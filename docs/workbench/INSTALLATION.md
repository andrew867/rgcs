# RGCS Coordinate Workbench — Installation

The workbench ships as the `rgcs_coordinate` package inside the RGCS
repository distribution, plus a zero-install static HTML demo.

## Option 1 — no install (static demo)

Open `workbench/index.html` in any modern browser (double-click works;
`file://` is fully supported). It performs the complete 30-bit
structural decode in the browser, makes no network requests, and
exports trace JSON. It does **not** perform any physical projection.

## Option 2 — Python package

Requirements: Python 3.11+ (3.11–3.13 tested; structural decode is
pure stdlib — the scientific projection backend additionally uses the
repository's `numpy`/`scipy` stack, installed automatically).

From a repository checkout:

```bash
python -m pip install .
```

For development (editable, with test tooling):

```bash
python -m pip install -e .[dev]
```

This installs the `rgcs-coordinate` console command. Verify:

```bash
rgcs-coordinate version --full
```

```bash
rgcs-coordinate doctor
```

`doctor` reports the structural codec, packaged fixtures, and whether
the scientific projection backend (`cwatlas.r1085a`) is importable.
When the backend is unavailable, structural decoding is unaffected and
`project`/`inverse` report `PROFILE_BACKEND_UNAVAILABLE` instead of
degrading silently.

Without installing, every command also works as a module from the
repository root:

```bash
python -m rgcs_coordinate.cli decode 165876523
```

## Verifying an installation

```bash
rgcs-coordinate corpus validate
```

validates the packaged golden vectors against the packet arithmetic
(exit 0 on success), and

```bash
python -m pytest tests/rgcs_coordinate -q
```

runs the workbench test suite from a repository checkout.

## Exit codes

| code | meaning |
|------|---------|
| 0 | success |
| 2 | invalid input |
| 3 | unsupported codec or body profile |
| 4 | projection underdetermined (result still printed — this is the honest current state) |
| 5 | failed round-trip |
| 70 | internal error |
