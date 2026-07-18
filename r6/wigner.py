"""Real Wigner D-matrices and polyhedral group projectors.

This module exists because the first version of the grid audit used a
"rotation-like" dense mixing of spherical-harmonic coefficients as a
stand-in for D^l(R). That stand-in destroyed exactly the structure the
audit was meant to measure: after mixing, power injected into a
group-invariant subspace was spread across all components, so the
detector could not find a symmetry of *any* strength. A null result
from a blind detector is worthless, so the real thing is implemented
here.

Two objects:

``wigner_D(l, alpha, beta, gamma)``
    The genuine (2l+1) x (2l+1) representation matrix, built from the
    Wigner small-d recursion, with the ZYZ convention

        D^l_{m'm} = e^{-i m' alpha} d^l_{m'm}(beta) e^{-i m gamma}.

``group_projector(l, group)``
    The projector onto the subspace of degree-l functions invariant
    under a polyhedral rotation group,

        P = (1/|G|) sum_{g in G} D^l(g),

built by explicitly enumerating the group elements as unit
quaternions. Because P is a projector, ``trace(P)`` must be a
non-negative *integer* equal to the dimension of the invariant
subspace — a strong self-check that the group enumeration and the
D-matrices are both correct. :func:`verify_projector` asserts it.
"""

from __future__ import annotations

import cmath
import math
from functools import lru_cache

PHI = (1.0 + math.sqrt(5.0)) / 2.0

#: Orders of the rotation groups (not the binary covers).
GROUP_ORDERS = {"TETRAHEDRAL": 12, "OCTAHEDRAL": 24,
                "ICOSAHEDRAL": 60, "DODECAHEDRAL": 60}


# --------------------------------------------------------------------
# Wigner small-d and D
# --------------------------------------------------------------------

@lru_cache(maxsize=None)
def _fact(n: int) -> float:
    return float(math.factorial(n))


def wigner_small_d(l: int, mp: int, m: int, beta: float) -> float:
    """Wigner small-d, d^l_{m'm}(beta), by the explicit sum.

    Exact term-by-term; fine for the degrees used here (l <= ~20).
    The sign convention is Varshalovich's, with the phase
    ``(-1)^(k - m + m')``. Using a bare ``(-1)^k`` instead produces a
    matrix related to the correct one by the diagonal similarity
    S = diag((-1)^m), which is unitary, idempotent under projection,
    and trace-preserving — so it passes every structural check while
    still giving wrong individual matrix elements. It is fixed here
    against the closed forms for l=1 rather than against a structural
    property that cannot see the error.
    """
    c = math.cos(beta / 2.0)
    s = math.sin(beta / 2.0)
    pref = math.sqrt(_fact(l + mp) * _fact(l - mp)
                     * _fact(l + m) * _fact(l - m))
    total = 0.0
    kmin = max(0, m - mp)
    kmax = min(l + m, l - mp)
    for k in range(kmin, kmax + 1):
        denom = (_fact(l + m - k) * _fact(k) * _fact(l - mp - k)
                 * _fact(mp - m + k))
        cpow = 2 * l + m - mp - 2 * k
        spow = mp - m + 2 * k
        term = ((-1.0) ** (k - m + mp)) / denom
        term *= (c ** cpow) if cpow else 1.0
        term *= (s ** spow) if spow else 1.0
        total += term
    return pref * total


def wigner_D(l: int, alpha: float, beta: float, gamma: float
             ) -> list[list[complex]]:
    """D^l(alpha, beta, gamma), indexed [m'+l][m+l]."""
    n = 2 * l + 1
    out = [[0j] * n for _ in range(n)]
    for i in range(n):
        mp = i - l
        for j in range(n):
            m = j - l
            out[i][j] = (cmath.exp(-1j * mp * alpha)
                         * wigner_small_d(l, mp, m, beta)
                         * cmath.exp(-1j * m * gamma))
    return out


def apply_D(D: list[list[complex]], vec: list[complex]) -> list[complex]:
    return [sum(D[i][j] * vec[j] for j in range(len(vec)))
            for i in range(len(D))]


# --------------------------------------------------------------------
# Group elements as quaternions
# --------------------------------------------------------------------

def _norm(q):
    n = math.sqrt(sum(x * x for x in q))
    return tuple(x / n for x in q)


def _even_permutations(t):
    a, b, c, d = t
    return [(a, b, c, d), (a, c, d, b), (a, d, b, c),
            (b, a, d, c), (b, c, a, d), (b, d, c, a),
            (c, a, b, d), (c, b, d, a), (c, d, a, b),
            (d, a, c, b), (d, b, a, c), (d, c, b, a)]


def _dedupe_projective(quats):
    """Collapse q and -q (they are the same rotation)."""
    out = []
    for q in quats:
        q = _norm(q)
        dup = False
        for r in out:
            if all(abs(a - b) < 1e-9 for a, b in zip(q, r)) or \
               all(abs(a + b) < 1e-9 for a, b in zip(q, r)):
                dup = True
                break
        if not dup:
            out.append(q)
    return out


def _binary_tetrahedral():
    q = []
    for i in range(4):
        for s in (1.0, -1.0):
            v = [0.0] * 4
            v[i] = s
            q.append(tuple(v))
    for a in (0.5, -0.5):
        for b in (0.5, -0.5):
            for c in (0.5, -0.5):
                for d in (0.5, -0.5):
                    q.append((a, b, c, d))
    return q


