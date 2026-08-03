"""The force boundary, v0.7.

Exactly ONE function in this package computes a candidate force, and it
is this module's ``candidate_force``. Its inputs are the exact-arithmetic
eta candidate and a COUPLED ring power -- wall power is not accepted here
at all; it must first pass through ``rgcs_phyrll_v06.resonance.
ring_power_from_wall`` with a declared eta_couple, which raises without
one.

A thrust CLAIM is a different object from a candidate force, and
``thrust_claim`` refuses to construct one unless a measured eta with an
uncertainty exists. There is no configuration of this package in which
arithmetic alone produces a thrust claim.
"""

from __future__ import annotations

from fractions import Fraction as F

from .roles import REGISTRY, Coefficient

#: The exact-arithmetic candidate, lane B. Units N per coupled ring watt.
ETA_EXACT_CANDIDATE = F(64672, 961)


class ThrustClaimRefused(RuntimeError):
    """Raised whenever a thrust claim is attempted without a measured eta."""


def candidate_force(p_ring_coupled_W: float,
                    eta=ETA_EXACT_CANDIDATE) -> dict:
    """F_candidate = eta_exact_candidate * P_ring_coupled.

    The single permitted candidate-force computation. The result is a
    CANDIDATE tagged BENCH_REQUIRED -- a number the bench must confirm or
    kill, never a performance statement.
    """
    if p_ring_coupled_W < 0:
        raise ValueError("power must be non-negative")
    return {"F_candidate_N": float(eta) * p_ring_coupled_W,
            "eta_used": str(eta),
            "eta_role": "EXACT_ARITHMETIC",
            "power_kind": "P_ring_coupled",
            "claim": "BENCH_REQUIRED",
            "is_thrust_claim": False}


def thrust_claim(eta_measured: Coefficient | None,
                 p_ring_coupled_W: float) -> dict:
    """Construct a thrust claim -- possible ONLY from a measurement.

    ``eta_measured`` must be a lane-D coefficient with a measured value
    and an uncertainty. Anything else -- None, a lane-B fraction, a bare
    float -- is refused. As shipped, the registry contains no such
    measurement, so this function currently cannot succeed, which is the
    intended state of the package.
    """
    if not isinstance(eta_measured, Coefficient):
        raise ThrustClaimRefused(
            "a thrust claim requires a typed lane-D measurement, not "
            f"{type(eta_measured).__name__}")
    if not eta_measured.may_claim_performance:
        raise ThrustClaimRefused(
            f"{eta_measured.name} may not claim performance: lane="
            f"{eta_measured.lane}, role={eta_measured.role}, measured="
            f"{eta_measured.measured_value}, "
            f"uncertainty={eta_measured.uncertainty}")
    return {"F_N": eta_measured.measured_value * p_ring_coupled_W,
            "uncertainty_N": eta_measured.uncertainty * p_ring_coupled_W,
            "claim": "PHYSICAL_MEASUREMENT",
            "is_thrust_claim": True}


def no_claimant_exists() -> bool:
    """True while the shipped registry holds no performance-eligible eta."""
    return not any(c.may_claim_performance for c in REGISTRY)


__all__ = ["ETA_EXACT_CANDIDATE", "ThrustClaimRefused", "candidate_force",
           "thrust_claim", "no_claimant_exists"]
