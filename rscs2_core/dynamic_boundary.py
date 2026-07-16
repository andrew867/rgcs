"""Dynamic boundaries, modal projection, work-energy accounting, and
symmetry lowering (Agent M6). CLASSICAL throughout: mode mixing is
never called photon creation; microscopic (proton) tunnelling is an
INTERFACE_ONLY record; continuum symmetry sweeps ground no tunnelling
claims (M1 exclusion matrix)."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

FORBIDDEN_WORDINGS = ("photon creation", "particle creation",
                      "proton tunnelling observed")


@dataclass(frozen=True)
class BoundarySchedule:
    """Typed time-dependent boundary parameter p(t)."""
    kind: str            # mechanical_support|electrical_potential|optical_condition
    profile: str         # sudden|ramp|sinusoid|event
    p_initial: float
    p_final: float
    t_switch_s: float
    duration_s: float = 0.0          # ramp duration (0 for sudden)
    frequency_hz: float = 0.0        # sinusoid

    _KINDS = ("mechanical_support", "electrical_potential",
              "optical_condition")
    _PROFILES = ("sudden", "ramp", "sinusoid", "event")

    def __post_init__(self):
        if self.kind not in self._KINDS:
            raise ValueError(f"unknown schedule kind {self.kind}")
        if self.profile not in self._PROFILES:
            raise ValueError(f"unknown profile {self.profile}")
        if self.profile == "ramp" and self.duration_s <= 0:
            raise ValueError("ramp requires positive duration")
        if self.t_switch_s < 0 or self.duration_s < 0:
            raise ValueError("negative times rejected")

    def value(self, t_s) -> np.ndarray:
        t = np.asarray(t_s, float)
        if self.profile == "sudden":
            return np.where(t < self.t_switch_s, self.p_initial,
                            self.p_final)
        if self.profile == "ramp":
            x = np.clip((t - self.t_switch_s) / self.duration_s,
                        0.0, 1.0)
            return self.p_initial + (self.p_final
                                     - self.p_initial) * x
        if self.profile == "sinusoid":
            return self.p_initial + (self.p_final - self.p_initial) \
                * 0.5 * (1 - np.cos(2 * np.pi * self.frequency_hz
                                    * np.maximum(t, 0.0)))
        return np.full_like(t, self.p_initial)      # event: external

    def switching_rate_measure(self, modal_period_s: float) -> float:
        """Dimensionless rate: modal period / switch duration.
        >> 1 sudden, << 1 adiabatic."""
        dur = self.duration_s if self.duration_s > 0 else 1e-300
        return modal_period_s / dur


# --- modal projection ----------------------------------------------------

def mode_mixing_matrix(problem, sol_before: dict,
                       sol_after: dict) -> np.ndarray:
    """M-weighted overlap O_ij = phi_after_i^T M phi_before_j between
    the mass-orthonormal bases (same mesh/DOF layout required)."""
    A = sol_after["modes"]
    B = sol_before["modes"]
    if A.shape[0] != B.shape[0]:
        raise ValueError("bases live on different DOF spaces")
    return A.T @ (problem.M @ B)


def project_state(mix: np.ndarray, coeffs_before: np.ndarray
                  ) -> np.ndarray:
    return mix @ np.asarray(coeffs_before, float)


def degenerate_subspace_overlap(mix: np.ndarray, idx_before: list,
                                idx_after: list) -> float:
    """Rotation-invariant subspace overlap: mean squared singular
    value of the cross-block (1.0 = same subspace regardless of the
    arbitrary basis inside a degenerate pair)."""
    blk = mix[np.ix_(idx_after, idx_before)]
    s = np.linalg.svd(blk, compute_uv=False)
    return float(np.mean(s ** 2))


# --- work-energy accounting (analytic oscillator) -------------------------

def oscillator_schedule(omega_of_t, x0: float, v0: float,
                        t_end_s: float, n: int = 200_000) -> dict:
    """Integrate x'' = -w(t)^2 x (RK4) and close the energy ledger:
    E(t) - E(0) must equal the injected boundary work
    W = ∫ w wdot x^2 dt (since dH/dt = w wdot x^2)."""
    dt = t_end_s / n
    t = np.arange(n + 1) * dt
    w = np.asarray(omega_of_t(t), float)
    x, v = x0, v0
    xs = np.empty(n + 1)
    vs = np.empty(n + 1)
    xs[0], vs[0] = x, v

    def acc(ti, xi):
        return -float(omega_of_t(ti)) ** 2 * xi

    for i in range(n):
        ti = t[i]
        k1x, k1v = v, acc(ti, x)
        k2x, k2v = v + 0.5 * dt * k1v, acc(ti + 0.5 * dt,
                                           x + 0.5 * dt * k1x)
        k3x, k3v = v + 0.5 * dt * k2v, acc(ti + 0.5 * dt,
                                           x + 0.5 * dt * k2x)
        k4x, k4v = v + dt * k3v, acc(ti + dt, x + dt * k3x)
        x += dt * (k1x + 2 * k2x + 2 * k3x + k4x) / 6
        v += dt * (k1v + 2 * k2v + 2 * k3v + k4v) / 6
        xs[i + 1], vs[i + 1] = x, v
    E = 0.5 * vs ** 2 + 0.5 * w ** 2 * xs ** 2
    wdot = np.gradient(w, t)
    work = np.concatenate([[0.0], np.cumsum(
        (w * wdot * xs ** 2)[:-1] * dt + 0.5 * np.diff(
            w * wdot * xs ** 2) * dt)])
    closure = abs((E[-1] - E[0]) - work[-1]) / max(E[0], 1e-300)
    return {"t_s": t, "x": xs, "v": vs, "energy_j": E,
            "boundary_work_j": work, "closure_rel_err": closure,
            "adiabatic_invariant": E / np.maximum(w, 1e-300)}


# --- symmetry lowering -----------------------------------------------------

def participation_ratio(mode: np.ndarray) -> float:
    """PR = (sum u^2)^2 / (N sum u^4) in (0, 1]; small = localized."""
    u2 = np.asarray(mode, float) ** 2
    return float(u2.sum() ** 2 / (len(u2) * (u2 ** 2).sum()))


def symmetry_lowering_sweep(eps_values, base_side_m=0.01,
                            length_m=0.12, e_pa=210e9, nu=0.3,
                            rho=7850.0, divisions=(3, 3, 18)) -> dict:
    """Break the square-section degeneracy geometrically: section
    a x a(1+eps). Returns the bending-pair splitting, participation,
    and mode-shape correlation across the sweep (continuation)."""
    from . import fem
    rows = []
    prev_mode = None
    for eps in eps_values:
        mesh = fem.box_mesh((base_side_m, base_side_m * (1 + eps),
                             length_m), divisions)
        prob = fem.assemble_isotropic(mesh, e_pa, nu, rho)
        sol = fem.solve_modes(prob, 10)
        f = sol["elastic_frequencies_hz"]
        pair = np.sort(f[:2])
        nr = sol["n_rigid_modes"]
        m0 = sol["modes"][:, nr]
        corr = None
        if prev_mode is not None and len(m0) == len(prev_mode):
            corr = abs(float(prev_mode @ (prob.M @ m0)))
        prev_mode = m0
        rows.append({"eps": float(eps),
                     "f_pair_hz": pair.tolist(),
                     "splitting_hz": float(pair[1] - pair[0]),
                     "rel_split": float((pair[1] - pair[0])
                                        / pair.mean()),
                     "participation": participation_ratio(m0),
                     "mode_correlation_prev": corr})
    return {"sweep": rows,
            "note": "continuum symmetry sensitivity; grounds NO "
                    "microscopic tunnelling claim (exclusion matrix)"}


# --- microscopic tunnelling interface (INTERFACE_ONLY) ---------------------

def tunnelling_interface_record(potential_description: dict) -> dict:
    """Schema-only hook for a future microscopic solver."""
    return {"classification": "INTERFACE_ONLY",
            "evidence_tags": ["ENG"],
            "potential": dict(potential_description),
            "note": "no tunnelling computation is implemented; "
                    "continuum symmetry sweeps do not ground "
                    "tunnelling claims"}
