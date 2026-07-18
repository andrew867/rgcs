"""A19-A23, A27, A33-A42 — closure/delay ambiguity, probe design,
multipath simulation, estimation, the identifiability gate, and the
reconstruction verdict.

Two facts organise this module:

1. **Exact closure is a delay alias.** If every tone in a recipe
   closes an integer cycle count in window W, then the observed phases
   are IDENTICAL for path delays τ and τ + kW. Perfect closure is
   simultaneously the synchronization feature (v4.6) and the ambiguity
   (v4.7). ``closure_delay_ambiguity`` computes the alias grid;
   ``dual_lattice_probe`` breaks it with a second, coprime window so
   the combined unambiguous range is the LCM (CRT argument).

2. **Recovery must be allowed to refuse.** ``reconstruct`` solves the
   linear phase model only after the identifiability gate reports
   rank, conditioning, and posterior width; a non-identifiable system
   returns a REFUSED verdict listing the aliases, never a best guess
   dressed as an answer.

Everything is deterministic given seeds. Nothing here is a
measurement.
"""

from __future__ import annotations

import cmath
import math
import random
from dataclasses import dataclass
from fractions import Fraction

import numpy as np

from . import ClaimBoundaryError, IdentifiabilityError
from .worldline import PathState
from fkey_instrument.phase_closure import common_closure_window

TWO_PI = 2.0 * math.pi


# --- closure as alias (A21) ----------------------------------------------

def closure_delay_ambiguity(freqs_hz: list, max_delay_s: float) -> dict:
    """The alias grid implied by a recipe's exact closure window.

    Any delay τ and τ + k·W produce identical wrapped phases for every
    tone in the family (W = common closure window). The 'exact
    closure removes ambiguity' claim is refused arithmetically.
    """
    fr = [Fraction(str(f)) if not isinstance(f, Fraction) else f
          for f in freqs_hz]
    win = common_closure_window(fr)
    w = float(win["window_s"])
    n_alias = int(max_delay_s / w)
    return {
        "closure_window_s": w,
        "alias_spacing_s": w,
        "aliases_within_max_delay": n_alias + 1,
        "unambiguous_range_s": w,
        "statement": "delays tau and tau + k*W are indistinguishable "
                     "for every tone in this family; exact closure IS "
                     "the alias (firewall CLOSURE_REMOVES_AMBIGUITY)",
        "evidence_class": "DERIVED_ARITHMETIC",
    }


def dual_lattice_probe(family_a: list, family_b: list) -> dict:
    """A22: break the alias with a second tone family whose closure
    window is coprime (in the rational sense) with the first. The
    combined unambiguous delay range is the LCM of the windows."""
    wa = common_closure_window([Fraction(str(f)) for f in family_a])
    wb = common_closure_window([Fraction(str(f)) for f in family_b])
    a, b = Fraction(wa["window_s"]), Fraction(wb["window_s"])
    lcm = _lcm_fractions(a, b)
    return {
        "window_a_s": float(a), "window_b_s": float(b),
        "combined_unambiguous_range_s": float(lcm),
        "combined_unambiguous_range_exact": str(lcm),
        "improvement_over_a": float(lcm / a),
        "statement": "two coprime closure lattices extend the "
                     "unambiguous range to their LCM; one lattice "
                     "alone cannot",
        "evidence_class": "DERIVED_ARITHMETIC",
    }


def _lcm_fractions(a: Fraction, b: Fraction) -> Fraction:
    num = abs(a.numerator * b.numerator) // math.gcd(a.numerator,
                                                     b.numerator)
    den = math.gcd(a.denominator, b.denominator)
    return Fraction(num, den)


# --- multipath simulator (A27) --------------------------------------------

@dataclass(frozen=True)
class Observation:
    """Complex baseband observation of one tone: sum over paths."""
    frequency_hz: float
    value: complex
    noise_sigma: float


def simulate_observations(freqs_hz: list, paths: list,
                          noise_sigma: float = 0.0,
                          seed: int = 20260718) -> list:
    """Deterministic forward model: y(f) = Σ_p g_p · exp(-i·2π·f·τ_p)
    (+ complex Gaussian noise). SYNTHETIC by construction."""
    rng = random.Random(seed)
    out = []
    for f in freqs_hz:
        v = sum(p.complex_gain *
                cmath.exp(-1j * TWO_PI * f * p.delay_s * p.doppler_scale)
                for p in paths)
        if noise_sigma > 0:
            v += complex(rng.gauss(0, noise_sigma),
                         rng.gauss(0, noise_sigma))
        out.append(Observation(float(f), v, noise_sigma))
    return out


# --- identifiability gate (A33) --------------------------------------------

