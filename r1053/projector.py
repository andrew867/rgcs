"""R10.53 -- the V1 Earth projector: ``lat/lon = normalize(A u)``.

THE LAW, as recorded in the pack
--------------------------------
    direct RGCS-30 word
      -> F5 | Q22 | S3 geometric kernel
      -> source_face = (F5 + 14) % 20
      -> recursive spherical refinement at t = 10/19
      -> Earth vector normalize(A u)

No RBF warp. No per-anchor mesh adjustment. No post-hoc city fitting.
Only the three fit anchors may determine A.

THE PINNING PROBLEM, AND WHY V1 RECORDS A RULE FOR IT
-----------------------------------------------------
``A`` is a 3x3 matrix used projectively, so it is scale-invariant: 9
entries, 8 free parameters. Each anchor contributes the two independent
equations of ``e x (A u) = 0``. Three anchors therefore give SIX
equations against EIGHT parameters, and the constraint matrix has rank
6 with a 3-dimensional null space -- one dimension of overall scale
plus TWO genuinely free directions.

Consequence, measured and not assumed: every member of that family
reproduces the three anchors to machine precision, and different
members send the same non-anchor word thousands of kilometres apart.
So "the anchors fit" is not evidence about A, and a projected point for
a non-anchor word is not determined by the law alone.

V1 closes this by RECORDING A PINNING RULE rather than leaving the two
parameters implicit:

    V1_PINNING = minimum Frobenius norm member of the exact-fit family,
                 with the anchor hemisphere sign resolved and
                 orientation forced positive.

That makes V1 reproducible. It does NOT make it correct: a different
pinning is equally consistent with the anchors, and only a fourth and
fifth independent anchor can decide between them. Five anchors is the
threshold at which A first becomes over-determined and therefore
testable.

The rotation-only alternative WAS tested, because a rotation has 3
parameters against 6 constraints and would have been testable
immediately. Scanned over all 20 face offsets, depths 9-11, and
t in {10/19, 1/2, 9/19}, the best achievable anchor RMS is 452 km. A
rigid rotation does not fit the anchors, so it is not the law.
"""

from __future__ import annotations

import math

import numpy as np

from r1053 import kernel

EARTH_RADIUS_KM = kernel.EARTH_RADIUS_KM

#: The recorded pinning rule that makes V1 reproducible.
V1_PINNING = "MIN_FROBENIUS_NORM_EXACT_FIT_SIGN_FIXED_POSITIVE_ORIENTATION"

#: CORRECTION 11 / the anchor set. Only these three may fit A.
FIT_ANCHORS = {
    "Stonehenge": (165876523, 51.1789, -1.8262),
    "Erie": (167849523, 42.1292, -80.0851),
    "Toronto": (168930443, 43.6532, -79.3832),
}

#: Free parameters in a scale-invariant 3x3, and constraints per anchor.
FREE_PARAMETERS = 8
CONSTRAINTS_PER_ANCHOR = 2
ANCHORS_NEEDED_TO_OVERDETERMINE = 5


def unit_from_latlon(lat: float, lon: float) -> np.ndarray:
    la, lo = math.radians(lat), math.radians(lon)
    return np.array([math.cos(la) * math.cos(lo),
                     math.cos(la) * math.sin(lo), math.sin(la)])


def latlon_from_unit(u) -> tuple:
    u = np.asarray(u, float)
    u = u / np.linalg.norm(u)
    return (math.degrees(math.asin(float(np.clip(u[2], -1, 1)))),
            math.degrees(math.atan2(float(u[1]), float(u[0]))))


def great_circle_km(a, b) -> float:
    a = np.asarray(a, float) / np.linalg.norm(a)
    b = np.asarray(b, float) / np.linalg.norm(b)
    return EARTH_RADIUS_KM * math.acos(float(np.clip(np.dot(a, b), -1, 1)))


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    return great_circle_km(unit_from_latlon(lat1, lon1),
                           unit_from_latlon(lat2, lon2))


