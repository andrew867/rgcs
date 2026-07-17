"""Butterworth-Van Dyke equivalent-circuit model + extraction
(Agent C06; coverage A14-A15; gate G13).

Z(w) = Zc0 || (R1 + jwL1 + 1/(jwC1)), fs = 1/(2pi sqrt(L1 C1)),
fp = fs sqrt(1 + C1/C0), Q = 2pi fs L1/R1,
k_eff^2 = (fp^2 - fs^2)/fp^2 (IEEE-176 form, matching the frozen v4
piezo convention). Extraction reports identifiability honestly."""

from __future__ import annotations

import math

import numpy as np


def bvd_impedance(f_hz, c0_f: float, r1_ohm: float, l1_h: float,
                  c1_f: float) -> np.ndarray:
    w = 2 * np.pi * np.asarray(f_hz, float)
    zm = r1_ohm + 1j * w * l1_h + 1.0 / (1j * w * c1_f)
    zc0 = 1.0 / (1j * w * c0_f)
    return zm * zc0 / (zm + zc0)


def derived_parameters(c0_f, r1_ohm, l1_h, c1_f) -> dict:
    fs = 1.0 / (2 * math.pi * math.sqrt(l1_h * c1_f))
    fp = fs * math.sqrt(1.0 + c1_f / c0_f)
    q = 2 * math.pi * fs * l1_h / r1_ohm
    keff2 = (fp ** 2 - fs ** 2) / fp ** 2
    return {"fs_hz": fs, "fp_hz": fp, "q": q, "k_eff2": keff2}


def extract_bvd(f_hz: np.ndarray, z_abs_ohm: np.ndarray) -> dict:
    """Extract C0, R1, L1, C1, fs, fp, Q, k_eff^2 from an |Z(f)|
    sweep. Spurious modes = additional local minima. Identifiability:
    both resonances must be resolved inside the band, else the record
    says INSUFFICIENT_RESOLUTION instead of guessing."""
    f = np.asarray(f_hz, float)
    z = np.asarray(z_abs_ohm, float)
    i_s = int(np.argmin(z))
    i_p = int(np.argmax(z))
    interior = 0 < i_s < len(f) - 1 and 0 < i_p < len(f) - 1
    if not interior or f[i_p] <= f[i_s]:
        return {"identifiable": False,
                "status": "INSUFFICIENT_RESOLUTION",
                "reason": "series and/or parallel resonance not "
                          "resolved inside the sweep band; no "
                          "parameters are guessed"}
    fs, fp = f[i_s], f[i_p]
    r1 = float(z[i_s])                       # |Z| at series resonance
    # C0 from the high-frequency capacitive asymptote |Z| ~ 1/(w C0)
    tail = slice(int(0.9 * len(f)), len(f))
    c0 = float(np.mean(1.0 / (2 * np.pi * f[tail] * z[tail])))
    c1 = c0 * ((fp / fs) ** 2 - 1.0)
    l1 = 1.0 / ((2 * np.pi * fs) ** 2 * c1)
    q = 2 * math.pi * fs * l1 / r1
    keff2 = (fp ** 2 - fs ** 2) / fp ** 2
    # spurious modes: local minima other than the main series dip
    lm = np.nonzero((z[1:-1] < z[:-2]) & (z[1:-1] < z[2:]))[0] + 1
    spurious = [float(f[i]) for i in lm if abs(int(i) - i_s) > 2]
    return {"identifiable": True, "status": "REDUCED_ORDER_VALIDATED",
            "c0_f": c0, "r1_ohm": r1, "l1_h": l1, "c1_f": c1,
            "fs_hz": float(fs), "fp_hz": float(fp), "q": float(q),
            "k_eff2": float(keff2),
            "spurious_modes_hz": spurious,
            "note": "resolution-limited estimates; fs/fp quantized "
                    "to the sweep grid"}


# --- open/short/load calibration (C06) ---------------------------------------

def osl_correct(z_meas: np.ndarray, z_open: np.ndarray,
                z_short: np.ndarray, z_load: np.ndarray,
                z_load_ref_ohm: float = 50.0) -> np.ndarray:
    """One-port open-short-load correction. The measured reflection is
    de-embedded through the standard 3-term error model:

        Z_dut = Z_load_ref * (Z_m - Z_s) * (Z_o - Z_l)
                            / ((Z_o - Z_m) * (Z_l - Z_s))

    Uncalibrated fixture impedance is one of the ordinary channels that
    must be bounded before any residual is interesting (C07/G14)."""
    zm = np.asarray(z_meas, complex)
    zo = np.asarray(z_open, complex)
    zs = np.asarray(z_short, complex)
    zl = np.asarray(z_load, complex)
    num = (zm - zs) * (zo - zl)
    den = (zo - zm) * (zl - zs)
    bad = np.abs(den) < 1e-30
    if np.any(bad):
        raise ValueError("OSL standards are degenerate at some "
                         "frequencies (open==measured or load==short)")
    return z_load_ref_ohm * num / den


