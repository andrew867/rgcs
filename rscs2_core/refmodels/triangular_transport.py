"""Triangular many-body transport reference (Agent Q02).

Source: s41467-026-75051-3_reference.pdf (article in press),
DOI 10.1038/s41467-026-75051-3 — TBTAP trimers/hexamers on Pb(111),
three-impurity Anderson model + Pauli master-equation transport.

Reduced model here: three sites, each empty/occupied (8 states),
on-site energies with inter-site Coulomb V, tip/substrate tunneling
via a Pauli master equation. It reproduces the paper's central
distinction QUALITATIVELY: features in the spatial response that come
from INTERNAL CHARGE REARRANGEMENT at constant total charge, versus
features from total-charge changes — plus population trapping and
negative differential conductance (NDC).

SOURCE SYSTEM: molecular assemblies at cryogenic STM conditions.
FORBIDDEN: transferring 'charging rings' or NDC to PCB resonators or
quartz; the classification vocabulary transfers, the physics does
not."""

from __future__ import annotations

import itertools

import numpy as np

SOURCE = {"doi": "10.1038/s41467-026-75051-3",
          "file": "s41467-026-75051-3_reference.pdf",
          "publication_state": "article in press (unedited "
                               "manuscript in the supplied file)",
          "system": "TBTAP trimers/hexamers on Pb(111), STM",
          "allowed_transfer": "master-equation bookkeeping; the "
                              "total-change vs redistribution vs "
                              "trapping vs transfer-function "
                              "classification",
          "forbidden_transfer": "charging physics to PCB/quartz"}

STATES = list(itertools.product((0, 1), repeat=3))   # 8 basis states


def state_energy(occ, eps, v_inter: float) -> float:
    """E = sum eps_i n_i + V * sum_{i<j} n_i n_j (triangle: all pairs
    interact equally)."""
    e = sum(eps[i] * occ[i] for i in range(3))
    pairs = occ[0] * occ[1] + occ[0] * occ[2] + occ[1] * occ[2]
    return e + v_inter * pairs


def rates(eps, v_inter, bias, site_couplings, kt: float = 0.02):
    """Pauli master-equation rates between states differing by one
    electron on one site. Tip adds electrons when the addition energy
    is below the bias window (Fermi factors at temperature kt)."""
    n = len(STATES)
    w = np.zeros((n, n))
    for a, sa in enumerate(STATES):
        for i in range(3):
            sb = list(sa)
            sb[i] ^= 1
            b = STATES.index(tuple(sb))
            de = state_energy(STATES[b], eps, v_inter) - \
                state_energy(sa, eps, v_inter)
            gamma = site_couplings[i]
            if sb[i] == 1:      # addition, driven by the tip at bias
                f = 1.0 / (1.0 + np.exp((de - bias) / kt))
            else:
                # removal to the substrate (mu = 0): the electron
                # leaves when its energy eps = E(a) - E(b) = -de sits
                # ABOVE the substrate Fermi level, i.e. rate ~
                # 1 - f_FD(eps) = 1/(1 + exp(-eps/kt))
                #              = 1/(1 + exp(+de/kt))
                f = 1.0 / (1.0 + np.exp(de / kt))
            w[b, a] += gamma * f
    return w


def steady_state(w: np.ndarray) -> np.ndarray:
    a = w.copy()
    np.fill_diagonal(a, 0.0)
    a = a - np.diag(a.sum(axis=0))
    m = np.vstack([a, np.ones(len(STATES))])
    rhs = np.zeros(len(STATES) + 1)
    rhs[-1] = 1.0
    p, *_ = np.linalg.lstsq(m, rhs, rcond=None)
    return np.clip(p, 0.0, None) / max(p.sum(), 1e-300)


def observables(eps, v_inter, bias, site_couplings) -> dict:
    w = rates(eps, v_inter, bias, site_couplings)
    p = steady_state(w)
    occ = np.zeros(3)
    for k, s in enumerate(STATES):
        occ += p[k] * np.asarray(s)
    total = float(occ.sum())
    current = float(sum(
        w[b, a] * p[a]
        for a, sa in enumerate(STATES)
        for i in range(3)
        for b in [STATES.index(tuple(
            sa[:i] + ((sa[i] ^ 1),) + sa[i + 1:]))]
        if STATES[b][i] == 1))
    return {"site_occupations": occ.tolist(),
            "total_charge": total, "current_au": current,
            "state_probabilities": p.tolist()}


def classify_feature(occ_before, occ_after,
                     tol: float = 0.05) -> str:
    """The paper's central classification (its engineering lesson):
    a spatial-response feature is one of

    - TOTAL_CHANGE: total charge moved by >= tol;
    - REDISTRIBUTION: total constant, but site occupations moved;
    - NO_CHANGE: neither (the feature is a transfer-function effect
      of the measurement, not of the cluster state)."""
    b, a = np.asarray(occ_before), np.asarray(occ_after)
    d_total = abs(a.sum() - b.sum())
    d_sites = np.abs(a - b).max()
    if d_total >= tol:
        return "TOTAL_CHANGE"
    if d_sites >= tol:
        return "REDISTRIBUTION"
    return "NO_CHANGE_TRANSFER_FUNCTION_CANDIDATE"


def bias_sweep(eps, v_inter, biases, site_couplings) -> dict:
    """Sweep bias; report current, dI/dV, and any NDC regions.
    Asymmetric site couplings + inter-site Coulomb produce population
    trapping and NDC qualitatively, as in the paper."""
    cur = [observables(eps, v_inter, b, site_couplings)["current_au"]
           for b in biases]
    cur = np.asarray(cur)
    didv = np.gradient(cur, biases)
    return {"bias": list(biases), "current_au": cur.tolist(),
            "didv": didv.tolist(),
            "ndc_present": bool((didv < -1e-6).any()),
            "note": "QUALITATIVE reproduction only; no fit to the "
                    "paper's data is claimed"}
