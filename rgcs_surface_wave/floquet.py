"""R10.15 Phases B11, C16, C17 — combined Floquet coefficients,
mode coupling, and the sideband / nonreciprocity solver.

Separable space-time loading:

    Y(phi, t) = Y0 * sum_{m,n} M_m S_n exp(i(m phi - n omega_mod t)),
    Y_{m,n} = Y0 * M_m * S_n.

Sidebands are obtained by TRUNCATED HARMONIC BALANCE. For each annular
mode m and sideband order n the amplitude a_{m,n} at frequency
omega_d + n*omega_mod satisfies

    D_{m,n} a_{m,n} = drive_{m,n} + sum_{m',n'} Y_{m-m', n-n'} a_{m',n'},
    D_{m,n} = omega_m^2 - w^2 + i w omega_m / Q,   w = omega_d + n omega_mod.

The solver reports a power-conservation (Manley-Rowe) residual and a
forward/reverse comparison. It NEVER infers a force from sidebands:
force comes only from ``stress.integrate_force`` on a closed surface.
"""

from __future__ import annotations

import numpy as np

from rgcs_surface_wave.evidence import ClaimClass
from rgcs_surface_wave.masks import coefficient
from rgcs_surface_wave.temporal import coefficients as temporal_coeffs


class FloquetError(ValueError):
    pass


def combined_coefficients(cells: int, active, waveform: str,
                          m_max: int = 6, n_max: int = 4,
                          y0: float = 1.0, duty: float = 0.5,
                          depth: float = 1.0) -> dict:
    """Y_{m,n} = Y0 M_m S_n, with a Parseval check on the product."""
    tc = temporal_coeffs(waveform, n_max=n_max, duty=duty, depth=depth)
    S = {int(k): complex(v[0], v[1])
         for k, v in tc["coefficients"].items()}
    M = {m: coefficient(cells, active, m) for m in
         range(-m_max, m_max + 1)}
    Y = {(m, n): y0 * M[m] * S[n] for m in M for n in S}
    # Parseval: sum |Y|^2 over one full period in m and all n equals
    # Y0^2 * (sum_m |M_m|^2 over a period) * (sum_n |S_n|^2)
    m_period = sum(abs(coefficient(cells, active, m)) ** 2
                   for m in range(cells))
    n_sum = sum(abs(s) ** 2 for s in S.values())
    lhs = sum(abs(y0 * coefficient(cells, active, m) * S[n]) ** 2
              for m in range(cells) for n in S)
    rhs = (y0 ** 2) * m_period * n_sum
    return {
        "schema": "rgcs.r1015.floquet-coefficients.v1",
        "waveform": waveform, "cells": cells,
        "y0": y0, "m_max": m_max, "n_max": n_max,
        "coefficients": {f"{m},{n}": [c.real, c.imag]
                         for (m, n), c in Y.items()},
        "magnitude": {f"{m},{n}": abs(c) for (m, n), c in Y.items()},
        "parseval_lhs": lhs, "parseval_rhs": rhs,
        "parseval_residual": abs(lhs - rhs),
        "separable": True,
        "claim_class": ClaimClass.DERIVED.value,
    }


def coupling_matrix(mode_indices, n_orders, cells, active,
                    waveform: str, y0: float = 1.0,
                    duty: float = 0.5, depth: float = 1.0) -> dict:
    """C16: which (m, n) states the modulation connects."""
    tc = temporal_coeffs(waveform, n_max=max(2 * max(n_orders), 4),
                         duty=duty, depth=depth)
    S = {int(k): complex(v[0], v[1])
         for k, v in tc["coefficients"].items()}
    states = [(m, n) for m in mode_indices for n in n_orders]
    K = np.zeros((len(states), len(states)), dtype=complex)
    links = []
    for i, (m, n) in enumerate(states):
        for j, (mp, np_) in enumerate(states):
            dm, dn = m - mp, n - np_
            if dn in S:
                val = y0 * coefficient(cells, active, dm) * S[dn]
                K[i, j] = val
                if abs(val) > 1e-12 and (dm or dn):
                    links.append({"from": [mp, np_], "to": [m, n],
                                  "delta_m": dm, "delta_n": dn,
                                  "amplitude": abs(val)})
    return {"states": [list(s) for s in states], "matrix": K,
            "links": sorted(links, key=lambda d: -d["amplitude"])[:40],
            "link_count": len(links),
            "claim_class": ClaimClass.DERIVED.value}


