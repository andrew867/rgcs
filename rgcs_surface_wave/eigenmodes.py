"""R10.15 Phase C15 — annular eigenmodes as a declared eigenvalue
problem.

Model: a dielectric-loaded annular parallel-plate region, PEC walls at
r = Ri and r = Ro, no z variation (TM_{m,n,0}). The axial field is

    E_z(r, phi) = [A J_m(k r) + B Y_m(k r)] exp(i m phi),
    k = omega * sqrt(mu0 eps0 eps_eff).

The PEC conditions give a 2x2 homogeneous system whose determinant is
the EIGENVALUE CONDITION

    D_m(k) = J_m(k Ri) Y_m(k Ro) - J_m(k Ro) Y_m(k Ri) = 0.

Roots are found by bracketing and Brent's method. Loss enters
perturbatively: the unloaded Q combines dielectric, conductor, and (as
a declared placeholder) radiation channels.

VERIFICATION (executed in tests, not asserted here):
  * Ri -> 0 reduces the annulus to a disk and the roots must approach
    the zeros of J_m.
  * A thin annulus (Ro - Ri << R) reduces to a slab and the roots must
    approach k (Ro - Ri) = p*pi.
  * For a dielectric-filled cavity with lossless conductor, Q -> 1/tan(delta).
"""

from __future__ import annotations

import math

import numpy as np
from scipy.optimize import brentq
from scipy.special import jv, yv

from rgcs_surface_wave.evidence import ClaimClass
from rgcs_surface_wave.geometry import (C0, AnnularGeometry, Conductor,
                                        DielectricSlab)


class EigenmodeError(ValueError):
    pass


def determinant(m: int, k: float, r_i: float, r_o: float) -> float:
    """D_m(k): the annular PEC eigenvalue condition."""
    if k <= 0:
        raise EigenmodeError("k must be positive")
    return float(jv(m, k * r_i) * yv(m, k * r_o)
                 - jv(m, k * r_o) * yv(m, k * r_i))


def radial_roots(m: int, r_i: float, r_o: float, n_roots: int = 4,
                 k_max_factor: float = 40.0) -> list:
    """Bracket and solve the first ``n_roots`` radial eigenvalues."""
    if not (0 < r_i < r_o):
        raise EigenmodeError("require 0 < inner < outer radius")
    width = r_o - r_i
    k_hi = k_max_factor * math.pi / width
    n_scan = max(4000, int(20 * k_hi * width / math.pi))
    ks = np.linspace(1e-6, k_hi, n_scan)
    vals = np.array([determinant(m, k, r_i, r_o) for k in ks])
    roots = []
    for i in range(len(ks) - 1):
        a, b = vals[i], vals[i + 1]
        if np.isfinite(a) and np.isfinite(b) and a * b < 0:
            try:
                roots.append(float(brentq(
                    lambda k: determinant(m, k, r_i, r_o),
                    ks[i], ks[i + 1], xtol=1e-14, rtol=1e-15)))
            except (ValueError, RuntimeError):        # pragma: no cover
                continue
            if len(roots) >= n_roots:
                break
    return roots


def _quality_factors(frequency_hz: float, slab: DielectricSlab | None,
                     conductor: Conductor, plate_gap_m: float,
                     eps_eff: float) -> dict:
    """Dielectric, conductor, and declared radiation Q channels."""
    q_d = (1.0 / slab.loss_tangent) if (slab and slab.loss_tangent > 0) \
        else float("inf")
    eta = math.sqrt(4e-7 * math.pi / (8.8541878128e-12 * eps_eff))
    k = 2 * math.pi * frequency_hz * math.sqrt(eps_eff) / C0
    r_s = conductor.surface_resistance_ohm(frequency_hz)
    # standard parallel-plate estimate Q_c = k*h*eta/(2*R_s)
    q_c = (k * plate_gap_m * eta) / (2.0 * r_s) if r_s > 0 \
        else float("inf")
    inv = 0.0
    for q in (q_d, q_c):
        if math.isfinite(q) and q > 0:
            inv += 1.0 / q
    q_total = (1.0 / inv) if inv > 0 else float("inf")
    return {"q_dielectric": q_d, "q_conductor": q_c,
            "q_radiation": None,
            "q_radiation_status": "NOT_MODELLED: an open annulus "
                                  "radiates; this reduced closed "
                                  "parallel-plate model cannot "
                                  "estimate it, so the reported Q is "
                                  "an UPPER BOUND",
            "q_total_upper_bound": q_total}


