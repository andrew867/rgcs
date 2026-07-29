"""R10.35 — the EarthStar / Becker-Hagens / UVG grid layer.

THE 62 NODES ARE CONSTRUCTIBLE, NOT DOWNLOADED
----------------------------------------------
The pack asks for the exact Becker-Hagens KMZ. Web research is not
authorized here, but it is not needed for the node SET: the EarthStar
grid is the icosidodecahedral vertex set, and 62 falls out exactly:

    12  icosahedron vertices
  + 20  dodecahedron vertices (= icosahedron face centres)
  + 30  icosahedron edge midpoints
  ---
    62  nodes

and the 15 great circles are the 15 two-fold axes of the icosahedron.
Both counts are verified by construction here.

WHAT IS *NOT* AVAILABLE: the canonical BH ORIENTATION (which node sits
at which lat/lon). That constant is not sourced in this run, so no
absolute node coordinate is emitted and no per-site distance is claimed.

THE DECISIVE RESULT DOES NOT NEED THE ORIENTATION
-------------------------------------------------
By symmetry, the FRACTION of Earth's surface within a given distance of
the 15 great circles is orientation-independent. So the chance baseline
can be computed exactly, and it settles the "~135-151 km from edge
11-20" observation:

    within  50 km of any edge : 11.4% of Earth
    within 100 km            : 22.2%
    within 135 km            : 29.2%
    within 151 km            : 32.4%      <-- about 1 point in 3
    within 200 km            : 41.6%

**A site 135-151 km from a grid edge is what roughly one random point in
three looks like.** Edge proximity at that scale is not evidence, and no
amount of site-picking makes it evidence.

NODE proximity is a different matter and IS discriminating:

    within  50 km of any node : 0.09% of Earth
    within 150 km             : 0.86%
    within 300 km             : 3.4%

That is a ~35x tighter target at 150 km. So the actionable conclusion is
**test against NODES, not EDGES** -- and against MINOR points only once
their construction rule is sourced, since adding points always loosens
the target.

NO PLACE-NAME SCORING: this module contains no site list and no place
names. Sites are supplied by the caller as coordinates.
"""

from __future__ import annotations

import math

import numpy as np

from r1025.hedra import families

EARTH_R_KM = 6371.0
EXPECTED_NODES = 62
EXPECTED_GREAT_CIRCLES = 15


def _ico():
    return families()["ICOSAHEDRON_20_FACE_CENTRE"]


def _unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def edge_midpoints() -> list:
    ico = _ico()
    edges = set()
    for f in range(ico.face_count):
        idx = ico.faces[f]
        for i in range(3):
            edges.add(tuple(sorted((idx[i], idx[(i + 1) % 3]))))
    return [_unit(np.asarray(ico.vertices[a], float)
                  + np.asarray(ico.vertices[b], float))
            for a, b in sorted(edges)]


def nodes_62() -> np.ndarray:
    """The 62 EarthStar nodes as unit vectors, up to global orientation."""
    ico = _ico()
    pts = [_unit(v) for v in ico.vertices[:12]]
    for f in range(ico.face_count):
        pts.append(_unit(sum(np.asarray(x, float)
                             for x in ico.face_triangle(f))))
    pts += edge_midpoints()
    arr = np.unique(np.round(np.array(pts), 9), axis=0)
    return arr


def great_circle_poles() -> np.ndarray:
    """The 15 two-fold axes; each is the pole of one grid great circle."""
    axes = []
    for m in edge_midpoints():
        if not any(abs(abs(float(np.dot(m, a))) - 1) < 1e-9 for a in axes):
            axes.append(m)
    return np.array(axes)


def structure_check() -> dict:
    n, p = nodes_62(), great_circle_poles()
    return {
        "nodes": len(n), "nodes_match_62": len(n) == EXPECTED_NODES,
        "great_circles": len(p),
        "great_circles_match_15": len(p) == EXPECTED_GREAT_CIRCLES,
        "decomposition": "12 icosahedron vertices + 20 face centres "
                         "(dodecahedron vertices) + 30 edge midpoints",
        "orientation_sourced": False,
        "note": "node SET is exact by construction; the canonical "
                "Becker-Hagens orientation is NOT sourced in this run, "
                "so no absolute node coordinate is emitted",
    }