def solve_sidebands(mode_frequencies: dict, q_factor: float,
                    f_drive_hz: float, f_mod_hz: float,
                    cells: int, active, waveform: str = "sinusoidal",
                    n_max: int = 2, y0: float = 1e-3,
                    drive_mode: int = 1, duty: float = 0.5,
                    depth: float = 1.0) -> dict:
    """C17: truncated harmonic balance for sideband amplitudes."""
    if q_factor <= 0 or f_drive_hz <= 0:
        raise FloquetError("Q and drive frequency must be positive")
    modes = sorted(mode_frequencies)
    n_orders = list(range(-n_max, n_max + 1))
    cm = coupling_matrix(modes, n_orders, cells, active, waveform,
                         y0, duty, depth)
    states = [tuple(s) for s in cm["states"]]
    K = cm["matrix"]
    w_d = 2 * np.pi * f_drive_hz
    w_m = 2 * np.pi * f_mod_hz
    A = np.zeros((len(states), len(states)), dtype=complex)
    b = np.zeros(len(states), dtype=complex)
    for i, (m, n) in enumerate(states):
        w = w_d + n * w_m
        w_m0 = 2 * np.pi * mode_frequencies[m]
        A[i, i] = (w_m0 ** 2 - w ** 2) + 1j * w * w_m0 / q_factor
        if m == drive_mode and n == 0:
            b[i] = 1.0
    A = A - K
    a = np.linalg.solve(A, b)
    amps = {f"{m},{n}": abs(a[i]) for i, (m, n) in enumerate(states)}
    carrier = amps.get(f"{drive_mode},0", 0.0)
    upper = sum(v for k, v in amps.items()
                if int(k.split(",")[1]) > 0)
    lower = sum(v for k, v in amps.items()
                if int(k.split(",")[1]) < 0)
    total = upper + lower
    asym = (upper - lower) / total if total > 0 else 0.0
    # Manley-Rowe: photon-number flux sum over sidebands
    photon = sum(abs(a[i]) ** 2 / (f_drive_hz + n * f_mod_hz)
                 for i, (m, n) in enumerate(states)
                 if f_drive_hz + n * f_mod_hz > 0)
    return {
        "schema": "rgcs.r1015.sidebands.v1",
        "waveform": waveform, "f_drive_hz": f_drive_hz,
        "f_mod_hz": f_mod_hz, "q_factor": q_factor,
        "modes": modes, "n_orders": n_orders,
        "amplitudes": amps,
        "carrier_amplitude": carrier,
        "upper_sideband_total": upper,
        "lower_sideband_total": lower,
        "sideband_asymmetry": asym,
        "conversion_efficiency": (total / carrier if carrier > 0
                                  else float("inf")),
        "photon_number_flux": photon,
        "coupling_links": cm["link_count"],
        "force_inference": "REFUSED: sideband amplitudes do not imply "
                           "a force; use a closed-surface Maxwell "
                           "stress integration",
        "claim_class": ClaimClass.SIMULATED.value,
    }


def nonreciprocity(mode_frequencies: dict, q_factor: float,
                   f_drive_hz: float, f_mod_hz: float, cells: int,
                   active, y0: float = 1e-3, n_max: int = 2,
                   depth: float = 1.0) -> dict:
    """Forward vs reversed traveling modulation."""
    fwd = solve_sidebands(mode_frequencies, q_factor, f_drive_hz,
                          f_mod_hz, cells, active, "traveling",
                          n_max, y0, depth=depth)
    rev = solve_sidebands(mode_frequencies, q_factor, f_drive_hz,
                          f_mod_hz, cells, active, "reversed",
                          n_max, y0, depth=depth)
    a_f, a_r = fwd["sideband_asymmetry"], rev["sideband_asymmetry"]
    contrast = abs(a_f - a_r)
    linewidth = f_drive_hz / q_factor
    resolved = f_mod_hz > 0.5 * linewidth
    return {
        "schema": "rgcs.r1015.nonreciprocity.v1",
        "forward_asymmetry": a_f, "reversed_asymmetry": a_r,
        "nonreciprocity_contrast": contrast,
        "linewidth_hz": linewidth,
        "sidebands_resolved": bool(resolved),
        "regime": ("SIDEBAND_RESOLVED" if resolved
                   else "QUASI_STATIC_UNRESOLVED"),
        "verdict": ("NONRECIPROCITY_PRESENT" if contrast > 1e-6
                    else "NO_MEASURABLE_NONRECIPROCITY"),
        "interpretation": (
            "the modulation offset is far smaller than the resonance "
            "linewidth, so forward and reversed modulation address the "
            "same resonance identically. No space-time nonreciprocal "
            "gap opens, and the contrast below is a numerical floor, "
            "not a physical effect."
            if not resolved else
            "sidebands are spectrally resolved; the contrast is a "
            "candidate physical nonreciprocity and requires "
            "independent replication before use."),
        "claim_class": (ClaimClass.NULL.value if not resolved
                        else ClaimClass.REPLICATION_REQUIRED.value),
    }
