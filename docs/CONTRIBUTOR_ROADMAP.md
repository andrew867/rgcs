# Contributor Roadmap (Agent 15)

What the project needs, sized and sorted, with the **software vs
experimental** boundary explicit. Rules of entry: `CONTRIBUTING.md`
(the three inviolables). Everything below is ENG planning — no item
changes v3 mathematics; anything that would goes through ledger
governance first.

## A. Experimental work (bench; the highest-value lane)

| Item | What it takes | Deliverable | Size |
|---|---|---|---|
| **Phase 0 commissioning** | the `BENCH_HARDWARE.md` bench (€€–€€€ class) | H-29/H-30 gate results — the campaign's first data | M |
| Modal survey + ladders (H-01 family) | Phase 0 bench + 2 specimens | adjudicated Phase I rows | M |
| Node menu scans (H-24..H-28) | Phase I bench + micrometer stage | five definitions kept/retired | M |
| Optical branch incl. the pre-registered nulls (H-20..H-23, H-25) | class-3R rail, enclosed | null acceptances or a very interesting problem | L |
| Coherence campaign (H-10..H-14) | DAQ + n≥100 ensembles | Phase IV adjudications | L |
| **Independent replication** of any adjudicated row | your own bench | replication row in the registers | any |
| **Measured datasets** contribution | any calibrated run per the manifests | schema-valid datasets under `experiments/` lineage | S–M |
| Crystal characterization service runs | X-ray/polariscope orientation of community specimens | `orientation_known: true` records → anisotropic model applies | S |

Negative results are first-class. Every bench contribution arrives as
schema-valid manifests + the pipeline outputs, or it didn't happen.

## B. Software work (no bench required)

| Item | Notes | Size |
|---|---|---|
| **T2 desktop panels** | thin Qt views over the already-tested headless services (provenance graph, waveform/timing preview, phase-budget view, inspectors) — contracts in `SOFTWARE_HARDWARE_ARCHITECTURE.md` §3 | M |
| **FEM/FEA integration (T3)** | import scripts consuming the `fea_export` material-card contract (CalculiX/Elmer first); eigenmode comparison harness vs the 1D/compact ladders — feeds H-01a directly | M–L |
| **GPU acceleration (CUDA/OpenCL)** | see `MODELLING_ROADMAP.md` — batch Christoffel sweeps, Monte Carlo uncertainty; must keep the CPU path as the reference oracle | L |
| **Optical simulation** | extend the straight-ray model: refraction at exit facets, birefringent ray splitting, Jones-matrix chains along paths — all EST optics, tolerance-tested against the closed forms | M |
| **Crystal libraries** | material cards beyond α-quartz (handbook constants with declared provenance, same D5-002 pattern): calcite, sapphire, lithium niobate… each = constants + tests + registry note | S each |
| **Benchmark datasets** | golden problems with known analytic answers (bar modes, sphere modes) as cross-solver benchmarks; tolerance-aware, platform-portable (the D-V3-04 lesson) | S–M |
| **Additional resonant systems** | the RSCS layer is system-agnostic by design: rooms, plates, microwave cavities as new *application* packages (like `rgcs_core` is for quartz) — never by editing the framework | L |
| **Firmware (T4/T5)** | HG Embedded OS per `embedded/HG_EMBEDDED_OS_CONTRACT.md`; the timing acceptance requirements are the spec | L |
| Windows/macOS packaging | PyInstaller recipes per platform, reproducibility-manifested | M |

## C. Documentation / methodology work

- Translate the discipline layer into a standalone "how to add claim
  classification to YOUR project" guide (most-requested reuse).
- Review the pre-registered statistics (`VALIDATION_PLAN.md` §1)
  *before* bench data exists — issues keyed to claim ids.
- Accessibility pass on the manuscripts (alt text, tagged PDFs).

## The boundary, stated once

**Software work** may never adjudicate a physical hypothesis — it can
make adjudication possible, cheaper, or better-instrumented.
**Experimental work** may never bypass the pipeline, the controls, or
the pre-registered analysis — the bench earns its claims the same way
the code does: through the registers.
