"""Analytic reference formulas for the RSCS2 validation benchmarks
(RSCS2-V.*). All EST closed-form results; these are the *truth* the CPU
solver must reproduce, and they are correct and testable independently of
the solver. Provenance: standard vibration theory (Blevins, "Formulas for
Natural Frequency and Mode Shape"; Timoshenko, "Vibration Problems in
Engineering"; Landau-Lifshitz "Theory of Elasticity").

No new physics (DV4-012): these are textbook formulas.
"""

from __future__ import annotations

import math

# Fixed-free (cantilever) Euler-Bernoulli beam eigenvalue roots (beta_n * L).
CANTILEVER_BETA_L = (1.8751040687, 4.6940911330, 7.8547574382,
                     10.9955407349, 14.1371683910)

# Free-free Euler-Bernoulli beam eigenvalue roots (beta_n * L), n>=1
# (rigid-body modes excluded).
FREE_FREE_BETA_L = (4.7300407449, 7.8532046241, 10.9956078380,
                    14.1371654913, 17.2787596574)


def rod_longitudinal_free_free_hz(youngs_pa: float, density_kg_m3: float,
                                  length_m: float, n: int = 1) -> float:
    """n-th longitudinal natural frequency of a free-free uniform rod:
    f_n = n * c / (2 L), c = sqrt(E / rho). (RSCS2-V.1)"""
    if n < 1:
        raise ValueError("n must be >= 1")
    c = math.sqrt(youngs_pa / density_kg_m3)
    return n * c / (2.0 * length_m)


def rod_longitudinal_fixed_free_hz(youngs_pa: float, density_kg_m3: float,
                                   length_m: float, n: int = 1) -> float:
    """n-th longitudinal frequency of a fixed-free rod:
    f_n = (2n-1) c / (4 L), c = sqrt(E/rho)."""
    if n < 1:
        raise ValueError("n must be >= 1")
    c = math.sqrt(youngs_pa / density_kg_m3)
    return (2 * n - 1) * c / (4.0 * length_m)


def euler_bernoulli_cantilever_hz(youngs_pa: float, density_kg_m3: float,
                                  length_m: float, width_m: float,
                                  thickness_m: float, n: int = 1) -> float:
    """n-th flexural frequency of a fixed-free Euler-Bernoulli beam bending
    in the thickness direction (RSCS2-V.2):
        f_n = (beta_n L)^2 / (2 pi) * sqrt(E I / (rho A L^4)),
    with I = width * thickness^3 / 12, A = width * thickness.
    Valid for slender beams (L >> thickness)."""
    if n < 1 or n > len(CANTILEVER_BETA_L):
        raise ValueError(f"n must be 1..{len(CANTILEVER_BETA_L)}")
    inertia = width_m * thickness_m ** 3 / 12.0
    area = width_m * thickness_m
    bl2 = CANTILEVER_BETA_L[n - 1] ** 2
    return (bl2 / (2.0 * math.pi)) * math.sqrt(
        youngs_pa * inertia / (density_kg_m3 * area * length_m ** 4))


def timoshenko_cantilever_hz(youngs_pa: float, shear_modulus_pa: float,
                             density_kg_m3: float, length_m: float,
                             width_m: float, thickness_m: float,
                             shear_coeff: float = 5.0 / 6.0,
                             n: int = 1) -> float:
    """First-order Timoshenko correction to the cantilever flexural
    frequency (RSCS2-V.3): the EB frequency reduced by shear + rotary
    inertia. Returns the corrected f_n. Reduces to EB as thickness/L -> 0.

    Uses the standard first-order multiplicative correction
        f_T = f_EB / sqrt(1 + (r/L)^2 * (beta_n L)^2 * (1 + E/(k' G)) )
    with radius of gyration r = thickness / sqrt(12). This is the
    slender-to-moderate approximation; a full Timoshenko dispersion solve
    is the solver's job, not this reference."""
    f_eb = euler_bernoulli_cantilever_hz(youngs_pa, density_kg_m3, length_m,
                                         width_m, thickness_m, n)
    r = thickness_m / math.sqrt(12.0)
    bl = CANTILEVER_BETA_L[n - 1]
    corr = 1.0 + (r / length_m) ** 2 * bl ** 2 * (
        1.0 + youngs_pa / (shear_coeff * shear_modulus_pa))
    return f_eb / math.sqrt(corr)


def cube_lame_mode_hz(shear_modulus_pa: float, density_kg_m3: float,
                      edge_m: float) -> float:
    """Fundamental Lame (equivoluminal) mode of a FREE isotropic cube —
    an EXACT closed-form eigenfrequency, independent of Poisson's ratio:
        f = v_s / (sqrt(2) * a),  v_s = sqrt(G / rho).
    Classical exact solution; used by Demarest (JASA 49, 768 (1971),
    'Cube-Resonance Method to Determine the Elastic Constants of
    Solids') as the 8-significant-digit check for cube spectra.
    (RSCS2-V.5 anchor.)"""
    v_s = math.sqrt(shear_modulus_pa / density_kg_m3)
    return v_s / (math.sqrt(2.0) * edge_m)


def lame_from_e_nu(youngs_pa: float, poisson: float) -> tuple[float, float]:
    """(lambda, mu) Lame parameters from (E, nu). EST identity."""
    lam = youngs_pa * poisson / ((1 + poisson) * (1 - 2 * poisson))
    mu = youngs_pa / (2 * (1 + poisson))
    return lam, mu
