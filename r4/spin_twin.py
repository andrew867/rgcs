"""A42-A47 — the four-level spin digital twin, write compiler, readout
engine, voxel crosstalk, and retention/endurance model.

A spin-3/2 system in an axial field has four levels m_s = -3/2, -1/2,
+1/2, +3/2 with zero-field splitting D and Zeeman term. The twin is
analytic (no fitted parameters) so its fixtures can be checked against
closed-form values.

Three honesty features:

- The **write compiler refuses unsupported transitions** (A39/R39):
  magnetic dipole transitions obey Delta m_s = +/-1, so a direct
  -3/2 -> +3/2 pulse does not exist and is compiled as a refusal or a
  multi-step path, never silently.
- The **readout engine reports pair degeneracy** (A40/R40): the common
  optical readout of a spin-3/2 defect distinguishes |m_s| pairs, so
  sign information is ERASED unless an extra operation resolves it.
  The engine returns an explicit erasure rather than a guess.
- **Retention is finite** (R42): T1 relaxation toward thermal
  equilibrium is modelled, so no state is stored forever.

SYNTHETIC throughout. No spin has been prepared or measured.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from . import ClaimBoundaryError

MU_B = 9.274_010_0783e-24        # J/T
H_PLANCK = 6.626_070_15e-34      # J s
K_B = 1.380_649e-23              # J/K

M_S_LEVELS = (-1.5, -0.5, 0.5, 1.5)


@dataclass(frozen=True)
class SpinThreeHalves:
    """Axial spin-3/2: H = D[S_z^2 - S(S+1)/3] + g mu_B B S_z."""
    d_zfs_hz: float = 35.0e6          # ~35 MHz, SiC V_Si scale
    g_factor: float = 2.0
    b_field_T: float = 0.01

    def level_energies_hz(self) -> dict:
        """Energy of each m_s level in Hz."""
        s = 1.5
        out = {}
        for m in M_S_LEVELS:
            zfs = self.d_zfs_hz * (m ** 2 - s * (s + 1) / 3.0)
            zee = (self.g_factor * MU_B * self.b_field_T / H_PLANCK) * m
            out[m] = zfs + zee
        return out

    def transition_frequencies_hz(self) -> dict:
        """Allowed magnetic-dipole transitions (Delta m_s = +/-1)."""
        e = self.level_energies_hz()
        out = {}
        for a, b in ((-1.5, -0.5), (-0.5, 0.5), (0.5, 1.5)):
            out[(a, b)] = abs(e[b] - e[a])
        return out

    def thermal_populations(self, temperature_K: float) -> dict:
        if temperature_K <= 0:
            raise ClaimBoundaryError("temperature must be positive")
        e = self.level_energies_hz()
        w = {m: math.exp(-H_PLANCK * v / (K_B * temperature_K))
             for m, v in e.items()}
        z = sum(w.values())
        return {m: v / z for m, v in w.items()}


# --- write compiler (A43) ------------------------------------------------------

def compile_write(initial_ms: float, target_ms: float,
                  twin: SpinThreeHalves) -> dict:
    """Compile a state preparation. Delta m_s = +/-1 only."""
    if initial_ms not in M_S_LEVELS or target_ms not in M_S_LEVELS:
        raise ClaimBoundaryError(
            f"levels must be in {M_S_LEVELS}")
    if initial_ms == target_ms:
        return {"path": [], "n_pulses": 0, "supported": True,
                "note": "already in the target state"}
    step = 1.0 if target_ms > initial_ms else -1.0
    path, freqs = [], []
    m = initial_ms
    tf = twin.transition_frequencies_hz()
    while m != target_ms:
        nxt = m + step
        key = (min(m, nxt), max(m, nxt))
        path.append((m, nxt))
        freqs.append(tf[key])
        m = nxt
    direct = abs(target_ms - initial_ms) == 1.0
    return {
        "path": path, "n_pulses": len(path),
        "pulse_frequencies_hz": freqs,
        "supported": True,
        "direct_transition_exists": direct,
        "note": ("single allowed magnetic-dipole transition"
                 if direct else
                 f"NO direct {initial_ms} -> {target_ms} magnetic "
                 f"dipole transition exists (Delta m_s = "
                 f"{target_ms - initial_ms:+.0f}); compiled as "
                 f"{len(path)} sequential allowed pulses"),
        "evidence_class": "ANALYTIC_MODEL",
    }


def refuse_forbidden_transition(initial_ms: float,
                                target_ms: float) -> None:
    """Explicit refusal for a single-pulse forbidden transition."""
    if abs(target_ms - initial_ms) > 1.0:
        raise ClaimBoundaryError(
            f"single-pulse {initial_ms} -> {target_ms} is a "
            f"Delta m_s = {target_ms - initial_ms:+.0f} transition and "
            "is magnetic-dipole forbidden; use compile_write for a "
            "multi-step path")


# --- readout with pair degeneracy (A44) -----------------------------------------

def optical_readout(true_ms: float, resolve_sign: bool = False,
                    snr: float = 10.0, seed: int = 20260718) -> dict:
    """Common spin-3/2 optical readout distinguishes |m_s| PAIRS.

    Without an extra sign-resolving operation the sign is ERASED — the
    engine reports an erasure, never a coin-flip dressed as a result.
    """
    if true_ms not in M_S_LEVELS:
        raise ClaimBoundaryError(f"levels must be in {M_S_LEVELS}")
    magnitude = abs(true_ms)
    rng = np.random.default_rng(seed)
    noisy = magnitude + rng.normal(0, 1.0 / max(snr, 1e-9))
    est_mag = 1.5 if noisy > 1.0 else 0.5
    if not resolve_sign:
        return {"measured_magnitude": est_mag,
                "sign": None,
                "outcome": "ERASURE",
                "candidates": [-est_mag, est_mag],
                "bits_recovered": 1.0,
                "note": "|m_s| pair resolved; SIGN ERASED without an "
                        "additional sign-resolving operation "
                        "(R40 pair degeneracy)"}
    return {"measured_magnitude": est_mag,
            "sign": math.copysign(1.0, true_ms),
            "outcome": "RESOLVED",
            "estimated_ms": math.copysign(est_mag, true_ms),
            "bits_recovered": 2.0,
            "note": "sign resolved by an extra operation; cost must be "
                    "carried in the rate budget"}


def confusion_matrix(snr: float = 10.0, trials: int = 400,
                     resolve_sign: bool = True,
                     seed: int = 20260718) -> dict:
    """The 4x4 physical confusion matrix the ECC design needs
    (core/06). SYNTHETIC — from the twin, not an instrument."""
    rng = np.random.default_rng(seed)
    idx = {m: i for i, m in enumerate(M_S_LEVELS)}
    M = np.zeros((4, 4))
    for m in M_S_LEVELS:
        for t in range(trials):
            noisy_mag = abs(m) + rng.normal(0, 1.0 / max(snr, 1e-9))
            est_mag = 1.5 if noisy_mag > 1.0 else 0.5
            if resolve_sign:
                sign = math.copysign(
                    1.0, m + rng.normal(0, 1.0 / max(snr, 1e-9)))
            else:
                sign = math.copysign(1.0, m)   # ideal-sign upper bound
            est = math.copysign(est_mag, sign)
            M[idx[m], idx[est]] += 1
    M = M / trials
    return {"matrix": M.tolist(), "levels": list(M_S_LEVELS),
            "mean_fidelity": float(np.mean(np.diag(M))),
            "snr": snr, "trials": trials,
            "status": "SYNTHETIC — from the digital twin; a real "
                      "confusion matrix requires a calibrated "
                      "instrument",
            "evidence_class": "NUMERICAL_SIMULATION"}


# --- voxel crosstalk (A45) --------------------------------------------------------

def voxel_crosstalk(spacing_nm: float, spot_fwhm_nm: float) -> dict:
    """Neighbour excitation from an overlapping optical spot: Gaussian
    profile at the neighbour's distance."""
    if spacing_nm <= 0 or spot_fwhm_nm <= 0:
        raise ClaimBoundaryError("spacing and spot size must be positive")
    sigma = spot_fwhm_nm / (2 * math.sqrt(2 * math.log(2)))
    frac = math.exp(-(spacing_nm ** 2) / (2 * sigma ** 2))
    return {"spacing_nm": spacing_nm, "spot_fwhm_nm": spot_fwhm_nm,
            "neighbour_excitation_fraction": frac,
            "isolated_at_1e-3": frac < 1e-3,
            "note": "addressing density is bounded by the optical "
                    "spot, not by the address space; 4096 addresses "
                    "do not imply 4096 resolvable voxels",
            "evidence_class": "ANALYTIC_MODEL"}


