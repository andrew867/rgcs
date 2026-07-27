"""R10.9 Earth alignment V2 — EARTH_ALIGNMENT_V2_MONTREAL_DIRECT.

V1 (EARTH_ALIGNMENT_V1_LEGACY_CALIBRATED, archive 2026-07-26) is
preserved byte-for-byte under ``docs/r109/earth_v1/`` and loaded, never
refit. V2 uses the corrected DIRECT compact Montréal packet 165879243
as its Montréal anchor and is fit with the same composed-Gaussian-RBF
family as V1. Both operators are CALIBRATED_CANDIDATEs; neither is
independent validation.

Recovered packet->pre-warp convention (SOFTWARE_RESULT):
spherical midpoint triangle subdivision on the V1 rigid mesh, child map
(2,1,0,3) per quaternary symbol, chart corner order (1,0,2) over the
face's listed vertex triple. EXACT on mesh face 12 (Stonehenge and the
orange triplet reproduce the archived V1 numbers to ~1e-14). Mesh face
19 is recovered only APPROXIMATELY (~0.1..2.5 deg vs the archived
anchor rows); unchanged face-19 anchors therefore use V1's RECORDED
pre-warp positions, and the face-19 convention stays UNRESOLVED.

The frozen blind holdout 167854923 is decoded under BOTH operators for
the record; it is never a calibration input and V2 is never adjusted to
move it (R109-HLD-01).
"""

from __future__ import annotations

import csv
import gzip
import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

import rgcs_coordinate as rc

V1_DIR = Path(__file__).resolve().parents[1] / "docs" / "r109" / "earth_v1" / \
    "RGCS_Earth_Alignment_Candidate_2026-07-26"

V1_PROFILE_ID = "EARTH_ALIGNMENT_V1_LEGACY_CALIBRATED"
V2_PROFILE_ID = "EARTH_ALIGNMENT_V2_MONTREAL_DIRECT"

CHILD_MAP = (2, 1, 0, 3)
CORNER_PERM = (1, 0, 2)

#: face-12 convention exactness evidence threshold (deg, from probes)
FACE12_EXACT = True
FACE19_STATUS = "APPROXIMATE_CONVENTION_UNRESOLVED"


# ------------------------------------------------------------- geometry
def unit(lat_deg: float, lon_deg: float) -> np.ndarray:
    la, lo = math.radians(lat_deg), math.radians(lon_deg)
    return np.array([math.cos(la) * math.cos(lo),
                     math.cos(la) * math.sin(lo),
                     math.sin(la)])


def latlon(v: np.ndarray) -> tuple[float, float]:
    v = np.asarray(v, float)
    v = v / np.linalg.norm(v)
    return (math.degrees(math.asin(v[2])),
            math.degrees(math.atan2(v[1], v[0])))


def _load_mesh() -> tuple[dict, dict]:
    verts = {int(r["vertex_id"]):
             np.array([float(r["source_x"]), float(r["source_y"]),
                       float(r["source_z"])])
             for r in csv.DictReader(
                 open(V1_DIR / "MAPPED_ICOSAHEDRON_VERTICES.csv"))}
    faces = {int(r["mesh_face"]): [int(v) for v in r["vertex_ids"].split()]
             for r in csv.DictReader(
                 open(V1_DIR / "MAPPED_FACE_CENTROIDS.csv"))}
    return verts, faces


_VERTS, _FACES = None, None


def prewarp_unit(raw: int, mesh_face: int) -> np.ndarray:
    """Recovered packet -> pre-warp unit vector (exact on face 12)."""
    global _VERTS, _FACES
    if _VERTS is None:
        _VERTS, _FACES = _load_mesh()
    path = rc.decode_coordinate(raw).to_dict()["q22_path"]
    vids = _FACES[mesh_face]
    A, B, C = [(_VERTS[vids[CORNER_PERM[i]]] /
                np.linalg.norm(_VERTS[vids[CORNER_PERM[i]]]))
               for i in range(3)]
    for p in path:
        def mid(a, b):
            m = (a + b) / 2
            return m / np.linalg.norm(m)
        mAB, mBC, mCA = mid(A, B), mid(B, C), mid(C, A)
        A, B, C = [(A, mAB, mCA), (mAB, B, mBC),
                   (mCA, mBC, C), (mAB, mBC, mCA)][CHILD_MAP[p]]
    c = A + B + C
    return c / np.linalg.norm(c)


# ------------------------------------------------------------- operators
def load_v1_steps() -> list:
    with gzip.open(V1_DIR / "operator" / "WARP_STEPS.json.gz", "rt",
                   encoding="utf-8") as fh:
        return json.load(fh)


