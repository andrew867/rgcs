"""Agent 07: accelerator backend — parity ladder with REAL devices.

OpenCL tests skip cleanly when no device is present (CPU-only CI stays
green); when devices exist they earn NUMERICALLY_PARITY_TESTED per
device against the CPU float64 authority within the REGISTERED
tolerances. No silent fallback: explicit backends raise if unavailable.
"""
from __future__ import annotations

import numpy as np
import pytest

from rgcs_core.anisotropy import (ALPHA_QUARTZ_DENSITY_KG_M3,
                                  alpha_quartz_stiffness_pa)
from rscs_core.propagation import voigt_to_tensor
from rscs2_core import accel

C = voigt_to_tensor(alpha_quartz_stiffness_pa())
RHO = ALPHA_QUARTZ_DENSITY_KG_M3
DEVICES = accel.discover_devices()
needs_cl = pytest.mark.skipif(not DEVICES, reason="no OpenCL device")


def _dirs(n=5000, seed=1):
    rng = np.random.default_rng(seed)
    d = rng.normal(size=(n, 3))
    return d / np.linalg.norm(d, axis=1, keepdims=True)


def test_capability_report_shape():
    rep = accel.capability_report()
    assert "opencl_devices" in rep and "cuda" in rep
    assert rep["cuda"]["available"] is False   # honest for this machine


def test_cpu_closed_form_matches_lapack_authority():
    d = _dirs(2000)
    a = accel.cpu_christoffel_sweep(C, RHO, d)
    b = accel.cpu_christoffel_closed_form(C, RHO, d)
    assert np.max(np.abs(a - b) / a) < 1e-12


def test_cuda_interface_is_honest():
    with pytest.raises(RuntimeError, match="INTERFACE_TESTED"):
        accel.sweep(C, RHO, _dirs(10), backend="cuda_interface")


def test_explicit_unavailable_backend_raises_no_silent_fallback():
    with pytest.raises((RuntimeError, Exception)):
        accel.OpenCLChristoffel("nonexistent-device-xyz")
    with pytest.raises(ValueError):
        accel.sweep(C, RHO, _dirs(10), backend="bogus")


def test_auto_backend_reports_choice():
    res = accel.sweep(C, RHO, _dirs(100), backend="auto")
    assert "auto_choice" in res
    assert res["speeds_m_s"].shape == (100, 3)


@needs_cl
def test_opencl_parity_every_device():
    """NUMERICALLY_PARITY_TESTED: every discovered OpenCL device matches
    the CPU float64 authority within its dtype's registered tolerance.
    With >=2 passing devices this is also MULTI_DEVICE_REPRODUCED."""
    d = _dirs(20000)
    ref = accel.cpu_christoffel_sweep(C, RHO, d)
    passed = []
    for dev in DEVICES:
        r = accel.OpenCLChristoffel(dev["device"]).sweep(C, RHO, d)
        tol = accel.PARITY_TOL[r["dtype"]]
        rel = np.max(np.abs(r["speeds_m_s"] - ref) / ref)
        assert rel < tol, f"{dev['device']}: {rel} > {tol}"
        passed.append((dev["device"], r["dtype"], float(rel)))
    assert len(passed) >= 1
    # record for evidence collection
    print("PARITY:", passed)


@needs_cl
def test_opencl_deterministic_across_runs():
    d = _dirs(3000, seed=9)
    dev = DEVICES[0]["device"]
    a = accel.OpenCLChristoffel(dev).sweep(C, RHO, d)["speeds_m_s"]
    b = accel.OpenCLChristoffel(dev).sweep(C, RHO, d)["speeds_m_s"]
    assert np.array_equal(a, b)            # same device, same input, same bits
