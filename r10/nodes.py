"""P08/P12/P13 — a node registry and the look-elsewhere null it needs.

The tempting question is "do these special sites form a Platonic
solid on the globe?" The honest answer requires a machine that most
node-geometry claims skip, and building that machine is the whole
contribution here.

The trap is degrees of freedom. To "fit" N sites to a polyhedron you
get to choose:

* which polyhedron (tetra, cube, octa, icosa, dodeca -- five families,
  with 4 to 20 vertices);
* its orientation (a full 3-DOF rotation, continuous);
* which of its vertices each site maps to;
* how much coordinate slop to allow (sites are points, but "near a
  vertex" is a tolerance you pick).

With that much freedom a *handful* of points fits *something* well
almost always. So a small residual is not evidence. The only thing
that is evidence is a residual smaller than **random sites** achieve
under the *same* search -- and that is what :func:`alignment_pvalue`
measures. It fits the best polyhedron+orientation to the real sites,
then does the identical fit to many random site sets, and reports the
fraction that fit at least as well. This is a look-elsewhere / matched
null, the same discipline that turned the CW arithmetic from p=1e-5
into p=1.0 once the right null was used.

**The public registry contains public geodetic/heritage coordinates
only.** Giza and Chichen Itza are public survey facts. Antarctica and
a Bahamas "crystal sphere" narrative has no established
coordinate and are held as ``LOCATION_UNKNOWN`` -- a status this module
refuses to overwrite without a cited authority. Operator site
hypotheses and any private node labels are tested in the private
repository with this same engine and never appear here.

No gateway, stargate, or dimensional-node status is asserted anywhere.
Those fields exist in the schema so they can be pinned to
``UNSUPPORTED``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np


class NodeStatusError(ValueError):
    """Raised on a forbidden node-status transition."""


# --- the registry -------------------------------------------------------

@dataclass(frozen=True)
class Node:
    """A candidate site. Public rows carry public coordinates only."""

    node_id: str
    public_alias: str
    latitude: float | None       # None when LOCATION_UNKNOWN
    longitude: float | None
    coordinate_authority: str
    uncertainty_km: float
    provenance_class: str        # PUBLIC_HERITAGE | GEODETIC | UNKNOWN
    gateway_status: str = "UNSUPPORTED"
    stargate_status: str = "UNSUPPORTED"
    evidence_status: str = "CONVENTIONAL_REFERENCE"

    def __post_init__(self) -> None:
        for f in ("gateway_status", "stargate_status"):
            if getattr(self, f) not in ("UNSUPPORTED", "UNKNOWN"):
                raise NodeStatusError(
                    f"{f} may only be UNSUPPORTED or UNKNOWN here; a "
                    f"positive gateway/stargate status needs independent "
                    f"physical evidence that does not exist")
        located = self.latitude is not None and self.longitude is not None
        if not located and self.evidence_status != "LOCATION_UNKNOWN":
            raise NodeStatusError(
                "a node without coordinates must be LOCATION_UNKNOWN")

    @property
    def located(self) -> bool:
        return self.latitude is not None and self.longitude is not None

    def unit_vector(self) -> np.ndarray:
        if not self.located:
            raise NodeStatusError(
                f"{self.node_id} is LOCATION_UNKNOWN; it has no vector")
        return latlon_to_unit(self.latitude, self.longitude)


#: Public heritage / geodetic coordinates. These are published survey
#: facts, not source claims. Approximate to the site, uncertainties
#: generous.
PUBLIC_NODES = (
    Node("giza", "Giza pyramid field", 29.9792, 31.1342,
         "published geodetic survey", 1.0, "PUBLIC_HERITAGE"),
    Node("chichen_itza", "Chichen Itza", 20.6843, -88.5678,
         "published geodetic survey", 1.0, "PUBLIC_HERITAGE"),
    # No established coordinate. Held open, not guessed.
    Node("antarctic_candidate", "Antarctic candidate", None, None,
         "none", math.inf, "UNKNOWN", gateway_status="UNKNOWN",
         evidence_status="LOCATION_UNKNOWN"),
    Node("bahamas_crystal_sphere", "Bahamas 'crystal sphere' narrative",
         None, None, "none", math.inf, "UNKNOWN",
         evidence_status="LOCATION_UNKNOWN"),
)


def located_nodes(nodes=PUBLIC_NODES) -> list[Node]:
    return [n for n in nodes if n.located]


def refuse_location_for_unknown(node: Node) -> None:
    """LOCATION_UNKNOWN must not become a precise coordinate freely."""
    if not node.located:
        raise NodeStatusError(
            f"{node.node_id} is LOCATION_UNKNOWN. Assigning it a "
            f"coordinate requires a cited survey or heritage authority; "
            f"an intuition, a map guess, or a round number is not one. "
            f"The Bahamas 'crystal sphere' narrative and the Antarctic "
            f"candidate stay unlocated until such a source exists.")


# --- geometry -----------------------------------------------------------

def latlon_to_unit(lat_deg: float, lon_deg: float) -> np.ndarray:
    lat, lon = math.radians(lat_deg), math.radians(lon_deg)
    return np.array([
        math.cos(lat) * math.cos(lon),
        math.cos(lat) * math.sin(lon),
        math.sin(lat),
    ])


def _regular_polyhedra() -> dict[str, np.ndarray]:
    phi = (1 + 5 ** 0.5) / 2
    # tetrahedron
    tet = np.array([[1, 1, 1], [1, -1, -1], [-1, 1, -1], [-1, -1, 1]],
                   float)
    # octahedron
    octa = np.array([[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0],
                     [0, 0, 1], [0, 0, -1]], float)
    # cube
    cube = np.array([[x, y, z] for x in (-1, 1) for y in (-1, 1)
                     for z in (-1, 1)], float)
    # icosahedron (12)
    ico = []
    for a, b in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        ico += [[0, a, b * phi], [a, b * phi, 0], [b * phi, 0, a]]
    ico = np.array(ico, float)
    # dodecahedron (20) = cube verts + 12 from (0, ±1/phi, ±phi) cyclic
    dod = [list(v) for v in cube]
    for s1 in (-1, 1):
        for s2 in (-1, 1):
            dod += [[0, s1 / phi, s2 * phi],
                    [s1 / phi, s2 * phi, 0],
                    [s2 * phi, 0, s1 / phi]]
    dod = np.array(dod, float)
    out = {}
    for name, v in (("tetrahedron", tet), ("octahedron", octa),
                    ("cube", cube), ("icosahedron", ico),
                    ("dodecahedron", dod)):
        out[name] = v / np.linalg.norm(v, axis=1, keepdims=True)
    return out


POLYHEDRA = _regular_polyhedra()


def _random_rotations(n: int, rng) -> np.ndarray:
    """n uniform random rotation matrices via QR of Gaussian matrices."""
    mats = []
    for _ in range(n):
        q, r = np.linalg.qr(rng.standard_normal((3, 3)))
        q = q @ np.diag(np.sign(np.diag(r)))
        if np.linalg.det(q) < 0:
            q[:, 0] = -q[:, 0]
        mats.append(q)
    return np.array(mats)


def best_polyhedron_fit(site_vectors: np.ndarray, *, rotations: int = 600,
                        seed: int = 0) -> dict:
    """Smallest achievable max-angular residual over all the freedom.

    Searches every polyhedron family and `rotations` random
    orientations, assigning each site to its nearest rotated vertex,
    and returns the best (smallest worst-case) residual in degrees.
    """
    rng = np.random.default_rng(seed)
    rots = _random_rotations(rotations, rng)
    best = {"residual_deg": 180.0, "polyhedron": None}
    for name, verts in POLYHEDRA.items():
        for R in rots:
            rv = verts @ R.T
            # cosine of angle between each site and each vertex
            cos = np.clip(site_vectors @ rv.T, -1, 1)
            nearest = cos.max(axis=1)              # best vertex per site
            worst = math.degrees(math.acos(nearest.min()))
            if worst < best["residual_deg"]:
                best = {"residual_deg": worst, "polyhedron": name}
    return best


def _random_sites(n: int, rng) -> np.ndarray:
    v = rng.standard_normal((n, 3))
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def alignment_pvalue(site_vectors: np.ndarray, *, rotations: int = 300,
                     null_trials: int = 400, seed: int = 20260721) -> dict:
    """Do the real sites fit a polyhedron better than random sites?

    The matched null: the same fit search applied to random site sets
    of the same size. p is the fraction of random sets fitting at least
    as tightly (with the +1 correction).
    """
    rng = np.random.default_rng(seed)
    n = len(site_vectors)
    observed = best_polyhedron_fit(site_vectors, rotations=rotations,
                                   seed=int(rng.integers(1 << 30)))
    at_least_as_good = 0
    null_res = []
    for _ in range(null_trials):
        rs = _random_sites(n, rng)
        r = best_polyhedron_fit(rs, rotations=rotations,
                                seed=int(rng.integers(1 << 30)))
        null_res.append(r["residual_deg"])
        if r["residual_deg"] <= observed["residual_deg"]:
            at_least_as_good += 1
    p = (at_least_as_good + 1) / (null_trials + 1)
    return {
        "n_sites": n,
        "observed_residual_deg": observed["residual_deg"],
        "observed_polyhedron": observed["polyhedron"],
        "null_median_residual_deg": float(np.median(null_res)),
        "p_value": p,
        "verdict": ("NO_BETTER_THAN_CHANCE" if p > 0.05
                    else "TIGHTER_THAN_CHANCE"),
        "note": (
            "a small residual alone is meaningless: random sites fit a "
            "polyhedron about this well under the same search. Only a "
            "residual random sites rarely reach would be evidence, and "
            "with a few sites and this much orientational freedom that "
            "essentially never happens"),
        "look_elsewhere_paid": True,
    }


def node_report() -> dict:
    located = located_nodes()
    return {
        "registry_size": len(PUBLIC_NODES),
        "located_public": [n.node_id for n in located],
        "location_unknown": [n.node_id for n in PUBLIC_NODES
                             if not n.located],
        "polyhedra_searched": sorted(POLYHEDRA),
        "gateway_statuses": sorted({n.gateway_status for n in PUBLIC_NODES}),
        "the_trap": (
            "orientation is 3 continuous DOF, there are five polyhedra "
            "with 4-20 vertices, and 'near a vertex' is a tolerance you "
            "choose. A few sites fit something almost always"),
        "the_test": (
            "alignment_pvalue compares the real fit to the same fit on "
            "random sites; only beating random sites counts"),
        "evidence_class": "DERIVED_MATHEMATICS",
        "measured_here": "nothing",
        "what_this_does_not_say": (
            "It does not say any site is a node, a gateway, or a "
            "stargate; those statuses are pinned UNSUPPORTED. It does "
            "not assign a coordinate to any LOCATION_UNKNOWN site. And "
            "it does not treat a tight polyhedral fit as a discovery, "
            "because random points achieve tight fits under the same "
            "freedom."),
    }
