"""Composite modes, coherent averaging, and angular structure
(Agent R11), adapting the MATHEMATICS of the white-beam neutron
spin-echo OAM paper (065211_1_5.0321755.pdf, DOI 10.1063/5.0321755).

What transfers (coherent-sum mathematics):
- a coherent superposition of two displaced/phased partial waves has
  azimuthal mode content selected by the relative phase (parity) and
  a mode distribution controlled by separation/coherence ratio;
- azimuthal decomposition c_m = <e^{i m phi} | psi> is basis math.

What does NOT transfer (forbidden): any neutron physics, any claim
that a PCB resonator produces OAM beams, any quantum interpretation.
The transfer firewall test enforces this."""

from __future__ import annotations

import numpy as np

SOURCE = {"doi": "10.1063/5.0321755",
          "file": "065211_1_5.0321755.pdf",
          "system": "CANISIUS white-beam neutron spin-echo "
                    "interferometer",
          "allowed_transfer": "coherent-sum and azimuthal mode-"
                              "decomposition mathematics",
          "forbidden_transfer": "neutron physics; OAM beam claims "
                                "for PCB resonators; quantum "
                                "interpretation"}


def displaced_gaussian_pair(grid_n: int = 128, w: float = 1.0,
                            separation: float = 0.5,
                            rel_phase_rad: float = 0.0) -> dict:
    """psi = g(r - d/2) + e^{i phi} g(r + d/2): the paper's
    incomplete-recombination composite state, as pure wave math on a
    2-D grid."""
    x = np.linspace(-4 * w, 4 * w, grid_n)
    xx, yy = np.meshgrid(x, x)

    def g(cx):
        return np.exp(-((xx - cx) ** 2 + yy ** 2) / (2 * w * w))
    psi = g(-separation / 2) + np.exp(1j * rel_phase_rad) \
        * g(+separation / 2)
    return {"x": x, "psi": psi, "w": w, "separation": separation,
            "rel_phase_rad": rel_phase_rad}


def azimuthal_content(state: dict, m_max: int = 4) -> dict:
    """c_m via angular integration on radial shells; returns the
    normalized |c_m|^2 distribution."""
    x = state["x"]
    n = len(x)
    xx, yy = np.meshgrid(x, x)
    phi = np.arctan2(yy, xx)
    r = np.hypot(xx, yy)
    shell = (r > 0.2 * state["w"]) & (r < 3.0 * state["w"])
    psi = state["psi"]
    power = {}
    for m in range(-m_max, m_max + 1):
        cm = np.sum(psi[shell] * np.exp(-1j * m * phi[shell]))
        power[m] = abs(cm) ** 2
    total = sum(power.values()) or 1.0
    return {m: p / total for m, p in power.items()}


def parity_selection(separation: float = 0.5) -> dict:
    """The paper's key mathematical lesson: relative phase selects
    mode PARITY — phase 0 gives even m content, phase pi gives odd.
    Verified by direct computation, not asserted."""
    even_state = displaced_gaussian_pair(separation=separation,
                                         rel_phase_rad=0.0)
    odd_state = displaced_gaussian_pair(separation=separation,
                                        rel_phase_rad=np.pi)
    pe = azimuthal_content(even_state)
    po = azimuthal_content(odd_state)
    even_frac_0 = sum(v for m, v in pe.items() if m % 2 == 0)
    odd_frac_pi = sum(v for m, v in po.items() if m % 2 == 1)
    return {"even_content_at_phase_0": even_frac_0,
            "odd_content_at_phase_pi": odd_frac_pi,
            "parity_selected": bool(even_frac_0 > 0.95
                                    and odd_frac_pi > 0.95),
            "source": SOURCE["doi"]}


def separation_controls_distribution(seps=(0.2, 0.8, 2.0)) -> dict:
    """Residual separation relative to coherence width controls how
    much power leaves m=0 (the paper's second lesson)."""
    out = {}
    for s in seps:
        p = azimuthal_content(displaced_gaussian_pair(
            separation=s, rel_phase_rad=np.pi))
        out[f"{s:g}"] = {"m=+1": p[1], "m=-1": p[-1],
                         "m=0": p[0]}
    return out


def partial_resonator_array(n_partials: int, phases_rad: list,
                            amplitudes: list) -> dict:
    """Multi-partial resonator CONCEPT: n disk resonators driven with
    controlled relative phase and amplitude. The composite response is
    the coherent sum; symmetry of the drive pattern selects the
    composite azimuthal order. ENGINEERING_PROTOTYPE — a design
    concept with matched nulls, not a fabricated array."""
    if not (len(phases_rad) == len(amplitudes) == n_partials):
        raise ValueError("one phase and amplitude per partial")
    th = 2 * np.pi * np.arange(n_partials) / n_partials
    # composite order content from drive weights. With n discrete
    # partials, orders m and m+n are ALIASED (indistinguishable):
    # only the band (-n/2, n/2] is meaningful, exactly like temporal
    # Nyquist. Reporting orders outside it would double-count.
    m_lo = -(n_partials // 2) + 1
    m_hi = n_partials // 2
    c = {}
    for m in range(m_lo, m_hi + 1):
        cm = np.sum(np.asarray(amplitudes)
                    * np.exp(1j * (np.asarray(phases_rad)
                                   - m * th)))
        c[m] = abs(cm) ** 2
    tot = sum(c.values()) or 1.0
    return {"drive_order_content": {m: v / tot for m, v in c.items()},
            "alias_band": [m_lo, m_hi],
            "alias_note": f"orders m and m+{n_partials} are "
                          "indistinguishable with "
                          f"{n_partials} partials (angular Nyquist)",
            "controls": {
                "matched_null": "all phases equal -> pure m=0",
                "randomized": "shuffled phases -> broadband content",
                "rule": "a composite-order claim must beat both"},
            "status": "ENGINEERING_PROTOTYPE",
            "boundary": "this is drive-pattern mathematics; no OAM "
                        "beam and no neutron physics is claimed"}


def transfer_firewall(claim: str) -> dict:
    """Refuses forbidden transfers by keyword class; the test suite
    drives this with real attempted claims."""
    banned = ("neutron", "quantum", "oam beam", "orbital angular "
              "momentum of the board", "spin-echo hardware")
    hits = [b for b in banned if b in claim.lower()]
    return {"claim": claim, "allowed": not hits,
            "violations": hits,
            "rule": SOURCE["forbidden_transfer"]}
