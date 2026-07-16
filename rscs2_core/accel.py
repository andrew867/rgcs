"""Accelerator backend layer (Agent 07, RSCS2-A.1/A.2/A.3/A.5).

Backends: 'cpu' (numpy/scipy — the AUTHORITY, DV4-004), 'opencl'
(PyOpenCL; Intel iGPU / CPU runtimes), 'cuda_interface' (interface only —
no CUDA hardware in this environment; calling it raises with an honest
status), 'auto' (best available, logged, never silent).

Accelerated workload shipped: BATCHED CHRISTOFFEL ORIENTATION SWEEP —
for N unit directions build Gamma_ik = C_ijkl n_j n_l and take the
closed-form eigenvalues of the symmetric 3x3 (trigonometric method),
returning the three phase speeds. This is element-local, embarrassingly
parallel, and parity-testable against the validated CPU
`quartz.christoffel_speeds`.

Precision policy (RSCS2-A.4): float64 is authority. The Intel Iris Xe
iGPU exposes NO cl_khr_fp64 -> it runs float32 with a REGISTERED parity
tolerance; the Intel CPU OpenCL device has fp64 and runs float64. A
backend/device/dtype record accompanies every result; there is no
silent CPU fallback — a requested backend that is unavailable raises.

Status ladder (DV4-007): statuses are EARNED per device by the tests in
tests/v4/test_rscs2_accel.py and recorded in evidence, never asserted
from imports.
"""

from __future__ import annotations

import json
import platform
import time

import numpy as np

__all__ = ["discover_devices", "capability_report", "ChristoffelSweep",
           "cpu_christoffel_sweep", "OpenCLChristoffel",
           "cuda_interface_christoffel", "sweep", "PARITY_TOL"]

#: Registered parity tolerances vs the CPU float64 authority.
PARITY_TOL = {"float64": 1e-10, "float32": 2e-4}   # relative, on speeds


# --- discovery --------------------------------------------------------

