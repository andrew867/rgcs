"""R10.15 Phase E25/E30 rung 1 — manufactured analytic verification.

Closed-form problems whose exact force is known, used to verify the
Maxwell-stress integrator before any device result is trusted. These
are the strongest tests in the package: they compare a numerical
surface integral against an exact analytic answer.

  M1  point charge q in a uniform field E0  ->  F = q E0 exactly
  M2  two point charges                     ->  F = q1 q2 / (4 pi eps0 d^2)
  M3  source-free region                    ->  F = 0 exactly
  M4  charge pair, both surfaces            ->  F1 + F2 = 0 (momentum closure)
"""

from __future__ import annotations

import numpy as np

from rgcs_surface_wave.evidence import ClaimClass
from rgcs_surface_wave.geometry import EPS0
from rgcs_surface_wave.stress import integrate_force, sphere_surface


def point_charge_field(q: float, pos) -> callable:
    p0 = np.asarray(pos, float)

    def E(pts):
        d = np.asarray(pts, float) - p0
        r = np.linalg.norm(d, axis=-1, keepdims=True)
        return q * d / (4 * np.pi * EPS0 * r ** 3)
    return E


def superpose(*fields) -> callable:
    def E(pts):
        return sum(f(pts) for f in fields)
    return E


def uniform_field(vec) -> callable:
    v = np.asarray(vec, float)

    def E(pts):
        return np.broadcast_to(v, np.asarray(pts, float).shape).copy()
    return E


def zero_field(pts):
    return np.zeros_like(np.asarray(pts, float))


def m1_charge_in_uniform_field(q: float = 1e-9,
                               e0=(0.0, 0.0, 1e3),
                               radius: float = 0.05,
                               n_theta: int = 60,
                               n_phi: int = 120) -> dict:
    """F must equal q*E0 exactly (the self-field contributes nothing)."""
    E = superpose(point_charge_field(q, (0, 0, 0)), uniform_field(e0))
    surf = sphere_surface(radius, (0, 0, 0), n_theta, n_phi)
    got = integrate_force(surf, E, zero_field, time_averaged=False)
    exact = q * np.asarray(e0, float)
    err = np.linalg.norm(np.array(got["force_n"]) - exact) \
        / np.linalg.norm(exact)
    return {"case": "M1_charge_in_uniform_field",
            "exact_force_n": exact.tolist(),
            "computed_force_n": got["force_n"],
            "relative_error": float(err),
            "closure_defect": got["closure_defect"],
            "passed": bool(err < 1e-9),
            "claim_class": ClaimClass.DERIVED.value}


def m2_two_point_charges(q1: float = 1e-9, q2: float = 2e-9,
                         separation: float = 0.10,
                         radius: float = 0.03,
                         n_theta: int = 60, n_phi: int = 120) -> dict:
    """Coulomb force recovered by surface integration around charge 1."""
    p1 = np.array([0.0, 0.0, 0.0])
    p2 = np.array([separation, 0.0, 0.0])
    E = superpose(point_charge_field(q1, p1), point_charge_field(q2, p2))
    surf = sphere_surface(radius, p1, n_theta, n_phi)
    got = integrate_force(surf, E, zero_field, time_averaged=False)
    mag = q1 * q2 / (4 * np.pi * EPS0 * separation ** 2)
    exact = np.array([-mag, 0.0, 0.0])       # like charges repel: -x
    err = np.linalg.norm(np.array(got["force_n"]) - exact) / abs(mag)
    return {"case": "M2_two_point_charges",
            "exact_force_n": exact.tolist(),
            "computed_force_n": got["force_n"],
            "coulomb_magnitude_n": mag,
            "relative_error": float(err),
            "passed": bool(err < 1e-9),
            "claim_class": ClaimClass.DERIVED.value}


def m3_source_free(radius: float = 0.05) -> dict:
    """A uniform field exerts no net force on an empty closed surface."""
    surf = sphere_surface(radius, (0, 0, 0), 40, 80)
    got = integrate_force(surf, uniform_field((3.0, -2.0, 5.0)),
                          zero_field, time_averaged=False)
    mag = got["force_magnitude_n"]
    return {"case": "M3_source_free_uniform",
            "computed_force_n": got["force_n"],
            "force_magnitude_n": mag,
            "passed": bool(mag < 1e-18),
            "claim_class": ClaimClass.DERIVED.value}


def m4_pair_momentum_closure(q1: float = 1e-9, q2: float = -2e-9,
                             separation: float = 0.08,
                             radius: float = 0.025) -> dict:
    """Newton's third law as a momentum-closure test: F1 + F2 = 0."""
    p1 = np.array([0.0, 0.0, 0.0])
    p2 = np.array([separation, 0.0, 0.0])
    E = superpose(point_charge_field(q1, p1), point_charge_field(q2, p2))
    f1 = integrate_force(sphere_surface(radius, p1, 60, 120), E,
                         zero_field, time_averaged=False)
    f2 = integrate_force(sphere_surface(radius, p2, 60, 120), E,
                         zero_field, time_averaged=False)
    total = np.array(f1["force_n"]) + np.array(f2["force_n"])
    scale = max(np.linalg.norm(f1["force_n"]), 1e-30)
    return {"case": "M4_pair_momentum_closure",
            "force_body_1_n": f1["force_n"],
            "force_body_2_n": f2["force_n"],
            "sum_n": total.tolist(),
            "relative_residual": float(np.linalg.norm(total) / scale),
            "passed": bool(np.linalg.norm(total) / scale < 1e-9),
            "claim_class": ClaimClass.DERIVED.value}


def run_all() -> dict:
    cases = [m1_charge_in_uniform_field(), m2_two_point_charges(),
             m3_source_free(), m4_pair_momentum_closure()]
    return {"schema": "rgcs.r1015.manufactured.v1",
            "cases": cases,
            "all_passed": all(c["passed"] for c in cases),
            "claim_class": ClaimClass.DERIVED.value}
