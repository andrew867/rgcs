"""Alpha-quartz anisotropic phonon-polariton lane (V5).

Alpha-quartz is modeled as an anisotropic polaritonic transfer
medium, not merely a passive piezoelectric rod. Anchors: Falge, Otto,
Sohler 1974 ATR dispersion (ledger P020), direct s-SNOM SPhP
observation (P023), Scott and Ushioda polariton intensities (P025).
Sources prove measured polariton dispersion on quartz; nothing here
validates RGCS hardware.

Every computed value is labeled MODEL_ESTIMATE unless measured data
are supplied. No force, thrust, torque, or lift callable exists.
"""

from __future__ import annotations

import math

C_M_PER_S = 299_792_458.0

MEDIUM_REQUIRED_FIELDS = (
    "crystal_cut", "handedness", "optic_axis_vector",
    "surface_normal_vector", "epsilon_parallel", "epsilon_perpendicular",
    "reststrahlen_band_cm1", "TO_parallel_cm1", "LO_parallel_cm1",
    "TO_perpendicular_cm1", "LO_perpendicular_cm1",
    "damping_parameters", "Raman_active_modes", "IR_active_modes",
    "surface_gap_um", "launcher_material", "launcher_geometry",
)

ORIENTATIONS = ("optic_axis_parallel_to_surface",
                "optic_axis_perpendicular_to_surface")


def validate_medium(medium: dict) -> list[str]:
    return [f"quartz medium missing field '{field}'"
            for field in MEDIUM_REQUIRED_FIELDS if field not in medium]


def polariton_k(omega_rad_s: float, eps_x: float, eps_z: float) -> float:
    """k_p = (omega/c) sqrt((eps_x eps_z - eps_z)/(eps_x eps_z - 1)),
    the optic-axis-parallel anisotropic surface branch."""
    numer = eps_x * eps_z - eps_z
    denom = eps_x * eps_z - 1.0
    if abs(denom) < 1e-12:
        raise ValueError("polariton denominator near singular")
    return omega_rad_s / C_M_PER_S * math.sqrt(abs(numer / denom))


def branch_components(orientation: str, eps_parallel: float,
                      eps_perpendicular: float) -> dict:
    """Orientation selects WHICH tensor components enter the branch;
    parallel and perpendicular geometries must never share them."""
    if orientation not in ORIENTATIONS:
        raise ValueError(f"orientation must be one of {ORIENTATIONS}")
    if orientation == "optic_axis_parallel_to_surface":
        eps_x, eps_z = eps_perpendicular, eps_parallel
    else:
        eps_x, eps_z = eps_parallel, eps_perpendicular
    return {"orientation": orientation, "eps_x": eps_x, "eps_z": eps_z,
            "label": "MODEL_ESTIMATE"}


def fringe_profile(x_m: float, amplitude: float, decay_length_m: float,
                   period_m: float, phase_rad: float = 0.0) -> float:
    """s(x) = A exp(-x/L_p) sin(2 pi x / d - phi)."""
    if decay_length_m <= 0 or period_m <= 0:
        raise ValueError("decay length and period must be positive")
    return (amplitude * math.exp(-x_m / decay_length_m)
            * math.sin(2.0 * math.pi * x_m / period_m - phase_rad))


def measured_k_from_fringes(period_m: float, k0_per_m: float,
                            theta_in_rad: float) -> float:
    """k_p' = 2 pi / d - k0 cos(theta_in), the experimental
    conversion from fringe period to polariton wavevector."""
    if period_m <= 0:
        raise ValueError("fringe period must be positive")
    return 2.0 * math.pi / period_m - k0_per_m * math.cos(theta_in_rad)


def atr_witness_metadata(surface_gap_um: float,
                         layer_thickness_um: float = 0.0) -> dict:
    """Gap and layer thickness are witness-sensitive ATR variables."""
    if surface_gap_um < 0 or layer_thickness_um < 0:
        raise ValueError("gap and thickness cannot be negative")
    sensitive = surface_gap_um > 0 or layer_thickness_um > 0
    return {"surface_gap_um": surface_gap_um,
            "layer_thickness_um": layer_thickness_um,
            "witness_sensitivity": ("ATR_GAP_OR_LAYER_SENSITIVE"
                                    if sensitive else "CONTACT_BASELINE"),
            "label": "MODEL_ESTIMATE"}


__all__ = ["C_M_PER_S", "MEDIUM_REQUIRED_FIELDS", "ORIENTATIONS",
           "validate_medium", "polariton_k", "branch_components",
           "fringe_profile", "measured_k_from_fringes",
           "atr_witness_metadata"]
