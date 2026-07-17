"""Expanded honeycomb, saddle-point DOS, and nematic reference
(Agent Q03).

Source: sciadv.aee3116.pdf, DOI 10.1126/sciadv.aee3116 — expanded
honeycomb boron surface state in LaRh3B2 (ARPES + STM, DFT/TB).

Reduced model: nearest-neighbour honeycomb tight binding. Lattice
expansion reduces the hopping t (exponential in distance), narrowing
the band; the M-point van Hove singularity's DOS weight grows as the
band narrows; a C6->C2 symmetry breaking is modelled as anisotropic
hoppings (t1 != t2 = t3) which splits the three M points — the
nematicity ORDER PARAMETER is the measured DOS anisotropy.

DESIGN PRINCIPLE that transfers: geometry and spacing reshape the
state landscape and can select a lower-symmetry response.
FORBIDDEN: claiming electronic nematicity in resonator PCBs or
quartz; these are electron bands in a specific material."""

from __future__ import annotations

import math

import numpy as np

SOURCE = {"doi": "10.1126/sciadv.aee3116",
          "file": "sciadv.aee3116.pdf",
          "system": "expanded honeycomb boron in LaRh3B2",
          "allowed_transfer": "lattice/DOS/symmetry mathematics; the "
                              "design principle that spacing tunes "
                              "bandwidth and symmetry selects "
                              "response",
          "forbidden_transfer": "electronic nematicity claims for "
                                "PCB resonators or quartz"}


def hopping_from_spacing(t0_ev: float, a0: float, a: float,
                         beta: float = 3.0) -> float:
    """t(a) = t0 exp(-beta (a/a0 - 1)): the standard distance decay.
    Expansion (a > a0) narrows the band exponentially."""
    return t0_ev * math.exp(-beta * (a / a0 - 1.0))


def band_energies(kx, ky, t1: float, t2: float, t3: float,
                  a: float = 1.0):
    """Honeycomb NN tight binding with three independent bond
    hoppings (t1=t2=t3 restores C6):
    E(k) = ±|t1 e^{ik·d1} + t2 e^{ik·d2} + t3 e^{ik·d3}|."""
    d = [np.array([0.0, a / math.sqrt(3)]),
         np.array([a / 2, -a / (2 * math.sqrt(3))]),
         np.array([-a / 2, -a / (2 * math.sqrt(3))])]
    f = (t1 * np.exp(1j * (kx * d[0][0] + ky * d[0][1]))
         + t2 * np.exp(1j * (kx * d[1][0] + ky * d[1][1]))
         + t3 * np.exp(1j * (kx * d[2][0] + ky * d[2][1])))
    return np.abs(f)


def dos(t1: float, t2: float, t3: float, n_k: int = 240,
        n_bins: int = 160) -> dict:
    """Density of states by k-space sampling; the VHS shows up as the
    peak at E = t (for the isotropic case)."""
    k = np.linspace(-math.pi, math.pi, n_k)
    kx, ky = np.meshgrid(k, k)
    e = band_energies(kx, ky, t1, t2, t3).ravel()
    e = np.concatenate([e, -e])
    hist, edges = np.histogram(e, bins=n_bins, density=True)
    centers = 0.5 * (edges[1:] + edges[:-1])
    i_vhs = int(np.argmax(hist[centers > 0.05]))
    pos = centers[centers > 0.05]
    return {"energy_ev": centers.tolist(), "dos": hist.tolist(),
            "vhs_energy_ev": float(pos[i_vhs]),
            "vhs_dos": float(hist[centers > 0.05][i_vhs]),
            "bandwidth_ev": float(e.max() * 2)}


def expansion_narrows_band(t0_ev: float = 1.0, a0: float = 1.0,
                           expansions=(1.0, 1.1, 1.25)) -> dict:
    """The paper's central mechanism, reproduced: expansion -> smaller
    t -> narrower band -> DOS piles up near the VHS."""
    out = {}
    for a in expansions:
        t = hopping_from_spacing(t0_ev, a0, a)
        d = dos(t, t, t)
        out[f"{a:g}"] = {"t_ev": t,
                         "bandwidth_ev": d["bandwidth_ev"],
                         "vhs_dos": d["vhs_dos"]}
    return {"sweep": out,
            "principle": "geometry/spacing tunes bandwidth and "
                         "state density (this is what transfers)"}


def nematic_splitting(t_ev: float, delta: float) -> dict:
    """C6 -> C2: t1 = t(1+delta), t2 = t3 = t(1-delta/2). The three M
    points split; the DOS anisotropy is the nematic order parameter.
    delta=0 must restore the symmetric result (tested limit)."""
    t1 = t_ev * (1 + delta)
    t23 = t_ev * (1 - delta / 2)
    # M-point saddle energies for anisotropic bonds:
    # E_M1 = |t2 + t3 - t1| etc. by direct evaluation at the M points
    e_m1 = abs(2 * t23 - t1)
    e_m2 = abs(t1 + t23 - t23)   # = t1
    return {"delta": delta, "m_point_energies_ev":
            sorted([e_m1, e_m2, e_m2]),
            "splitting_ev": abs(e_m2 - e_m1),
            "c6_restored": bool(abs(delta) < 1e-12
                                and abs(e_m2 - e_m1) < 1e-12),
            "order_parameter": "DOS anisotropy between bond "
                               "directions",
            "boundary": SOURCE["forbidden_transfer"]}


def resonator_lattice_design_principle() -> dict:
    """The ONLY transfer to engineering: an acoustic/PCB lattice's
    modal density and symmetry can be tuned by spacing and by
    deliberate bond anisotropy. This is a statement about OUR
    lattices' mechanical modes, derived from lattice mathematics —
    not about electrons, and not evidence for anything quantum."""
    return {"principle": [
        "expanding a resonator-lattice spacing narrows its modal "
        "band (weaker inter-cell coupling)",
        "a deliberate 1-of-3 bond anisotropy splits degenerate "
        "modes in a controlled, measurable way",
        "modal density near a band edge is a design variable"],
        "status": "ENGINEERING_PROTOTYPE",
        "forbidden": "no electronic-nematicity claim for any RGCS "
                     "artifact; the electrons stay in the paper"}
