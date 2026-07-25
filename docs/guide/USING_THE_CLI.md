# Using the CLI (`rgcs-v4`)

`rgcs-v4` is the RSCS 2.0 multiphysics command-line interface. After
installing (see [Install on Linux](INSTALL_LINUX.md) /
[Windows](INSTALL_WINDOWS.md)) it is on your `PATH`. If you installed from a
source venv, activate the venv first.

```bash
rgcs-v4 --help            # list all subcommands
rgcs-v4 <command> --help  # options for one command
```

All results are **computational**. Nothing here operates hardware or reports
a physical measurement.

## Subcommands

Many solve commands take a **variant** — `ideal_n7` or `nominal` — selecting
the canonical geometry, and share `--clmax` (mesh characteristic length),
`--workdir` (scratch dir, default `cli_work`), and `--n` (count).

| Command | What it does | Example |
|---|---|---|
| `devices` | CPU/OpenCL device capability report (JSON) | `rgcs-v4 devices` |
| `material` | print the frozen alpha-quartz material record | `rgcs-v4 material` |
| `geometry` | canonical geometry record | `rgcs-v4 geometry ideal_n7` |
| `mesh` | generate a gmsh mesh + manifest (needs gmsh) | `rgcs-v4 mesh nominal --clmax 8 --workdir run1` |
| `modes` | anisotropic modal solve → CSV | `rgcs-v4 modes ideal_n7 --n 12 --workdir run1` |
| `sweep` | Christoffel anisotropy sweep | `rgcs-v4 sweep --backend auto --n 10000 --seed 42` |
| `piezo` | piezoelectric coupled modes | `rgcs-v4 piezo nominal --condition short --n 8` |
| `optical` | probe-path projection | `rgcs-v4 optical ideal_n7 --wavelength 632.8` |
| `coil` | coil-pair on-axis field → CSV | `rgcs-v4 coil --radius 0.03 --separation 0.044 --current 1.0 --mode opposed` |
| `diagnostics` | eye diagnostic fields for one mode | `rgcs-v4 diagnostics ideal_n7 --mode 0` |
| `refsystems` | reference-system quick tables | `rgcs-v4 refsystems` |
| `capabilities` | material capability matrix / record / check | `rgcs-v4 capabilities quartz --check magnon` |
| `proof-bundle` | build the canonical-110 proof bundle | `rgcs-v4 proof-bundle canonical-110 --fast --out mybundle` |
| `report` | print a bundle's report | `rgcs-v4 report --bundle proof_bundle_110mm` |
| `verify-checksums` | verify a bundle's `SHA256SUMS.txt` | `rgcs-v4 verify-checksums --bundle proof_bundle_110mm` |

### Common options

- `variant` — `ideal_n7` (idealized 7-fold) or `nominal` (as-built nominal).
- `--clmax FLOAT` — mesh characteristic length; smaller = finer = slower.
- `--n INT` — number of modes / samples (per command).
- `--workdir DIR` — scratch/output directory (default `cli_work`).
- `--backend {cpu,opencl,cuda_interface,auto}` — compute backend for `sweep`
  (and recorded by `proof-bundle`); see [Configuration](CONFIGURATION.md).
- `--seed INT` — RNG seed, for reproducible sweeps.

## Typical sessions

**Inspect the frozen inputs:**

```bash
rgcs-v4 material
rgcs-v4 geometry ideal_n7
rgcs-v4 capabilities quartz          # the material capability matrix
```

**Run a modal solve and read the CSV it writes:**

```bash
rgcs-v4 modes nominal --n 12 --clmax 8 --workdir run1
```

**Build and verify the canonical proof bundle** (the flagship end-to-end
computation):

```bash
rgcs-v4 proof-bundle canonical-110 --fast --out proof_bundle_110mm
rgcs-v4 report --bundle proof_bundle_110mm
rgcs-v4 verify-checksums --bundle proof_bundle_110mm
```

`verify-checksums` recomputes every file hash against the bundle's
`SHA256SUMS.txt` and fails loudly on any mismatch — use it to confirm a
bundle you received is intact.

## Exit codes and output

Commands return `0` on success and non-zero on error. Records and reports are
printed to stdout (JSON or CSV as noted) or written under `--workdir` /
`--out`; redirect stdout to capture them:

```bash
rgcs-v4 devices > devices.json
rgcs-v4 modes ideal_n7 --n 8 --workdir run1   # CSV lands under run1/
```

## Evidence discipline

The CLI reflects the project's evidence rules: results are labelled by claim
class, unimplemented material mechanisms return a typed
`MECHANISM_NOT_IMPLEMENTED_FOR_MATERIAL` (never a fake zero, never a claim of
physical nonexistence), and no command emits a physical-measurement evidence
class. See [NON_CLAIMS.md](../../NON_CLAIMS.md).
