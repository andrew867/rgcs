"""Exciton-cavity-photon polariton reference (Agent C01; coverage
A01-A06; material reference.exciton_magnon — REFERENCE_ONLY, never
alpha quartz).

Hopfield 2x2 (exciton + cavity photon) and 3x3 (+ magnon) models with
complex linewidths, angle dispersion, polarization and magnetic-field
channels, and an INTERFACE_ONLY quantum-transduction hook (A06/C13)."""

from __future__ import annotations

import math

import numpy as np

from ..multiphysics import applicability, get_material, make_result
from ..multiphysics import not_applicable_result

MODULE_ID = "rscs2.refmodels.polariton"


def cavity_dispersion_ev(e_c0_ev: float, theta_rad, n_eff: float
                         ) -> np.ndarray:
    """Planar-cavity photon dispersion vs in-plane angle:
    E_c(theta) = E_c0 / sqrt(1 - sin^2(theta)/n_eff^2)  (standard)."""
    s = np.sin(np.asarray(theta_rad, float)) / n_eff
    return e_c0_ev / np.sqrt(1.0 - s * s)


def hopfield_2x2(e_x_ev: float, e_c_ev: float, omega_rabi_ev: float,
                 gamma_x_ev: float = 0.0, gamma_c_ev: float = 0.0
                 ) -> dict:
    """Complex 2x2 polariton eigenproblem. Returns upper/lower
    polariton energies, linewidths, and Hopfield fractions
    (|X|^2 + |C|^2 = 1 per branch)."""
    H = np.array([[e_x_ev - 1j * gamma_x_ev / 2, omega_rabi_ev / 2],
                  [omega_rabi_ev / 2, e_c_ev - 1j * gamma_c_ev / 2]],
                 complex)
    vals, vecs = np.linalg.eig(H)
    order = np.argsort(vals.real)
    vals, vecs = vals[order], vecs[:, order]
    hop = np.abs(vecs) ** 2
    hop = hop / hop.sum(axis=0, keepdims=True)
    return {"lower_ev": vals[0].real, "upper_ev": vals[1].real,
            "lower_linewidth_ev": -2 * vals[0].imag,
            "upper_linewidth_ev": -2 * vals[1].imag,
            "splitting_ev": vals[1].real - vals[0].real,
            "hopfield_exciton_fraction": [hop[0, 0], hop[0, 1]],
            "hopfield_photon_fraction": [hop[1, 0], hop[1, 1]]}


def strong_coupling_criterion(omega_rabi_ev: float,
                              gamma_x_ev: float,
                              gamma_c_ev: float) -> dict:
    """C01 boundary rule: a splitting is only STRONG coupling when it
    exceeds the losses. Two standard criteria are reported rather than
    one, because they disagree in the intermediate regime and the
    disagreement is the honest answer:

      strict   : Omega_R > (gamma_x + gamma_c) / 2   (resolvable peaks)
      standard : Omega_R > |gamma_x - gamma_c| / 2   (real splitting of
                 the complex eigenvalues; the exceptional point)

    At zero detuning the complex 2x2 eigenvalues split in the real axis
    only when 4*(Omega_R/2)^2 > ((gamma_x-gamma_c)/2)^2, which is the
    'standard' line; the peaks are only separately observable above the
    'strict' line."""
    gx, gc = float(gamma_x_ev), float(gamma_c_ev)
    om = float(omega_rabi_ev)
    strict = om > 0.5 * (gx + gc)
    standard = om > 0.5 * abs(gx - gc)
    if strict:
        regime = "STRONG_COUPLING"
    elif standard:
        regime = "INTERMEDIATE_SPLIT_BUT_UNRESOLVED"
    else:
        regime = "WEAK_COUPLING"
    return {"omega_rabi_ev": om, "gamma_x_ev": gx, "gamma_c_ev": gc,
            "strict_criterion_met": bool(strict),
            "standard_criterion_met": bool(standard),
            "cooperativity": om * om / max(gx * gc, 1e-300),
            "regime": regime,
            "rule": "no strong-coupling claim without comparing the "
                    "splitting to the linewidths (C01 boundary)"}


