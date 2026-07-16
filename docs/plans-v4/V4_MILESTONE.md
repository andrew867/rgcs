# V4 Milestones

**Status:** PLANNING. Milestones map to tranche exits; each is a
reviewable, independently valuable state. Dates are relative (no
calendar committed — this is an open contributor project).

| M | Name | Tranche | Deliverable | CPU-only usable? | Gate to next |
|---|---|---|---|---|---|
| M1 | Foundations | A | `rscs2_core` skeleton, registry namespaces, pinned CPU stack, backend decision | n/a | licence audit + PoCs pass |
| M2 | Meshing | B | import + mesh + tags + deterministic manifests | yes | mesh determinism + tag coverage |
| M3 | **CPU elastic solver (first usable)** | C | modal solver + EB/Timoshenko/convergence benchmarks | **yes** | **V.2/V.3/V.8 green** |
| M4 | Crystal multiphysics | D | anisotropic L2 + piezo L3; Christoffel + splitting anchors | yes | **V.6/V.9 green** (conservative ext.) |
| M5 | Acceleration | E | backend seam + CuPy/PyOpenCL interface + parity harness | yes | seam + fallback + parity ladder wired |
| M6 | Eye + projections | F | diagnostic family + consensus + optical/coil/thermal | yes | V.10 + NULL-model + robustness |
| M7 | Validation + inverse | G | fork + cantilever gates + datasets + inverse/UQ | yes | **V.4 + MAC + null-model** |
| M8 | **Release v4.0.0** | H | viz/report + desktop/CLI + manuscripts + QA + tag | yes | full gate table GREEN |

## Minimum-viable-product boundary

**M3 is the MVP:** a CPU-only, deterministic, benchmark-validated modal
solver is a genuinely useful, publishable tool on its own. Everything
above M3 is additive value; a slip in D–H never invalidates M3.

## Conservative-extension checkpoints (cannot be skipped)

- **M4 gate = V.6 (Christoffel) + V.9 (splitting):** v4 provably
  reproduces frozen v3. If either reds, M4 does not close.
- **M8 gate** re-runs all anchors + mandatory benchmarks before the tag.

## Honest-status milestones for GPU (parallel to M5)

GPU status is reported per the four-status ladder, not per milestone:
INTERFACE_TESTED is reachable at M5 on any machine; PARITY needs a
device; BENCHMARKED/MULTI_DEVICE need contributor hardware and may
arrive after v4.0.0 as `experimental`.
