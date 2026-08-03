"""Miami / Bermuda calibration lane, v0.6.

Three strictly separated parts:

1. the exact candidate ``236805/142`` against the declared Bermuda
   metrics -- with a look-elsewhere null control, because a coefficient
   list this rich can land near SOME declared distance by accident;
2. the two operator vector candidates parsed through every LEGAL branch
   of the EXISTING root projector (r1053). The projector is not modified
   and nothing is fitted to Miami;
3. frame honesty: the repo projector's own spherical haversine gives a
   different Miami-Bermuda figure than the (geodesic) metrics file, and
   the candidate is scored against BOTH so the frame choice is visible.
"""

from __future__ import annotations

import itertools
from fractions import Fraction as F

#: Declared Bermuda metrics (km), from the v0.6 calibration file.
BERMUDA_METRICS_KM = {
    "miami_bermuda": 1667.541270502605,
    "bermuda_san_juan": 1539.482176171109,
    "san_juan_miami": 1661.125124135473,
    "cuba_a_miami": 647.473428658922,
    "cuba_b_miami": 642.166913456247,
}

#: The candidate, exactly.
CANDIDATE = F(236805, 142)

#: v0.7 status assignments -- retagged per the R10.72 correction, and
#: fixed here so no later lane can quietly promote them.
LANE_STATUS = {
    "236805/142": "RECORDED_POSTHOC_LEAD",
    "1680769543": "UNRESOLVED_VECTOR_CANDIDATE_NO_SUPPORTING_PARSE",
    "168593073": "UNRESOLVED_VECTOR_CANDIDATE_NO_SUPPORTING_PARSE",
    "BERMUDA_FLORIDA_VERTEX": "CANDIDATE_LABEL_ONLY",
    "projector_fitting": "FORBIDDEN",
    "release_as_solved": "FORBIDDEN",
}

#: Reference vertex coordinates used ONLY for reporting distances of
#: projector outputs. They select nothing and fit nothing.
MIAMI = (25.7743, -80.1937)
BERMUDA = (32.2949, -64.7814)

#: Operator-reported vector candidates. Labels are candidates, not fact.
VECTOR_CANDIDATES = {
    "1680769543": "BERMUDA_FLORIDA_VERTEX_VECTOR_CANDIDATE",
    "168593073": "SECONDARY_CANDIDATE",
}

#: Direct-lane legality bound (30-bit word).
WORD_LIMIT = 1 << 30

#: Coefficient pool for the null control -- the v0.5/v0.6 ledger integers.
COEFFICIENT_POOL = (236805, 297634, 142, 897, 47, 63, 27, 93, 311, 631,
                    732, 573, 297, 23, 673, 37, 411, 4096, 64672, 961)


def candidate_error() -> dict:
    """The headline arithmetic, exact where possible."""
    cand = float(CANDIDATE)
    known = BERMUDA_METRICS_KM["miami_bermuda"]
    return {"candidate_exact": str(CANDIDATE), "candidate_km": cand,
            "reference_km": known, "abs_error_km": abs(cand - known),
            "rel_error": abs(cand - known) / known,
            "claim": "MODEL_OUTPUT"}


def frame_comparison() -> dict:
    """Candidate vs the geodesic figure AND the projector's own sphere.

    The metrics file's 1667.541 km is a geodesic (ellipsoidal) figure;
    the repo projector measures with spherical haversine, which gives a
    different Miami-Bermuda distance. Scoring against both keeps the
    frame choice visible instead of picking whichever flatters.
    """
    from r1053.projector import haversine_km
    sphere = haversine_km(*MIAMI, *BERMUDA)
    cand = float(CANDIDATE)
    return {"geodesic_reference_km": BERMUDA_METRICS_KM["miami_bermuda"],
            "projector_sphere_km": sphere,
            "candidate_km": cand,
            "err_vs_geodesic_km": abs(cand - BERMUDA_METRICS_KM["miami_bermuda"]),
            "err_vs_sphere_km": abs(cand - sphere),
            "frames_agree": abs(sphere - BERMUDA_METRICS_KM["miami_bermuda"]) < 0.5,
            "claim": "MODEL_OUTPUT"}


