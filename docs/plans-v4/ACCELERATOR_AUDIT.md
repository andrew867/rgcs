# Accelerator Audit (Agent 13 Role B)

Scope: Intel iGPU/OpenCL backend honesty (G12–G14).

| item | evidence | result |
|---|---|---|
| Devices are REAL | `evidence/v4/agent07/DEVICE_CAPABILITY_REPORT.*`: Intel Iris Xe Graphics (fp32-only, no cl_khr_fp64, driver 32.0.101.7085) + Intel i5-1135G7 CPU OpenCL (fp64) | queried live from pyopencl, copied into bundle with provenance |
| Parity vs CPU authority (G13) | max rel err vs cpu-float64 LAPACK: Iris Xe fp32 3.4e-05 (< registered 2e-4); i5 CL fp64 1.8e-14 (< 1e-10) | PASS |
| Benchmarks fair | GPU compared against the CPU CLOSED-FORM baseline (same algorithm), not the slower LAPACK path: 500k directions 6.6 ms (Xe) vs 346.6 ms (CPU closed-form) | fair-baseline documented |
| Status ladder honesty (G12) | kernel: HARDWARE_BENCHMARKED on 2 real devices → MULTI_DEVICE_REPRODUCED; CUDA: INTERFACE_TESTED only (raises with honest message; no hardware, DV4-013) | statuses earned, none inflated |
| No silent fallback (G14) | `sweep(backend="opencl")` on a machine without CL RAISES; `auto` records `auto_choice`; test `test_explicit_unavailable_backend_raises_no_silent_fallback` | enforced + tested |
| Determinism | same device, same input → identical output (tested) | green |
| Hosted CI posture | pyopencl deliberately NOT installed on CI runners; accel tests self-skip; nothing on CI can masquerade as GPU evidence | by construction |
| Kernel correctness | closed-form trigonometric symmetric-3×3 eigenvalues vs LAPACK on random directions | within registered dtype tolerance |

No defects found. All GPU claims trace to measured device evidence.