def dist_to_nodes_km(unit_pts: np.ndarray) -> np.ndarray:
    n = nodes_62()
    return EARTH_R_KM * np.arccos(
        np.clip(np.asarray(unit_pts) @ n.T, -1, 1)).min(axis=1)


def dist_to_edges_km(unit_pts: np.ndarray) -> np.ndarray:
    p = great_circle_poles()
    return EARTH_R_KM * np.arcsin(
        np.clip(np.abs(np.asarray(unit_pts) @ p.T), -1, 1)).min(axis=1)


def chance_baseline(distances_km=(50, 100, 135, 151, 200, 300),
                    samples: int = 400_000, seed: int = 20260729) -> list:
    """Fraction of Earth within d km of any edge / any node.

    Orientation-independent by symmetry, so this holds whatever the
    canonical BH alignment turns out to be.
    """
    rng = np.random.default_rng(seed)
    pts = rng.normal(size=(samples, 3))
    pts /= np.linalg.norm(pts, axis=1, keepdims=True)
    de, dn = dist_to_edges_km(pts), dist_to_nodes_km(pts)
    rows = []
    for d in distances_km:
        fe, fn = float((de <= d).mean()), float((dn <= d).mean())
        rows.append({
            "distance_km": d,
            "fraction_within_of_any_edge": round(fe, 5),
            "one_in_n_random_points_edge": round(1 / fe, 1) if fe else None,
            "fraction_within_of_any_node": round(fn, 5),
            "one_in_n_random_points_node": round(1 / fn, 1) if fn else None,
            "edge_test_is_discriminating": fe < 0.05,
            "node_test_is_discriminating": fn < 0.05,
        })
    return rows


def score_sites(sites) -> list:
    """sites: iterable of (label, lat, lon). Coordinates only, no names
    used for scoring. Distances are reported ONLY as
    orientation-unresolved, because the BH alignment is not sourced."""
    rows = []
    for label, lat, lon in sites:
        la, lo = math.radians(lat), math.radians(lon)
        p = np.array([[math.cos(la) * math.cos(lo),
                       math.cos(la) * math.sin(lo), math.sin(la)]])
        rows.append({
            "site": label, "lat": lat, "lon": lon,
            "edge_km_unoriented_grid": round(float(dist_to_edges_km(p)[0]), 1),
            "node_km_unoriented_grid": round(float(dist_to_nodes_km(p)[0]), 1),
            "orientation_sourced": False,
            "scored_as_evidence": False,
            "note": "distances are to an UNORIENTED construction of the "
                    "grid and are NOT comparable to published BH "
                    "figures; they are emitted for structure only",
        })
    return rows


def report() -> dict:
    base = chance_baseline()
    at151 = next(r for r in base if r["distance_km"] == 151)
    return {
        "schema": "rgcs.r1035.earthstar.v1",
        "structure": structure_check(),
        "chance_baseline": base,
        "headline": (
            f"{100 * at151['fraction_within_of_any_edge']:.1f}% of Earth's "
            f"surface lies within 151 km of one of the 15 grid great "
            f"circles, so an edge distance in the 135-151 km band is what "
            f"about 1 random point in 3 looks like"),
        "edge_test_verdict": "NOT_DISCRIMINATING_AT_135_TO_151_KM",
        "node_test_verdict": "DISCRIMINATING_0_86_PERCENT_AT_150_KM",
        "recommendation": "score against NODES, not edges; add minor "
                          "points only after their construction rule is "
                          "sourced, since more points always loosen the "
                          "target",
        "blind_test_passed": False,
        "projector_promoted": False,
        "verdict": ("R10_35_EARTHSTAR_GRID_LAYER_CANDIDATE_ONLY_"
                    "EXACT_FAILURES_EMITTED"),
        "exact_failure": (
            "the canonical Becker-Hagens ORIENTATION is not sourced in "
            "this run, so no site-to-node distance can be compared with "
            "published figures; and the edge-proximity observation that "
            "motivated the lane is at chance. No blind test was run and "
            "nothing is promoted."),
    }
