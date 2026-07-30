"""R10.25 Agent 01 — compression-node solver.

The open source phrases were "compression node", "phase-conjugation
node", "frequency key shot at the node". Only the first is a defined
acoustic quantity, and it is computed here. The other two are NOT
given a solver, because naming a thing does not make it measurable.

PHYSICS (free-free slender bar, 1-D):

    displacement   u(x)      ~ cos(n*pi*x/L)
    strain/stress  du/dx     ~ sin(n*pi*x/L)

so for a free-free bar the DISPLACEMENT NODES and the STRESS ANTINODES
are the same points:

    x_k = L*(2k+1)/(2n),   k = 0 .. n-1

That coincidence is the whole content of "compression node": the place
that moves least is the place under greatest alternating compression.
It is therefore simultaneously

  * the correct MOUNTING point (minimum radiated/clamp loss), and
  * the correct PIEZO PICKUP / DRIVE point (maximum stress coupling).

Those two facts are what make the phrase operationally meaningful. No
claim is made about phase conjugation, harvesting, or transponding.

Evidence class: DERIVED (analytic 1-D model). This is a slender-bar
approximation; it is NOT a substitute for the anisotropic FEM in
``r1013.fem_api`` and never reports a measurement.
"""

from __future__ import annotations

import math

#: Scale A mechanical crystal, from R10.15A.
SCALE_A_LENGTH_MM = 463.8671875
SCALE_A_SHEAR_HZ = 4096.0


class NodeError(ValueError):
    pass


def compression_nodes_mm(length_mm: float, mode_n: int) -> list:
    """Displacement nodes == stress antinodes, free-free bar, mode n."""
    if length_mm <= 0:
        raise NodeError("length must be positive")
    if mode_n < 1:
        raise NodeError("mode index starts at 1")
    return [length_mm * (2 * k + 1) / (2 * mode_n) for k in range(mode_n)]


def displacement_antinodes_mm(length_mm: float, mode_n: int) -> list:
    """Free ends plus interior maxima: where motion is greatest."""
    if mode_n < 1:
        raise NodeError("mode index starts at 1")
    return [length_mm * k / mode_n for k in range(mode_n + 1)]


def half_wave_speed_m_s(length_mm: float, freq_hz: float) -> float:
    """Wave speed implied by a half-wave fit. Arithmetic, not a claim."""
    return 2.0 * (length_mm / 1000.0) * freq_hz


def node_report(length_mm: float, freq_hz: float, modes=(1, 2, 3, 4, 5)) -> dict:
    rows = []
    for n in modes:
        nodes = compression_nodes_mm(length_mm, n)
        rows.append({
            "mode_n": n,
            "frequency_hz": freq_hz * n,
            "compression_nodes_mm": [round(x, 4) for x in nodes],
            "displacement_antinodes_mm":
                [round(x, 4) for x in displacement_antinodes_mm(length_mm, n)],
            "recommended_mount_mm": round(nodes[0], 4),
            "recommended_pickup_mm": round(nodes[0], 4),
            "node_count": len(nodes),
        })
    return {
        "schema": "rgcs.r1025.compression-nodes.v1",
        "length_mm": length_mm,
        "fundamental_hz": freq_hz,
        "implied_half_wave_speed_m_s": round(
            half_wave_speed_m_s(length_mm, freq_hz), 3),
        "rows": rows,
        "identity": "for a free-free bar the displacement nodes and the "
                    "stress antinodes coincide; that is what makes a "
                    "compression node both the low-loss mount point and "
                    "the high-coupling drive/pickup point",
        "model": "SLENDER_BAR_1D_ANALYTIC",
        "not_a_measurement": True,
        "phase_conjugation_node": "NOT_SOLVED_NOT_DEFINED_AS_A_MEASURABLE",
    }


def scale_a_report() -> dict:
    r = node_report(SCALE_A_LENGTH_MM, SCALE_A_SHEAR_HZ)
    r["specimen"] = "SCALE_A_MECHANICAL_CRYSTAL_R10_15A"
    r["note"] = ("Scale A is the MECHANICAL lane. 4096 Hz is a shear "
                 "half-wave here and must never become an "
                 "electromagnetic carrier without a new geometry, a new "
                 "eigenproblem, holdout criteria and an explicit result.")
    return r
