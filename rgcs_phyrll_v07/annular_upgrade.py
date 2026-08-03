"""Brown annular proxy upgrade, v0.7.

Adds the third configuration the correction asks for -- WEIGHTED mask
displacement (graded per-sector drive as a real boundary condition) --
and reports every electronic option as a RATIO to the physical
off-centre case, which is the honest yardstick.

Centered must stay 0. No force function exists here or in the v0.6 proxy
it builds on.
"""

from __future__ import annotations

import math

from rgcs_phyrll_v06 import brown_annular_proxy as B
from rgcs_phyrll_v06 import ring37 as R


def _weights_graded(depth: float = 0.85, width: float = 4.0,
                    blanks=(0, 1, 2, 3), n_cells: int = 37) -> list:
    """Blanked sector open; neighbouring actives tapered down."""
    centre = sum(blanks) / len(blanks)
    out = []
    for k in range(n_cells):
        if k in blanks:
            out.append(0.0)
            continue
        d = abs(k - centre) % n_cells
        d = min(d, n_cells - d)
        out.append(1.0 - depth * math.exp(-(d / width) ** 2))
    return out


def compare_with_weighted(n: int = 41, outer_r: float = 12.0,
                          inner_r: float = 3.0, displacement: float = 4.0,
                          iters: int = 600) -> dict:
    """Centered / physical / binary mask / graded mask, one pass.

    The deliverable number is ``ratio_to_physical`` for each electronic
    option: how much of a literal geometric displacement the electronics
    recover.
    """
    mask = R.mask_with_blanks([0, 1, 2, 3])
    graded = _weights_graded()
    cases = {
        "centered_symmetric": dict(inner_dx=0.0),
        "physical_displacement": dict(inner_dx=displacement),
        "binary_mask_displacement": dict(inner_dx=0.0, cell_mask=mask),
        "weighted_mask_displacement": dict(inner_dx=0.0,
                                           cell_weights=graded),
    }
    out = {}
    for name, kw in cases.items():
        v = B.solve_potential(n, outer_r, inner_r, 1.0, -1.0,
                              iters=iters, **kw)
        _ex, _ey, u = B.field_and_energy(v)
        out[name] = B.asymmetry_proxy(u)
    phys = out["physical_displacement"]["asymmetry_scalar"]
    for name in ("binary_mask_displacement", "weighted_mask_displacement"):
        out[name]["ratio_to_physical"] = (
            out[name]["asymmetry_scalar"] / phys if phys else None)
    out["claim"] = "PRIOR_ART_ANALOGUE"
    out["no_force_function"] = True
    return out


__all__ = ["compare_with_weighted"]
