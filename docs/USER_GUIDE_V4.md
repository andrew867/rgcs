# RGCS v4 User Guide (RSCS 2.0)

RGCS v4 adds a validated 3-D computational stack on top of the frozen
v3 framework: anisotropic FEM modal analysis, piezoelectric coupling,
optical/coil/drive projections, an eye diagnostic + consensus engine,
Intel iGPU OpenCL acceleration, and a one-command reproducibility
bundle for the canonical 110 mm crystal.

Nothing in v4 modifies the frozen authorities (tags v2.0.0/v3.0.x,
`archive/v2.0.0/`, the RGCS-M/RSCS-C/RSCS-O registries). New objects
live in the RSCS2-* registry (`rscs2_core/registry/rscs2_registry.yaml`).

## Install

```bash
git clone https://github.com/andrew867/rgcs
cd rgcs
python -m venv .venv && . .venv/bin/activate   # or .venv\Scripts\activate
pip install -e .[dev]
pip install scikit-fem meshio gmsh matplotlib   # v4 solver stack
pip install pyopencl                            # optional: iGPU backend
```

gmsh is invoked as an external SUBPROCESS only (GPL isolation,
DV4-006); the MIT-licensed package never links it.

## The CLI

Every capability is scriptable via `rgcs-v4` (or
`python -m rscs2_core.cli`):

| command | purpose |
|---|---|
| `rgcs-v4 devices` | CPU/OpenCL capability report (JSON) |
| `rgcs-v4 geometry ideal_n7\|nominal` | canonical geometry record |
| `rgcs-v4 mesh ideal_n7 --clmax 8` | gmsh mesh + deterministic manifest |
| `rgcs-v4 material` | frozen α-quartz tensor record |
| `rgcs-v4 modes ideal_n7 --n 12` | anisotropic modal solve (CSV) |
| `rgcs-v4 sweep --backend cpu\|opencl\|auto --n 10000` | Christoffel anisotropy sweep |
| `rgcs-v4 piezo ideal_n7 --condition short\|open` | coupled piezo modes |
| `rgcs-v4 optical ideal_n7` | probe-path projection (frozen ray model) |
| `rgcs-v4 coil --radius 0.03` | coil-pair on-axis field (CSV) |
| `rgcs-v4 diagnostics ideal_n7 --mode 0` | eye diagnostic fields |
| `rgcs-v4 refsystems` | cavity-vs-exact reference table |
| `rgcs-v4 proof-bundle canonical-110` | **the** reproducibility bundle |
| `rgcs-v4 report --bundle proof_bundle_110mm` | print a bundle's report |
| `rgcs-v4 verify-checksums --bundle proof_bundle_110mm` | integrity check |

Backend policy (DV4-004/007): CPU float64 is the numerical authority;
an explicitly requested backend that is unavailable RAISES — nothing
falls back silently. CUDA is INTERFACE_TESTED only (no hardware).

## The proof bundle

```bash
rgcs-v4 proof-bundle canonical-110          # ~5-10 min, full meshes
rgcs-v4 verify-checksums                    # 115/115 OK expected
```

Produces `proof_bundle_110mm/` — geometry (STL/OBJ/GLB/VTU + hashes),
frozen material tensors, live benchmarks, ideal+nominal mode tables,
field exports, the full eye-consensus rerun with the corrected
uncertainty-aware node comparison, 17 figures (PNG+PDF), and reports.
The verdict is machine-read from `VERDICT.json`; for the canonical
crystal (v4.1.0) it is **UNCERTAINTY_OVERLAPS_CONVENTIONAL_NODE** —
the one 3-family candidate sits 3.906 mm from the nearest conventional
station with a 3.08 mm localization halfwidth, so the conventional
model *may* explain it within uncertainty (not established that it
does; finer meshes discriminate). A null or indeterminate verdict is a
passing scientific outcome.

## The scripted demo

```bash
python tools/demo_v4.py          # full; --fast for a quick pass
```

From a clean workspace: detects devices, generates both crystals,
meshes, solves modes, runs a static piezo field, computes diagnostics,
renders offscreen screenshots, builds the proof bundle, verifies
checksums, and writes `demo_out/demo_run_record.json` (runtime, peak
memory, device, artifact paths, hashes).

## Python API in one page

```python
from skfem import MeshTet
from rscs2_core import crystal110, fem, eye, projections, piezo
from rgcs_core.anisotropy import (ALPHA_QUARTZ_DENSITY_KG_M3,
                                  alpha_quartz_stiffness_pa)
from rscs_core.propagation import voigt_to_tensor

c = crystal110.build_crystal("ideal_n7")
m = crystal110.mesh_crystal(c, clmax_mm=8.0, workdir="work")
C = voigt_to_tensor(alpha_quartz_stiffness_pa())
prob = fem.assemble_anisotropic(MeshTet(m["nodes_m"].T, m["tets"].T),
                                C, ALPHA_QUARTZ_DENSITY_KG_M3)
sol = fem.solve_modes(prob, 12)      # 6 rigid + elastic, residuals
fields = eye.evaluate_elastic_diagnostics(prob, sol, 0, C, pair_index=1)
paths = projections.probe_paths(c, wavelength_nm=632.8)
```

## Desktop

The v3 desktop app (`rgcs_desktop`) is unchanged. v4-specific GUI
views (mode viewer, field selector, candidate comparison) are STAGED
past v4.0.0 per the desktop spec's staging clause; the CLI plus
offscreen rendering (matplotlib Agg, tested) covers every v4 function.

## Honesty rails to know about

- The eye engine never assumes an eye; `eye_coordinate` is null in all
  canonical records. Verdicts are never forced.
- The "octave" wavelength presets (532.538 / 1065.077 nm = c/2⁴⁹,
  c/2⁴⁸) are arithmetic, not a coupling claim.
- GPU statuses follow the 4-rung ladder: INTERFACE_TESTED →
  NUMERICALLY_PARITY_TESTED → HARDWARE_BENCHMARKED →
  MULTI_DEVICE_REPRODUCED. Only earned statuses appear.
- Safety envelopes (optical ≤3R ≤5 mW; coil ≤30 V ≤3 A ≤5 mJ) bind
  every run description; v4 ships no high-power instructions.