def annular_modes(geo: AnnularGeometry, m_values=(0, 1, 2, 3),
                  n_roots: int = 3,
                  plate_gap_m: float | None = None) -> dict:
    """C15: solve the annular eigenproblem and DERIVE f_SW."""
    slab = geo.dielectric
    eps_eff = slab.epsilon_r if slab else 1.0
    gap = plate_gap_m if plate_gap_m is not None else (
        slab.gap_m + slab.thickness_m if slab else 1e-3)
    modes = []
    for m in m_values:
        for idx, k in enumerate(radial_roots(m, geo.inner_radius_m,
                                             geo.outer_radius_m,
                                             n_roots), start=1):
            f = k * C0 / (2 * math.pi * math.sqrt(eps_eff))
            qs = _quality_factors(f, slab, geo.conductor, gap, eps_eff)
            modes.append({
                "m": m, "radial_index": idx,
                "k_rad_per_m": k, "frequency_hz": f,
                "frequency_mhz": f / 1e6,
                "free_space_wavelength_m": C0 / f,
                "determinant_residual": abs(determinant(
                    m, k, geo.inner_radius_m, geo.outer_radius_m)),
                **qs})
    modes.sort(key=lambda d: d["frequency_hz"])
    lowest = modes[0] if modes else None
    return {
        "schema": "rgcs.r1015.annular-eigenmodes.v1",
        "geometry": geo.record(),
        "epsilon_effective": eps_eff,
        "plate_gap_m": gap,
        "mode_count": len(modes), "modes": modes,
        "f_surface_wave_derived_hz": lowest["frequency_hz"] if lowest
        else None,
        "f_surface_wave_basis": "lowest annular eigenmode of the "
                                "declared parallel-plate model",
        "model": "PEC-walled dielectric-loaded annular parallel-plate, "
                 "no z variation, loss added perturbatively",
        "limitations": [
            "closed PEC walls: a real open annulus radiates and the "
            "reported Q is an upper bound",
            "no z variation: higher-order axial modes are excluded",
            "the angular patterning is NOT in this eigenproblem; it "
            "enters as a perturbation through the mask spectrum",
        ],
        "claim_class": ClaimClass.SIMULATED.value,
    }


def test_candidate_carrier(geo: AnnularGeometry,
                           f_candidate_hz: float = 4096.0) -> dict:
    """Explicit controlled test of a candidate carrier frequency.

    This is the falsification path required by the R10.15 override:
    4096 Hz is tested as ONE candidate, never assumed.
    """
    lam0 = C0 / f_candidate_hz
    circ = 2 * math.pi * geo.mean_radius_m
    modes = annular_modes(geo, m_values=(1,), n_roots=1)
    f_lowest = modes["f_surface_wave_derived_hz"]
    ratio = f_lowest / f_candidate_hz if f_lowest else float("inf")
    # what the candidate would demand of the surface
    lam_g_needed = circ            # m = 1 resonance
    slow_needed = lam0 / lam_g_needed
    verdict = ("SUPPORTED" if 0.5 < ratio < 2.0
               else "FALSIFIED_AS_ELECTROMAGNETIC_CARRIER")
    return {
        "schema": "rgcs.r1015.candidate-carrier-test.v1",
        "f_candidate_hz": f_candidate_hz,
        "candidate_free_space_wavelength_m": lam0,
        "annulus_circumference_m": circ,
        "circumference_in_wavelengths": circ / lam0,
        "lowest_derived_eigenmode_hz": f_lowest,
        "ratio_derived_over_candidate": ratio,
        "required_slow_wave_factor_for_m1": slow_needed,
        "verdict": verdict,
        "interpretation": (
            "the candidate is consistent with a derived annular "
            "eigenmode"
            if verdict == "SUPPORTED" else
            "the structure is electrically tiny at the candidate "
            "frequency: it cannot support a bound annular surface-wave "
            "resonance there. The candidate frequency is retained as a "
            "SWITCHING and PHASE reference, which is what the source "
            "record actually describes, and NOT as the "
            "electromagnetic carrier. This is a NULL result for the "
            "carrier reading, not a failure of the device concept."),
        "claim_class": ClaimClass.NULL.value if verdict.startswith(
            "FALSIFIED") else ClaimClass.SIMULATED.value,
    }
