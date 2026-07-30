"""R10.15 Phases C13, C14 — reduced surface-impedance model and the
unit-cell eigenvalue problem.

DECLARED SCOPE. This is a reduced, effective-surface-impedance model.
It is NOT a full spoof-surface-plasmon dispersion law, and it is not
a substitute for a periodic full-wave unit-cell solve. Its
approximations are listed in ``MODEL_ASSUMPTIONS`` and travel with
every result.

Established physics used (ClaimClass.ESTABLISHED, cited):
  * A capacitive/inductive impedance surface Z_s = jX with X > 0
    (inductive) supports a bound TM surface wave with
        k_x = k0 * sqrt(1 + (X/eta0)^2),  alpha = k0 * X / eta0,
    where alpha is the transverse decay constant into the half space.
    [Sievenpiper et al., IEEE MTT 47(11), 1999; Pozar, Microwave
    Engineering, 4th ed., ch. 3.]
  * A groove/pin array of period d, aperture fraction a/d and depth h
    behaves as X = eta0 * (a/d) * tan(k0 h) in the effective-medium
    limit d << lambda0. [Pendry, Martin-Moreno, Garcia-Vidal,
    Science 305, 847 (2004).]

The unit-cell problem is posed as an eigenvalue problem: find the
propagation constant k_x that annihilates the declared dispersion
residual D(omega, k_x) = 0.
"""

from __future__ import annotations

import math

from scipy.optimize import brentq

from rgcs_surface_wave.evidence import ClaimClass
from rgcs_surface_wave.geometry import C0, EPS0, MU0

ETA0 = math.sqrt(MU0 / EPS0)

MODEL_ASSUMPTIONS = (
    "effective-medium surface impedance: cell period small compared "
    "with the free-space wavelength",
    "single TM surface-wave branch; no higher-order Floquet space "
    "harmonics of the periodic surface",
    "isotropic homogeneous half space above the surface",
    "conductor treated as a perfect electric conductor for the "
    "dispersion; loss added perturbatively afterwards",
    "curvature of the annulus neglected in the unit cell (straight "
    "cell approximation, valid when the cell pitch is small compared "
    "with the mean radius)",
)


class ImpedanceError(ValueError):
    pass


def groove_reactance(frequency_hz: float, depth_m: float,
                     aperture_fraction: float,
                     epsilon_r: float = 1.0) -> float:
    """Effective inductive surface reactance X of a grooved surface."""
    if not (0 < aperture_fraction <= 1):
        raise ImpedanceError("aperture_fraction must lie in (0, 1]")
    if depth_m <= 0 or frequency_hz <= 0:
        raise ImpedanceError("depth and frequency must be positive")
    k = 2 * math.pi * frequency_hz * math.sqrt(epsilon_r) / C0
    return ETA0 * aperture_fraction * math.tan(k * depth_m)


def dispersion_residual(frequency_hz: float, k_x: float,
                        reactance_ohm: float) -> float:
    """D(omega, k_x) for the declared impedance-surface eigenproblem.

    Bound TM surface wave requires k_x^2 = k0^2 + alpha^2 with
    alpha = k0 X / eta0, i.e. residual = k_x^2 - k0^2 (1 + (X/eta0)^2).
    """
    k0 = 2 * math.pi * frequency_hz / C0
    return k_x ** 2 - k0 ** 2 * (1.0 + (reactance_ohm / ETA0) ** 2)


