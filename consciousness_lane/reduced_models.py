"""T01/T03/T05 reduced-order dynamical models.

These are mathematics about abstract oscillator populations and
first-order state variables. They are NOT brain measurements, NOT
evidence for any consciousness hypothesis, and NOT importable into
quartz computation (see the package quarantine contract)."""

from __future__ import annotations

import math

import numpy as np

STATUS = "REDUCED_ORDER_VALIDATED"


# --- C001/C002/C006/C041: decaying resonance of state change ---------

def state_change_response(t, omega_hz: float, zeta: float,
                          drive=None) -> dict:
    """C001: x'' + 2 zeta w x' + w^2 x = f(t) — a damped resonator in
    an abstract 'state-change' coordinate. C002: awareness proxy is
    |dx/dt| (the current velocity of state change). Units: x is
    dimensionless, t in s, omega_hz in Hz."""
    t = np.asarray(t, float)
    w = 2 * math.pi * omega_hz
    dt = float(t[1] - t[0])
    x = np.zeros(len(t))
    v = np.zeros(len(t))
    f = np.zeros(len(t)) if drive is None else np.asarray(drive,
                                                          float)
    for i in range(1, len(t)):
        a = f[i - 1] - 2 * zeta * w * v[i - 1] - w * w * x[i - 1]
        v[i] = v[i - 1] + a * dt
        x[i] = x[i - 1] + v[i] * dt
    tau = 1.0 / (zeta * w) if zeta > 0 else float("inf")
    return {"t": t, "x": x, "dxdt": v, "tau_s": tau,
            "awareness_proxy": np.abs(v), "status": STATUS,
            "note": "abstract state coordinate; not a measured "
                    "neural signal"}


def dream_wake_constraint(k_ext: float, k_sensory: float,
                          k_int: float = 1.0) -> dict:
    """C041/C042: constraint budget C = k_sensory + k_int + k_ext.
    Wake is the high-k_sensory regime, dream the low one. k_ext is the
    QUARANTINED external-field term: it is a free parameter that must
    be fitted, never assumed nonzero (C030/C042)."""
    if k_ext != 0.0:
        note = ("k_ext != 0 is a HYPOTHESIS under test, not an "
                "assumption; falsified if fits return k_ext ~ 0")
    else:
        note = "k_ext = 0 is the default null (no external field)"
    return {"constraint_total": k_sensory + k_int + k_ext,
            "regime": "wake" if k_sensory > k_int else "dream",
            "k_ext": k_ext, "k_ext_quarantined": True, "note": note,
            "status": STATUS}


# --- C010/C025/C024/C045/C046/C047/C048: Kuramoto ---------------------

def kuramoto(omega: np.ndarray, k: float, t_end: float = 50.0,
             dt: float = 0.01, seed: int = 3) -> dict:
    """C025: theta_i' = omega_i + (K/N) sum_j sin(theta_j - theta_i).
    Returns the order parameter r(t) = |mean e^{i theta}|."""
    rng = np.random.default_rng(seed)
    omega = np.asarray(omega, float)
    n = len(omega)
    th = rng.uniform(0, 2 * math.pi, n)
    steps = int(t_end / dt)
    r = np.zeros(steps)
    for s in range(steps):
        z = np.mean(np.exp(1j * th))
        r[s] = abs(z)
        th = th + dt * (omega + k * abs(z) *
                        np.sin(np.angle(z) - th))
    return {"r_t": r, "r_final": float(np.mean(r[-steps // 5:])),
            "k": k, "status": STATUS}


def kuramoto_critical_k(gamma: float) -> float:
    """C025 analytic limit: for a Lorentzian frequency distribution of
    half-width gamma, K_c = 2 gamma (Kuramoto's mean-field result).
    EST relation; the simulation is validated against it."""
    return 2.0 * gamma


def synchrony_with_surrogates(sig_a, sig_b, n_surrogate: int = 200,
                              seed: int = 11) -> dict:
    """C024/C045 control: phase-locking value against phase-shuffled
    surrogates. Reports the surrogate-corrected p-value, because raw
    PLV between two slow signals is high by construction."""
    rng = np.random.default_rng(seed)
    a = np.asarray(sig_a, float)
    b = np.asarray(sig_b, float)

    def _plv(x, y):
        return abs(np.mean(np.exp(1j * (np.angle(_analytic(x)) -
                                        np.angle(_analytic(y))))))
    obs = _plv(a, b)
    null = np.array([_plv(a, rng.permutation(b))
                     for _ in range(n_surrogate)])
    p = float((np.sum(null >= obs) + 1) / (n_surrogate + 1))
    return {"plv": float(obs), "p_surrogate": p,
            "exceeds_surrogates": p < 0.05, "status": STATUS,
            "note": "synthetic or supplied signals only; no measured "
                    "human data in this lane"}


def _analytic(x):
    X = np.fft.fft(x)
    h = np.zeros(len(x))
    h[0] = 1
    h[1:(len(x) + 1) // 2] = 2
    return np.fft.ifft(X * h)


def coherence_is_not_truth() -> dict:
    """C048 control demonstration: two oscillator populations, both
    driven to r ~ 1, encoding contradictory 'states'. High coherence
    in both proves coherence measures ORDER, not veridicality."""
    a = kuramoto(np.full(60, 1.0), k=8.0, seed=1)
    b = kuramoto(np.full(60, -1.0), k=8.0, seed=2)
    return {"population_a_r": a["r_final"],
            "population_b_r": b["r_final"],
            "states_contradictory": True,
            "both_coherent": a["r_final"] > 0.9 and
            b["r_final"] > 0.9,
            "conclusion": "coherence is not truth: both populations "
                          "are maximally coherent while encoding "
                          "opposite states",
            "status": STATUS}


# --- C015/C016: microtubule causal threshold -------------------------

def microtubule_threshold(tau_c_s: float, eta_phi: float,
                          k_cross: float,
                          theta_neural_bias: float = 1.0) -> dict:
    """C016/C033/G33: the causal threshold that any microtubule
    coherence claim must clear before it can bias a neural decision:

        tau_c * eta_phi * K_cross > theta_neural_bias

    tau_c   coherence lifetime (s)
    eta_phi transduction efficiency to a neural variable (1/s scale)
    K_cross cross-scale coupling gain (dimensionless)
    theta   the bias a synaptic event already produces (reference 1)

    HYP status. The reference decoherence estimate at 310 K
    (Tegmark-type, ~1e-13 s) is included so the comparison is
    explicit rather than rhetorical."""
    product = tau_c_s * eta_phi * k_cross
    ref = 1e-13
    return {"product": product, "threshold": theta_neural_bias,
            "clears_threshold": bool(product > theta_neural_bias),
            "tau_c_s": tau_c_s,
            "reference_decoherence_310K_s": ref,
            "tau_c_exceeds_reference": bool(tau_c_s > ref),
            "status": "SOURCE_HYPOTHESIS",
            "evidence_tags": ["HYP"],
            "note": "a hypothesis clears this threshold only with "
                    "MEASURED tau_c, eta_phi, and K_cross in a "
                    "biological preparation; none exist here"}