# --- retention and endurance (A46) -------------------------------------------------

def retention(t1_s: float, hold_s: float, temperature_K: float,
              twin: SpinThreeHalves) -> dict:
    """T1 relaxation toward thermal equilibrium. Nothing is stored
    forever."""
    if t1_s <= 0:
        raise ClaimBoundaryError(
            "T1 must be positive and finite — an infinite T1 is the "
            "perfect-memory claim this project keeps refusing")
    survive = math.exp(-hold_s / t1_s)
    eq = twin.thermal_populations(temperature_K)
    return {"t1_s": t1_s, "hold_s": hold_s,
            "state_survival_probability": survive,
            "thermal_equilibrium_populations":
                {str(k): v for k, v in eq.items()},
            "retention_status": "FINITE",
            "evidence_class": "ANALYTIC_MODEL"}


def endurance(cycles: int, error_per_cycle: float) -> dict:
    """Cumulative write/erase degradation."""
    if not (0.0 <= error_per_cycle < 1.0):
        raise ClaimBoundaryError("error_per_cycle must lie in [0, 1)")
    return {"cycles": cycles, "error_per_cycle": error_per_cycle,
            "survival": (1.0 - error_per_cycle) ** cycles,
            "note": "scrubbing/refresh must be budgeted; see "
                    "physical channel coding"}


def scrub_interval(t1_s: float, max_error: float = 1e-3) -> dict:
    """A47: how often must a physical channel be refreshed?"""
    if not (0 < max_error < 1):
        raise ClaimBoundaryError("max_error must lie in (0, 1)")
    interval = -t1_s * math.log(1 - max_error)
    return {"t1_s": t1_s, "max_error": max_error,
            "scrub_interval_s": interval,
            "note": "physical ECC here is CLASSICAL error correction "
                    "over measured symbols; it is not quantum error "
                    "correction and does not protect coherence",
            "evidence_class": "ANALYTIC_MODEL"}
