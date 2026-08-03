"""Brown-compatible annular asymmetry proxy, v0.6.

Distinguishes three electrode configurations on a numerical grid:

  * centered annular electrode (symmetric 37 ring);
  * off-center inner electrode;
  * 37-cell electronic displacement via a mask.

Method: Laplace relaxation for the potential on a square grid with fixed
electrode potentials, finite-difference E-field, energy-density map
u = eps0/2 * |E|^2, and a vector asymmetry proxy

    A_vec = integral( u * r_hat ) dA

which is a WEIGHTED DIRECTION OF FIELD ENERGY, not a force. The Maxwell
stress on a closed boundary in vacuum electrostatics with no free charge
between the electrodes integrates against the mounts, and nothing here
computes momentum flux to a body. Every output is MODEL_OUTPUT or
PRIOR_ART_ANALOGUE; no thrust claim is available from this module by
construction (there is no function that returns a force).
"""

from __future__ import annotations

import math

EPS0 = 8.8541878128e-12


def _grid(n: int) -> list:
    return [[0.0] * n for _ in range(n)]


def _electrode_masks(n: int, outer_r: float, inner_r: float,
                     inner_dx: float = 0.0, cell_mask=None,
                     n_cells: int = 37, cell_weights=None):
    """Boolean maps of fixed-potential sites.

    The outer annulus sits at radius ``outer_r`` (grid units, centre
    origin); the inner disc at ``inner_r`` displaced by ``inner_dx``.
    ``cell_mask`` blanks angular sectors of the OUTER ring -- the
    electronic-displacement configuration.
    """
    c = (n - 1) / 2.0
    ring = _grid(n)
    disc = _grid(n)
    band = max(1.5, n / 40.0)
    for j in range(n):
        for i in range(n):
            x, y = i - c, j - c
            r = math.hypot(x, y)
            if abs(r - outer_r) <= band:
                k = int((math.atan2(y, x) % (2 * math.pi))
                        / (2 * math.pi) * n_cells) % n_cells
                if cell_weights is not None:
                    # v0.7 upgrade: graded per-sector drive. The ring
                    # site carries a WEIGHT, applied to the electrode
                    # potential, so a taper is a real boundary condition
                    # rather than a post-hoc scaling.
                    ring[j][i] = float(cell_weights[k])
                else:
                    keep = True
                    if cell_mask is not None:
                        keep = bool(cell_mask[k])
                    ring[j][i] = 1.0 if keep else 0.0
            if math.hypot(x - inner_dx, y) <= inner_r:
                disc[j][i] = 1.0
    return ring, disc


def solve_potential(n: int, outer_r: float, inner_r: float,
                    v_ring: float, v_disc: float, inner_dx: float = 0.0,
                    cell_mask=None, iters: int = 1500,
                    cell_weights=None) -> list:
    """Gauss-Seidel Laplace relaxation with fixed electrode potentials.

    With ``cell_weights`` the outer-ring potential is v_ring * w_k per
    angular sector (v0.7 graded-drive upgrade); zero-weight sectors are
    open (not fixed at zero volts).
    """
    ring, disc = _electrode_masks(n, outer_r, inner_r, inner_dx,
                                  cell_mask, cell_weights=cell_weights)
    v = _grid(n)
    fixed = _grid(n)
    for j in range(n):
        for i in range(n):
            if ring[j][i]:
                v[j][i], fixed[j][i] = v_ring * ring[j][i], 1.0
            elif disc[j][i]:
                v[j][i], fixed[j][i] = v_disc, 1.0
    for _ in range(iters):
        for j in range(1, n - 1):
            row, up, dn = v[j], v[j - 1], v[j + 1]
            fx = fixed[j]
            for i in range(1, n - 1):
                if not fx[i]:
                    row[i] = 0.25 * (row[i - 1] + row[i + 1]
                                     + up[i] + dn[i])
    return v


def field_and_energy(v: list) -> tuple:
    """Central-difference E = -grad(V) and u = eps0/2 |E|^2."""
    n = len(v)
    ex, ey, u = _grid(n), _grid(n), _grid(n)
    for j in range(1, n - 1):
        for i in range(1, n - 1):
            ex[j][i] = -(v[j][i + 1] - v[j][i - 1]) / 2.0
            ey[j][i] = -(v[j + 1][i] - v[j - 1][i]) / 2.0
            u[j][i] = 0.5 * EPS0 * (ex[j][i] ** 2 + ey[j][i] ** 2)
    return ex, ey, u


def asymmetry_proxy(u: list) -> dict:
    """Energy-weighted direction: sum(u * r_hat) over the grid.

    A DIRECTION PROXY. Scalar magnitude normalised by total energy so
    configurations of different stored energy are comparable.
    """
    n = len(u)
    c = (n - 1) / 2.0
    sx = sy = tot = 0.0
    for j in range(n):
        for i in range(n):
            w = u[j][i]
            if w <= 0.0:
                continue
            x, y = i - c, j - c
            r = math.hypot(x, y)
            if r < 1e-9:
                continue
            sx += w * x / r
            sy += w * y / r
            tot += w
    mag = math.hypot(sx, sy) / tot if tot else 0.0
    ang = math.degrees(math.atan2(sy, sx)) % 360.0 if mag > 1e-12 else None
    return {"asymmetry_scalar": mag, "direction_deg": ang,
            "total_energy_proxy": tot,
            "claim": "MODEL_OUTPUT",
            "is_a_force": False,
            "note": "energy-density direction proxy; no thrust claim"}


def compare_configurations(n: int = 61, outer_r: float = 24.0,
                           inner_r: float = 6.0, v_ring: float = 1.0,
                           v_disc: float = -1.0,
                           displacement: float = 8.0,
                           cell_mask=None, iters: int = 1500) -> dict:
    """Centered vs off-center vs masked, one deterministic pass."""
    out = {}
    cases = {
        "centered_symmetric": dict(inner_dx=0.0, cell_mask=None),
        "off_center_inner": dict(inner_dx=displacement, cell_mask=None),
        "masked_37_cells": dict(inner_dx=0.0, cell_mask=cell_mask),
    }
    for name, kw in cases.items():
        v = solve_potential(n, outer_r, inner_r, v_ring, v_disc,
                            iters=iters, **kw)
        _ex, _ey, u = field_and_energy(v)
        out[name] = asymmetry_proxy(u)
    out["claim"] = "PRIOR_ART_ANALOGUE"
    out["comparison"] = {
        "centered_lt_offcenter": (out["centered_symmetric"]["asymmetry_scalar"]
                                  < out["off_center_inner"]["asymmetry_scalar"]),
    }
    return out


__all__ = ["EPS0", "solve_potential", "field_and_energy",
           "asymmetry_proxy", "compare_configurations"]
