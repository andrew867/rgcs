"""Reduced-order spoof-SPP transmission-line simulator."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .receipts import receipt


@dataclass(frozen=True)
class MetasurfaceConfig:
    period_m: float = 0.005
    inductance_h_per_m: float = 2.0e-7
    capacitance_f_per_m: float = 8.0e-11
    resistance_ohm_per_m: float = 0.2
    conductance_s_per_m: float = 1.0e-6
    cells: int = 16
    f_min_hz: float = 1.0e9
    f_max_hz: float = 4.0e9
    points: int = 9
    input_power_w: float = 1.0


def sweep(cfg: MetasurfaceConfig | None = None) -> dict[str, object]:
    cfg = cfg or MetasurfaceConfig()
    if min(cfg.period_m, cfg.inductance_h_per_m, cfg.capacitance_f_per_m,
           cfg.cells, cfg.f_min_hz, cfg.f_max_hz, cfg.points,
           cfg.input_power_w) <= 0:
        raise ValueError("metasurface parameters must be positive")
    freqs = np.linspace(cfg.f_min_hz, cfg.f_max_hz, cfg.points)
    omega = 2 * np.pi * freqs
    z = np.sqrt((cfg.resistance_ohm_per_m + 1j * omega * cfg.inductance_h_per_m)
                / (cfg.conductance_s_per_m + 1j * omega * cfg.capacitance_f_per_m))
    gamma = np.sqrt((cfg.resistance_ohm_per_m + 1j * omega * cfg.inductance_h_per_m)
                    * (cfg.conductance_s_per_m + 1j * omega * cfg.capacitance_f_per_m))
    beta = np.imag(gamma)
    alpha = np.real(gamma)
    phase_velocity = omega / beta
    group_velocity = np.gradient(omega, beta)
    length = cfg.period_m * cfg.cells
    transmitted = cfg.input_power_w * np.exp(-2 * alpha * length)
    loss = cfg.input_power_w - transmitted
    q = beta / np.maximum(2 * alpha, 1e-30)
    dispersion = [
        {
            "frequency_hz": float(f),
            "beta_rad_per_m": float(b),
            "alpha_np_per_m": float(a),
            "phase_velocity_m_per_s": float(vp),
            "group_velocity_m_per_s": float(vg),
            "surface_impedance_ohm": {"re": float(zz.real), "im": float(zz.imag)},
            "q_estimate": float(qq),
        }
        for f, b, a, vp, vg, zz, qq in zip(freqs, beta, alpha,
                                           phase_velocity, group_velocity, z, q)
    ]
    result = {
        "geometry": {"period_m": cfg.period_m, "cells": cfg.cells,
                     "length_m": length},
        "assumptions": [
            "passive corrugated conductor represented as distributed RLCG line",
            "single-mode reduced-order transmission-line approximation",
        ],
        "valid_frequency_range_hz": [cfg.f_min_hz, cfg.f_max_hz],
        "dispersion_curve": dispersion,
        "field_or_mode_proxy": "complex propagation constant gamma = alpha + i beta",
        "power_ledger": {
            "units": "W",
            "input_electrical_power": cfg.input_power_w,
            "transmitted_power_min": float(np.min(transmitted)),
            "transmitted_power_max": float(np.max(transmitted)),
            "ohmic_and_dielectric_loss_min": float(np.min(loss)),
            "ohmic_and_dielectric_loss_max": float(np.max(loss)),
            "numerical_residual": float(np.max(np.abs(cfg.input_power_w - transmitted - loss))),
        },
        "warning": "This electromagnetic reduced-order model does not compute gravity or gravity coupling.",
    }
    return receipt(
        "metasurface", "YELLOW", ["REDUCED_ORDER_EM_SIMULATION", "UNDERDETERMINED_PHYSICS_LANE"],
        cfg.__dict__,
        [{"name": "passive_RLCG_spoof_spp_line",
          "units": {"L": "H/m", "C": "F/m", "R": "ohm/m",
                    "G": "S/m", "frequency": "Hz", "power": "W"}}],
        result,
        ["tests/rgcs_lab/test_metasurface.py"],
        warnings=[result["warning"]],
    )

