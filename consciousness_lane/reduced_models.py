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


# --- C010: Holographic Ring Attractor Lattice (T02 analogue) ----------

def ring_attractor(n: int = 64, k_exc: float = 16.0,
                   k_inh: float = 1.0, r_max: float = 1.0,
                   noise: float = 0.0,
                   input_dir: float | None = None,
                   steps: int = 600, dt: float = 0.05,
                   seed: int = 0) -> dict:
    """C010 as a CLEARLY LABELLED computational analogue (T02 rule).

    Continuous ring attractor with local excitation, global inhibition,
    and a SATURATING transfer function:

        dr_i/dt = -r_i + f( sum_j W_ij r_j / N + I_i )
        W_ij    = k_exc cos(theta_i - theta_j) - k_inh
        f(x)    = r_max * tanh( max(x, 0) / r_max )

    The input is applied for the first quarter of the run and then
    removed; a localized bump forms and PERSISTS without input, which
    is the property the source deck calls 'holographic memory'.

    The saturation is load-bearing, not cosmetic: with a bare ReLU the
    network only either decays to zero or diverges (rates ~1e7 by
    k_exc=8), so a 'persistent bump' would be a knife-edge artifact of
    the gain rather than an attractor. f() bounds the rates and makes
    the bump a genuine stable state across k_exc >= 8.

    This is a ring attractor from computational neuroscience. It is NOT
    evidence for the source's holographic claims, and naming it after
    the deck does not make the deck correct."""
    rng = np.random.default_rng(seed)
    th = np.linspace(0, 2 * math.pi, n, endpoint=False)
    W = k_exc * np.cos(th[:, None] - th[None, :]) - k_inh
    r = rng.uniform(0, 0.1, n)
    inp = np.zeros(n)
    if input_dir is not None:
        inp = np.exp(np.cos(th - input_dir) - 1.0)
    drive_steps = steps // 4
    for s in range(steps):
        i_t = inp if s < drive_steps else np.zeros(n)
        drive = W @ r / n + i_t
        act = r_max * np.tanh(np.maximum(drive, 0.0) / r_max)
        r = r + dt * (-r + act)
        if noise:
            r = np.maximum(r + noise * math.sqrt(dt)
                           * rng.standard_normal(n), 0.0)
    z = np.sum(r * np.exp(1j * th)) / max(r.sum(), 1e-12)
    # r.max() is the load-bearing test: the normalized vector length
    # stays high even for a decayed ring (it normalizes away amplitude)
    formed = bool(r.max() > 0.1 and abs(z) > 0.3)
    return {"rates": r, "bump_direction_rad": float(np.angle(z)),
            "bump_amplitude": float(np.abs(z)),
            "peak_rate": float(r.max()),
            "bump_formed": formed,
            "persisted_without_input": bool(formed
                                            and input_dir is not None),
            "status": STATUS,
            "note": "ring attractor analogue (established comp-neuro "
                    "model); NOT evidence for source holographic "
                    "claims"}


# --- C013/C023: cross-frequency coupling ------------------------------

def phase_amplitude_coupling(sig: np.ndarray, fs_hz: float,
                             phase_band: tuple, amp_band: tuple,
                             n_surrogate: int = 100,
                             seed: int = 2) -> dict:
    """C023: modulation index of phase-amplitude coupling with a
    surrogate null (Tort-style, simplified to a mean-vector length).

    Reported against phase-shuffled surrogates because PAC estimators
    return a nonzero value on pure noise; the raw number is not
    evidence (C013/C023 failure condition)."""
    rng = np.random.default_rng(seed)
    x = np.asarray(sig, float)
    ph = np.angle(_analytic(_bandpass(x, fs_hz, *phase_band)))
    am = np.abs(_analytic(_bandpass(x, fs_hz, *amp_band)))

    def _mi(p, a):
        return float(np.abs(np.mean(a * np.exp(1j * p))) /
                     max(np.mean(a), 1e-12))
    obs = _mi(ph, am)
    null = np.array([_mi(ph, rng.permutation(am))
                     for _ in range(n_surrogate)])
    p = float((np.sum(null >= obs) + 1) / (n_surrogate + 1))
    return {"modulation_index": obs, "p_surrogate": p,
            "exceeds_surrogates": bool(p < 0.05),
            "surrogate_mean": float(null.mean()),
            "status": STATUS,
            "note": "synthetic or supplied signals only; no measured "
                    "human data in this lane"}