def discover_devices() -> list[dict]:
    """Real OpenCL device discovery. Empty list if pyopencl or drivers
    are absent (recorded, not hidden)."""
    try:
        import pyopencl as cl
    except Exception:
        return []
    out = []
    try:
        for p in cl.get_platforms():
            for d in p.get_devices():
                out.append({
                    "platform": p.name.strip(),
                    "device": d.name.strip(),
                    "type": cl.device_type.to_string(d.type),
                    "driver": d.driver_version,
                    "global_mem_mb": int(d.global_mem_size // 2**20),
                    "max_workgroup": int(d.max_work_group_size),
                    "fp64": "cl_khr_fp64" in d.extensions,
                })
    except Exception:
        return out
    return out


def capability_report() -> dict:
    return {
        "os": platform.platform(),
        "cpu": platform.processor(),
        "python": platform.python_version(),
        "opencl_devices": discover_devices(),
        "cuda": {"available": False,
                 "note": "no NVIDIA driver in this environment; "
                         "cuda_interface status = INTERFACE_TESTED only"},
    }


# --- CPU authority ----------------------------------------------------

def cpu_christoffel_sweep(c_full: np.ndarray, density: float,
                          directions: np.ndarray) -> np.ndarray:
    """CPU float64 authority: speeds (N,3) descending. Thin wrapper over
    the validated quartz.christoffel_speeds (LAPACK eigh)."""
    from .quartz import christoffel_speeds
    return christoffel_speeds(c_full, density, directions)["speeds_m_s"]


def cpu_christoffel_closed_form(c_full: np.ndarray, density: float,
                                directions: np.ndarray) -> np.ndarray:
    """Vectorized numpy float64 CLOSED-FORM eigenvalues — the fair
    apples-to-apples CPU baseline for the OpenCL kernel (same algorithm,
    same arithmetic; benchmark speedups are quoted against BOTH this and
    the LAPACK authority)."""
    n = np.atleast_2d(np.asarray(directions, float))
    n = n / np.linalg.norm(n, axis=1, keepdims=True)
    g = np.einsum("ijkl,nj,nl->nik", np.asarray(c_full, float), n, n,
                  optimize=True)
    q = np.trace(g, axis1=1, axis2=2) / 3.0
    p1 = g[:, 0, 1]**2 + g[:, 0, 2]**2 + g[:, 1, 2]**2
    d = g[:, (0, 1, 2), (0, 1, 2)] - q[:, None]
    p2 = np.sum(d * d, axis=1) + 2.0 * p1
    p = np.sqrt(np.maximum(p2 / 6.0, 1e-300))
    b = (g - q[:, None, None] * np.eye(3)) / p[:, None, None]
    detb = (b[:, 0, 0] * (b[:, 1, 1] * b[:, 2, 2] - b[:, 1, 2] * b[:, 2, 1])
            - b[:, 0, 1] * (b[:, 1, 0] * b[:, 2, 2] - b[:, 1, 2] * b[:, 2, 0])
            + b[:, 0, 2] * (b[:, 1, 0] * b[:, 2, 1] - b[:, 1, 1] * b[:, 2, 0]))
    r = np.clip(detb / 2.0, -1.0, 1.0)
    phi = np.arccos(r) / 3.0
    e1 = q + 2 * p * np.cos(phi)
    e3 = q + 2 * p * np.cos(phi + 2.0943951023931953)
    e2 = 3 * q - e1 - e3
    eigs = np.stack([e1, e2, e3], axis=1)
    speeds = np.sqrt(np.maximum(eigs, 0.0) / density)
    return np.sort(speeds, axis=1)[:, ::-1]


# --- OpenCL backend ---------------------------------------------------

_KERNEL = r"""
#ifdef USE_FP64
#pragma OPENCL EXTENSION cl_khr_fp64 : enable
typedef double real;
#else
typedef float real;
#endif

__kernel void christoffel(__global const real *dirs,   // N*3
                          __constant real *C,          // 81 = C_ijkl
                          const real rho,
                          __global real *speeds)       // N*3 desc
{
    int g = get_global_id(0);
    real n[3] = {dirs[3*g], dirs[3*g+1], dirs[3*g+2]};
    // Gamma_ik = C[i][j][k][l] n_j n_l
    real G[3][3];
    for (int i = 0; i < 3; ++i)
      for (int k = 0; k < 3; ++k) {
        real s = 0;
        for (int j = 0; j < 3; ++j)
          for (int l = 0; l < 3; ++l)
            s += C[((i*3+j)*3+k)*3+l] * n[j] * n[l];
        G[i][k] = s;
      }
    // closed-form symmetric 3x3 eigenvalues (trigonometric method)
    real q = (G[0][0] + G[1][1] + G[2][2]) / (real)3.0;
    real p1 = G[0][1]*G[0][1] + G[0][2]*G[0][2] + G[1][2]*G[1][2];
    real a = G[0][0]-q, b = G[1][1]-q, c = G[2][2]-q;
    real p2 = a*a + b*b + c*c + (real)2.0*p1;
    real p = sqrt(p2 / (real)6.0);
    real e1, e2, e3;
    if (p < (real)1e-30) { e1 = e2 = e3 = q; }
    else {
      real B[3][3];
      for (int i = 0; i < 3; ++i)
        for (int k2 = 0; k2 < 3; ++k2)
          B[i][k2] = (G[i][k2] - (i==k2 ? q : (real)0.0)) / p;
      real detB = B[0][0]*(B[1][1]*B[2][2]-B[1][2]*B[2][1])
                - B[0][1]*(B[1][0]*B[2][2]-B[1][2]*B[2][0])
                + B[0][2]*(B[1][0]*B[2][1]-B[1][1]*B[2][0]);
      real r = detB / (real)2.0;
      r = clamp(r, (real)-1.0, (real)1.0);
      real phi = acos(r) / (real)3.0;
      e1 = q + (real)2.0 * p * cos(phi);
      e3 = q + (real)2.0 * p * cos(phi + (real)2.0943951023931953);
      e2 = (real)3.0 * q - e1 - e3;
    }
    speeds[3*g]   = sqrt(fmax(e1, (real)0.0) / rho);
    speeds[3*g+1] = sqrt(fmax(e2, (real)0.0) / rho);
    speeds[3*g+2] = sqrt(fmax(e3, (real)0.0) / rho);
}
"""


class OpenCLChristoffel:
    """OpenCL Christoffel sweep on a named device. fp64 where supported;
    fp32 otherwise, with its registered parity tolerance."""

    def __init__(self, device_substring: str = ""):
        import pyopencl as cl
        self.cl = cl
        dev = None
        for p in cl.get_platforms():
            for d in p.get_devices():
                if device_substring.lower() in d.name.lower():
                    dev = d
                    break
            if dev:
                break
        if dev is None:
            raise RuntimeError(
                f"no OpenCL device matching {device_substring!r} "
                f"(available: {[x['device'] for x in discover_devices()]})")
        self.device = dev
        self.fp64 = "cl_khr_fp64" in dev.extensions
        self.dtype = np.float64 if self.fp64 else np.float32
        self.ctx = cl.Context([dev])
        self.queue = cl.CommandQueue(
            self.ctx, properties=cl.command_queue_properties.PROFILING_ENABLE)
        opts = ["-DUSE_FP64"] if self.fp64 else []
        self.prog = cl.Program(self.ctx, _KERNEL).build(options=opts)

    def sweep(self, c_full: np.ndarray, density: float,
              directions: np.ndarray) -> dict:
        cl = self.cl
        n = np.ascontiguousarray(np.atleast_2d(directions), self.dtype)
        n = n / np.linalg.norm(n, axis=1, keepdims=True)
        c = np.ascontiguousarray(np.asarray(c_full).ravel(), self.dtype)
        out = np.empty((len(n), 3), self.dtype)
        mf = cl.mem_flags
        t0 = time.perf_counter()
        dbuf = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR,
                         hostbuf=n)
        cbuf = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR,
                         hostbuf=c)
        obuf = cl.Buffer(self.ctx, mf.WRITE_ONLY, out.nbytes)
        t1 = time.perf_counter()
        ev = self.prog.christoffel(self.queue, (len(n),), None, dbuf,
                                   cbuf, self.dtype(density), obuf)
        ev.wait()
        kernel_s = (ev.profile.end - ev.profile.start) * 1e-9
        t2 = time.perf_counter()
        cl.enqueue_copy(self.queue, out, obuf).wait()
        t3 = time.perf_counter()
        # descending sort per row (kernel emits e1>=e2>=e3 already, but
        # guarantee it)
        out64 = np.sort(out.astype(np.float64), axis=1)[:, ::-1]
        return {"speeds_m_s": out64,
                "device": self.device.name.strip(),
                "dtype": "float64" if self.fp64 else "float32",
                "timing_s": {"h2d": t1 - t0, "kernel_event": kernel_s,
                             "kernel_wall": t2 - t1, "d2h": t3 - t2,
                             "total": t3 - t0}}