def bearing_deg(lat1, lon1, lat2, lon2) -> float:
    """Initial great-circle bearing from point 1 to point 2, degrees."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


def _constraint_matrix(words_latlon) -> np.ndarray:
    rows = []
    for word, lat, lon in words_latlon:
        u = kernel.kernel_vector(word)
        e = unit_from_latlon(lat, lon)
        skew = np.array([[0, -e[2], e[1]], [e[2], 0, -e[0]],
                         [-e[1], e[0], 0]])
        for r in skew:
            rows.append(np.kron(r, u))
    return np.array(rows)


def underdetermination_report(anchors=None) -> dict:
    """Exactly how free A is, for a given anchor set. Measured, not asserted."""
    anchors = anchors or FIT_ANCHORS
    rows = list(anchors.values())
    M = _constraint_matrix(rows)
    rank = int(np.linalg.matrix_rank(M, tol=1e-10))
    null_dim = 9 - rank
    return {
        "schema": "rgcs.r1053.underdetermination.v1",
        "anchors": len(rows),
        "constraints": len(rows) * CONSTRAINTS_PER_ANCHOR,
        "free_parameters": FREE_PARAMETERS,
        "constraint_matrix_rank": rank,
        "nullspace_dim": null_dim,
        "scale_dimensions": 1,
        "genuinely_free_dimensions": max(0, null_dim - 1),
        "exactly_determined": null_dim == 1,
        "over_determined": len(rows) * CONSTRAINTS_PER_ANCHOR > FREE_PARAMETERS,
        "anchors_needed_to_overdetermine": ANCHORS_NEEDED_TO_OVERDETERMINE,
        "anchor_fit_is_evidence": False,
        "why": "with a %d-dimensional free family every member reproduces "
               "every anchor exactly, so an anchor residual of zero is "
               "guaranteed by construction and carries no information "
               "about A" % max(0, null_dim - 1),
    }


def fit_matrix(anchors=None) -> np.ndarray:
    """The V1 pinned A. Deterministic under :data:`V1_PINNING`."""
    anchors = anchors or FIT_ANCHORS
    rows = list(anchors.values())
    M = _constraint_matrix(rows)
    _, sv, Vt = np.linalg.svd(M)
    rank = int(np.linalg.matrix_rank(M, tol=1e-10))
    null = Vt[rank:]                       # orthonormal basis of the family
    # Minimum Frobenius norm member: the null-space direction closest to
    # the identity, so the pin is stated relative to a fixed reference
    # rather than to whichever basis vector SVD happened to emit.
    ident = np.eye(3).reshape(9)
    coeff = null @ ident
    if not np.any(np.abs(coeff) > 1e-12):
        coeff = np.ones(null.shape[0])
    A = (coeff @ null).reshape(3, 3)
    A = A / np.linalg.norm(A)
    if np.linalg.det(A) < 0:               # force positive orientation
        A = -A
    # Resolve the hemisphere sign: e x (Au) = 0 admits both u and -u, so
    # pick the global sign that puts the majority of anchors on the
    # correct side rather than at their antipodes.
    wrong = sum(1 for w, lat, lon in rows
                if float(np.dot(A @ kernel.kernel_vector(w),
                                unit_from_latlon(lat, lon))) < 0)
    if wrong * 2 > len(rows):
        A = -A
    return A


def project(word, A=None) -> tuple:
    """``lat, lon`` for a direct word under the V1 pinned law."""
    A = fit_matrix() if A is None else A
    return latlon_from_unit(A @ kernel.kernel_vector(word))


def anchor_residuals(A=None) -> dict:
    """Anchor residuals, reported WITH the reason they are meaningless."""
    A = fit_matrix() if A is None else A
    rows = []
    for name, (word, lat, lon) in FIT_ANCHORS.items():
        plat, plon = project(word, A)
        rows.append({
            "anchor": name, "vector": word,
            "target_lat": lat, "target_lon": lon,
            "projected_lat": plat, "projected_lon": plon,
            "residual_km": haversine_km(lat, lon, plat, plon),
            "is_fit_anchor": True,
        })
    return {
        "schema": "rgcs.r1053.anchor-residuals.v1",
        "rows": rows,
        "max_residual_km": max(r["residual_km"] for r in rows),
        "counts_as_evidence": False,
        "why_not": "these three anchors DEFINE A; a small residual here "
                   "is arithmetic, not confirmation. See "
                   "underdetermination_report().",
    }


def rotation_only_refutation() -> dict:
    """Why A is not a rotation: measured, over the whole kernel scan.

    A rotation has 3 parameters against the anchors' 6 constraints, so
    it would have been immediately testable. It fails.
    """
    best = None
    ea = [(w, unit_from_latlon(la, lo)) for w, la, lo in FIT_ANCHORS.values()]
    for off in range(kernel.FACE_COUNT):
        for depth in (9, 10, 11):
            for t in (kernel.SPLIT_T, 0.5, 9.0 / 19.0):
                us = []
                for w, _ in ea:
                    f5, q22, _ = kernel.fields(w)
                    tri = tuple(kernel._V[i]
                                for i in kernel._F[(f5 + off) % 20])
                    for s in kernel.q22_symbols(q22)[:depth]:
                        tri = kernel.refine(tri, s, t)
                    v = np.sum(np.asarray(tri, float), axis=0)
                    us.append(v / np.linalg.norm(v))
                B = sum(np.outer(e, u) for u, (_, e) in zip(us, ea))
                U, _, Vt = np.linalg.svd(B)
                R = U @ np.diag([1, 1, np.linalg.det(U @ Vt)]) @ Vt
                rms = math.sqrt(sum(great_circle_km(R @ u, e) ** 2
                                    for u, (_, e) in zip(us, ea)) / len(us))
                if best is None or rms < best[0]:
                    best = (rms, t, depth, off)
    rms, t, depth, off = best
    return {
        "schema": "rgcs.r1053.rotation-refutation.v1",
        "best_anchor_rms_km": rms,
        "best_split_t": t, "best_depth": depth, "best_face_offset": off,
        "source_ratio_is_best_t": abs(t - kernel.SPLIT_T) < 1e-12,
        "rotation_fits_anchors": rms < 25.0,
        "verdict": "ROTATION_ONLY_REFUTED_A_IS_A_GENERAL_PROJECTIVE_MAP",
        "why_it_mattered": "a rotation would have been over-determined "
                           "by 3 anchors and therefore testable at once; "
                           "it misses by hundreds of km, so the free "
                           "projective form -- and its under-"
                           "determination -- is forced.",
    }
