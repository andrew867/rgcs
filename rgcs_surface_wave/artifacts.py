"""R10.15 Phase D24 — ordinary-artifact estimates.

Every mechanism here can produce an apparent thrust on a bench without
any new physics. Each estimate uses a standard textbook expression with
its citation and its validity range. The purpose is adversarial: before
any anomaly is entertained, the candidate signal must be compared with
these, and the comparison must be published beside it.

Reference values assume a bench in air at room temperature.
"""

from __future__ import annotations

import math

from rgcs_surface_wave.evidence import ClaimClass
from rgcs_surface_wave.geometry import C0, EPS0

#: air at 20 C, 101.325 kPa
AIR = {"density_kg_m3": 1.204, "sound_speed_m_s": 343.0,
       "ion_mobility_m2_per_vs": 2.0e-4, "expansion_1_per_k": 3.41e-3,
       "breakdown_v_per_m": 3.0e6}


class ArtifactError(ValueError):
    pass


def electrostatic_attraction(voltage_v: float, area_m2: float,
                             gap_m: float) -> dict:
    """Parallel-plate attraction F = eps0 A V^2 / (2 g^2)."""
    if gap_m <= 0 or area_m2 <= 0:
        raise ArtifactError("area and gap must be positive")
    f = EPS0 * area_m2 * voltage_v ** 2 / (2 * gap_m ** 2)
    return {"mechanism": "electrostatic_attraction", "force_n": f,
            "formula": "eps0 A V^2 / (2 g^2)",
            "note": "always attractive, scales as V^2 so it is EVEN "
                    "under polarity reversal, exactly like a Maxwell "
                    "stress signal; polarity reversal does NOT "
                    "discriminate them",
            "claim_class": ClaimClass.DERIVED.value}


def corona_onset(radius_m: float, rel_air_density: float = 1.0) -> dict:
    """Peek's law onset field for a cylindrical conductor in air."""
    if radius_m <= 0:
        raise ArtifactError("radius must be positive")
    e = 3.0e6 * rel_air_density * (1 + 0.301 /
                                   math.sqrt(rel_air_density * radius_m))
    return {"mechanism": "corona_onset", "onset_field_v_per_m": e,
            "formula": "Peek: 3e6 * delta * (1 + 0.301/sqrt(delta r))",
            "reference": "Peek, Dielectric Phenomena in High Voltage "
                         "Engineering (1929)",
            "claim_class": ClaimClass.ESTABLISHED.value}


def ion_wind_thrust(current_a: float, gap_m: float,
                    mobility_m2_per_vs: float | None = None) -> dict:
    """F = I d / mu: the dominant bench artifact at high voltage.

    Note the magnitude: even microamps across a centimetre produce
    forces far above a typical anomalous-thrust claim.
    """
    mu = mobility_m2_per_vs or AIR["ion_mobility_m2_per_vs"]
    if gap_m <= 0 or mu <= 0:
        raise ArtifactError("gap and mobility must be positive")
    f = current_a * gap_m / mu
    return {"mechanism": "ion_wind", "force_n": f,
            "formula": "I d / mu",
            "reference": "Christenson & Moller, AIAA J. 5(10), 1967",
            "note": "requires air; vanishes in hard vacuum, which is "
                    "the decisive control",
            "claim_class": ClaimClass.DERIVED.value}


def thermal_buoyancy(power_w: float, volume_m3: float,
                     delta_t_k: float = 1.0) -> dict:
    """Buoyant force from locally heated air."""
    rho, beta = AIR["density_kg_m3"], AIR["expansion_1_per_k"]
    f = rho * beta * delta_t_k * 9.80665 * volume_m3
    return {"mechanism": "thermal_buoyancy", "force_n": f,
            "power_w": power_w, "delta_t_k": delta_t_k,
            "formula": "rho beta dT g V",
            "note": "slow onset with a thermal time constant; a step "
                    "in drive followed by a slow force ramp is the "
                    "signature",
            "claim_class": ClaimClass.DERIVED.value}


def radiation_pressure(radiated_power_w: float,
                       anisotropy: float = 1.0) -> dict:
    """Upper bound F <= P/c, reached only for a perfectly one-sided beam."""
    if not (0.0 <= anisotropy <= 1.0):
        raise ArtifactError("anisotropy must lie in [0, 1]")
    f = radiated_power_w * anisotropy / C0
    return {"mechanism": "photon_radiation_pressure", "force_n": f,
            "formula": "P * anisotropy / c",
            "note": "isotropic radiation gives ZERO net force; this is "
                    "the hard ceiling for any purely radiative thrust "
                    "and it is not multiplied by Q",
            "claim_class": ClaimClass.ESTABLISHED.value}


