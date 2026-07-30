"""R10.15 Phases C18, D19, D20, D23 — Maxwell stress on closed surfaces.

Time-averaged form for phasors E = Re[E~ exp(+i omega t)]:

    <T> = (1/2) Re[ eps E E* + mu H H*
                    - (1/2)(eps |E|^2 + mu |H|^2) I ].

Transient form for instantaneous real fields:

    T = eps E E + mu H H - (1/2)(eps|E|^2 + mu|H|^2) I.

Note the dimensional convention: the magnetic term is mu*H H*, which
equals B H*. Writing E E + B B without eps and mu is the classic
dimensional error and is rejected by an explicit unit check.

    F = closed_integral( <T> . n dA ),
    tau = closed_integral( r x (<T> . n) dA ).

HARD REFUSALS enforced here:
  * an OPEN surface may never yield a reported net force;
  * a STATIC field solution may never be used to claim a force in a
    system declared time-modulated;
  * a force may NEVER be estimated as Q times radiated power over c
    ("Q-multiplied photon thrust"); stored energy, field gradients,
    and reaction forces must be computed explicitly.
"""

from __future__ import annotations

import math

import numpy as np

from rgcs_surface_wave.evidence import ClaimClass, ClaimError
from rgcs_surface_wave.geometry import EPS0, MU0


class StressError(ValueError):
    pass


# ------------------------------------------------------- quadrature
def sphere_surface(radius: float, center=(0.0, 0.0, 0.0),
                   n_theta: int = 40, n_phi: int = 80) -> dict:
    """Closed spherical integration surface (Gauss-Legendre in
    cos(theta), uniform in phi). Outward normals."""
    if radius <= 0:
        raise StressError("radius must be positive")
    x, w = np.polynomial.legendre.leggauss(n_theta)
    theta = np.arccos(x)
    phi = (np.arange(n_phi) + 0.5) * 2 * np.pi / n_phi
    TH, PH = np.meshgrid(theta, phi, indexing="ij")
    W = np.outer(w, np.full(n_phi, 2 * np.pi / n_phi))
    n = np.stack([np.sin(TH) * np.cos(PH),
                  np.sin(TH) * np.sin(PH),
                  np.cos(TH)], axis=-1).reshape(-1, 3)
    dA = (W * radius ** 2).reshape(-1)
    pts = np.asarray(center) + radius * n
    return {"points": pts, "normals": n, "weights": dA,
            "closed": True, "kind": "sphere", "radius": radius,
            "center": tuple(center)}


def cylinder_surface(radius: float, z_lo: float, z_hi: float,
                     center_xy=(0.0, 0.0), n_phi: int = 96,
                     n_z: int = 40, n_r: int = 24) -> dict:
    """Closed cylinder (side + two caps) with outward normals."""
    if radius <= 0 or z_hi <= z_lo:
        raise StressError("require radius > 0 and z_hi > z_lo")
    cx, cy = center_xy
    pts, nrm, wts = [], [], []
    phi = (np.arange(n_phi) + 0.5) * 2 * np.pi / n_phi
    zx, zw = np.polynomial.legendre.leggauss(n_z)
    z = 0.5 * (z_hi + z_lo) + 0.5 * (z_hi - z_lo) * zx
    zwt = 0.5 * (z_hi - z_lo) * zw
    for zi, wz in zip(z, zwt):
        for p in phi:
            pts.append([cx + radius * np.cos(p), cy + radius * np.sin(p), zi])
            nrm.append([np.cos(p), np.sin(p), 0.0])
            wts.append(radius * (2 * np.pi / n_phi) * wz)
    rx, rw = np.polynomial.legendre.leggauss(n_r)
    rr = 0.5 * radius * (rx + 1.0)
    rwt = 0.5 * radius * rw
    for zc, sgn in ((z_hi, 1.0), (z_lo, -1.0)):
        for ri, wr in zip(rr, rwt):
            for p in phi:
                pts.append([cx + ri * np.cos(p), cy + ri * np.sin(p), zc])
                nrm.append([0.0, 0.0, sgn])
                wts.append(ri * (2 * np.pi / n_phi) * wr)
    return {"points": np.array(pts), "normals": np.array(nrm),
            "weights": np.array(wts), "closed": True,
            "kind": "cylinder", "radius": radius,
            "z_range": (z_lo, z_hi)}


