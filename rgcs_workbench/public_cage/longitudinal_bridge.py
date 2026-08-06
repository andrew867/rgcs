"""V4 longitudinal-mode bridge with the V4B dielectric witness layer.

Translates the source phrase "coherent longitudinal EMF" into the
conventional lane: charge-density oscillation, plasmon/polariton and
surface-bound slow-wave modes, coupled through gratings, phonons, or
time-varying boundaries. Free-space far fields are transverse; the
longitudinal component earns its keep only in matter, near fields,
and bounded interface modes, which is exactly where this model lives.

The dielectric witness layer (V4B) supplies epsilon_d and loss terms
to the SPP relation: surrounding media contaminated by the molecules
under observation shift the dielectric function and therefore the
plasmonic response. Residue is a witness-layer hypothesis to be
measured with spectroscopy and controls, never causal proof.

Every output is labeled ESTIMATE, SIMULATION, MEASURED, or
SOURCE_REPORTED. One variable changes at a time. Near-neighbor
frequency families are never silently merged (phi_ladders holds the
receipts). No force, thrust, torque, or lift callable exists here.
"""

from __future__ import annotations

import math

from rgcs_workbench.public_cage import phi_ladders as PL

C_M_PER_S = 299_792_458.0
EPSILON_0 = 8.8541878128e-12
E_CHARGE = 1.602176634e-19

OUTPUT_LABELS = ("ESTIMATE", "SIMULATION", "MEASURED", "SOURCE_REPORTED")

#: claim_status values a witness layer may carry; none may contain
#: VALIDATION (a witness is not a conclusion).
WITNESS_CLAIM_STATUSES = (
    "SOURCE_REPORTED", "ESTIMATE", "SIMULATION", "MEASUREMENT_TARGET",
    "MEASURED", "DIELECTRIC_WITNESS_LAYER_HYPOTHESIS",
)

WITNESS_REQUIRED_FIELDS = (
    "layer_id", "sample_id", "medium_type", "epsilon_d_estimate",
    "loss_tangent_estimate", "surface_conductivity_estimate",
    "water_film_state", "molecular_fingerprint_status",
    "mineral_particle_status", "Raman_available", "SERS_possible",
    "FTIR_available", "time_since_event_days", "control_sample_id",
    "claim_status",
)

#: Crop-formation records carry this residue block when sample
#: information exists. Defaults are honest unknowns and falses.
RESIDUE_DIELECTRIC_BLOCK_DEFAULTS = {
    "sample_status": "none",
    "sample_delay_days": "unknown",
    "plant_surface_film": "unknown",
    "water_or_airborne_contaminants": "unknown",
    "mineral_particles": "unknown",
    "Raman_fingerprint_available": False,
    "SERS_possible": False,
    "FTIR_available": False,
    "dielectric_shift_measured": False,
    "surface_conductivity_measured": False,
    "off_formation_control_available": False,
    "decay_retest_available": False,
    "notes": "",
    "interpretation_rule": ("residue is a possible dielectric witness "
                            "layer to measure, not causal proof"),
}


# ------------------------------------------------------ core physics

def plasma_frequency_rad_s(n_per_m3: float, m_eff_kg: float) -> float:
    """omega_p = sqrt(n e^2 / (epsilon_0 m_eff))."""
    if n_per_m3 <= 0 or m_eff_kg <= 0:
        raise ValueError("carrier density and effective mass must be "
                         "positive")
    return math.sqrt(n_per_m3 * E_CHARGE ** 2 / (EPSILON_0 * m_eff_kg))


def drude_epsilon(omega_rad_s: float, omega_p_rad_s: float,
                  gamma_rad_s: float, epsilon_inf: float = 1.0) -> complex:
    """epsilon(omega) = eps_inf - omega_p^2 / (omega^2 + i gamma omega)."""
    if omega_rad_s <= 0:
        raise ValueError("omega must be positive")
    return epsilon_inf - omega_p_rad_s ** 2 / (
        omega_rad_s ** 2 + 1j * gamma_rad_s * omega_rad_s)


