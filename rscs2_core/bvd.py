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
