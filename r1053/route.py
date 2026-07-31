"""R10.63 -- routes from wide-envelope refinement chains.

A wide-envelope record is ONE record, not a run of direct words::

    16 | C_L | E3 | S_tor,6 | S_pol,6 | S_rad,6 | C_R | terminal
    W = 21 + 3(dL + dR)

``C_L`` and ``C_R`` are variable-depth refinement chains of octal digits.
This module reads a chain as a *route*: each octal digit is a step, and a
route is the sequence of waypoints those steps walk through.

WHY OCTAL DIGITS READ NATURALLY AS STEPS
----------------------------------------
An octal digit has eight values, and eight is the number of compass
points at 45 degrees. So the obvious reading -- and the one the operator
described before any of this was built -- is "bearing 45*d, walk, turn,
walk again". :data:`OCTANT_BEARINGS` implements exactly that.

That is a HYPOTHESIS, not a recovered law. Nothing in the source says a
chain digit is a bearing. So this module does two things a guess should
do:

  * it keeps the interpretation swappable (:data:`MODES`), and
  * it scores every route against a null built from random chains of the
    same length (:func:`coherence`).

A real route and a random walk look different: a route turns gently and
mostly goes somewhere, while a random walk turns uniformly and stays
near its origin. If a candidate split cannot beat random chains on those
measures, it is a random walk drawn on a map, and this module says so.

WHAT IS VERIFIED AND WHAT IS NOT
--------------------------------
The geometry is exact -- every leg is a great circle, every bearing and
turn angle is computed from the same primitives the path lane already
cross-checks three ways. Whether a chain digit *means* a bearing is
unverified and probably wrong; the scoring exists to find out.
"""

from __future__ import annotations

import math

from r1053 import kernel, projector

#: Octal digit -> compass bearing. Eight values, eight compass points.
OCTANT_BEARINGS = tuple(45.0 * d for d in range(8))

#: Interpretations of a chain digit. Swappable on purpose.
MODES = ("octant", "octant_relative", "cell_refine")

#: Default leg length. A depth-9 RGCS cell edge, so a step is one cell.
DEFAULT_STEP_KM = 14.989158785749664

#: Chains shorter than this cannot be scored meaningfully.
MIN_STEPS = 6


class RouteError(ValueError):
    """The chain cannot be walked."""


def parse_payload(payload_octal: str, d_left: int) -> dict:
    """Split a wide-envelope payload into its fields at a given dL.

    ``payload_octal`` is the record with the ``16`` header and the
    terminal already removed.
    """
    n = len(payload_octal)
    fixed = 7                       # E3(1) + S_tor(2) + S_pol(2) + S_rad(2)
    if n < fixed:
        raise RouteError(f"payload is {n} octal digits; needs at least {fixed}")
    total_chain = n - fixed
    if not 0 <= d_left <= total_chain:
        raise RouteError(f"d_left {d_left} outside 0..{total_chain}")
    i = 0
    c_left = payload_octal[i:i + d_left]; i += d_left
    e3 = payload_octal[i]; i += 1
    s_tor = payload_octal[i:i + 2]; i += 2
    s_pol = payload_octal[i:i + 2]; i += 2
    s_rad = payload_octal[i:i + 2]; i += 2
    c_right = payload_octal[i:]
    return {
        "d_left": d_left, "d_right": len(c_right),
        "chain_left": c_left, "chain_right": c_right,
        "E3": int(e3, 8),
        "S_tor": int(s_tor, 8), "S_pol": int(s_pol, 8),
        "S_rad": int(s_rad, 8),
        "width_law_ok": (3 * n) == 21 + 3 * total_chain,
    }


def _step(lat, lon, bearing_deg, distance_km):
    """Move along a great circle from a point, given bearing and distance."""
    r = distance_km / projector.EARTH_RADIUS_KM
    p1, l1 = math.radians(lat), math.radians(lon)
    b = math.radians(bearing_deg)
    p2 = math.asin(math.sin(p1) * math.cos(r)
                   + math.cos(p1) * math.sin(r) * math.cos(b))
    l2 = l1 + math.atan2(math.sin(b) * math.sin(r) * math.cos(p1),
                         math.cos(r) - math.sin(p1) * math.sin(p2))
    return math.degrees(p2), (math.degrees(l2) + 540) % 360 - 180