def spp_factor(epsilon_m: float, epsilon_d: float) -> float:
    """Dimensionless sqrt(eps_m eps_d / (eps_m + eps_d)) magnitude."""
    denom = epsilon_m + epsilon_d
    if abs(denom) < 1e-12:
        raise ValueError("SPP denominator near singular")
    return math.sqrt(abs(epsilon_m * epsilon_d / denom))


def spp_k_per_m(omega_rad_s: float, epsilon_m: float,
                epsilon_d: float) -> float:
    """k_spp = (omega/c) * spp_factor."""
    return omega_rad_s / C_M_PER_S * spp_factor(epsilon_m, epsilon_d)


def momentum_bridge_k(k_incident: float, g_grating: float,
                      k_phonon: float, sign: int = 1) -> float:
    """k_surface = k_incident + G_grating +/- K_phonon."""
    if sign not in (1, -1):
        raise ValueError("sign must be +1 or -1")
    return k_incident + g_grating + sign * k_phonon


# --------------------------------------------- dielectric witness layer

def validate_witness_layer(layer: dict) -> list[str]:
    problems = [f"witness layer missing field '{field}'"
                for field in WITNESS_REQUIRED_FIELDS
                if field not in layer]
    status = str(layer.get("claim_status", ""))
    if status and status not in WITNESS_CLAIM_STATUSES:
        problems.append(f"unknown claim_status '{status}'")
    if "VALIDAT" in status.upper():
        problems.append("a witness layer can never carry a validation "
                        "status; it is a hypothesis or a measurement")
    return problems


def residue_dielectric_block(**overrides) -> dict:
    """Cookbook metadata block with honest-unknown defaults."""
    block = dict(RESIDUE_DIELECTRIC_BLOCK_DEFAULTS)
    unknown = set(overrides) - set(block)
    if unknown:
        raise ValueError(f"unknown residue-block fields: {sorted(unknown)}")
    block.update(overrides)
    return block


# ----------------------------------------------- state-space surrogate

def bridge_run(*, carrier_hz: float, envelope_hz: float = 4096.0,
               epsilon_m: float = -2.0, gamma_rad_s: float = 1.0e12,
               modulation_depth: float = 0.1,
               witness_layer: dict | None = None) -> dict:
    """One surrogate run. The witness layer, when present, supplies
    epsilon_d and loss; the baseline without a layer uses air.

    Outputs are labeled; the SPP residual is the change of the SPP
    factor against the air baseline, an arithmetic quantity only.
    """
    if witness_layer is not None:
        problems = validate_witness_layer(witness_layer)
        if problems:
            raise ValueError(f"invalid witness layer: {problems}")
        epsilon_d = float(witness_layer["epsilon_d_estimate"])
        loss_tangent = float(witness_layer["loss_tangent_estimate"])
    else:
        epsilon_d, loss_tangent = 1.0, 0.0

    omega = 2.0 * math.pi * carrier_hz
    factor_air = spp_factor(epsilon_m, 1.0)
    factor_here = spp_factor(epsilon_m, epsilon_d)
    sidebands = [carrier_hz + n * envelope_hz for n in (-2, -1, 1, 2)]
    damping_status = ("LOSSY_LAYER_DAMPING_EXPECTED"
                      if loss_tangent > 1e-3 else "LOW_LOSS_LAYER")
    return {
        "label": "SIMULATION",
        "carrier_hz": carrier_hz,
        "envelope_hz": envelope_hz,
        "epsilon_d": epsilon_d,
        "spp_factor": factor_here,
        "spp_k_per_m": spp_k_per_m(omega, epsilon_m, epsilon_d),
        "spp_residual_vs_air": factor_here - factor_air,
        "predicted_sidebands_hz": sidebands,
        "modulation_depth": modulation_depth,
        "damping_status": damping_status,
        "witness_layer_present": witness_layer is not None,
        "claim": "STATE_SPACE_SURROGATE_NO_PHYSICAL_CLAIM",
    }


