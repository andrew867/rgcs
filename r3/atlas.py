"""P11 (A71-A80) — the nested tetrahedral Earth/celestial atlas, with
the null-rotation campaign that keeps it honest.

An Earth-scale tetrahedral grid is a PROJECTION CHOICE — an
ANTHROPOGENIC/REPRESENTATION artifact, not a discovered structure.
The classic failure of "earth grid" claims is selection: with enough
landmarks and a rotatable grid, some orientation always "fits". The
null-rotation campaign quantifies that: landmark hit-rates for the
claimed orientation are compared against a seeded ensemble of random
rotations, and an orientation that beats none of them is noise.

Portal/nodal claims get an ontology with no supported physical rung,
and nested frames are declared (Earth-fixed inside barycentric inside
galactic) so a cross-frame address must name its frame chain.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from . import ClaimBoundaryError
from .address import DestinationCertificate

EARTH_RADIUS_M = 6_378_137.0

#: Declared frame hierarchy (A77/A78). An address without a frame
#: chain is bookkeeping.
FRAME_HIERARCHY = ("EARTH_FIXED_ITRF", "EARTH_CENTERED_INERTIAL",
                   "SOLAR_SYSTEM_BARYCENTRIC", "GALACTIC")


def tetra_vertices_on_sphere(rotation_deg: float = 0.0) -> list:
    """Regular tetrahedron vertices on the unit sphere, optionally
    rotated about the z-axis — the 'grid' under audit."""
    base = [(1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)]
    s = 1 / math.sqrt(3)
    th = math.radians(rotation_deg)
    out = []
    for x, y, z in base:
        x, y, z = x * s, y * s, z * s
        out.append((x * math.cos(th) - y * math.sin(th),
                    x * math.sin(th) + y * math.cos(th), z))
    return out


def _angular_dist(p, q) -> float:
    dot = max(-1.0, min(1.0, sum(a * b for a, b in zip(p, q))))
    return math.degrees(math.acos(dot))


def landmark_hit_rate(landmarks_xyz: list, rotation_deg: float,
                      tolerance_deg: float = 10.0) -> float:
    """Fraction of landmarks within tolerance of a grid vertex."""
    verts = tetra_vertices_on_sphere(rotation_deg)
    hits = sum(1 for lm in landmarks_xyz
               if min(_angular_dist(lm, v) for v in verts)
               <= tolerance_deg)
    return hits / len(landmarks_xyz) if landmarks_xyz else 0.0


def null_rotation_campaign(landmarks_xyz: list,
                           claimed_rotation_deg: float,
                           n_null: int = 200,
                           seed: int = 20260718,
                           tolerance_deg: float = 10.0) -> dict:
    """A74: is the claimed grid orientation better than random ones?

    The p-value is the fraction of random rotations scoring at least
    as well. 'Some landmarks sit near vertices' at p ~ 0.5 is the
    definition of a selection effect.
    """
    obs = landmark_hit_rate(landmarks_xyz, claimed_rotation_deg,
                            tolerance_deg)
    rng = random.Random(seed)
    null = [landmark_hit_rate(landmarks_xyz, rng.uniform(0, 360),
                             tolerance_deg)
            for _ in range(n_null)]
    at_least = sum(1 for h in null if h >= obs)
    p = (at_least + 1) / (n_null + 1)
    return {"claimed_rotation_deg": claimed_rotation_deg,
            "observed_hit_rate": obs,
            "null_mean_hit_rate": sum(null) / len(null),
            "p_value": p,
            "beats_random_at_0_05": p < 0.05,
            "grid_status": "REPRESENTATION_ARTIFACT",
            "note": "a tetrahedral earth grid is a projection choice; "
                    "an orientation that does not beat seeded random "
                    "rotations is a selection effect",
            "evidence_class": "NUMERICAL_SIMULATION"}


#: A76: the portal/nodal claim ontology. No rung is physical.
PORTAL_CLAIM_ONTOLOGY = {
    "GRID_VERTEX": "a point selected by a chosen projection — "
                   "REPRESENTATION_ARTIFACT",
    "CULTURAL_SITE_COINCIDENCE": "site density plus tolerance makes "
                                 "coincidences guaranteed — audit "
                                 "with the null-rotation campaign",
    "GEOPHYSICAL_ANOMALY": "magnetic/gravity anomalies are surveyed, "
                           "mundane, and uncorrelated with any "
                           "tetrahedral grid until shown otherwise",
    "PORTAL": "no supported physical meaning; UNSUPPORTED",
}


@dataclass(frozen=True)
class NestedAddress:
    """A79: a cross-frame destination names its whole frame chain."""
    certificate: DestinationCertificate
    frame_chain: tuple

    def __post_init__(self):
        if not self.frame_chain or \
                any(f not in FRAME_HIERARCHY for f in self.frame_chain):
            raise ClaimBoundaryError(
                f"frame chain must use declared frames "
                f"{FRAME_HIERARCHY}")
        chain_idx = [FRAME_HIERARCHY.index(f) for f in self.frame_chain]
        if chain_idx != sorted(chain_idx):
            raise ClaimBoundaryError(
                "frame chain must be ordered inner -> outer")
