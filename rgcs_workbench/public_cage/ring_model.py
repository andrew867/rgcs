"""37-cell annular resonator model -- state equations, never force.

The ring is a stationary structure carrying a synthetic traveling
angular-momentum bias: cell parameters (impedance, capacitance,
inductance, resistance) vary in time as

    X_k(t) = X_0 + dX cos(m * theta_k - Omega * t + phi_0)

which is a resonator STATE equation. This module deliberately
contains no force, thrust, torque, or lift function, and a release
test asserts that by inspection. The first bench observable is
direction agreement between a commanded bias and a measured
near-field response, not any mechanical quantity.

Conventional anchors: angular-momentum-biased ring resonators
(US9405136B2, Nature Physics nphys3134, ACS Photonics ph400058y) and
tunable-loss ring modulation (US7561759B2). Anchors support
nonreciprocity and spatiotemporal modulation only; no anomalous
claim rides on them.
"""

from __future__ import annotations

import cmath
import math
from fractions import Fraction

CELL_COUNT = 37
RUN_ACTIVE_COUNT = 35
STEER_ACTIVE_COUNT = 33
EXTERNAL_RESONANCE_HZ = 4096 * 411          # 1,683,456 Hz

#: The hardware lane is millimetres; the field-comparison lane is
#: metres. They are DIFFERENT profiles and must never silently mix.
BENCH_PROFILE = {
    "name": "RGCS_RING_PROFILE_BENCH_MM",
    "unit": "mm",
    "outer_diameter": 288.0,
    "inner_diameter": 188.0,
    "status": "BENCH_GEOMETRY_LOCKED",
}
FIELD_PROFILE = {
    "name": "RGCS_RING_PROFILE_FIELD_M",
    "unit": "m",
    "outer_diameter": None,
    "inner_diameter": None,
    "status": "PROFILE_DECLARED_VALUES_PENDING",
}

CELL_STATES = ("active", "loaded", "lossy", "open", "guard")

#: Parameters the state equation may modulate. There is no force
#: parameter, by construction.
MODULATABLE = ("Z", "C", "L", "R")


def inner_outer_ratio() -> Fraction:
    """188/288 reduces exactly to 47/72; locked by test."""
    return Fraction(int(BENCH_PROFILE["inner_diameter"]),
                    int(BENCH_PROFILE["outer_diameter"]))


def theta(k: int) -> float:
    if not 0 <= k < CELL_COUNT:
        raise ValueError(f"cell index {k} outside 0..{CELL_COUNT - 1}")
    return 2.0 * math.pi * k / CELL_COUNT


def theta_table() -> list[dict]:
    return [{"k": k,
             "theta_rad": theta(k),
             "theta_deg": math.degrees(theta(k))}
            for k in range(CELL_COUNT)]


def make_cells(states: dict[int, str] | None = None) -> list[dict]:
    """All cells active unless a state override says otherwise."""
    states = states or {}
    cells = []
    for k in range(CELL_COUNT):
        state = states.get(k, "active")
        if state not in CELL_STATES:
            raise ValueError(f"unknown cell state '{state}'")
        cells.append({"k": k,
                      "theta_rad": theta(k),
                      "theta_deg": math.degrees(theta(k)),
                      "amplitude": 1.0 if state == "active" else 0.0,
                      "phase_rad": 0.0,
                      "state": state,
                      "C_rel": 1.0, "L_rel": 1.0, "R_rel": 1.0})
    return cells


def running_mask() -> list[dict]:
    """35/37 occupancy: two opposite-ish sectors open."""
    return make_cells({0: "open", 18: "open"})


def steering_mask(open_sector: int = 0) -> list[dict]:
    """33 active steering state: an open sector flanked by loaded and
    lossy guards produces the commanded asymmetry."""
    o = open_sector % CELL_COUNT
    return make_cells({o: "open",
                       (o + 1) % CELL_COUNT: "lossy",
                       (o - 1) % CELL_COUNT: "lossy",
                       (o + 18) % CELL_COUNT: "loaded"})


def active_count(cells) -> int:
    return sum(1 for c in cells if c["state"] == "active")


def modulated_state(k: int, t: float, *, parameter: str = "Z",
                    base: float = 1.0, delta: float = 0.1,
                    m: int = 1, omega: float = 2.0 * math.pi * 4096.0,
                    phi0: float = 0.0) -> dict:
    """X_k(t) = X_0 + dX cos(m theta_k - Omega t + phi_0).

    A field/resonator state value with its receipt. Not a force
    equation; there is nothing here to integrate into one.
    """
    if parameter not in MODULATABLE:
        raise ValueError(f"parameter must be one of {MODULATABLE}")
    value = base + delta * math.cos(m * theta(k) - omega * t + phi0)
    return {"k": k, "parameter": parameter, "t": t, "value": value,
            "m": m, "omega": omega, "phi0": phi0,
            "claim": "RESONATOR_STATE_EQUATION_ONLY"}


def commanded_direction(cells) -> float:
    """arg(d_eff) of the commanded cell weighting; radians."""
    d_eff = sum(c["amplitude"] * cmath.exp(1j * c["theta_rad"])
                for c in cells)
    if abs(d_eff) < 1e-15:
        raise ValueError("mask is isotropic; no commanded direction")
    return cmath.phase(d_eff)


def wrap_angle(delta_rad: float) -> float:
    """Wrap to (-pi, pi]."""
    return math.atan2(math.sin(delta_rad), math.cos(delta_rad))


def direction_agreement(commanded_rad: float, measured_rad: float,
                        tolerance_rad: float) -> dict:
    """First bench observable: does the measured near-field delta-B
    direction agree with the commanded bias direction? Pass/fail with
    the residual; not a force measurement."""
    residual = wrap_angle(measured_rad - commanded_rad)
    return {"commanded_rad": commanded_rad,
            "measured_rad": measured_rad,
            "residual_rad": residual,
            "tolerance_rad": tolerance_rad,
            "agrees": abs(residual) <= tolerance_rad,
            "observable": "NEAR_FIELD_DELTA_B_DIRECTION",
            "claim": "DIRECTION_AGREEMENT_ONLY"}


__all__ = ["CELL_COUNT", "RUN_ACTIVE_COUNT", "STEER_ACTIVE_COUNT",
           "EXTERNAL_RESONANCE_HZ", "BENCH_PROFILE", "FIELD_PROFILE",
           "CELL_STATES", "MODULATABLE", "inner_outer_ratio", "theta",
           "theta_table", "make_cells", "running_mask", "steering_mask",
           "active_count", "modulated_state", "commanded_direction",
           "wrap_angle", "direction_agreement"]
