"""R10.15 Phase D21 — momentum ledger.

    F_annulus + F_dielectric + F_supports + dP_field/dt + F_radiation = 0

Every interacting body contributes its own closed-surface force. A run
is RED when the residual exceeds the declared tolerance, and a ledger
that is missing a body refuses rather than closing on a subset -- a
ledger that omits the supports will appear to show net thrust, which
is the single most common way this class of measurement goes wrong.
"""

from __future__ import annotations

import numpy as np

from rgcs_surface_wave.evidence import ClaimClass
from rgcs_surface_wave.geometry import C0

REQUIRED_BODIES = ("annulus", "dielectric", "supports", "enclosure")


class MomentumError(ValueError):
    pass


def field_momentum(poynting_w_per_m2: np.ndarray,
                   volume_m3: float) -> np.ndarray:
    """P_field = (1/c^2) * integral(S) dV, evaluated on a mean S."""
    return np.asarray(poynting_w_per_m2, float) * volume_m3 / C0 ** 2


def radiated_momentum_rate(radiated_power_w: float,
                           directivity_vector=None) -> np.ndarray:
    """dP/dt carried by radiation. Isotropic radiation carries ZERO net
    momentum; only the anisotropic part contributes."""
    if directivity_vector is None:
        return np.zeros(3)
    d = np.asarray(directivity_vector, float)
    return radiated_power_w * d / C0


def close(bodies: dict, d_p_field_dt=(0.0, 0.0, 0.0),
          radiation=(0.0, 0.0, 0.0), tolerance: float = 1e-6,
          require_all: bool = True) -> dict:
    """Assemble and verify the momentum ledger."""
    missing = [b for b in REQUIRED_BODIES if b not in bodies]
    if require_all and missing:
        raise MomentumError(
            f"refused: momentum ledger is missing {missing}. A ledger "
            "assembled from a subset of bodies can show an apparent "
            "net force that is really an unaccounted reaction. Provide "
            "every body, or pass require_all=False and accept an "
            "explicitly OPEN ledger that cannot support any claim.")
    total = np.zeros(3)
    rows = {}
    for name, f in bodies.items():
        v = np.asarray(f, float)
        if v.shape != (3,):
            raise MomentumError(f"force for {name!r} must be a 3-vector")
        rows[name] = v.tolist()
        total += v
    dp = np.asarray(d_p_field_dt, float)
    rad = np.asarray(radiation, float)
    residual = total + dp + rad
    scale = max(float(np.max([np.linalg.norm(v) for v in
                              [np.asarray(x) for x in bodies.values()]]
                             )) if bodies else 0.0, 1e-30)
    rel = float(np.linalg.norm(residual) / scale)
    closed = rel <= tolerance
    return {
        "schema": "rgcs.r1015.momentum-ledger.v1",
        "bodies": rows,
        "sum_of_body_forces_n": total.tolist(),
        "d_p_field_dt_n": dp.tolist(),
        "radiation_reaction_n": rad.tolist(),
        "residual_n": residual.tolist(),
        "residual_magnitude_n": float(np.linalg.norm(residual)),
        "relative_residual": rel,
        "tolerance": tolerance,
        "status": "GREEN" if closed else "RED",
        "ledger_complete": not missing,
        "missing_bodies": missing,
        "interpretation": (
            "momentum closes: the force on any one body is balanced by "
            "reactions on the others. This is the ordinary result and "
            "it supports no propulsion claim."
            if closed else
            "momentum does NOT close to tolerance. Treat every force "
            "number in this run as unverified: an unclosed ledger "
            "means a body, a surface, or a flux term is missing."),
        "claim_class": ClaimClass.SIMULATED.value,
    }