def apply_steps(points, steps) -> np.ndarray:
    y = np.atleast_2d(np.asarray(points, float))
    y = y / np.linalg.norm(y, axis=1)[:, None]
    for s in steps:
        c = np.asarray(s["centers_ecef"], float)
        w = np.asarray(s["weights_ecef"], float)
        sg = float(s["sigma"])
        d2 = np.sum((y[:, None, :] - c[None, :, :]) ** 2, axis=2)
        y = y + np.exp(-d2 / (2 * sg * sg)) @ w
        y = y / np.linalg.norm(y, axis=1)[:, None]
    return y


@dataclass(frozen=True)
class Anchor:
    name: str
    source_unit: tuple[float, float, float]
    target_lat: float
    target_lon: float
    provenance: str


def v2_anchors() -> list[Anchor]:
    """The V2 calibration anchor set (R109-EAR-01). Sources for
    unchanged anchors are V1's RECORDED pre-warp positions; the new
    Montréal anchor uses the exactly-recovered face-12 convention."""
    rows = list(csv.DictReader(open(V1_DIR / "ANCHOR_FORWARD_RESULTS.csv")))
    by = {r["anchor"]: r for r in rows}

    def rec(name):
        r = by[name]
        return unit(float(r["source_lat_like_deg_before_warp"]),
                    float(r["source_lon_like_deg_before_warp"])), \
            float(r["target_lat_deg"]), float(r["target_lon_deg"])

    anchors = []
    for name in ("WILKES_ROOT", "SAA_PHASE_ZERO", "STONEHENGE", "ERIE",
                 "TORONTO"):
        src, tla, tlo = rec(name)
        anchors.append(Anchor(name, tuple(src), tla, tlo,
                              "V1 recorded pre-warp source (unchanged anchor)"))
    m = prewarp_unit(165879243, 12)
    anchors.append(Anchor(
        "MONTREAL_DIRECT", tuple(m), 45.508822, -73.554077,
        "direct compact packet 165879243, face 4 -> mesh face 12, "
        "exact recovered face-12 convention (R109-MTL-01)"))
    return anchors


def fit_v2(sigma_primary: float = 0.09, sigma_local: float = 0.02,
           gain: float = 0.5, max_steps_primary: int = 2000,
           max_steps_local: int = 3000, tol_deg: float = 1e-9) -> dict:
    """Composed Gaussian RBF landmark registration (same family as V1).

    Two stages like V1: a primary stage at V1's sigma, then a local
    stage at V1's orange-plane sigma. Deterministic. Returns the
    operator steps and the convergence record; makes NO claim beyond
    CALIBRATED_CANDIDATE.
    """
    anchors = v2_anchors()
    S = np.array([a.source_unit for a in anchors])
    T = np.array([unit(a.target_lat, a.target_lon) for a in anchors])
    steps: list[dict] = []
    cur = S.copy()

    def resid_deg(cur):
        d = np.einsum("ij,ij->i", cur, T).clip(-1, 1)
        return np.degrees(np.arccos(d))

    history = []
    for stage, (sigma, max_steps) in enumerate(
            [(sigma_primary, max_steps_primary),
             (sigma_local, max_steps_local)]):
        best = float("inf")
        stall = 0
        for _ in range(max_steps):
            r = float(resid_deg(cur).max())
            if r < tol_deg:
                break
            # stop-on-stall: a step that no longer improves the worst
            # residual only bloats the operator (numerical floor).
            if r < best - 1e-12:
                best, stall = r, 0
            else:
                stall += 1
                if stall >= 25:
                    break
            w = gain * (T - cur)
            step = {"sigma": sigma,
                    "centers_ecef": cur.tolist(),
                    "weights_ecef": w.tolist()}
            steps.append(step)
            cur = apply_steps(cur, [step])
        history.append({"stage": stage, "sigma": sigma,
                        "steps_so_far": len(steps),
                        "max_residual_deg": float(resid_deg(cur).max())})
        if float(resid_deg(cur).max()) < tol_deg:
            break
    final = resid_deg(cur)
    return {
        "profile_id": V2_PROFILE_ID,
        "family": "composed Gaussian radial-basis landmark registration on S2 "
                  "(same family as V1)",
        "anchors": [
            {"name": a.name, "target_lat": a.target_lat,
             "target_lon": a.target_lon, "provenance": a.provenance,
             "final_residual_deg": float(final[i])}
            for i, a in enumerate(anchors)],
        "stages": history,
        "total_steps": len(steps),
        "converged": bool(final.max() < 1e-6),
        "steps": steps,
        "claim_status": "CALIBRATED_CANDIDATE_NOT_VALIDATED",
    }