def cuda_interface_christoffel(*_args, **_kw):
    """CUDA interface stub — this environment has NO CUDA hardware
    (user decision DV4-013: CUDA is interface-only until hardware).
    Raises with an honest status; the interface contract is exercised
    by tests via this exception path."""
    raise RuntimeError(
        "cuda_interface: no CUDA hardware/driver available; status = "
        "INTERFACE_TESTED only (DV4-013). Use backend='cpu' or 'opencl'.")


def sweep(c_full, density, directions, backend: str = "auto",
          device: str = "") -> dict:
    """Backend-dispatched Christoffel sweep. NEVER falls back silently:
    an explicit backend that is unavailable raises."""
    if backend == "cpu":
        return {"speeds_m_s": cpu_christoffel_sweep(c_full, density,
                                                    directions),
                "device": "cpu-numpy", "dtype": "float64"}
    if backend == "opencl":
        return OpenCLChristoffel(device).sweep(c_full, density, directions)
    if backend == "cuda_interface":
        return cuda_interface_christoffel()
    if backend == "auto":
        devs = discover_devices()
        if devs:
            gpus = [d for d in devs if "GPU" in d["type"].upper()]
            pick = (gpus or devs)[0]["device"]
            res = OpenCLChristoffel(pick).sweep(c_full, density, directions)
            res["auto_choice"] = f"opencl:{pick}"
            return res
        res = {"speeds_m_s": cpu_christoffel_sweep(c_full, density,
                                                   directions),
               "device": "cpu-numpy", "dtype": "float64",
               "auto_choice": "cpu (no OpenCL devices)"}
        return res
    raise ValueError("backend must be cpu|opencl|cuda_interface|auto")


def write_capability_report(path_json, path_md) -> dict:
    rep = capability_report()
    with open(path_json, "w", encoding="utf-8") as fh:
        json.dump(rep, fh, indent=2)
    lines = ["# Device Capability Report\n",
             f"- OS: {rep['os']}", f"- CPU: {rep['cpu']}",
             f"- Python: {rep['python']}", "", "## OpenCL devices", ""]
    if rep["opencl_devices"]:
        lines.append("| platform | device | type | driver | mem (MB) | "
                     "fp64 |")
        lines.append("|---|---|---|---|---|---|")
        for d in rep["opencl_devices"]:
            lines.append(f"| {d['platform']} | {d['device']} | {d['type']}"
                         f" | {d['driver']} | {d['global_mem_mb']} | "
                         f"{d['fp64']} |")
    else:
        lines.append("none detected")
    lines += ["", "## CUDA", "",
              rep["cuda"]["note"]]
    with open(path_md, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return rep
