"""Nonlinear AFM trajectory + phonon-controlled exchange (Agent M12;
RGCS-V4-EQ-006/007; materials reference.nonlinear_afm and
reference.phonon_exchange; primary sources SRC-V4-03 (Schlauderer,
TmFeO3) and SRC-V4-04 (Afanasiev) — metadata-only locally.

A: phi'' = -gamma phi' - dW/dphi + tau(t), W multi-minimum.
B: driven phonon Q(t) modulates exchange J(Q); the classifier
   distinguishes INDIRECT parameter modulation from DIRECT
   hybridization (an indirect frequency shift is never labeled an
   avoided crossing)."""

from __future__ import annotations

import math

import numpy as np

from ..multiphysics import applicability, get_material
from ..multiphysics import make_result, not_applicable_result

MODULE_ID = "rscs2.refmodels.nonlinear_spin"


# --- A: nonlinear trajectory (EQ-006) ----------------------------------------

def potential(phi, k1: float = 1.0):
    """W(phi) = -k1 cos(2 phi)/2: minima at 0 and pi, barrier at
    pi/2 of height k1 (normalized units: rad, 1/s)."""
    return -0.5 * k1 * np.cos(2 * np.asarray(phi))


def _dW(phi, k1):
    return k1 * math.sin(2 * phi)


def gaussian_torque(t, t0, width, amp, channel="impulsive"):
    """Impulsive = derivative-of-gaussian (net zero impulse on phi'),
    displacive = gaussian."""
    x = (np.asarray(t) - t0) / width
    g = np.exp(-0.5 * x * x)
    if channel == "impulsive":
        return -amp * x * g
    if channel == "displacive":
        return amp * g
    raise ValueError("channel must be impulsive|displacive")


def waveform_transfer(waveform: np.ndarray,
                      fir: np.ndarray | None = None) -> np.ndarray:
    """Measured waveform -> local near-field drive through a declared
    FIR transfer function (identity when fir is None)."""
    if fir is None:
        return np.asarray(waveform, float)
    return np.convolve(waveform, np.asarray(fir, float),
                       mode="same")


def spin_trajectory(material_id: str, amp: float, k1: float = 1.0,
                    gamma: float = 0.05, t_end: float = 60.0,
                    n: int = 30000, channel: str = "impulsive",
                    phi0: float = 0.0, fir=None) -> dict:
    """Deterministic RK4 integration; classifies the regime and
    projects the Faraday observable ~ sin(phi) with probe weighting."""
    mat = get_material(material_id)
    app = applicability(mat, "magnetic_order")
    if app["applicability"] == "NOT_APPLICABLE":
        return not_applicable_result(MODULE_ID, material_id,
                                     app["reason_code"], app["reason"])
    dt = t_end / n
    t = np.arange(n + 1) * dt
    tau = waveform_transfer(
        gaussian_torque(t, 5.0, 0.8, amp, channel), fir)
    phi, w = float(phi0), 0.0
    phis = np.empty(n + 1)
    phis[0] = phi

    def acc(i, p, v):
        return -gamma * v - _dW(p, k1) + tau[min(i, n)]

    for i in range(n):
        k1v = acc(i, phi, w)
        k1x = w
        k2v = acc(i, phi + 0.5 * dt * k1x, w + 0.5 * dt * k1v)
        k2x = w + 0.5 * dt * k1v
        k3v = acc(i, phi + 0.5 * dt * k2x, w + 0.5 * dt * k2v)
        k3x = w + 0.5 * dt * k2v
        k4v = acc(i + 1, phi + dt * k3x, w + dt * k3v)
        k4x = w + dt * k3v
        phi += dt * (k1x + 2 * k2x + 2 * k3x + k4x) / 6
        w += dt * (k1v + 2 * k2v + 2 * k3v + k4v) / 6
        phis[i + 1] = phi
    final = phis[-1]
    minima = np.pi * np.round(final / np.pi)
    switched = abs(minima - np.pi * np.round(phi0 / np.pi)) > 0.5
    slip = abs(final - phi0)
    regime = ("over_barrier_switching" if switched
              else "under_barrier_oscillation")
    faraday = np.sin(phis)                       # unit probe weight
    return make_result(
        MODULE_ID, material_id, "REDUCED_ORDER_VALIDATED", ["DER"],
        {"regime": regime, "switched": bool(switched),
         "phase_slip_rad": float(slip),
         "final_phi_rad": float(final),
         "long_lived_offset": float(abs(final - phi0) > 0.5)},
        {"phi": "rad", "time": "normalized 1/w0 units"},
        source_ids=["SRC-V4-03"], equation_ids=["RGCS-V4-EQ-006"],
        assumptions=["reduced sine-Gordon-type trajectory; no "
                     "ab-initio spin dynamics"]) | {
        "t": t, "phi": phis, "faraday": faraday, "tau": tau}