# ------------------------------------------------------------- verification
def icosphere(level: int = 5) -> tuple[np.ndarray, np.ndarray]:
    """Geodesic icosphere (verts, tris) by midpoint subdivision."""
    phi = (1 + 5 ** 0.5) / 2
    v = [(-1, phi, 0), (1, phi, 0), (-1, -phi, 0), (1, -phi, 0),
         (0, -1, phi), (0, 1, phi), (0, -1, -phi), (0, 1, -phi),
         (phi, 0, -1), (phi, 0, 1), (-phi, 0, -1), (-phi, 0, 1)]
    V = [np.array(x, float) / np.linalg.norm(x) for x in v]
    F = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
         (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
         (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
         (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
    for _ in range(level):
        cache: dict = {}
        NV = list(V)
        def mid(i, j):
            key = (min(i, j), max(i, j))
            if key in cache:
                return cache[key]
            m = (NV[i] + NV[j]) / 2
            m = m / np.linalg.norm(m)
            NV.append(m)
            cache[key] = len(NV) - 1
            return cache[key]
        NF = []
        for a, b, c in F:
            ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
            NF += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
        V, F = NV, NF
    return np.array(V), np.array(F, int)


def mesh_verification(steps, level: int = 5) -> dict:
    """Orientation reversals + area distortion over a dense mesh."""
    V, F = icosphere(level)
    W = apply_steps(V, steps)

    def signed(vv):
        a, b, c = vv[F[:, 0]], vv[F[:, 1]], vv[F[:, 2]]
        return np.einsum("ij,ij->i", np.cross(b - a, c - a), (a + b + c) / 3)

    s0, s1 = signed(V), signed(W)
    flips = int(np.sum(np.sign(s0) != np.sign(s1)))
    ratio = np.abs(s1) / np.abs(s0)
    return {
        "vertices": int(len(V)), "triangles": int(len(F)),
        "orientation_reversals": flips,
        "min_area_proxy_ratio": float(ratio.min()),
        "max_area_proxy_ratio": float(ratio.max()),
        "p01_area_proxy_ratio": float(np.quantile(ratio, 0.01)),
        "p99_area_proxy_ratio": float(np.quantile(ratio, 0.99)),
        "rms_log_area_proxy": float(np.sqrt(np.mean(np.log(ratio) ** 2))),
    }


def inverse_error(steps, samples: int = 200, seed: int = 7,
                  iters: int = 40) -> dict:
    """Numerical inverse via batched Gauss-Newton on the sphere.

    All samples iterate together (finite-difference Jacobians batched)
    so the composed-operator cost stays tractable; reports how well the
    forward image of the recovered pre-image returns to the target.
    """
    rng = np.random.default_rng(seed)
    pts = rng.normal(size=(samples, 3))
    pts = pts / np.linalg.norm(pts, axis=1)[:, None]
    target = apply_steps(pts, steps)
    x = target.copy()
    eps = 1e-6
    eye = np.eye(3)
    for _ in range(iters):
        fx = apply_steps(x, steps)
        g = fx - target
        if float(np.abs(g).max()) < 1e-12:
            break
        # batched finite-difference Jacobian: 3 perturbed batch passes
        cols = [ (apply_steps(x + eps * eye[k], steps) - fx) / eps
                 for k in range(3) ]
        J = np.stack(cols, axis=2)            # (n, 3, 3)
        try:
            dx = np.linalg.solve(J + 1e-9 * eye[None, :, :],
                                 g[:, :, None])[:, :, 0]
        except np.linalg.LinAlgError:
            break
        x = x - dx
        x = x / np.linalg.norm(x, axis=1)[:, None]
    back = apply_steps(x, steps)
    d = np.clip(np.einsum("ij,ij->i", back, target), -1, 1)
    e = np.degrees(np.arccos(d))
    return {"samples": samples, "mean_deg": float(e.mean()),
            "max_deg": float(e.max()), "p50_deg": float(np.quantile(e, .5)),
            "p90_deg": float(np.quantile(e, .9)),
            "p99_deg": float(np.quantile(e, .99))}


def v1_v2_displacement(v1_steps, v2_steps, level: int = 4) -> dict:
    V, _ = icosphere(level)
    a = apply_steps(V, v1_steps)
    b = apply_steps(V, v2_steps)
    d = np.degrees(np.arccos(np.einsum("ij,ij->i", a, b).clip(-1, 1)))
    return {"grid_points": int(len(V)),
            "mean_displacement_deg": float(d.mean()),
            "max_displacement_deg": float(d.max()),
            "p50_deg": float(np.quantile(d, .5)),
            "p90_deg": float(np.quantile(d, .9))}
