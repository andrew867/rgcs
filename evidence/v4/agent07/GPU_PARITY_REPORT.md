# GPU Parity & Benchmark Report (Agent 07) — REAL HARDWARE

All numbers measured on this machine (see DEVICE_CAPABILITY_REPORT).
Workload: batched Christoffel orientation sweep (alpha-quartz full
tensor, closed-form symmetric-3x3 eigenvalues), the registered
RSCS2-A.3 kernel. CPU float64 (LAPACK path) is the authority.

## Devices and earned statuses (DV4-007 ladder)

| Device | dtype | Status earned | Evidence |
|---|---|---|---|
| Intel Iris Xe Graphics (iGPU) | float32 (no cl_khr_fp64) | INTERFACE + NUMERICALLY_PARITY_TESTED + **HARDWARE_BENCHMARKED** | parity 2.3e-06..3.4e-05 (< registered 2e-4) across 10k..500k; timings below |
| Intel i5-1135G7 (CPU OpenCL) | float64 | INTERFACE + NUMERICALLY_PARITY_TESTED + **HARDWARE_BENCHMARKED** | parity 7.3e-15..1.8e-14 (< 1e-10) |
| both devices | -- | **MULTI_DEVICE_REPRODUCED** (this kernel) | parity passing on 2 distinct devices |
| CUDA | -- | INTERFACE_TESTED only | no CUDA hardware (DV4-013); stub raises honestly, contract tested |

## Benchmarks (warm, mean of 3; N=500,000 directions)

| Path | dtype | total (ms) | kernel event (ms) | max rel err vs authority |
|---|---|---|---|---|
| cpu numpy LAPACK (authority) | f64 | 1430.6 | -- | 0 (definition) |
| cpu numpy closed-form (fair baseline) | f64 | 346.6 | -- | 2.1e-14 |
| **Iris Xe iGPU** | f32 | **6.6** | 0.32 | 3.4e-05 |
| i5-1135G7 OpenCL | f64 | 9.8 | 4.28 | 1.8e-14 |

Honest speedup accounting: the OpenCL kernel and the numpy closed-form
baseline use the SAME algorithm; the fair speedup at N=500k is
**~52x (iGPU fp32)** and **~35x (CPU-CL fp64)** vs the closed-form CPU
baseline, and ~216x vs the LAPACK authority path (which pays per-batch
LAPACK overhead -- an algorithmic difference, stated, not hidden).
Cold-start (first call incl. context+build): ~24 ms iGPU / ~10 ms CPU-CL.
Transfer time dominates warm totals (kernel events are 0.02-4.3 ms).

## Policy compliance

- fp64 authority; iGPU fp32 results carry the registered 2e-4 tolerance
  and their dtype in every result record (RSCS2-A.4).
- No silent fallback: explicit unavailable backends raise (tested);
  'auto' records its choice in the result.
- Determinism: same device + same input -> bit-identical output (tested).
- Full CSV: benchmark.csv; plots: parity_and_benchmark.png (real runs).
