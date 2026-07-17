"""Additive-manufactured macro resonators (Agent R08; R057-R066 band).

Process/material cards for FDM, SLA, SLS, ceramic, and printed-silica
resonators, with scaling laws and the loss terms that dominate each
process. Two boundaries are enforced in code:

- **Printed fused silica is NOT crystalline quartz.** It is amorphous,
  it has no piezoelectric tensor, and any attempt to register a
  printed-silica part as 'quartz' raises.
- Everything here is a design card; nothing has been printed.
"""

from __future__ import annotations

import math


class AdditiveError(RuntimeError):
    pass


# process: (E_pa, rho_kg_m3, typical_Q, anisotropy, min_feature_mm,
#           dominant losses)
PROCESS_CARDS = {
    "FDM_PLA": dict(E_pa=3.5e9, rho=1240.0, q_typ=40,
                    anisotropic=True, min_feature_mm=0.8,
                    losses=["viscoelastic (dominant)",
                            "layer-interface friction",
                            "infill-dependent damping"]),
    "FDM_PETG": dict(E_pa=2.1e9, rho=1270.0, q_typ=30,
                     anisotropic=True, min_feature_mm=0.8,
                     losses=["viscoelastic (worse than PLA)"]),
    "SLA_resin": dict(E_pa=2.8e9, rho=1180.0, q_typ=60,
                      anisotropic=False, min_feature_mm=0.2,
                      losses=["viscoelastic", "cure-state dependent",
                              "moisture uptake"]),
    "SLS_nylon": dict(E_pa=1.7e9, rho=950.0, q_typ=35,
                      anisotropic=True, min_feature_mm=0.6,
                      losses=["porosity friction", "viscoelastic"]),
    "ceramic_print": dict(E_pa=200e9, rho=3900.0, q_typ=800,
                          anisotropic=False, min_feature_mm=0.4,
                          losses=["grain-boundary",
                                  "sinter porosity"]),
    "printed_silica": dict(E_pa=72e9, rho=2200.0, q_typ=5000,
                           anisotropic=False, min_feature_mm=0.3,
                           losses=["surface", "residual porosity"]),
}


def process_card(process: str) -> dict:
    if process not in PROCESS_CARDS:
        raise AdditiveError(f"unknown process {process}")
    c = dict(PROCESS_CARDS[process])
    c["process"] = process
    c["record"] = ["print scale", "orientation", "layer height",
                   "infill", "cure schedule", "as-built mass",
                   "surface finish", "dimensional inspection"]
    c["status"] = "ENGINEERING_PROTOTYPE — nothing printed"
    if process == "printed_silica":
        c["material_boundary"] = (
            "printed fused silica is AMORPHOUS SiO2: not crystalline "
            "quartz, no piezoelectric tensor, no crystallographic "
            "axes. It is a geometry and low-loss reference, never a "
            "quartz surrogate.")
    else:
        c["material_boundary"] = ("polymer/ceramic parts are geometry "
                                  "references, not quartz dynamical "
                                  "surrogates")
    return c


def register_material(name: str, is_crystalline_quartz: bool,
                      process: str) -> dict:
    """The silica/quartz distinction, enforced (printed gates)."""
    if is_crystalline_quartz and process in PROCESS_CARDS:
        raise AdditiveError(
            "no additive process in this registry produces "
            "crystalline quartz; a printed part cannot be registered "
            "as quartz (R08 boundary)")
    return {"name": name, "process": process,
            "is_crystalline_quartz": False,
            "card": process_card(process)}


def beam_f1_hz(process: str, length_m: float, thickness_m: float
               ) -> dict:
    """First flexural mode of a printed cantilever test beam:
    f1 = (1.875^2 / 2 pi) * sqrt(E I / (rho A)) / L^2, rectangular
    section => f1 = 0.1615 * t/L^2 * sqrt(E/rho). The cheap first
    experiment for any process card."""
    c = PROCESS_CARDS[process]
    f1 = 0.1615 * thickness_m / length_m ** 2 * \
        math.sqrt(c["E_pa"] / c["rho"])
    return {"process": process, "f1_hz": f1,
            "expected_q": c["q_typ"],
            "anisotropy_warning": c["anisotropic"],
            "note": "prediction from the card; as-built parts WILL "
                    "deviate (record the deviation, do not adjust "
                    "the card silently)"}


def print_campaign_plan() -> dict:
    """The staged macro-resonator campaign: cheapest process first,
    every part inspected before use, trim experiments on FDM before
    anything precious."""
    return {"stages": [
        {"n": 1, "process": "FDM_PLA",
         "part": "cantilever beam set (5 lengths)",
         "purpose": "process-card calibration; sanding-based trim "
                    "practice (bidirectional: sand=remove, "
                    "epoxy=add)"},
        {"n": 2, "process": "FDM_PLA", "part": "disk, trim tabs",
         "purpose": "full closed-loop dry run at zero material cost"},
        {"n": 3, "process": "SLA_resin", "part": "disk",
         "purpose": "finer features, isotropy check"},
        {"n": 4, "process": "ceramic_print", "part": "disk",
         "purpose": "first meaningful-Q resonator"},
        {"n": 5, "process": "printed_silica", "part": "disk",
         "purpose": "low-loss reference; NOT quartz"}],
        "status": "PROTOCOL_READY_HARDWARE_REQUIRED",
        "blocker": "no printer access has been engaged; costs and "
                   "vendors are a human decision"}