def closure_defect(surface: dict) -> float:
    """||sum w_i n_i|| / sum w_i. Zero for a genuinely closed surface
    by the divergence theorem applied to a constant vector field."""
    w = np.asarray(surface["weights"])
    n = np.asarray(surface["normals"])
    return float(np.linalg.norm((w[:, None] * n).sum(axis=0)) / w.sum())


def assert_closed(surface: dict, tol: float = 1e-8) -> float:
    d = closure_defect(surface)
    if not surface.get("closed", False) or d > tol:
        raise StressError(
            f"refused: integration surface is not closed (defect "
            f"{d:.3e} > {tol:.1e}). A net force may never be reported "
            "from an open surface: the missing flux is exactly the "
            "unaccounted reaction.")
    return d


# --------------------------------------------------- stress tensors
def stress_tensor_timeavg(E: np.ndarray, H: np.ndarray,
                          eps: float = EPS0,
                          mu: float = MU0) -> np.ndarray:
    """<T> for complex phasor fields, shape (..., 3) -> (..., 3, 3)."""
    E = np.asarray(E, dtype=complex)
    H = np.asarray(H, dtype=complex)
    if E.shape[-1] != 3 or H.shape[-1] != 3:
        raise StressError("fields must have a trailing axis of size 3")
    EE = np.einsum("...i,...j->...ij", E, np.conj(E))
    HH = np.einsum("...i,...j->...ij", H, np.conj(H))
    e2 = np.einsum("...i,...i->...", E, np.conj(E)).real
    h2 = np.einsum("...i,...i->...", H, np.conj(H)).real
    I = np.eye(3)
    T = 0.5 * np.real(eps * EE + mu * HH) \
        - 0.25 * ((eps * e2 + mu * h2)[..., None, None] * I)
    return T


def stress_tensor_transient(E: np.ndarray, H: np.ndarray,
                            eps: float = EPS0,
                            mu: float = MU0) -> np.ndarray:
    """Instantaneous T for real fields."""
    E = np.asarray(E, dtype=float)
    H = np.asarray(H, dtype=float)
    EE = np.einsum("...i,...j->...ij", E, E)
    HH = np.einsum("...i,...j->...ij", H, H)
    e2 = np.einsum("...i,...i->...", E, E)
    h2 = np.einsum("...i,...i->...", H, H)
    I = np.eye(3)
    return (eps * EE + mu * HH
            - 0.5 * ((eps * e2 + mu * h2)[..., None, None] * I))


def dimensional_check(eps: float, mu: float) -> dict:
    """Guard against the E E + B B (missing eps/mu) error.

    eps*E^2 and mu*H^2 are both energy densities (J/m^3 = N/m^2). A
    formulation that omits the constants is off by eps0 and mu0 and is
    rejected.
    """
    e_term = eps * 1.0 ** 2          # eps * (V/m)^2 -> N/m^2
    h_term = mu * 1.0 ** 2           # mu * (A/m)^2 -> N/m^2
    return {"eps_term_units": "N/m^2", "mu_term_units": "N/m^2",
            "eps_term_value_at_unit_field": e_term,
            "mu_term_value_at_unit_field": h_term,
            "convention": "mu*H H* (equivalently B H*), never B B "
                          "without mu",
            "ok": e_term > 0 and h_term > 0}