def _bandpass(x: np.ndarray, fs: float, lo: float, hi: float
              ) -> np.ndarray:
    """Zero-phase brick-wall band-pass via FFT (adequate for the
    synthetic fixtures used here; declared, not a filter-design
    claim)."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1.0 / fs)
    X[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(X, n=len(x))


# --- C032: quantum cognition versus classical comparator --------------

def order_effect_model(p_a_first: float, p_b_first: float) -> dict:
    """C032/T07: question-order effects.

    A CLASSICAL joint-probability model requires P(A then B) = P(B then
    A) for the same conjunction. Measured order effects violate that.
    Quantum-probability (projection) models reproduce the asymmetry
    because projectors do not commute.

    BOUNDARY: this is quantum PROBABILITY applied to behaviour. It is
    NOT evidence of quantum processes in neurons. A non-commuting
    measurement model fitting survey data says something about the
    algebra of the questions, not the physics of the tissue."""
    asym = p_a_first - p_b_first
    classical_ok = abs(asym) < 1e-9
    return {"p_a_first": p_a_first, "p_b_first": p_b_first,
            "order_asymmetry": asym,
            "classical_joint_model_adequate": bool(classical_ok),
            "requires_noncommuting_model": bool(not classical_ok),
            "status": STATUS,
            "boundary": "quantum-probability models of decisions are "
                        "NOT evidence of a quantum brain (G37)"}


def qq_equality(p_ab: float, p_ba: float, p_a_not_b: float,
                p_not_a_b: float) -> dict:
    """The QQ equality: quantum question-order models predict
        (P(A then B) + P(notA then notB)) - (P(B then A) +
         P(notB then notA)) = 0
    a parameter-free prediction that classical models do not make. It
    is testable and can FAIL, which is what makes it a model rather
    than a metaphor."""
    q = (p_ab + p_a_not_b) - (p_ba + p_not_a_b)
    return {"qq_value": q, "satisfied": bool(abs(q) < 0.05),
            "status": STATUS,
            "note": "parameter-free; a violation falsifies the "
                    "quantum-order model for this dataset"}


def classical_comparator(p_a: float, p_b_given_a: float) -> dict:
    """The classical baseline any 'quantum-like' claim must beat: a
    plain conditional-probability chain."""
    return {"p_joint": p_a * p_b_given_a, "commutes": True,
            "status": STATUS,
            "note": "if this fits the data, no quantum-probability "
                    "model is warranted (parsimony control)"}


# --- C003: subjective time from update/novelty/arousal ----------------

def subjective_time(novelty: np.ndarray, arousal: np.ndarray,
                    dt_s: float = 1.0, w_novelty: float = 1.0,
                    w_arousal: float = 0.5) -> dict:
    """C003: perceived duration as accumulated salient change,
        D_hat = sum_t (w_n * novelty_t + w_a * arousal_t) * dt
    (a declared linear accumulator, the standard reduced form of
    change/attentional-gate models).

    Falsified if duration judgements are unaffected by novelty and
    arousal manipulations under preregistered analysis."""
    n = np.asarray(novelty, float)
    a = np.asarray(arousal, float)
    if n.shape != a.shape:
        raise ValueError("novelty and arousal must have equal length")
    rate = w_novelty * n + w_arousal * a
    d_hat = float(np.sum(rate) * dt_s)
    clock = len(n) * dt_s
    return {"perceived_duration_s": d_hat,
            "clock_duration_s": clock,
            "ratio": d_hat / max(clock, 1e-12),
            "dilated": bool(d_hat > clock),
            "status": STATUS,
            "note": "abstract accumulator; no human data in this lane"}