def null_control(tolerance_km: float = 0.1, lo: float = 100.0,
                 hi: float = 20000.0) -> dict:
    """Look-elsewhere control for the 236805/142 hit.

    Every ordered pair a/b from the coefficient pool that lands in a
    plausible geodesic range is tested against every declared metric. The
    hit count says how surprising ONE fraction within ``tolerance_km`` of
    ONE metric actually is, given this many chances.
    """
    hits, tried = [], 0
    for a, b in itertools.permutations(COEFFICIENT_POOL, 2):
        val = a / b
        if not (lo <= val <= hi):
            continue
        tried += 1
        for name, ref in BERMUDA_METRICS_KM.items():
            if abs(val - ref) <= tolerance_km:
                hits.append({"fraction": f"{a}/{b}", "value_km": val,
                             "metric": name, "abs_err_km": abs(val - ref)})
    return {"tolerance_km": tolerance_km, "fractions_in_range": tried,
            "comparisons": tried * len(BERMUDA_METRICS_KM),
            "hits": hits, "hit_count": len(hits),
            "claim": "MODEL_OUTPUT",
            "note": ("hit_count > 1 means the candidate is not unique in "
                     "its own pool; interpret the headline hit "
                     "accordingly")}


def legal_branches(wire: str) -> list:
    """Every legal parse branch for one decimal wire, R10.14A split.

    Branches: payload-only, payload+terminal, whole-wire -- each admitted
    to the direct 30-bit lane ONLY if it fits the word limit. Nothing is
    truncated to fit; an over-limit branch is reported as refused.
    """
    if not (wire.startswith("16") and wire.endswith("3") and len(wire) > 3):
        return [{"branch": "R10_14A_SPLIT", "legal": False,
                 "reason": "wire does not match H=16 ... T=3"}]
    payload = wire[2:-1]
    views = {
        "payload_only": int(payload),
        "payload_plus_terminal": int(payload + wire[-1]),
        "whole_wire": int(wire),
    }
    out = []
    for name, val in views.items():
        legal = val < WORD_LIMIT
        out.append({"branch": name, "word": val, "legal": legal,
                    "reason": None if legal else
                    f"exceeds 30-bit direct lane ({val} >= {WORD_LIMIT})"})
    return out


def map_vector(wire: str) -> dict:
    """Project every legal branch through the EXISTING projector.

    Distances to the Miami and Bermuda vertices are REPORTED for each
    output; they influence nothing upstream. The projector is the frozen
    r1053 lane, unmodified.
    """
    from r1053.projector import haversine_km, project
    rows = []
    for br in legal_branches(wire):
        if not br.get("legal"):
            rows.append({**br, "claim": "MODEL_OUTPUT"})
            continue
        lat, lon = project(br["word"])
        rows.append({**br, "lat": lat, "lon": lon,
                     "km_to_miami": haversine_km(lat, lon, *MIAMI),
                     "km_to_bermuda": haversine_km(lat, lon, *BERMUDA),
                     "claim": "MODEL_OUTPUT"})
    return {"wire": wire,
            "label_status": VECTOR_CANDIDATES.get(wire, "UNREGISTERED"),
            "projector": "r1053 (existing, unmodified)",
            "target_fitted": False,
            "branches": rows}


def calibration_report() -> dict:
    return {"candidate": candidate_error(),
            "frames": frame_comparison(),
            "null": null_control(),
            "vectors": [map_vector(w) for w in VECTOR_CANDIDATES]}


__all__ = ["BERMUDA_METRICS_KM", "CANDIDATE", "MIAMI", "BERMUDA",
           "VECTOR_CANDIDATES", "WORD_LIMIT", "COEFFICIENT_POOL",
           "candidate_error", "frame_comparison", "null_control",
           "legal_branches", "map_vector", "calibration_report"]