def solve_unit_cell(frequency_hz: float, depth_m: float,
                    aperture_fraction: float, period_m: float,
                    epsilon_r: float = 1.0) -> dict:
    """C14: solve the unit-cell eigenproblem at one frequency."""
    if period_m <= 0:
        raise ImpedanceError("period must be positive")
    k0 = 2 * math.pi * frequency_hz / C0
    lam0 = C0 / frequency_hz
    X = groove_reactance(frequency_hz, depth_m, aperture_fraction,
                         epsilon_r)
    bound = X > 0                      # inductive surface binds TM
    validity = period_m / lam0
    if not bound:
        return {"frequency_hz": frequency_hz, "reactance_ohm": X,
                "bound_surface_wave": False,
                "reason": "surface reactance is capacitive or the "
                          "groove is beyond quarter-wave resonance; no "
                          "bound TM branch in this reduced model",
                "effective_medium_validity_d_over_lambda": validity,
                "claim_class": ClaimClass.SIMULATED.value}
    k_x = k0 * math.sqrt(1.0 + (X / ETA0) ** 2)
    alpha = k0 * X / ETA0
    resid = dispersion_residual(frequency_hz, k_x, X)
    # group velocity by central difference on the solved branch
    def kx_of(f):
        Xf = groove_reactance(f, depth_m, aperture_fraction, epsilon_r)
        return (2 * math.pi * f / C0) * math.sqrt(1.0 + (Xf / ETA0) ** 2)
    df = max(frequency_hz * 1e-6, 1.0)
    dk = (kx_of(frequency_hz + df) - kx_of(frequency_hz - df))
    v_g = (2 * math.pi * 2 * df / dk) if dk != 0 else float("inf")
    return {
        "schema": "rgcs.r1015.unit-cell.v1",
        "frequency_hz": frequency_hz,
        "k0_rad_per_m": k0, "k_x_rad_per_m": k_x,
        "slow_wave_factor": k_x / k0,
        "guided_wavelength_m": 2 * math.pi / k_x,
        "reactance_ohm": X,
        "transverse_decay_alpha_per_m": alpha,
        "confinement_length_m": (1.0 / alpha if alpha > 0
                                 else float("inf")),
        "group_velocity_m_per_s": v_g,
        "group_index": C0 / v_g if v_g else float("inf"),
        "bound_surface_wave": True,
        "dispersion_residual": resid,
        "effective_medium_validity_d_over_lambda": validity,
        "effective_medium_valid": validity < 0.1,
        "assumptions": list(MODEL_ASSUMPTIONS),
        "claim_class": ClaimClass.SIMULATED.value,
    }


def required_slow_wave_factor(target_frequency_hz: float,
                              circumference_m: float,
                              angular_index: int) -> dict:
    """What slow-wave factor would a target carrier need?

    An annular resonance needs an integer number of guided wavelengths
    around the ring: k_x * R = m, i.e. lambda_g = circumference / m.
    This inverts that condition, which is how a candidate carrier
    frequency is falsified or supported.
    """
    if angular_index < 1:
        raise ImpedanceError("angular index must be >= 1")
    lam0 = C0 / target_frequency_hz
    lam_g = circumference_m / angular_index
    n_slow = lam0 / lam_g
    # depth needed from X = eta0 (a/d) tan(k0 h) with a/d -> 1
    k0 = 2 * math.pi / lam0
    x_over_eta = math.sqrt(max(n_slow ** 2 - 1.0, 0.0))
    depth = math.atan(x_over_eta) / k0 if k0 > 0 else float("inf")
    return {
        "target_frequency_hz": target_frequency_hz,
        "angular_index": angular_index,
        "free_space_wavelength_m": lam0,
        "required_guided_wavelength_m": lam_g,
        "required_slow_wave_factor": n_slow,
        "required_reactance_over_eta0": x_over_eta,
        "required_groove_depth_m": depth,
        "physically_reasonable": bool(n_slow < 100.0),
        "claim_class": ClaimClass.DERIVED.value,
    }


def solve_frequency_for_kx(k_x_target: float, depth_m: float,
                           aperture_fraction: float,
                           f_lo: float = 1e6, f_hi: float = 20e9) -> float:
    """Invert the unit-cell eigenproblem: find f such that k_x matches."""
    def resid(f):
        X = groove_reactance(f, depth_m, aperture_fraction)
        k0 = 2 * math.pi * f / C0
        if X <= 0:
            return 1e30
        return k0 * math.sqrt(1.0 + (X / ETA0) ** 2) - k_x_target
    # keep the bracket below the first groove (quarter-wave) resonance
    f_res = C0 / (4.0 * depth_m)
    hi = min(f_hi, 0.99 * f_res)
    if resid(f_lo) * resid(hi) > 0:
        raise ImpedanceError(
            f"no bracketed solution for k_x={k_x_target:.4g} between "
            f"{f_lo:.4g} Hz and {hi:.4g} Hz; widen the bracket or "
            "change the surface parameters")
    return float(brentq(resid, f_lo, hi, xtol=1.0, rtol=1e-12))
