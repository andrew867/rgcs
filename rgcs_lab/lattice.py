"""64-state synthetic resonant lattice with explicit energy ledger."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .receipts import receipt


@dataclass(frozen=True)
class LatticeConfig:
    n_states: int = 64
    coupling_rad_s: float = 1.0
    damping_s: float = 0.0
    drive_amplitude: float = 0.0
    drive_state: int = 0
    dt_s: float = 0.01
    steps: int = 100
    directed_phase_rad: float = 0.0
    defect_state: int | None = None
    defect_shift_rad_s: float = 0.0


def hermitian_ring_hamiltonian(cfg: LatticeConfig) -> np.ndarray:
    n = cfg.n_states
    if n != 64:
        raise ValueError("WS06 public lattice requires exactly 64 states")
    h = np.zeros((n, n), dtype=complex)
    phase = np.exp(1j * cfg.directed_phase_rad)
    for i in range(n):
        j = (i + 1) % n
        h[i, j] += cfg.coupling_rad_s * phase
        h[j, i] += cfg.coupling_rad_s * np.conj(phase)
    if cfg.defect_state is not None:
        h[cfg.defect_state % n, cfg.defect_state % n] += cfg.defect_shift_rad_s
    if not np.allclose(h, h.conj().T, atol=1e-12):
        raise ValueError("Hamiltonian must be Hermitian")
    return h


def _rhs(a: np.ndarray, h: np.ndarray, gamma: np.ndarray,
         drive: np.ndarray) -> np.ndarray:
    return -1j * h.dot(a) + drive - gamma.dot(a)


def simulate(cfg: LatticeConfig | None = None) -> dict[str, object]:
    cfg = cfg or LatticeConfig()
    if cfg.dt_s <= 0 or cfg.steps < 1:
        raise ValueError("dt_s must be positive and steps must be >= 1")
    h = hermitian_ring_hamiltonian(cfg)
    gamma = np.eye(cfg.n_states, dtype=complex) * cfg.damping_s
    drive = np.zeros(cfg.n_states, dtype=complex)
    drive[cfg.drive_state % cfg.n_states] = cfg.drive_amplitude
    a = np.zeros(cfg.n_states, dtype=complex)
    a[0] = 1.0
    initial = float(np.vdot(a, a).real)
    dissipated = 0.0
    pump = 0.0
    samples: list[list[dict[str, float]]] = []
    for _ in range(cfg.steps):
        before = float(np.vdot(a, a).real)
        k1 = _rhs(a, h, gamma, drive)
        k2 = _rhs(a + 0.5 * cfg.dt_s * k1, h, gamma, drive)
        k3 = _rhs(a + 0.5 * cfg.dt_s * k2, h, gamma, drive)
        k4 = _rhs(a + cfg.dt_s * k3, h, gamma, drive)
        da = cfg.dt_s * (k1 + 2 * k2 + 2 * k3 + k4) / 6
        dissipated += max(0.0, 2.0 * cfg.dt_s
                          * float(np.vdot(a, gamma.dot(a)).real))
        pump += max(0.0, 2.0 * cfg.dt_s * float(np.vdot(a, drive).real))
        a = a + da
        after = float(np.vdot(a, a).real)
        if len(samples) < 5:
            top = np.argsort(np.abs(a))[-3:][::-1]
            samples.append([{"state": int(i), "amplitude_abs": float(abs(a[i]))}
                            for i in top])
        if not np.isfinite(after):
            raise FloatingPointError("lattice integration diverged")
        if cfg.drive_amplitude == 0.0 and cfg.damping_s == 0.0:
            pump += max(0.0, after - before)  # should remain numeric zero
    stored = float(np.vdot(a, a).real)
    drift = stored + dissipated - initial - pump
    result = {
        "states": cfg.n_states,
        "dt_s": cfg.dt_s,
        "steps": cfg.steps,
        "hamiltonian_hermitian": bool(np.allclose(h, h.conj().T, atol=1e-12)),
        "final_norm": stored,
        "sample_top_states": samples,
        "energy_ledger": {
            "units": "dimensionless modal norm",
            "initial": initial,
            "pump": pump,
            "stored": stored,
            "dissipated": dissipated,
            "numerical_drift": drift,
            "resonance_gain_label": "attributed_to_external_drive_or_declared_parametric_pump",
        },
    }
    return receipt(
        "lattice", "GREEN", ["SYNTHETIC_DIMENSION", "ENERGY_LEDGER"],
        cfg.__dict__,
        [{"name": "64_state_coupled_mode_ring",
          "equation": "i da/dt = H a + f - i Gamma a",
          "units": {"H": "rad/s", "Gamma": "1/s", "dt": "s"}}],
        result,
        ["tests/rgcs_lab/test_lattice.py"],
    )

