"""Passive reduced-order spoof-SPP metasurface cell — energy conserving."""

from __future__ import annotations

import cmath
import math
from typing import Any


def corrugated_cell(
    frequency_hz: float = 1.0e9,
    groove_depth_m: float = 2.0e-3,
    period_m: float = 5.0e-3,
    loss_tan: float = 0.01,
) -> dict[str, Any]:
    """Toy 1-port reduced-order model with explicit energy accounting.

    This is IMPLEMENTED_SOFTWARE / CONVENTIONAL_PHYSICS for a passive cell.
    High-fidelity full-wave spoof-SPP remains YELLOW / UNDERDETERMINED.
    """
    if frequency_hz <= 0 or groove_depth_m <= 0 or period_m <= 0:
        raise ValueError("frequency, groove_depth, and period must be positive")
    if loss_tan < 0:
        raise ValueError("loss_tan must be >= 0")

    c0 = 299_792_458.0
    k0 = 2.0 * math.pi * frequency_hz / c0
    # Soft resonance near quarter-wave groove depth.
    phi = k0 * groove_depth_m
    resonance = math.sin(phi) ** 2
    # Passive reflectance/transmittance with dielectric loss.
    absorption = min(0.95, loss_tan * (1.0 + 4.0 * resonance))
    # Remaining power split between R and T with a phase.
    remain = max(0.0, 1.0 - absorption)
    r_mag = math.sqrt(remain * (0.35 + 0.5 * resonance))
    t_mag = math.sqrt(max(0.0, remain - r_mag * r_mag))
    phase = cmath.exp(1j * (-phi))
    r = r_mag * phase
    t = t_mag * phase

    power_sum = abs(r) ** 2 + abs(t) ** 2 + absorption
    return {
        "model": "corrugated-cell-reduced-order-v1",
        "fidelity": "reduced-order",
        "high_fidelity_status": "YELLOW_UNDERDETERMINED",
        "inputs": {
            "frequency_hz": frequency_hz,
            "groove_depth_m": groove_depth_m,
            "period_m": period_m,
            "loss_tan": loss_tan,
        },
        "s_parameters": {
            "R": {"re": r.real, "im": r.imag, "mag": abs(r)},
            "T": {"re": t.real, "im": t.imag, "mag": abs(t)},
        },
        "energy_ledger": {
            "incident": 1.0,
            "reflected": abs(r) ** 2,
            "transmitted": abs(t) ** 2,
            "absorbed": absorption,
            "sum": power_sum,
            "conservation_residual": abs(power_sum - 1.0),
            "units": "fraction of incident power",
        },
        "claims": {
            "gravity_modification": False,
            "labels_generic_eigenmode_as_gravity": False,
        },
    }


def sweep(
    frequencies_hz: list[float] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    freqs = frequencies_hz or [0.8e9, 1.0e9, 1.2e9]
    points = [corrugated_cell(frequency_hz=f, **kwargs) for f in freqs]
    return {
        "model": "corrugated-cell-sweep-v1",
        "points": points,
        "max_conservation_residual": max(
            p["energy_ledger"]["conservation_residual"] for p in points
        ),
    }