def switching_threshold(material_id: str, lo: float, hi: float,
                        n_iter: int = 18, **kw) -> dict:
    """Bisect the torque amplitude threshold between oscillation and
    switching; uncertainty = final bracket width."""
    for _ in range(n_iter):
        mid = 0.5 * (lo + hi)
        out = spin_trajectory(material_id, mid, **kw)
        if out["value"]["switched"]:
            hi = mid
        else:
            lo = mid
    return {"threshold_amp": 0.5 * (lo + hi),
            "uncertainty": hi - lo}


# --- B: phonon-controlled exchange (EQ-007) ------------------------------------

def phonon_exchange(material_id: str, drive_amp: float,
                    drive_freq: float, phonon_freq: float = 1.0,
                    phonon_gamma: float = 0.05, j0: float = 1.0,
                    c1: float = 0.3, c2: float = 0.0,
                    t_end: float = 200.0, n: int = 40000) -> dict:
    """Driven phonon Q(t) modulates J(Q) = j0 (1 + c1 Q + c2 Q^2);
    the local spin frequency follows sqrt(J/j0) (curvature). Reports
    the shift, transient chirp, and off-resonance behavior."""
    mat = get_material(material_id)
    app = applicability(mat, "spin_phonon_coupling")
    if app["applicability"] == "NOT_APPLICABLE":
        return not_applicable_result(MODULE_ID + ".exchange",
                                     material_id, app["reason_code"],
                                     app["reason"])
    dt = t_end / n
    t = np.arange(n + 1) * dt
    env = np.clip(t / 20.0, 0, 1) * np.exp(-np.maximum(
        t - 120.0, 0.0) / 30.0)
    drive = drive_amp * env * np.cos(drive_freq * t)
    q, v = 0.0, 0.0
    qs = np.empty(n + 1)
    qs[0] = 0.0
    for i in range(n):
        a = -phonon_gamma * v - phonon_freq ** 2 * q + drive[i]
        q += dt * (v + 0.5 * dt * a)
        v += dt * a
        qs[i + 1] = q
    # cycle-averaged envelope of Q (rectified smooth)
    w_len = max(int((2 * np.pi / phonon_freq) / dt), 5)
    kern = np.ones(w_len) / w_len
    q_env = np.convolve(np.abs(qs), kern, mode="same")
    j_t = j0 * (1 + c1 * q_env + c2 * q_env ** 2)
    omega_s = np.sqrt(np.maximum(j_t / j0, 1e-12))
    chirp = np.gradient(omega_s, t)
    return make_result(
        MODULE_ID + ".exchange", material_id,
        "REDUCED_ORDER_VALIDATED", ["DER"],
        {"max_shift": float(omega_s.max() - 1.0),
         "min_shift": float(omega_s.min() - 1.0),
         "max_chirp": float(np.abs(chirp).max()),
         "q_peak": float(np.abs(qs).max())},
        {"omega_s": "normalized to unperturbed", "Q": "normalized"},
        source_ids=["SRC-V4-04"], equation_ids=["RGCS-V4-EQ-007"],
        assumptions=["indirect parameter modulation; no DFT exchange "
                     "values"]) | {
        "t": t, "q": qs, "omega_s": omega_s, "chirp": chirp}


def coupling_mechanism_classifier(freq_traces: np.ndarray,
                                  drive_envelope: np.ndarray) -> dict:
    """Distinguish DIRECT hybridization (two branches with a
    persistent avoided gap) from INDIRECT parameter modulation (a
    single branch tracking the drive envelope). Gate H7: an indirect
    shift is never labeled an avoided crossing."""
    tr = np.atleast_2d(np.asarray(freq_traces, float))
    if tr.shape[0] >= 2:
        gap = np.min(np.abs(tr[1] - tr[0]))
        branch_span = np.ptp(tr[0]) + np.ptp(tr[1])
        if gap > 0.05 * max(branch_span, 1e-12) and branch_span > 0:
            return {"mechanism": "direct_hybridization",
                    "min_gap": float(gap)}
    env = np.asarray(drive_envelope, float)
    shift = tr[0] - tr[0][0]
    sc = shift - shift.mean()
    ec = env - env.mean()
    denom = np.linalg.norm(sc) * np.linalg.norm(ec)
    corr = float(sc @ ec / denom) if denom else 0.0
    if abs(corr) > 0.8:
        return {"mechanism": "indirect_parameter_modulation",
                "envelope_correlation": corr}
    return {"mechanism": "inconclusive",
            "envelope_correlation": corr}