def _binary_octahedral():
    q = list(_binary_tetrahedral())
    r = 1.0 / math.sqrt(2.0)
    for i in range(4):
        for j in range(i + 1, 4):
            for si in (r, -r):
                for sj in (r, -r):
                    v = [0.0] * 4
                    v[i] = si
                    v[j] = sj
                    q.append(tuple(v))
    return q


def _binary_icosahedral():
    q = list(_binary_tetrahedral())[:8]
    for a in (0.5, -0.5):
        for b in (0.5, -0.5):
            for c in (0.5, -0.5):
                for d in (0.5, -0.5):
                    q.append((a, b, c, d))
    half = 0.5
    base = (0.0, half, half / PHI, half * PHI)
    seen = []
    for s1 in (1, -1):
        for s2 in (1, -1):
            for s3 in (1, -1):
                t = (base[0], s1 * base[1], s2 * base[2], s3 * base[3])
                for p in _even_permutations(t):
                    seen.append(p)
    q.extend(seen)
    return q


@lru_cache(maxsize=None)
def group_elements(group: str) -> tuple:
    """Unit quaternions for one representative of each rotation."""
    if group in ("ICOSAHEDRAL", "DODECAHEDRAL"):
        raw = _binary_icosahedral()
    elif group == "OCTAHEDRAL":
        raw = _binary_octahedral()
    elif group == "TETRAHEDRAL":
        raw = _binary_tetrahedral()
    else:
        raise ValueError(f"no rotation group for {group!r}")
    els = _dedupe_projective(raw)
    expected = GROUP_ORDERS[group]
    if len(els) != expected:
        raise RuntimeError(
            f"{group}: enumerated {len(els)} rotations, expected "
            f"{expected}; the group construction is wrong")
    return tuple(els)


def quat_to_euler_zyz(q) -> tuple[float, float, float]:
    """Unit quaternion -> ZYZ Euler angles."""
    w, x, y, z = q
    # rotation matrix entries needed for ZYZ extraction
    r02 = 2 * (x * z + w * y)
    r12 = 2 * (y * z - w * x)
    r22 = 1 - 2 * (x * x + y * y)
    r20 = 2 * (x * z - w * y)
    r21 = 2 * (y * z + w * x)
    beta = math.acos(max(-1.0, min(1.0, r22)))
    if abs(math.sin(beta)) < 1e-12:
        # degenerate: fold alpha and gamma together
        r00 = 1 - 2 * (y * y + z * z)
        r10 = 2 * (x * y + w * z)
        alpha = math.atan2(r10, r00)
        gamma = 0.0
    else:
        alpha = math.atan2(r12, r02)
        gamma = math.atan2(r21, -r20)
    return alpha, beta, gamma


# --------------------------------------------------------------------
# Group projector
# --------------------------------------------------------------------

@lru_cache(maxsize=None)
def group_projector(l: int, group: str) -> tuple:
    """P = (1/|G|) sum_g D^l(g), as a tuple-of-tuples matrix."""
    els = group_elements(group)
    n = 2 * l + 1
    acc = [[0j] * n for _ in range(n)]
    for q in els:
        a, b, g = quat_to_euler_zyz(q)
        D = wigner_D(l, a, b, g)
        for i in range(n):
            for j in range(n):
                acc[i][j] += D[i][j]
    inv = 1.0 / len(els)
    return tuple(tuple(x * inv for x in row) for row in acc)


def invariant_dimension(l: int, group: str) -> int:
    """dim of the invariant subspace = trace of the projector.

    The trace must come out an integer; a non-integer means the group
    enumeration or the D-matrices are wrong, so it is checked rather
    than rounded silently.
    """
    P = group_projector(l, group)
    tr = sum(P[i][i] for i in range(len(P)))
    if abs(tr.imag) > 1e-6:
        raise RuntimeError(
            f"projector trace for l={l}, {group} is not real: {tr}")
    d = round(tr.real)
    if abs(tr.real - d) > 1e-6:
        raise RuntimeError(
            f"projector trace for l={l}, {group} is {tr.real:.6f}, "
            f"not an integer; the projector is not idempotent")
    return d


def verify_projector(l: int, group: str, tol: float = 1e-8) -> dict:
    """Check P^2 = P and P = P^dagger."""
    P = group_projector(l, group)
    n = len(P)
    max_idem = 0.0
    for i in range(n):
        for j in range(n):
            p2 = sum(P[i][k] * P[k][j] for k in range(n))
            max_idem = max(max_idem, abs(p2 - P[i][j]))
    max_herm = max(abs(P[i][j] - P[j][i].conjugate())
                   for i in range(n) for j in range(n))
    return {
        "l": l, "group": group,
        "dimension": invariant_dimension(l, group),
        "max_idempotency_error": max_idem,
        "max_hermiticity_error": max_herm,
        "ok": max_idem < tol and max_herm < tol,
    }


def project(vec: list[complex], l: int, group: str) -> list[complex]:
    P = group_projector(l, group)
    return [sum(P[i][j] * vec[j] for j in range(len(vec)))
            for i in range(len(P))]
