"""Spin-orbit-exciton / phonon avoided-crossing reference (Agent M4;
RGCS-V4-EQ-005; material reference.soe_phonon).

Two- and three-mode Hamiltonians with complex poles (linewidths),
hybridization fractions, and uncertainty propagation. The lossless
two-mode case MUST reproduce the FROZEN v3 coupled_two_mode."""

from __future__ import annotations

import numpy as np

from ..multiphysics import applicability, get_material, make_result
from ..multiphysics import not_applicable_result

MODULE_ID = "rscs2.refmodels.avoided_crossing"


def poles(freqs_hz, couplings_hz, linewidths_hz=None) -> dict:
    """Complex eigenpoles of the mode matrix
    H_ii = f_i - i*gamma_i/2, H_ij = g_ij (Hz units).
    Returns poles (complex Hz), participation |v|^2 per mode."""
    f = np.asarray(freqs_hz, float)
    n = len(f)
    g = np.asarray(couplings_hz, float)
    if g.shape != (n, n):
        raise ValueError("couplings must be an (n,n) matrix")
    if not np.allclose(g, g.T):
        raise ValueError("coupling matrix must be symmetric")
    gam = np.zeros(n) if linewidths_hz is None \
        else np.asarray(linewidths_hz, float)
    H = g.astype(complex)
    np.fill_diagonal(H, f - 1j * gam / 2.0)
    vals, vecs = np.linalg.eig(H)
    order = np.argsort(vals.real)
    vals, vecs = vals[order], vecs[:, order]
    part = np.abs(vecs) ** 2
    part = part / part.sum(axis=0, keepdims=True)
    return {"poles_hz": vals, "participation": part}


def two_mode(material_id: str, fa_hz: float, fb_hz: float, g_hz: float,
             gamma_a_hz: float = 0.0, gamma_b_hz: float = 0.0) -> dict:
    """Capability-gated two-mode hybridization. Lossless limit anchors
    the FROZEN rgcs_core coupled_two_mode (tested)."""
    mat = get_material(material_id)
    app = applicability(mat, "spin_orbit_coupling")
    if app["applicability"] == "NOT_APPLICABLE":
        return not_applicable_result(MODULE_ID, material_id,
                                     app["reason_code"], app["reason"])
    out = poles([fa_hz, fb_hz],
                np.array([[0.0, g_hz], [g_hz, 0.0]]),
                [gamma_a_hz, gamma_b_hz])
    lo, hi = out["poles_hz"]
    return make_result(
        MODULE_ID, material_id, "REDUCED_ORDER_VALIDATED",
        ["DER", "EST"],
        {"lower_hz": lo.real, "upper_hz": hi.real,
         "lower_linewidth_hz": -2 * lo.imag,
         "upper_linewidth_hz": -2 * hi.imag,
         "splitting_hz": hi.real - lo.real,
         "participation": out["participation"].tolist()},
        {"frequency": "Hz", "linewidth": "Hz (FWHM)"},
        source_ids=["SRC-V4-13"], equation_ids=["RGCS-V4-EQ-005"],
        assumptions=["reduced two-mode Hamiltonian; anchors frozen "
                     "RSCS-O.4 in the lossless limit"])


def detuning_sweep(fa_hz: np.ndarray, fb_hz: float, g_hz: float,
                   gamma_a_hz: float = 0.0,
                   gamma_b_hz: float = 0.0) -> dict:
    lo, hi, plo = [], [], []
    for fa in np.asarray(fa_hz, float):
        out = poles([fa, fb_hz], np.array([[0, g_hz], [g_hz, 0]]),
                    [gamma_a_hz, gamma_b_hz])
        lo.append(out["poles_hz"][0])
        hi.append(out["poles_hz"][1])
        plo.append(out["participation"][0, 0])
    return {"fa_hz": np.asarray(fa_hz, float),
            "lower": np.array(lo), "upper": np.array(hi),
            "participation_a_in_lower": np.array(plo)}


def splitting_uncertainty(fa_hz: float, fb_hz: float, g_hz: float,
                          sigma: dict, rel_step: float = 1e-6) -> dict:
    """First-order uncertainty on the splitting from parameter sigmas
    {fa, fb, g} via central finite-difference Jacobian."""
    def split(fa, fb, g):
        p = poles([fa, fb], np.array([[0, g], [g, 0]]))["poles_hz"]
        return float(p[1].real - p[0].real)
    s0 = split(fa_hz, fb_hz, g_hz)
    var = 0.0
    jac = {}
    for name, val, sig in (("fa", fa_hz, sigma.get("fa", 0.0)),
                           ("fb", fb_hz, sigma.get("fb", 0.0)),
                           ("g", g_hz, sigma.get("g", 0.0))):
        h = max(abs(val) * rel_step, 1e-9)
        args = {"fa": fa_hz, "fb": fb_hz, "g": g_hz}
        ap, am = dict(args), dict(args)
        ap[name] += h
        am[name] -= h
        d = (split(**ap) - split(**am)) / (2 * h)
        jac[name] = d
        var += (d * sig) ** 2
    return {"splitting_hz": s0, "sigma_splitting_hz": var ** 0.5,
            "jacobian": jac}