def acoustic_radiation_pressure(acoustic_power_w: float,
                                area_m2: float) -> dict:
    """p = I / c_s; couples to the balance through the enclosure."""
    if area_m2 <= 0:
        raise ArtifactError("area must be positive")
    intensity = acoustic_power_w / area_m2
    p = intensity / AIR["sound_speed_m_s"]
    return {"mechanism": "acoustic_radiation_pressure",
            "pressure_pa": p, "force_n": p * area_m2,
            "formula": "I / c_sound", "claim_class": ClaimClass.DERIVED.value}


def eddy_current_force(b_tesla: float, area_m2: float,
                       conductivity_s_per_m: float, thickness_m: float,
                       frequency_hz: float) -> dict:
    """Order-of-magnitude eddy-current force on a nearby conductor."""
    if min(area_m2, thickness_m, frequency_hz) <= 0:
        raise ArtifactError("area, thickness, frequency must be positive")
    omega = 2 * math.pi * frequency_hz
    f = 0.5 * conductivity_s_per_m * thickness_m * omega * \
        b_tesla ** 2 * area_m2 * 1e-3
    return {"mechanism": "eddy_current", "force_n": f,
            "formula": "order-of-magnitude sigma t omega B^2 A scaling",
            "approximation": "ORDER_OF_MAGNITUDE_ONLY: not a solved "
                             "eddy-current problem; use it to decide "
                             "whether a full solve is needed",
            "claim_class": ClaimClass.HYPOTHESIS.value}


def cable_stiffness_force(displacement_m: float,
                          stiffness_n_per_m: float = 0.05) -> dict:
    """Cables are springs: any drive-correlated motion reads as force."""
    return {"mechanism": "cable_stiffness",
            "force_n": displacement_m * stiffness_n_per_m,
            "formula": "k x",
            "note": "the classic false positive on a torsion balance; "
                    "control by cable routing and by driving with the "
                    "balance locked",
            "claim_class": ClaimClass.DERIVED.value}


def vibration_rectification(acceleration_m_s2: float, mass_kg: float,
                            asymmetry: float = 0.01) -> dict:
    """Asymmetric vibration rectifies into an apparent steady force."""
    return {"mechanism": "vibration_rectification",
            "force_n": mass_kg * acceleration_m_s2 * asymmetry,
            "formula": "m a * asymmetry_fraction",
            "claim_class": ClaimClass.HYPOTHESIS.value}


def budget(candidate_force_n: float, drive: dict | None = None) -> dict:
    """Compare a candidate force against the ordinary artifact floor."""
    d = {"voltage_v": 100.0, "area_m2": 4e-3, "gap_m": 1e-3,
         "current_a": 1e-6, "radiated_power_w": 1e-3,
         "volume_m3": 1e-4, "displacement_m": 1e-6,
         **(drive or {})}
    est = [
        electrostatic_attraction(d["voltage_v"], d["area_m2"], d["gap_m"]),
        ion_wind_thrust(d["current_a"], d["gap_m"]),
        thermal_buoyancy(d["radiated_power_w"], d["volume_m3"]),
        radiation_pressure(d["radiated_power_w"]),
        cable_stiffness_force(d["displacement_m"]),
    ]
    largest = max(est, key=lambda e: e["force_n"])
    ratio = candidate_force_n / largest["force_n"] \
        if largest["force_n"] > 0 else float("inf")
    return {
        "schema": "rgcs.r1015.artifact-budget.v1",
        "candidate_force_n": candidate_force_n,
        "estimates": est,
        "largest_artifact": largest["mechanism"],
        "largest_artifact_force_n": largest["force_n"],
        "candidate_over_largest_artifact": ratio,
        "verdict": ("CANDIDATE_BELOW_ARTIFACT_FLOOR" if ratio <= 1.0
                    else "CANDIDATE_ABOVE_ARTIFACT_FLOOR"),
        "required_controls": [
            "hard vacuum (removes ion wind and convection)",
            "sham drive at matched dissipated power",
            "drive reversal and polarity reversal",
            "balance locked during drive",
            "dielectric removed",
            "geometry mirrored",
            "blind analysis of the force channel",
        ],
        "note": "exceeding the artifact floor is NECESSARY and not "
                "sufficient; it only earns the right to a controlled "
                "measurement",
        "claim_class": ClaimClass.DERIVED.value,
    }