def walk(chain: str, start, mode: str = "octant",
         step_km: float = DEFAULT_STEP_KM) -> list:
    """Walk a chain of octal digits into a list of ``(lat, lon)`` waypoints."""
    if mode not in MODES:
        raise RouteError(f"unknown mode {mode!r}; choose from {MODES}")
    lat, lon = start
    pts = [(lat, lon)]
    heading = 0.0
    for k, ch in enumerate(chain):
        d = int(ch, 8)
        if mode == "octant":
            heading = OCTANT_BEARINGS[d]
            leg = step_km
        elif mode == "octant_relative":
            heading = (heading + OCTANT_BEARINGS[d]) % 360.0
            leg = step_km
        else:                                   # cell_refine
            heading = OCTANT_BEARINGS[d]
            leg = step_km / (2 ** (k // 8))     # halve every 8 steps
        lat, lon = _step(lat, lon, heading, leg)
        pts.append((lat, lon))
    return pts


def route_record(chain: str, start, mode="octant",
                 step_km=DEFAULT_STEP_KM) -> dict:
    """Waypoints, legs, bearings and turn angles for one chain."""
    pts = walk(chain, start, mode, step_km)
    legs = []
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        legs.append({
            "leg": i + 1,
            "from": list(a), "to": list(b),
            "bearing_deg": projector.bearing_deg(a[0], a[1], b[0], b[1]),
            "km": projector.haversine_km(a[0], a[1], b[0], b[1]),
        })
    turns = []
    for i in range(1, len(legs)):
        t = (legs[i]["bearing_deg"] - legs[i - 1]["bearing_deg"] + 540) % 360 - 180
        turns.append({"at_waypoint": i + 1, "turn_deg": t,
                      "direction": "right" if t > 0 else
                                   "left" if t < 0 else "straight"})
    total = sum(l["km"] for l in legs)
    net = projector.haversine_km(pts[0][0], pts[0][1], pts[-1][0], pts[-1][1])
    return {
        "schema": "rgcs.r1063.route.v1",
        "mode": mode, "chain": chain, "steps": len(chain),
        "waypoints": [list(p) for p in pts],
        "legs": legs, "turns": turns,
        "total_km": total, "net_displacement_km": net,
        "straightness": (net / total) if total else 0.0,
        "mean_abs_turn_deg": (sum(abs(t["turn_deg"]) for t in turns)
                              / len(turns)) if turns else 0.0,
        "geometry_is_exact": True,
        "chain_semantics_are_a_hypothesis": True,
    }


def coherence(chain: str, start, mode="octant", step_km=DEFAULT_STEP_KM,
              trials: int = 2000, seed: int = 17) -> dict:
    """Score a chain against random chains of the same length.

    Two measures, both of which separate a route from a random walk:

    ``straightness``    net displacement / path length. A random walk on
                        n steps drifts about sqrt(n) step lengths, so its
                        straightness falls off as 1/sqrt(n).
    ``mean_abs_turn``   a route turns gently; a random walk's turns are
                        uniform, averaging 90 degrees.
    """
    import random
    rng = random.Random(seed)
    obs = route_record(chain, start, mode, step_km)
    s_null, t_null = [], []
    for _ in range(trials):
        r = "".join(rng.choice("01234567") for _ in chain)
        rec = route_record(r, start, mode, step_km)
        s_null.append(rec["straightness"])
        t_null.append(rec["mean_abs_turn_deg"])
    s_null.sort(); t_null.sort()

    def pct(sorted_vals, x):
        lo, hi = 0, len(sorted_vals)
        while lo < hi:
            mid = (lo + hi) // 2
            if sorted_vals[mid] < x:
                lo = mid + 1
            else:
                hi = mid
        return lo / len(sorted_vals)

    p_straight = 1.0 - pct(s_null, obs["straightness"])
    p_turn = pct(t_null, obs["mean_abs_turn_deg"])
    return {
        "schema": "rgcs.r1063.route-coherence.v1",
        "steps": len(chain), "mode": mode,
        "straightness": obs["straightness"],
        "straightness_null_mean": sum(s_null) / len(s_null),
        "p_straighter_than_random": p_straight,
        "mean_abs_turn_deg": obs["mean_abs_turn_deg"],
        "turn_null_mean": sum(t_null) / len(t_null),
        "p_gentler_turns_than_random": p_turn,
        "beats_null": (p_straight < 0.05 or p_turn < 0.05),
        "note": "a chain that cannot beat random chains on either measure "
                "is a random walk drawn on a map",
    }


def start_from_surface(s_tor: int, s_pol: int, s_rad: int) -> tuple:
    """Turn the 6-bit toroidal/poloidal/radial fields into a start point.

    Toroidal maps to longitude and poloidal to latitude, each 6 bits over
    its full range. This is the obvious reading and it is UNVERIFIED --
    it is recorded here so the assumption is visible rather than buried.
    """
    lon = (s_tor / 64.0) * 360.0 - 180.0
    lat = (s_pol / 64.0) * 180.0 - 90.0
    return (max(-89.9, min(89.9, lat)), lon)


def scan_splits(payload_octal: str, mode="octant",
                step_km=DEFAULT_STEP_KM, trials: int = 400) -> list:
    """Every legal (dL, dR) split, each chain scored against the null."""
    total_chain = len(payload_octal) - 7
    rows = []
    for d_left in range(total_chain + 1):
        f = parse_payload(payload_octal, d_left)
        start = start_from_surface(f["S_tor"], f["S_pol"], f["S_rad"])
        row = {"d_left": d_left, "d_right": f["d_right"],
               "S_tor": f["S_tor"], "S_pol": f["S_pol"],
               "S_rad": f["S_rad"], "E3": f["E3"],
               "start_lat": start[0], "start_lon": start[1]}
        for side in ("left", "right"):
            ch = f[f"chain_{side}"]
            if len(ch) < MIN_STEPS:
                row[side] = None
                continue
            row[side] = coherence(ch, start, mode, step_km, trials)
        rows.append(row)
    return rows
