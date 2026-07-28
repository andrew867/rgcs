"""R10.13 Phase 26 — aperture ring timing and geometry (exact).

Regenerates the 35/33/2 aperture family, the 29/89 radial relation,
the 16 Hz passage rates, sub-bin counts, and the integer master-clock
lattice from equations. The two gap indices are PARAMETERS with no
source authority: selecting them refuses. RESEARCH ONLY.
"""

from __future__ import annotations

import math
from fractions import Fraction

from r1013.errors import UserError

POSITIONS = 35
ACTIVE = 33
OMITTED = POSITIONS - ACTIVE                    # 2
PATTERN_HZ = 16
SUB_BINS_PER_POSITION = 16
AREA_INDEX_INNER = 29
AREA_INDEX_OUTER = 89


def geometry(outer_radius: float = None, unit: str = "units") -> dict:
    """29/89 radial relation; scalable. Default outer radius is the
    prime-ratio candidate 144.1096998 units."""
    ratio = Fraction(AREA_INDEX_INNER, AREA_INDEX_OUTER)
    Ro = outer_radius if outer_radius is not None else 144.1096998
    Ri = Ro * math.sqrt(ratio)
    return {"positions": POSITIONS, "active": ACTIVE,
            "omitted": OMITTED,
            "occupancy": [ACTIVE, POSITIONS],
            "area_ratio": [AREA_INDEX_INNER, AREA_INDEX_OUTER],
            "outer_radius": Ro, "inner_radius": Ri, "unit": unit,
            "annular_width": Ro - Ri,
            "torus_major": (Ro + Ri) / 2, "torus_minor": (Ro - Ri) / 2,
            "delta_theta_deg": 360.0 / POSITIONS,
            "five_positions_deg": 5 * 360.0 / POSITIONS,
            "five_positions_exact": "360/7 degrees",
            "evidence_class": "SOURCE_PROVENANCE_ONLY",
            "missing_geometry": ["gap indices", "aperture diameter and "
                                 "shape", "plate thickness", "ring "
                                 "offsets", "optical path", "material "
                                 "implementation", "drive and sensor "
                                 "geometry"]}


def rates(pattern_hz: int = PATTERN_HZ) -> dict:
    """Passage and bin rates for a traveling pattern; derived, and
    verified as exact integers."""
    total = POSITIONS * pattern_hz
    active = ACTIVE * pattern_hz
    gaps = OMITTED * pattern_hz
    assert total == active + gaps
    return {"pattern_hz": pattern_hz,
            "total_passages_per_s": total,
            "active_passages_per_s": active,
            "gap_passages_per_s": gaps,
            "sub_bins_total": POSITIONS * SUB_BINS_PER_POSITION,
            "sub_bins_active": ACTIVE * SUB_BINS_PER_POSITION,
            "sub_bins_blank": OMITTED * SUB_BINS_PER_POSITION,
            "evidence_class": "SOURCE_PROVENANCE_ONLY"}


def master_clock(pattern_hz: int = PATTERN_HZ) -> dict:
    """Integer master-timing lattice regenerated from constraints:
    ticks per revolution must be divisible by positions and sub-bins;
    the canonical family uses 400 ticks per sub-bin."""
    ticks_per_sub_bin = 400
    ticks_per_rev = POSITIONS * SUB_BINS_PER_POSITION * ticks_per_sub_bin
    clock_hz = ticks_per_rev * pattern_hz
    rec = {"ticks_per_sub_bin": ticks_per_sub_bin,
           "ticks_per_revolution": ticks_per_rev,
           "master_clock_hz": clock_hz,
           "master_clock_mhz": clock_hz / 1e6,
           "divisibility": {
               "by_positions": ticks_per_rev % POSITIONS == 0,
               "by_sub_bins": ticks_per_rev %
               (POSITIONS * SUB_BINS_PER_POSITION) == 0},
           "evidence_class": "SOURCE_PROVENANCE_ONLY"}
    assert rec["ticks_per_revolution"] == 224000
    assert rec["master_clock_hz"] == 3_584_000
    return rec


def gap_indices(select: tuple[int, int] | None = None) -> dict:
    """The two omitted positions. There is NO source authority for
    which two: selecting refuses unless bounded-variant enumeration is
    requested explicitly."""
    if select is not None:
        raise UserError(
            "RGCS-E013",
            "The two gap indices have no source authority; RGCS will "
            "not select them. Use enumerate_gap_variants() to study "
            "bounded variants without asserting any one of them.")
    return {"status": "UNDERDETERMINED",
            "positions": POSITIONS, "omitted": OMITTED,
            "variant_count": POSITIONS * (POSITIONS - 1) // 2,
            "evidence_class": "SOURCE_PROVENANCE_ONLY"}


def enumerate_gap_variants(symmetry: str = "all") -> dict:
    """Bounded variant families for the two gaps: all 595 unordered
    pairs, or the 17 antipodal-ish separations by gap distance."""
    pairs = [(i, j) for i in range(POSITIONS)
             for j in range(i + 1, POSITIONS)]
    if symmetry == "all":
        sel = pairs
    elif symmetry == "by-separation":
        sel = sorted({min((j - i) % POSITIONS, (i - j) % POSITIONS)
                      for i, j in pairs})
    else:
        raise UserError("RGCS-E006", "symmetry must be 'all' or "
                        "'by-separation'.")
    return {"symmetry": symmetry, "count": len(sel),
            "variants": sel[:50],
            "truncated": len(sel) > 50,
            "note": "enumeration only; no variant is selected"}