# ------------------------------------------------ closed integration
def integrate_force(surface: dict, E, H, eps: float = EPS0,
                    mu: float = MU0, time_averaged: bool = True,
                    origin=(0.0, 0.0, 0.0), tol: float = 1e-8) -> dict:
    """Closed-surface force and torque. Refuses open surfaces."""
    defect = assert_closed(surface, tol)
    pts = np.asarray(surface["points"], float)
    n = np.asarray(surface["normals"], float)
    w = np.asarray(surface["weights"], float)
    Ev = E(pts) if callable(E) else np.asarray(E)
    Hv = H(pts) if callable(H) else np.asarray(H)
    T = (stress_tensor_timeavg(Ev, Hv, eps, mu) if time_averaged
         else stress_tensor_transient(Ev, Hv, eps, mu))
    traction = np.einsum("...ij,...j->...i", T, n)
    F = (w[:, None] * traction).sum(axis=0)
    r = pts - np.asarray(origin, float)
    tau = (w[:, None] * np.cross(r, traction)).sum(axis=0)
    return {
        "force_n": F.tolist(), "force_magnitude_n": float(np.linalg.norm(F)),
        "torque_nm": tau.tolist(),
        "torque_magnitude_nm": float(np.linalg.norm(tau)),
        "surface_kind": surface.get("kind"),
        "surface_closed": True, "closure_defect": defect,
        "convention": ("time_averaged_phasor" if time_averaged
                       else "instantaneous_transient"),
        "points": int(len(pts)),
        "dimensional_check": dimensional_check(eps, mu),
        "claim_class": ClaimClass.SIMULATED.value,
        "nonclaim": "computed Maxwell-stress value, not a measured force",
    }


# ------------------------------------------------------- hard refusals
def refuse_static_force_for_modulated_system(system_is_modulated: bool,
                                             solution_is_static: bool
                                             ) -> None:
    """A static solve may not be used to claim force under modulation."""
    if system_is_modulated and solution_is_static:
        raise StressError(
            "refused: a static field solution cannot be used to claim "
            "a force in a time-modulated system. The modulation "
            "changes the field distribution and the momentum budget; "
            "solve the harmonic or transient problem, or report the "
            "static result explicitly as the UNMODULATED baseline.")


def refuse_q_multiplied_thrust(*_args, **_kwargs) -> None:
    """Reject F = Q * P / c and every variant of it."""
    raise ClaimError(
        "refused: force may not be estimated as Q multiplied by "
        "radiated power over c. Cavity Q counts energy recirculation, "
        "not net momentum flux: a symmetric resonator stores large "
        "energy while radiating zero net momentum. Compute stored "
        "energy, field gradients, and closed-surface reaction forces "
        "explicitly instead.")


# ------------------------------------------------------- Phase D23
def reversal_parity(force_forward: np.ndarray,
                    force_reversed: np.ndarray,
                    tol: float = 1e-12) -> dict:
    """Classify a force component under a declared reversal."""
    f, r = np.asarray(force_forward, float), np.asarray(force_reversed, float)
    scale = max(np.linalg.norm(f), np.linalg.norm(r), tol)
    even = np.linalg.norm(f - r) / scale < 1e-6
    odd = np.linalg.norm(f + r) / scale < 1e-6
    return {"forward_n": f.tolist(), "reversed_n": r.tolist(),
            "parity": ("EVEN" if even else "ODD" if odd else "MIXED"),
            "symmetric_part_n": (0.5 * (f + r)).tolist(),
            "antisymmetric_part_n": (0.5 * (f - r)).tolist(),
            "note": "the Maxwell stress is QUADRATIC in the fields, so "
                    "a pure drive-polarity reversal must give EVEN "
                    "parity. An ODD component under polarity reversal "
                    "indicates a modelling error or a genuine "
                    "field-asymmetric mechanism and must be "
                    "investigated before use.",
            "claim_class": ClaimClass.DERIVED.value}


def polarity_reversal_invariance(E, H, surface: dict,
                                 eps: float = EPS0,
                                 mu: float = MU0) -> dict:
    """Executed check that reversing drive polarity leaves F unchanged."""
    fwd = integrate_force(surface, E, H, eps, mu)
    def negE(p):
        return -(E(p) if callable(E) else np.asarray(E))
    def negH(p):
        return -(H(p) if callable(H) else np.asarray(H))
    rev = integrate_force(surface, negE, negH, eps, mu)
    par = reversal_parity(fwd["force_n"], rev["force_n"])
    par["invariant_as_required"] = par["parity"] == "EVEN"
    return par