def identifiability_gate(freqs_hz: list, candidate_delays_s: list,
                         noise_sigma: float,
                         cond_limit: float = 1e8) -> dict:
    """Is the linear system y = A·g identifiable for these candidate
    delays? Reports rank, conditioning and a posterior width proxy;
    the verdict is REFUSED when the answer is no.

    A is the steering matrix A[k, j] = exp(-i 2π f_k τ_j).
    """
    A = np.array([[cmath.exp(-1j * TWO_PI * f * t)
                   for t in candidate_delays_s] for f in freqs_hz])
    rank = int(np.linalg.matrix_rank(A, tol=1e-10))
    n_param = len(candidate_delays_s)
    sv = np.linalg.svd(A, compute_uv=False)
    cond = float(sv[0] / sv[-1]) if sv[-1] > 0 else math.inf
    # posterior width proxy: noise amplified through the pseudo-inverse
    width = float(noise_sigma * (1.0 / sv[-1])) if sv[-1] > 0 else \
        math.inf
    identifiable = rank >= n_param and cond < cond_limit
    reasons = []
    if rank < n_param:
        reasons.append(f"rank {rank} < parameters {n_param}: multiple "
                       "path histories explain the observation "
                       "exactly (firewall ONE_RESIDUAL_ONE_PATH)")
    if cond >= cond_limit:
        reasons.append(f"condition number {cond:.3g} exceeds "
                       f"{cond_limit:.0e}: estimates would be noise "
                       "amplified beyond meaning")
    return {
        "n_observations": len(freqs_hz), "n_parameters": n_param,
        "rank": rank, "condition_number": cond,
        "posterior_width_proxy": width,
        "identifiable": identifiable,
        "refusal_reasons": reasons,
        "evidence_class": "NUMERICAL_SIMULATION",
    }


# --- unwrapping / cycle solver (A36) ---------------------------------------

def integer_cycle_candidates(measured_phase_rad: float,
                             frequency_hz: float,
                             delay_window_s: tuple) -> list:
    """All delays in a window consistent with one wrapped phase — the
    honest output of unwrapping: a LIST, not a value."""
    lo, hi = delay_window_s
    out = []
    k_lo = math.ceil((lo * frequency_hz) - measured_phase_rad / TWO_PI)
    k = k_lo
    while True:
        tau = (measured_phase_rad / TWO_PI + k) / frequency_hz
        if tau > hi:
            break
        if tau >= lo:
            out.append(tau)
        k += 1
    return out


def synthetic_wavelength(f1_hz: float, f2_hz: float) -> dict:
    """A41: two carriers give a beat whose effective wavelength sets
    the coarse unambiguous range; the fine carrier then refines within
    it. Standard multi-wavelength interferometry, no magic."""
    if f1_hz == f2_hz:
        raise ClaimBoundaryError("identical carriers give no beat")
    df = abs(f1_hz - f2_hz)
    return {"beat_hz": df,
            "coarse_unambiguous_delay_s": 1.0 / df,
            "fine_cycle_s": 1.0 / max(f1_hz, f2_hz),
            "leverage": max(f1_hz, f2_hz) / df,
            "evidence_class": "DERIVED_ARITHMETIC"}


# --- reconstruction verdict (A37/A39/A42) -----------------------------------

def reconstruct(freqs_hz: list, observations: list,
                candidate_delays_s: list, noise_sigma: float,
                cond_limit: float = 1e8) -> dict:
    """Least-squares path-gain recovery behind the identifiability
    gate.

    Returns a verdict dict:
    - REFUSED with reasons and the alias structure when the gate
      fails;
    - RECOVERED with estimates, posterior width, residual, and the
      alias caveat when it passes.

    Never returns a bare point estimate.
    """
    gate = identifiability_gate(freqs_hz, candidate_delays_s,
                                noise_sigma, cond_limit)
    if not gate["identifiable"]:
        return {
            "verdict": "REFUSED",
            "gate": gate,
            "refusal_reasons": gate["refusal_reasons"],
            "alternatives_note":
                "the candidate set is not identifiable from these "
                "observations; collecting more diverse frequencies or "
                "a second closure lattice may make it so",
            "evidence_class": "NUMERICAL_SIMULATION",
        }
    A = np.array([[cmath.exp(-1j * TWO_PI * f * t)
                   for t in candidate_delays_s] for f in freqs_hz])
    y = np.array([o.value for o in observations])
    g, res, _, _ = np.linalg.lstsq(A, y, rcond=None)
    resid = float(np.linalg.norm(y - A @ g))
    return {
        "verdict": "RECOVERED",
        "gate": gate,
        "path_gains": [complex(x) for x in g],
        "residual_norm": resid,
        "posterior_width_proxy": gate["posterior_width_proxy"],
        "alias_caveat":
            "delays are recovered modulo the recipe's closure window; "
            "see closure_delay_ambiguity",
        "claim_boundary":
            "recovery of SYNTHETIC observations under a declared "
            "model. Not a measurement; not evidence any physical "
            "channel behaves this way.",
        "evidence_class": "NUMERICAL_SIMULATION",
    }


def spoof_check(observations_a: list, observations_b: list,
                tolerance: float = 1e-9) -> dict:
    """A40: two DIFFERENT path sets producing indistinguishable
    observations is the spoofing/ambiguity condition. Detecting it is
    a feature, not an error."""
    if len(observations_a) != len(observations_b):
        raise ValueError("observation sets must align")
    dmax = max(abs(a.value - b.value)
               for a, b in zip(observations_a, observations_b))
    return {"max_difference": dmax,
            "indistinguishable": dmax < tolerance,
            "meaning": "if indistinguishable, no receiver can tell "
                       "these path histories apart — a spoofing "
                       "surface AND a reconstruction ambiguity",
            "evidence_class": "NUMERICAL_SIMULATION"}