def polariton_dispersion(material_id: str, e_x_ev: float,
                         e_c0_ev: float, omega_rabi_ev: float,
                         n_eff: float, theta_deg: np.ndarray,
                         gamma_x_ev: float = 0.0,
                         gamma_c_ev: float = 0.0) -> dict:
    """Capability-gated angle dispersion sweep (A03)."""
    mat = get_material(material_id)
    app = applicability(mat, "exciton_frenkel")
    if app["applicability"] == "NOT_APPLICABLE":
        return not_applicable_result(MODULE_ID, material_id,
                                     app["reason_code"], app["reason"])
    th = np.radians(np.asarray(theta_deg, float))
    ec = cavity_dispersion_ev(e_c0_ev, th, n_eff)
    lo, up, split = [], [], []
    for e in ec:
        out = hopfield_2x2(e_x_ev, float(e), omega_rabi_ev,
                           gamma_x_ev, gamma_c_ev)
        lo.append(out["lower_ev"])
        up.append(out["upper_ev"])
        split.append(out["splitting_ev"])
    return make_result(
        MODULE_ID, material_id, "REDUCED_ORDER_VALIDATED",
        ["DER", "EST"],
        {"min_splitting_ev": float(np.min(split)),
         "rabi_input_ev": omega_rabi_ev},
        {"energy": "eV", "angle": "deg"},
        source_ids=["SRC-V4-06"],
        assumptions=["Hopfield reduced model; no BSE/microscopic "
                     "content; separate reference system, never "
                     "alpha quartz"]) | {
        "theta_deg": np.asarray(theta_deg, float),
        "cavity_ev": ec, "lower_ev": np.array(lo),
        "upper_ev": np.array(up), "splitting_ev": np.array(split)}


def hopfield_3x3(e_x_ev: float, e_c_ev: float, e_m_ev: float,
                 omega_xc_ev: float, omega_xm_ev: float,
                 b_field_t: float = 0.0,
                 magnon_shift_ev_per_t: float = 0.0) -> dict:
    """Magnon-polariton third-mode extension (A04): the magnon level
    shifts linearly with B (declared Zeeman channel, A05)."""
    em = e_m_ev + magnon_shift_ev_per_t * b_field_t
    H = np.array([[e_x_ev, omega_xc_ev / 2, omega_xm_ev / 2],
                  [omega_xc_ev / 2, e_c_ev, 0.0],
                  [omega_xm_ev / 2, 0.0, em]], float)
    vals, vecs = np.linalg.eigh(H)
    frac = vecs ** 2
    return {"branches_ev": vals.tolist(),
            "magnon_level_ev": em,
            "fractions": frac.tolist()}


def polarization_channel(omega_rabi_ev: float, theta_rad: float,
                         mode: str) -> float:
    """Declared TE/TM coupling rule (A05): TE couples fully; TM
    scales by cos(theta) (field-projection ENG rule, stated)."""
    if mode == "TE":
        return omega_rabi_ev
    if mode == "TM":
        return omega_rabi_ev * math.cos(theta_rad)
    raise ValueError("mode must be TE|TM")


def transduction_interface(material_id: str) -> dict:
    """A06: quantum-transduction hook — INTERFACE_ONLY, no photon
    conversion computation is implemented or implied (C13)."""
    get_material(material_id)
    return {"classification": "INTERFACE_ONLY",
            "evidence_tags": ["ENG"],
            "module_id": MODULE_ID + ".transduction",
            "value": None,
            "declares": ["input mode (polariton branch, Hopfield "
                         "fractions)", "output mode (itinerant "
                         "photon)", "efficiency: NOT COMPUTED"],
            "note": "schema hook for a future microscopic "
                    "transduction solver; emits no numbers"}
