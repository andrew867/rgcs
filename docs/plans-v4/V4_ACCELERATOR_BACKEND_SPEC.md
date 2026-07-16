# V4 Accelerator Backend Spec — `rscs2_core.accel` (RSCS2-A.*)

**Status:** PLANNING. **CPU is authoritative and always present
(DV4-004). No GPU exists on the planning machine** → this pass can
specify to INTERFACE/PARITY only; HARDWARE_BENCHMARKED requires a
contributor with hardware (DV4-007).

## 1. The seam (RSCS2-A.1)

A single backend-neutral module exposing a **numpy-subset array API**
(array creation, elementwise, reductions, sparse matvec, dense small
eigensolve hooks). Consumers (solver, diagnostics, MC) call the seam,
never a backend directly. Backends:

| Backend | Library | Licence | Status ceiling this pass |
|---|---|---|---|
| CPU (default/authority) | numpy/scipy | BSD | full |
| CUDA | CuPy (drop-in numpy-like) | MIT | INTERFACE + PARITY (no local HW) |
| OpenCL | PyOpenCL | MIT | INTERFACE (+ PARITY where a device exists) |
| future HIP/SYCL | — | — | boundary only (documented seam) |

CuPy is provisional-primary because its numpy-identical API gives the
cleanest parity story (same test, two backends). All GPU backends are
**optional extras**; `pip install rscs2` with no extras is CPU-only and
complete.

## 2. Capability detection (RSCS2-A.2)

Enumerate devices, query total/available memory, supported dtypes,
double-precision support. Result recorded in run provenance. **Absence
is normal:** no device → CPU, no warning beyond an info log.

## 3. Operations (RSCS2-A.3/A.4)

- Chunked sparse matvec / SpMV with an explicit **memory budget**
  (problem tiled to fit device memory; budget recorded).
- **Precision policy (RSCS2-A.4):** float64 is authority. float32 is
  opt-in and only permitted for an operation that has a recorded
  CPU-vs-CPU-f32 error bound AND a GPU parity record; the f32 error is
  propagated into `UncertainValue`, never hidden.

## 4. The parity ladder (RSCS2-A.5) — honest GPU status

Per operation, a status is earned and recorded:

1. **INTERFACE_TESTED** — the op runs through the seam on the backend
   and returns correctly-shaped output (can be checked with a CPU-backed
   mock of the backend API; achievable now, no GPU).
2. **NUMERICALLY_PARITY_TESTED** — backend output matches CPU authority
   within a declared tolerance on a fixed problem set (needs the real
   backend + a device; contributor-provided or CI GPU runner).
3. **HARDWARE_BENCHMARKED** — timing on named hardware, reported with
   device, driver, dtype, problem size, and variance. **Never claimed
   without the hardware.**
4. **MULTI_DEVICE_REPRODUCED** — parity + benchmark reproduced on ≥2
   distinct devices/vendors.

An op may execute on a backend **only at ≥ status 2** for that op;
otherwise the seam routes to CPU and logs the downgrade. No silent GPU
path; no "it imports therefore it's fast" claim (DV4-007).

## 5. Reproducibility

Seeds fixed and recorded; backend + dtype policy in every artifact's
provenance; cross-backend comparison is tolerance-aware (a GPU result is
"equivalent" not "byte-identical"). A run's headline numbers are always
reproducible on CPU alone.

## 6. Tests

Seam contract tests (CPU); CuPy/PyOpenCL interface tests behind
`@requires_backend` skips (green-by-skip on CPU-only CI, green-by-run on
a GPU runner); parity tests (SpMV, reductions, dense small eigensolve)
tolerance-checked; memory-budget/tiling correctness; f32 error-bound
recording; a **negative test** that a not-yet-parity-tested op refuses
to run on GPU and falls back; provenance records the backend actually
used. CI matrix: the existing 3-OS CPU matrix always runs the full
suite; an optional GPU job (self-hosted/contributed) runs the
`@requires_backend` set and uploads parity evidence.