def witness_run_matrix() -> list[dict]:
    """RUN_DWL_0001..0006: one variable changes per run."""
    base_layer = {
        "layer_id": "DWL_TEMPLATE", "sample_id": "NONE",
        "medium_type": "plant_surface_film",
        "epsilon_d_estimate": 1.0, "loss_tangent_estimate": 0.0,
        "surface_conductivity_estimate": 0.0,
        "water_film_state": "unknown",
        "molecular_fingerprint_status": "unknown",
        "mineral_particle_status": "unknown",
        "Raman_available": False, "SERS_possible": False,
        "FTIR_available": False, "time_since_event_days": "unknown",
        "control_sample_id": "NONE",
        "claim_status": "SIMULATION",
    }
    runs = []
    runs.append({"run_id": "RUN_DWL_0001", "change": "baseline",
                 "result": bridge_run(carrier_hz=1.683456e6)})
    layer = dict(base_layer, layer_id="DWL_0002",
                 epsilon_d_estimate=4.0 / 3.0)
    runs.append({"run_id": "RUN_DWL_0002", "change": "epsilon_d only",
                 "result": bridge_run(carrier_hz=1.683456e6,
                                      witness_layer=layer)})
    layer = dict(base_layer, layer_id="DWL_0003",
                 loss_tangent_estimate=0.05)
    runs.append({"run_id": "RUN_DWL_0003", "change": "loss_tangent only",
                 "result": bridge_run(carrier_hz=1.683456e6,
                                      witness_layer=layer)})
    layer = dict(base_layer, layer_id="DWL_0004",
                 mineral_particle_status="iron")
    runs.append({"run_id": "RUN_DWL_0004", "change": "mineral flag only",
                 "result": bridge_run(carrier_hz=1.683456e6,
                                      witness_layer=layer)})
    layer = dict(base_layer, layer_id="DWL_0005",
                 water_film_state="present")
    runs.append({"run_id": "RUN_DWL_0005", "change": "water film only",
                 "result": bridge_run(carrier_hz=1.683456e6,
                                      witness_layer=layer)})
    layer = dict(base_layer, layer_id="DWL_0006",
                 time_since_event_days=14)
    runs.append({"run_id": "RUN_DWL_0006", "change": "decay retest only",
                 "result": bridge_run(carrier_hz=1.683456e6,
                                      witness_layer=layer)})
    return runs


# --------------------------------- SSPP corrugated-waveguide lane (V4B+)

#: Conventional anchor: Erementchouk, Joy, Mazumder 2016, spoof
#: surface plasmon polaritons on corrugated conductors. Dispersion
#: engineering only; no anomalous claim rides on the anchor.
SSPP_SOURCE = "Erementchouk, Joy, Mazumder 2016"


def sspp_period_m(outer_diameter_m: float, cells: int = 37) -> float:
    """period d = pi * OD / cells; for the bench ring this is the
    outer sector pitch (24.4535 mm at 288 mm / 37)."""
    if outer_diameter_m <= 0 or cells <= 0:
        raise ValueError("diameter and cell count must be positive")
    return math.pi * outer_diameter_m / cells


def sspp_beta_max_per_m(period_m: float) -> float:
    """Brillouin-zone edge beta_max = pi / d."""
    if period_m <= 0:
        raise ValueError("period must be positive")
    return math.pi / period_m


def sspp_plasma_frequency_hz(groove_depth_m: float,
                             epsilon_g: float = 1.0) -> float:
    """Quarter-wave asymptote f_p = c / (4 h sqrt(eps_g)). The groove
    fill dielectric lowers the asymptote; that is the witness hook."""
    if groove_depth_m <= 0:
        raise ValueError("groove depth must be positive")
    if epsilon_g <= 0:
        raise ValueError("epsilon_g must be positive")
    return C_M_PER_S / (4.0 * groove_depth_m * math.sqrt(epsilon_g))


