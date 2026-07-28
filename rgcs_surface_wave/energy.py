"""R10.15 Phase D22 — energy ledger.

    P_source + P_switch = dU_field/dt + P_conductor + P_dielectric
                          + P_radiated + P_mechanical + P_thermal

Stored energy and dissipation are computed explicitly. Q is reported
as a ratio of stored energy to loss per cycle -- never used as a
multiplier on radiated power to manufacture a thrust figure.
"""

from __future__ import annotations

import math

from rgcs_surface_wave.evidence import ClaimClass, ClaimError

CHANNELS = ("conductor", "dielectric", "radiated", "mechanical",
            "thermal")


class EnergyError(ValueError):
    pass


def stored_energy(peak_field_v_per_m: float, volume_m3: float,
                  epsilon_r: float = 1.0) -> dict:
    """Time-averaged stored energy of a resonant mode.

    At resonance the electric and magnetic stores are equal, so the
    total is twice the electric part: U = (1/2) eps |E|^2 V for a
    peak-amplitude phasor convention.
    """
    from rgcs_surface_wave.geometry import EPS0
    if volume_m3 <= 0:
        raise EnergyError("volume must be positive")
    u_e = 0.25 * EPS0 * epsilon_r * peak_field_v_per_m ** 2 * volume_m3
    return {"u_electric_j": u_e, "u_magnetic_j": u_e,
            "u_total_j": 2.0 * u_e,
            "convention": "peak-amplitude phasor; equipartition at "
                          "resonance",
            "claim_class": ClaimClass.DERIVED.value}


def q_from_energy(u_total_j: float, power_loss_w: float,
                  frequency_hz: float) -> dict:
    """Q = omega U / P_loss, reported as a ratio, not a force factor."""
    if power_loss_w <= 0 or frequency_hz <= 0:
        raise EnergyError("loss power and frequency must be positive")
    q = 2 * math.pi * frequency_hz * u_total_j / power_loss_w
    return {"q": q, "stored_energy_j": u_total_j,
            "power_loss_w": power_loss_w,
            "definition": "Q = omega * U_stored / P_loss",
            "forbidden_use": "Q must not multiply radiated power to "
                             "produce a thrust estimate; it counts "
                             "energy recirculation, not net momentum "
                             "flux",
            "claim_class": ClaimClass.DERIVED.value}


def thrust_from_q(*_a, **_k):
    """Explicitly unavailable."""
    raise ClaimError(
        "refused: there is no Q-multiplied thrust path in this "
        "package. A high-Q symmetric resonator stores large energy and "
        "radiates zero NET momentum. Compute closed-surface forces "
        "with stress.integrate_force and close the ledger in "
        "momentum.close instead.")


def close(source_w: float, switch_w: float, d_u_dt_w: float,
          losses_w: dict, tolerance: float = 1e-6) -> dict:
    """Assemble and verify the energy ledger."""
    unknown = [k for k in losses_w if k not in CHANNELS]
    if unknown:
        raise EnergyError(
            f"unknown loss channels {unknown}; declared channels are "
            f"{list(CHANNELS)}")
    for k, v in losses_w.items():
        if v < 0:
            raise EnergyError(
                f"loss channel {k!r} is negative ({v}); a passive "
                "channel cannot generate energy. If this came from a "
                "solve, the run is invalid.")
    total_out = d_u_dt_w + sum(losses_w.values())
    total_in = source_w + switch_w
    residual = total_in - total_out
    scale = max(abs(total_in), abs(total_out), 1e-30)
    rel = abs(residual) / scale
    closed = rel <= tolerance
    return {
        "schema": "rgcs.r1015.energy-ledger.v1",
        "p_source_w": source_w, "p_switch_w": switch_w,
        "d_u_field_dt_w": d_u_dt_w,
        "losses_w": {k: losses_w.get(k, 0.0) for k in CHANNELS},
        "total_in_w": total_in, "total_out_w": total_out,
        "residual_w": residual, "relative_residual": rel,
        "tolerance": tolerance,
        "status": "GREEN" if closed else "RED",
        "channels_declared": list(CHANNELS),
        "interpretation": (
            "energy closes: all supplied power is accounted for by "
            "storage, dissipation, radiation, and mechanical work"
            if closed else
            "energy does NOT close: a channel is missing or a solver "
            "result is inconsistent. No downstream force number from "
            "this run may be used."),
        "claim_class": ClaimClass.SIMULATED.value,
    }
