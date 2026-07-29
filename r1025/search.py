"""R10.25 Agent 02 — the projector search and its honesty budget.

Two lanes, kept apart because their evidential value differs by orders
of magnitude:

  SEALED   orientations recorded before this run (cwatlas trained frame
           and sealed contexts). Low DOF. A survivor here is meaningful.
  GRID     a systematic orientation sweep. High DOF. A survivor here is
           expected by chance unless the false-hit expectation says
           otherwise, so it is reported separately and never headlined.

The false-hit expectation is computed for BOTH lanes and printed with
every survivor count. A survivor without its false-hit number is not a
result, it is a coincidence waiting to be discovered.
"""

from __future__ import annotations

import itertools
import math

import numpy as np

from r1025 import hedra
from r1025.projector import (
    HARD_ANCHORS,
    Candidate,
    evaluate,
    fields,
)


def sealed_orientations() -> dict:
    """Frames recorded before this run. Not fitted here."""
    out = {"IDENTITY": np.eye(3)}
    try:
        from cwatlas.r1085a import final_projection as fp
        frame, _ = fp.training_alignment(2025.0)
        out["TRAINED"] = np.asarray(frame.rotation, float)
        for ctx, rot in fp.sealed_contexts().items():
            out[f"SEALED_{ctx}"] = np.asarray(rot, float)
    except Exception:                        # pragma: no cover
        pass
    return out


def _rot(axis, ang):
    a = np.asarray(axis, float)
    a = a / np.linalg.norm(a)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + math.sin(ang) * K + (1 - math.cos(ang)) * (K @ K)


def grid_orientations(n_axis: int = 6, n_ang: int = 6) -> dict:
    """A coarse SO(3) sweep. Explicitly high-DOF."""
    out = {}
    for i in range(n_axis):
        z = 1 - 2 * (i + 0.5) / n_axis
        r = math.sqrt(max(0.0, 1 - z * z))
        phi = math.pi * (1 + 5 ** 0.5) * i
        axis = (r * math.cos(phi), r * math.sin(phi), z)
        for j in range(n_ang):
            ang = 2 * math.pi * j / n_ang
            out[f"GRID_{i}_{j}"] = _rot(axis, ang)
    return out


def eligible_hedra() -> tuple:
    """Families that can host the observed F5 values at all."""
    keep, rejected = {}, []
    fam = hedra.families()
    maxf5 = max(fields(a.vector)[0] for a in HARD_ANCHORS)
    for name, h in sorted(fam.items()):
        if h.face_count > 32:
            rejected.append({
                "hedron_family": name, "base_face_count": h.face_count,
                "rejection_reason":
                    f"BASE_FACE_COUNT_{h.face_count}_EXCEEDS_F5_5_BIT_"
                    f"CAPACITY_32"})
        elif h.face_count <= maxf5:
            rejected.append({
                "hedron_family": name, "base_face_count": h.face_count,
                "rejection_reason":
                    f"BASE_FACE_COUNT_{h.face_count}_CANNOT_INDEX_"
                    f"OBSERVED_F5_MAX_{maxf5}"})
        else:
            keep[name] = h
    return keep, rejected


def _p_map_ok(n_pairs: int, branch: int) -> float:
    """P(n random (input,output) pairs form a consistent injective map).

    Exact, by DP over the number of distinct pairs already fixed. With
    k inputs already mapped, the next uniform pair (a, o) survives iff
    either a is already mapped and o matches its image -- (k/b)(1/b) --
    or a is new and o is unused -- ((b-k)/b)^2. Anything else is a
    contradiction or a collision and kills the candidate.
    """
    b = branch
    if n_pairs <= 0:
        return 1.0
    state = {0: 1.0}
    for _ in range(n_pairs):
        nxt = {}
        for k, pk in state.items():
            if k:
                nxt[k] = nxt.get(k, 0.0) + pk * (k / b) * (1.0 / b)
            if k < b:
                nxt[k + 1] = nxt.get(k + 1, 0.0) + pk * ((b - k) / b) ** 2
        state = nxt
    return sum(state.values())


def false_hit_expectation(n_candidates: int, child_constraints: int,
                          branch: int, distinct_f5: int,
                          n_anchors: int, child_model: str = "UNIFORM",
                          spatial_depth: int = 1) -> dict:
    """Probability a random candidate passes, and expected false hits.

    The face map is FITTED from the anchors, so it contributes no
    evidence: with `distinct_f5` distinct F5 values and enough faces it
    is satisfiable by construction.

    The two child models are NOT comparable. UNIFORM pools every level
    into one map, so all `child_constraints` pairs must agree -- strong.
    PER_LEVEL gives each level its own free map constrained by only
    `n_anchors` pairs, so it is close to unconstrained and its
    survivors are expected by chance.
    """
    b = branch
    if child_model == "UNIFORM":
        p = _p_map_ok(child_constraints, b)
    else:
        p = _p_map_ok(n_anchors, b) ** max(1, spatial_depth)
    return {
        "candidates_tested": n_candidates,
        "child_model": child_model,
        "child_constraints": child_constraints,
        "pairs_per_map": (child_constraints if child_model == "UNIFORM"
                          else n_anchors),
        "branch": b,
        "p_random_candidate_passes": p,
        "expected_false_survivors": n_candidates * p,
        "face_map_is_fitted_contributes_no_evidence": True,
        "distinct_f5_across_anchors": distinct_f5,
        "note": "face map is derived from the anchors themselves and so "
                "cannot corroborate; only child-map consistency and "
                "containment carry evidence",
    }


def run(lane: str = "SEALED", spatial_depths=(2, 3, 4, 6, 8),
        offsets=(0, 1, 2, 3, 4), branches=(4, 8),
        child_models=("UNIFORM", "PER_LEVEL"), anchors=HARD_ANCHORS) -> dict:
    keep, rejected = eligible_hedra()
    orients = (sealed_orientations() if lane == "SEALED"
               else grid_orientations())
    survivors, rejections, tested = [], list(rejected), 0
    max_constraints = 0
    for (hname, h), (oname, rot), hd, po, off, br, cm, depth in \
            itertools.product(keep.items(), orients.items(),
                              ("right", "mirrored"),
                              ("south_up", "north_up"),
                              offsets, branches, child_models,
                              spatial_depths):
        if off + depth > 11:
            continue
        cand = Candidate(hname, oname, hd, po, off, br, cm)
        r = evaluate(cand, h, rot, anchors, depth)
        tested += 1
        max_constraints = max(max_constraints, r["child_constraints"])
        if r["survivor"]:
            survivors.append(r)
        else:
            rejections.append({
                "candidate_id": r["candidate_id"],
                "hedron_family": r["hedron"],
                "spatial_depth": depth,
                "rejection_reason": r["rejection_reason"]})
    fh = false_hit_expectation(tested, max_constraints, 4,
                               len({a.f5 for a in anchors}), len(anchors))
    deep = [s for s in survivors if s["spatial_depth"] >= 6]
    return {
        "schema": "rgcs.r1025.projector-search.v1",
        "lane": lane,
        "hedra_eligible": sorted(keep),
        "hedra_rejected": rejected,
        "candidates_tested": tested,
        "survivors": survivors,
        "survivors_at_depth_ge_6": deep,
        "rejections": rejections,
        "false_hit": fh,
    }