def sspp_well_formed(groove_depth_m: float, period_m: float) -> bool:
    """Deep-groove condition h > d/2 for a well-formed SSPP band."""
    return groove_depth_m > period_m / 2.0


def sspp_lane(*, outer_diameter_m: float = 0.288, cells: int = 37,
              groove_depth_m: float = 0.014, epsilon_g: float = 1.0,
              epsilon_a: float = 1.0, t_layer_m: float = 0.0) -> dict:
    """SSPP corrugated-waveguide receipt with the dielectric layer.

    epsilon_g fills the grooves, epsilon_a is ambient above the
    surface, t_layer is a thin witness film. A non-default layer
    toggles sensitivity_status; a thin-layer mode is a measurement
    hypothesis, never causal proof.
    """
    d = sspp_period_m(outer_diameter_m, cells)
    layered = (epsilon_a != 1.0 or t_layer_m > 0.0)
    return {
        "source": SSPP_SOURCE,
        "period_m": d,
        "beta_max_per_m": sspp_beta_max_per_m(d),
        "f_p_hz": sspp_plasma_frequency_hz(groove_depth_m, epsilon_g),
        "well_formed": sspp_well_formed(groove_depth_m, d),
        "epsilon_g": epsilon_g,
        "epsilon_a": epsilon_a,
        "t_layer_m": t_layer_m,
        "sensitivity_status": ("WITNESS_SENSITIVE" if layered
                               else "BASELINE_NO_LAYER"),
        "label": "ESTIMATE",
        "claim": "THIN_LAYER_MODE_HYPOTHESIS_NOT_CAUSAL_PROOF",
    }


def nearest_family_match(frequency_hz: float) -> dict:
    """Nearest phi and RGCS keys with offsets; families reported side
    by side, never merged (near-neighbor rule from phi_ladders)."""
    phi_rows = PL.load_phi_schumann_ladder()
    nearest_phi = min(phi_rows,
                      key=lambda r: abs(r["frequency_hz"] - frequency_hz))
    rgcs_keys = {"RGCS_4096": 4096.0, "RGCS_4096_X5": 20480.0,
                 "RGCS_4096_X10": 40960.0, "RGCS_1683456": 1683456.0}
    rgcs_name, rgcs_hz = min(rgcs_keys.items(),
                             key=lambda kv: abs(kv[1] - frequency_hz))
    return {
        "frequency_hz": frequency_hz,
        "nearest_phi_n": nearest_phi["n"],
        "nearest_phi_hz": nearest_phi["frequency_hz"],
        "phi_offset_percent": PL.offset_percent(
            frequency_hz, nearest_phi["frequency_hz"]),
        "nearest_rgcs_key": rgcs_name,
        "nearest_rgcs_hz": rgcs_hz,
        "rgcs_offset_percent": PL.offset_percent(frequency_hz, rgcs_hz),
        "rule": "FAMILIES_NEVER_MERGE_WITHOUT_CORRECTION_RULE",
        "label": "ESTIMATE",
    }


__all__ = ["C_M_PER_S", "EPSILON_0", "E_CHARGE", "OUTPUT_LABELS",
           "WITNESS_CLAIM_STATUSES", "WITNESS_REQUIRED_FIELDS",
           "RESIDUE_DIELECTRIC_BLOCK_DEFAULTS", "plasma_frequency_rad_s",
           "drude_epsilon", "spp_factor", "spp_k_per_m",
           "momentum_bridge_k", "validate_witness_layer",
           "residue_dielectric_block", "bridge_run",
           "witness_run_matrix", "nearest_family_match", "SSPP_SOURCE",
           "sspp_period_m", "sspp_beta_max_per_m",
           "sspp_plasma_frequency_hz", "sspp_well_formed", "sspp_lane"]
