"""64-state synthetic resonant lattice — Hermitian coupling + energy ledger."""

from __future__ import annotations

import cmath
import math
from typing import Any

import numpy as np


N = 64


def _hermitize(m: np.ndarray) -> np.ndarray:
    return 0.5 * (m + m.conj().T)


def build_hamiltonian(
    model: str = "counterrotating-ring",
    coupling: float = 0.15,
    detuning: float = 0.02,
) -> np.ndarray:
    h = np.zeros((N, N), dtype=complex)
    if model == "static-hermitian":
        for i in range(N - 1):
            h[i, i + 1] = coupling
            h[i + 1, i] = coupling
        for i in range(N):
            h[i, i] = (i % 8) * detuning
    elif model == "counterrotating-ring":
        for i in range(N):
            j = (i + 1) % N
            phase = 1j * coupling if i % 2 == 0 else -1j * coupling
            h[i, j] = phase
            h[j, i] = -phase.conjugate()  # keep anti-Hermitian hop -> Hermitize
        h = _hermitize(h)
        for i in range(N):
            h[i, i] += detuning * ((i % 4) - 1.5)
    else:
        raise ValueError(f"unknown lattice model: {model}")
    # Enforce Hermiticity numerically.
    return _hermitize(h)


def run_example(
    model: str = "counterrotating-ring",
    steps: int = 40,
    dt: float = 0.05,
    gamma: float = 0.01,
    drive_amp: float = 0.05,
) -> dict[str, Any]:
    """Integrate i da/dt = H a + f - i Gamma a with a simple RK2 and ledger."""
    h = build_hamiltonian(model)
    # Damping (PSD diagonal).
    gamma_m = np.diag(np.full(N, gamma, dtype=float))
    a = np.zeros(N, dtype=complex)
    a[0] = 1.0 + 0j
    a /= np.linalg.norm(a)

    initial_norm = float(np.vdot(a, a).real)
    pump = 0.0
    dissipated = 0.0
    traces = []

    for k in range(steps):
        f = np.zeros(N, dtype=complex)
        f[0] = drive_amp * cmath.exp(1j * 0.3 * k * dt)
        # Power from drive ~ Re(conj(f)·a) * 2 roughly tracked as injected.
        inject = float((2.0 * np.vdot(a, f).real) * dt)
        pump += max(0.0, inject)

        def rhs(state: np.ndarray) -> np.ndarray:
            return -1j * (h @ state) + f - gamma_m @ state

        k1 = rhs(a)
        k2 = rhs(a + dt * k1)
        a = a + 0.5 * dt * (k1 + k2)
        # Dissipated estimate from damping term.
        dissipated += float(2.0 * gamma * np.vdot(a, a).real * dt)
        if k % 5 == 0 or k == steps - 1:
            traces.append({
                "t": round(k * dt, 6),
                "norm": float(np.vdot(a, a).real),
                "site0_abs": float(abs(a[0])),
            })

    final_norm = float(np.vdot(a, a).real)
    stored = final_norm
    # Numerical drift relative to a coarse energy proxy.
    drift = abs((initial_norm + pump) - (stored + dissipated))
    return {
        "model": model,
        "n_states": N,
        "steps": steps,
        "dt": dt,
        "hermitian_residual": float(np.linalg.norm(h - h.conj().T)),
        "energy_ledger": {
            "initial": initial_norm,
            "pump": pump,
            "stored": stored,
            "dissipated": dissipated,
            "numerical_drift": drift,
            "units": "norm-proxy (dimensionless field amplitude squared)",
        },
        "trace": traces,
        "note": "Parametric/drive growth is attributed to the explicit pump term f(t).",
    }