def electrode_loading(c0_f: float, coverage_fraction: float,
                      electrode_mass_kg: float = 0.0,
                      modal_mass_kg: float = 1.0) -> dict:
    """Electrode coverage scales the static capacitance and adds mass
    loading. Frequency pulls down as sqrt(m/(m+dm)) for a lumped modal
    mass (first-order Rayleigh estimate, declared)."""
    if not 0 < coverage_fraction <= 1:
        raise ValueError("coverage_fraction in (0, 1]")
    c0_eff = c0_f * coverage_fraction
    pull = math.sqrt(modal_mass_kg
                     / (modal_mass_kg + electrode_mass_kg))
    return {"c0_effective_f": c0_eff,
            "coverage_fraction": coverage_fraction,
            "frequency_pull_factor": pull,
            "delta_f_relative": pull - 1.0,
            "note": "first-order Rayleigh mass-loading estimate; not "
                    "a measured electrode calibration"}


def fit_uncertainty(f_hz: np.ndarray, z_abs_ohm: np.ndarray,
                    params: dict, noise_floor_ohm: float) -> dict:
    """Report parameter identifiability rather than a false precision.

    A BVD fit is non-identifiable when the resonance is not sampled
    finely enough to constrain L1/C1 independently: the frequency grid
    quantizes fs and fp, and the induced relative uncertainty in the
    derived parameters follows directly. When the |Z| contrast at
    resonance is below the noise floor, R1 is unconstrained."""
    f = np.asarray(f_hz, float)
    z = np.asarray(z_abs_ohm, float)
    df = float(np.median(np.diff(f)))
    fs = params["fs_hz"]
    fp = params["fp_hz"]
    u_fs = df / 2.0
    u_fp = df / 2.0
    # k_eff^2 = (fp^2-fs^2)/fp^2 -> propagate the grid uncertainty
    dk_dfs = -2 * fs / fp ** 2
    dk_dfp = 2 * fs ** 2 / fp ** 3
    u_k2 = math.hypot(dk_dfs * u_fs, dk_dfp * u_fp)
    contrast = float(z.max() / max(z.min(), 1e-30))
    r1_constrained = z.min() > noise_floor_ohm
    identifiable = (fp - fs) > 4 * df and r1_constrained
    return {"u_fs_hz": u_fs, "u_fp_hz": u_fp,
            "u_k_eff2": u_k2,
            "relative_u_k_eff2": u_k2 / max(params["k_eff2"], 1e-30),
            "impedance_contrast": contrast,
            "r1_constrained_by_noise_floor": bool(r1_constrained),
            "identifiable": bool(identifiable),
            "status": "REDUCED_ORDER_VALIDATED" if identifiable
            else "INSUFFICIENT_RESOLUTION",
            "reason": "" if identifiable else
            f"fp-fs = {fp - fs:.3f} Hz spans fewer than 4 grid steps "
            f"({df:.3f} Hz) or |Z|min is at/below the noise floor; "
            "the fit is non-identifiable and exact parameters must "
            "not be reported"}


def fit_multibranch(f_hz: np.ndarray, z_abs_ohm: np.ndarray,
                    max_branches: int = 3) -> dict:
    """Detect multiple motional branches. C06 boundary: do NOT fit a
    single branch to a multimode spectrum and call the residual
    structure noise. Each detected dip is reported as its own branch
    with its own fs; unmodelled dips are named, not absorbed."""
    f = np.asarray(f_hz, float)
    z = np.asarray(z_abs_ohm, float)
    lm = np.nonzero((z[1:-1] < z[:-2]) & (z[1:-1] < z[2:]))[0] + 1
    if len(lm) == 0:
        return {"n_branches": 0, "status": "INSUFFICIENT_RESOLUTION",
                "reason": "no resonance dip found in the band"}
    depth = z.max() - z[lm]
    order = np.argsort(depth)[::-1]
    keep = [int(lm[i]) for i in order[:max_branches]]
    branches = [{"fs_hz": float(f[i]), "r_min_ohm": float(z[i]),
                 "depth_ohm": float(z.max() - z[i])} for i in keep]
    extra = [float(f[int(lm[i])]) for i in order[max_branches:]]
    return {"n_branches": len(branches), "branches": branches,
            "unmodelled_dips_hz": extra,
            "status": "REDUCED_ORDER_VALIDATED",
            "single_branch_adequate": len(lm) == 1,
            "note": "unmodelled dips are reported explicitly; residual "
                    "structure is never relabelled noise (C06)"}


def to_spice(c0_f: float, r1_ohm: float, l1_h: float, c1_f: float,
             name: str = "XTAL") -> str:
    """Export the fitted BVD as a SPICE subcircuit for the apparatus
    simulation (C06 -> C07 handoff)."""
    return (f"* RGCS BVD equivalent circuit: {name}\n"
            f"* generated by rscs2_core.bvd.to_spice — fitted "
            f"reduced-order model, NOT a measured device\n"
            f".SUBCKT {name} 1 2\n"
            f"C0 1 2 {c0_f:.6e}\n"
            f"R1 1 3 {r1_ohm:.6e}\n"
            f"L1 3 4 {l1_h:.6e}\n"
            f"C1 4 2 {c1_f:.6e}\n"
            f".ENDS {name}\n")
