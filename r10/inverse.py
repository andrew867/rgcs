"""Q19 — Inverse hidden-hedron estimation.

Reproduce the method-of-moments estimator that recovers an unknown
tetrahedron's four vertices from points sampled uniformly inside it,
then measure precisely how much of that result survives when the
conditions the R10.1 pack actually cares about are imposed.

The short answer is: the reproduction works, and almost none of it
survives.

The algebra
-----------

Let the tetrahedron have vertices ``v_0..v_3`` and let ``X`` be a
uniform draw from its interior. Write ``X = sum_i W_i v_i`` with
barycentric weights ``W ~ Dirichlet(1,1,1,1)`` -- this is the standard
construction, and :func:`uniformity_chi_square` checks it rather than
assuming it.

*First moment.* ``E[W_i] = 1/4``, so the distribution mean is the
vertex centroid ``mu = (1/4) sum_i v_i``. Write ``c_i = v_i - mu`` for
the centred vertices; ``sum_i c_i = 0`` by construction.

*Second moment.* For ``Dirichlet(1,1,1,1)``, ``Cov(W) = (4I - J)/80``.
Pushing through the linear map ``V`` (the 3x4 matrix of vertices),

    Cov(X) = V Cov(W) V^T
           = (1/80)(4 V V^T - (V1)(V1)^T)
           = (1/20)(V V^T - 4 mu mu^T)
           = (1/20) sum_i c_i c_i^T

so the *scatter matrix* ``S = sum_i c_i c_i^T`` is exactly ``20`` times
the population covariance. That is :data:`SECOND_MOMENT_FACTOR`.

*Third moment.* The third central moments of ``Dirichlet(1,1,1,1)``
decompose exactly as

    m_ijk = A*[i=j=k] + B*(d_ij + d_ik + d_jk) + D

with ``A = 1/60``, ``B = -1/240``, ``D = 1/480``
(:func:`dirichlet_third_central_moments`). Contracting against
``c_i (x) c_j (x) c_k``, every ``B`` term carries a factor
``sum_i c_i = 0`` and the ``D`` term carries ``(sum_i c_i)^(x)3 = 0``,
so both annihilate and

    T = E[(X - mu)^(x)3] = (1/60) sum_i c_i^(x)3

exactly. That is :data:`THIRD_MOMENT_FACTOR`, and
:func:`test_third_moment_identity` in the test module checks it against
simulation rather than trusting the derivation.

*Why the third moment is not optional.* ``S`` has 6 independent
entries; the centred vertices have 9 degrees of freedom (12 minus the
3 imposed by ``sum c_i = 0``). Second moments are therefore three
short, and the deficiency is exactly an ``O(3)`` orbit:
:func:`second_moment_twin` constructs, in closed form, a genuinely
differently-shaped tetrahedron with *identical* mean and covariance.
Mean and covariance alone never identify a tetrahedron.

*The whitened configuration is always the same tetrahedron.* Let
``Wh = S^(-1/2)`` and ``u_i = Wh c_i``. Then ``sum_i u_i u_i^T = I``
and ``sum_i u_i = 0``, so the Gram matrix of the ``u_i`` is forced:
``G = U^T U`` has ``G1 = 0`` and the same nonzero spectrum as ``I_3``,
hence ``G = I_4 - J/4`` -- that is, ``|u_i|^2 = 3/4`` and
``u_i . u_j = -1/4`` for every tetrahedron whatsoever. The whitened
vertices are *always* a regular simplex frame, so after whitening the
only unknown left is an element of ``O(3)``, and the whitened third
moment ``T_w = sum_i u_i^(x)3`` is what pins it down.

*Extracting the rotation.* The cubic form ``f(x) = T_w(x,x,x)`` on the
unit sphere has strict maxima exactly at the four directions
``u_i/|u_i|``, with value ``1/sqrt(3)``. Textbook tensor power
iteration ``x <- T_w(I,x,x)/|.|`` does **not** work here, and this is a
real property of the problem rather than an implementation slip: at a
fixed point the transverse derivative of that map is exactly ``-1``, so
the fixed points are neutrally stable and the iterate wanders. The
shifted iteration

    x <- normalise( T_w(I,x,x) + f(x) * x )

cancels the ``-1`` to first order and converges in a handful of steps
(:func:`extract_directions`). The shift ``f(x)`` is not tuned; it is
the value that makes the first-order coefficient vanish identically.

Provenance and evidence class
-----------------------------

The prior art is operator-supplied: a 2018 method-of-moments paper on
recovering a simplex from uniform interior samples. **The citation
could not be verified in this environment**, so nothing here is
attributed to it in detail; the derivation above was carried out from
scratch and every step is checked numerically by the test module. The
correct evidence class for a successful run is
``LITERATURE_REPRODUCTION`` and never anything stronger. Per the
R10.1 claim policy: *a tetrahedral inverse estimator is not proof that
the hidden object is tetrahedral.* See
:func:`refuse_earth_sphere_inverse`.

Nothing in this module is a measurement. Every number it produces is
``SYNTHETIC_RESULT`` computed from a seeded generator.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from fractions import Fraction
from itertools import permutations

import numpy as np

# --- constants, with provenance ---------------------------------------

#: Dirichlet concentration giving the uniform distribution on the
#: 3-simplex. Derived, not chosen: Dirichlet(1,1,1,1) has constant
#: density on the simplex, and the barycentric map to the tetrahedron
#: is affine, so it carries uniform to uniform.
UNIFORM_ALPHA = 1.0

#: Cov(X) = (1/20) sum_i c_i c_i^T for uniform sampling in a
#: tetrahedron. Exact; derived in the module docstring from
#: Cov(Dirichlet(1,1,1,1)) = (4I - J)/80.
SECOND_MOMENT_FACTOR = Fraction(20)

#: E[(X-mu)^(x)3] = (1/60) sum_i c_i^(x)3. Exact; the other two terms
#: of the third-moment decomposition annihilate against sum_i c_i = 0.
THIRD_MOMENT_FACTOR = Fraction(60)

#: |u_i|^2 for the whitened vertices, forced by
#: sum u_i u_i^T = I and sum u_i = 0. Exact, and independent of the
#: tetrahedron being estimated.
WHITENED_VERTEX_NORM_SQ = Fraction(3, 4)

#: ||sum_i u_i^(x)3||_F^2 = sum_{i,j} (u_i . u_j)^3
#:                        = 4*(3/4)^3 + 12*(-1/4)^3 = 3/2.
#: Exact. Used as the denominator of the third-moment signal
#: diagnostic, so a whitened tensor from clean uniform data scores 1.
CANONICAL_THIRD_NORM_SQ = Fraction(3, 2)

#: Maximum of f(x) = T_w(x,x,x) on the unit sphere, attained at each
#: whitened vertex direction: (3/4)^1.5 + 3*(-1/4)*(3/4)^0.5*... see
#: docstring; the value is 1/sqrt(3).
CANONICAL_CUBIC_MAX = 1.0 / math.sqrt(3.0)

#: A whitened regular simplex frame with |e_i|^2 = 3/4 and
#: e_i . e_j = -1/4. Any tetrahedron whitens to an O(3) image of this.
CANONICAL_WHITENED_SIMPLEX = np.array(
    [[1.0, 1.0, 1.0],
     [1.0, -1.0, -1.0],
     [-1.0, 1.0, -1.0],
     [-1.0, -1.0, 1.0]]) / 2.0

#: Seed for every default draw in this module. Fixed so that reported
#: numbers, nulls and failures are reproducible.
DEFAULT_SEED = 20260719

#: Below this fraction of the canonical whitened third-moment norm the
#: estimator refuses rather than returning a shape. This threshold is a
#: judgement call, NOT a derived quantity: it was set by inspecting the
#: shell-constrained and uniform regimes, which are separated by more
#: than an order of magnitude. It catches the "no third-moment signal"
#: failure and it does NOT catch the non-uniform-density failure, which
#: leaves the signal healthy and the answer wrong.
THIRD_MOMENT_SIGNAL_FLOOR = 0.30


class EstimatorFailure(RuntimeError):
    """Raised when the estimator cannot return a tetrahedron it believes."""


class InverseClaimRefused(RuntimeError):
    """Raised when a reproduction is offered as an Earth-sphere result."""


class NotIdentifiable(ValueError):
    """Raised when the observation model cannot distinguish the answers."""


# --- exact moment algebra ----------------------------------------------

def dirichlet_uniform_covariance() -> list[list[Fraction]]:
    """Cov(W) for W ~ Dirichlet(1,1,1,1), exactly. Equals (4I - J)/80."""
    out = []
    for i in range(4):
        row = []
        for j in range(4):
            # E[W_i W_j] - 1/16, with E[W_i^2] = 1/10 and E[W_i W_j] = 1/20.
            raw = Fraction(1, 10) if i == j else Fraction(1, 20)
            row.append(raw - Fraction(1, 16))
        out.append(row)
    return out


def dirichlet_third_central_moments() -> dict[str, Fraction]:
    """Third central moments of Dirichlet(1,1,1,1), by index pattern.

    Computed from the raw moments
    ``E[W_i W_j W_k] = prod rising(alpha) / rising(alpha_0)`` with
    ``alpha_0 (alpha_0+1)(alpha_0+2) = 4*5*6 = 120``, then centred.
    """
    mu = Fraction(1, 4)
    e2_same, e2_diff = Fraction(1, 10), Fraction(1, 20)

    def central(raw: Fraction, pair_sum: Fraction) -> Fraction:
        return raw - mu * pair_sum + 2 * mu ** 3

    return {
        # i = j = k
        "triple": central(Fraction(6, 120), 3 * e2_same),
        # i = j != k
        "pair": central(Fraction(2, 120), e2_same + 2 * e2_diff),
        # i, j, k all distinct
        "distinct": central(Fraction(1, 120), 3 * e2_diff),
    }


def third_moment_decomposition() -> dict[str, Fraction]:
    """Solve ``m_ijk = A[i=j=k] + B(d_ij + d_ik + d_jk) + D``.

    Only ``A`` survives contraction against centred vertices, because
    every ``B`` and ``D`` term carries a factor ``sum_i c_i = 0``.
    ``1/A = 60`` is :data:`THIRD_MOMENT_FACTOR`.
    """
    m = dirichlet_third_central_moments()
    d = m["distinct"]
    b = m["pair"] - d
    a = m["triple"] - 3 * b - d
    return {"A": a, "B": b, "D": d}


# --- geometry helpers ---------------------------------------------------

def _as_vertices(vertices) -> np.ndarray:
    v = np.asarray(vertices, dtype=float)
    if v.shape != (4, 3):
        raise ValueError(f"expected 4 vertices in 3-D, got shape {v.shape}")
    return v


def tetrahedron_volume(vertices) -> float:
    v = _as_vertices(vertices)
    return abs(float(np.linalg.det(v[1:] - v[0]))) / 6.0


def tetrahedron_scale(vertices) -> float:
    """Max distance from centroid to a vertex. The length unit for
    every relative error reported here."""
    v = _as_vertices(vertices)
    return float(np.max(np.linalg.norm(v - v.mean(axis=0), axis=1)))


def insphere(vertices) -> tuple[np.ndarray, float]:
    """Centre and radius of the inscribed sphere.

    ``r = 3V/A_total``; the centre is the face-area-weighted mean of the
    opposite vertices. Used by the shell experiments and by the
    non-identifiability construction.
    """
    v = _as_vertices(vertices)
    areas = np.empty(4)
    for i in range(4):
        a, b, c = np.delete(v, i, axis=0)
        areas[i] = 0.5 * float(np.linalg.norm(np.cross(b - a, c - a)))
    total = float(areas.sum())
    if total <= 0:
        raise ValueError("degenerate tetrahedron has no insphere")
    centre = (areas[:, None] * v).sum(axis=0) / total
    radius = 3.0 * tetrahedron_volume(v) / total
    return centre, radius


def circumscribing_tetrahedron(normals, centre, radius) -> np.ndarray:
    """The tetrahedron whose four faces are tangent to a given sphere.

    ``normals`` are four outward unit face normals; the faces are the
    planes ``n_i . (x - centre) = radius``. The result has exactly that
    sphere as its insphere, whatever the normals are -- which is the
    whole content of :func:`shell_nonidentifiability_example`.
    """
    n = np.asarray(normals, dtype=float)
    if n.shape != (4, 3):
        raise ValueError(f"expected 4 normals, got shape {n.shape}")
    n = n / np.linalg.norm(n, axis=1, keepdims=True)
    if np.linalg.matrix_rank(n) < 3:
        raise ValueError("normals must span 3-D or the solid is unbounded")
    centre = np.asarray(centre, dtype=float)
    verts = []
    for drop in range(4):
        keep = np.delete(np.arange(4), drop)
        a = n[keep]
        if abs(float(np.linalg.det(a))) < 1e-12:
            raise ValueError("three face normals are coplanar")
        verts.append(np.linalg.solve(a, np.full(3, float(radius))) + centre)
    return np.array(verts)


def barycentric(points, vertices) -> np.ndarray:
    """Barycentric coordinates of points with respect to a tetrahedron."""
    v = _as_vertices(vertices)
    p = np.atleast_2d(np.asarray(points, dtype=float))
    m = np.vstack([v.T, np.ones(4)])
    rhs = np.vstack([p.T, np.ones(len(p))])
    return np.linalg.solve(m, rhs).T


def _rotation(axis, angle) -> np.ndarray:
    """Rodrigues rotation matrix."""
    k = np.asarray(axis, dtype=float)
    k = k / np.linalg.norm(k)
    kx = np.array([[0.0, -k[2], k[1]], [k[2], 0.0, -k[0]], [-k[1], k[0], 0.0]])
    return (np.eye(3) + math.sin(angle) * kx
            + (1.0 - math.cos(angle)) * (kx @ kx))


#: A reference tetrahedron: irregular enough that an isotropy bug shows
#: up, non-degenerate enough to whiten cleanly. Arbitrary, and fixed so
#: that reported numbers are reproducible.
REFERENCE_TETRAHEDRON = np.array(
    [[0.0, 0.0, 0.0],
     [3.0, 0.0, 0.0],
     [0.4, 2.0, 0.0],
     [0.7, 0.9, 1.6]])


# --- the forward model --------------------------------------------------

def _rng(seed_or_rng) -> np.random.Generator:
    if isinstance(seed_or_rng, np.random.Generator):
        return seed_or_rng
    return np.random.default_rng(DEFAULT_SEED if seed_or_rng is None
                                 else seed_or_rng)


def sample_uniform(vertices, n, seed=None) -> np.ndarray:
    """Uniform samples from a tetrahedron's interior.

    Barycentric weights from Dirichlet(1,1,1,1). This is the assumption
    the whole estimator rests on; :func:`uniformity_chi_square` tests it.
    """
    return sample_dirichlet(vertices, n, alpha=UNIFORM_ALPHA, seed=seed)


def sample_dirichlet(vertices, n, alpha=UNIFORM_ALPHA, seed=None
                     ) -> np.ndarray:
    """Samples with Dirichlet(alpha) barycentric weights.

    ``alpha`` may be a scalar or a length-4 vector. Anything other than
    all-ones is a violation of the estimator's assumption, and that is
    the point: this is the knob for the non-uniform-density experiment.
    Scalar ``alpha > 1`` concentrates towards the centroid, ``< 1``
    towards the vertices and edges; an unequal vector concentrates
    towards a face or a vertex.
    """
    v = _as_vertices(vertices)
    a = np.broadcast_to(np.asarray(alpha, dtype=float), (4,)).astype(float)
    if np.any(a <= 0):
        raise ValueError("Dirichlet concentrations must be positive")
    return _rng(seed).dirichlet(a, size=int(n)) @ v


def sample_normalised_uniform(vertices, n, seed=None) -> np.ndarray:
    """A *deliberately wrong* sampler: weights from normalised U(0,1).

    This looks like a reasonable way to get barycentric coordinates and
    is not uniform on the tetrahedron -- it concentrates towards the
    centroid. It exists so the uniformity test has something it must
    reject; a test that only ever sees correct input is not a test.
    """
    v = _as_vertices(vertices)
    w = _rng(seed).random((int(n), 4))
    return (w / w.sum(axis=1, keepdims=True)) @ v


def sample_shell(vertices, n, inner_frac=0.0, outer_frac=0.9, clip=False,
                 seed=None) -> np.ndarray:
    """Samples confined to a spherical shell about the insphere centre.

    ``inner_frac`` and ``outer_frac`` are fractions of the insphere
    radius, so ``outer_frac <= 1`` keeps the whole shell strictly inside
    the tetrahedron. That is the regime where the observations carry no
    information about the tetrahedron at all -- see
    :func:`shell_nonidentifiability_example`.

    ``clip=True`` discards points outside the tetrahedron, which only
    bites once ``outer_frac > 1``. The distinction matters: a shell
    strictly inside the solid is *non-identifiable*, whereas a shell cut
    by the faces does carry information about where the faces are. The
    second case is identifiable in principle and still not recoverable
    by this estimator, because the moment identities it inverts were
    derived for the uniform interior density and do not hold.
    """
    v = _as_vertices(vertices)
    centre, r_in = insphere(v)
    r0, r1 = float(inner_frac) * r_in, float(outer_frac) * r_in
    if not 0.0 <= r0 < r1:
        raise ValueError("need 0 <= inner_frac < outer_frac")
    rng = _rng(seed)
    n = int(n)
    kept = []
    total = 0
    while total < n:
        batch = max(int(n), 1024)
        d = rng.normal(size=(batch, 3))
        d /= np.linalg.norm(d, axis=1, keepdims=True)
        # radius with density proportional to r^2 between r0 and r1
        r = (r0 ** 3 + (r1 ** 3 - r0 ** 3) * rng.random(batch)) ** (1.0 / 3.0)
        pts = centre + r[:, None] * d
        if clip:
            pts = pts[(barycentric(pts, v) >= 0.0).all(axis=1)]
            if len(pts) == 0:
                raise ValueError(
                    "clipping removed every point; the shell lies entirely "
                    "outside the tetrahedron")
        kept.append(pts)
        total += len(pts)
    return np.concatenate(kept)[:n]


def sample_rotating(vertices, n, total_angle, axis=(0.0, 0.0, 1.0),
                    drift=(0.0, 0.0, 0.0), seed=None) -> np.ndarray:
    """Uniform samples from a tetrahedron moving during acquisition.

    Sample ``k`` is drawn from the tetrahedron rotated by
    ``total_angle * k/(n-1)`` about an axis through its centroid and
    translated by ``drift * k/(n-1)``. The estimator sees one point
    cloud and has no idea it is a mixture.
    """
    v = _as_vertices(vertices)
    n = int(n)
    centroid = v.mean(axis=0)
    w = _rng(seed).dirichlet(np.full(4, UNIFORM_ALPHA), size=n)
    angles = np.linspace(0.0, float(total_angle), n)
    # Rotate the tetrahedron, not the points: the target moves. Because
    # the barycentric map is affine, rotating the vertices and then
    # combining is the same as combining and then rotating, which makes
    # this a vectorised Rodrigues application rather than a loop.
    k = np.asarray(axis, dtype=float)
    k = k / np.linalg.norm(k)
    kx = np.array([[0.0, -k[2], k[1]], [k[2], 0.0, -k[0]],
                   [-k[1], k[0], 0.0]])
    body = w @ v - centroid
    frac = np.linspace(0.0, 1.0, n)[:, None]
    return (centroid + body
            + np.sin(angles)[:, None] * (body @ kx.T)
            + (1.0 - np.cos(angles))[:, None] * (body @ (kx @ kx).T)
            + frac * np.asarray(drift, dtype=float))


def sample_square_pyramid(n, half_base=1.0, height=2.0, seed=None
                          ) -> np.ndarray:
    """Uniform samples in a square pyramid. Not a tetrahedron, and not
    centrally symmetric either, so it is the interesting alternative
    model: it cannot be rejected merely for having a vanishing third
    moment."""
    rng = _rng(seed)
    n = int(n)
    h, a = float(height), float(half_base)
    # cross-section area falls as (1 - z/h)^2, so the height CDF gives
    # z = h(1 - (1-U)^(1/3)).
    z = h * (1.0 - (1.0 - rng.random(n)) ** (1.0 / 3.0))
    s = a * (1.0 - z / h)
    return np.stack([(2.0 * rng.random(n) - 1.0) * s,
                     (2.0 * rng.random(n) - 1.0) * s, z], axis=1)


def sample_box(n, half_widths=(1.0, 1.0, 1.0), seed=None) -> np.ndarray:
    """Uniform samples in a box. Centrally symmetric, so its third
    central moment vanishes identically."""
    hw = np.asarray(half_widths, dtype=float)
    return (2.0 * _rng(seed).random((int(n), 3)) - 1.0) * hw


def model_class_probe(n=100_000, seed=None) -> dict:
    """Does the estimator reject solids that are not tetrahedra?

    Recorded because honesty runs both ways. The estimator turns out to
    be more discriminating than "it returns a tetrahedron for anything":
    a box and a Gaussian have no third moment to decompose, and a square
    pyramid does have one but not a simplex frame, so all three are
    refused. That is a genuine and useful property.

    It is still not a licence. What the estimator cannot detect is a
    *true* tetrahedron observed through a broken assumption -- a biased
    density, a drift, a small rotation -- and those are precisely the
    conditions the R10.1 pack imposes. See :func:`degradation_report`:
    the alternatives it rejects are not the alternatives that matter
    here.
    """
    rng = _rng(seed)
    out = {}
    cases = {
        "tetrahedron_uniform": lambda: sample_uniform(
            REFERENCE_TETRAHEDRON, n, seed=rng),
        "square_pyramid": lambda: sample_square_pyramid(n, seed=rng),
        "box": lambda: sample_box(n, half_widths=(1.0, 1.3, 0.7), seed=rng),
        "gaussian": lambda: rng.normal(size=(int(n), 3)),
    }
    for name, make in cases.items():
        try:
            est = estimate_vertices(make(), seed=rng)
        except EstimatorFailure as exc:
            out[name] = {"refused": True, "reason": str(exc)}
        else:
            out[name] = {"refused": False,
                         "third_moment_signal": est.third_moment_signal,
                         "closure_residual": est.closure_residual}
    out["what_this_does_not_say"] = (
        "that a non-refusal identifies the object as a tetrahedron. "
        "These four alternatives were chosen by the author, they are not "
        "an exhaustive model space, and the failure modes that matter "
        "for the pack are all ones the estimator accepts without "
        "complaint")
    return out


# --- checking that the forward model really is uniform ------------------

def uniformity_chi_square(points, vertices) -> dict:
    """Chi-square test against exactly known sub-region volume ratios.

    Midpoint subdivision splits a tetrahedron into four corner cells
    (``w_i > 1/2``, each a half-scale copy, volume ratio ``1/8``) and a
    central octahedron (volume ratio ``1/2``). The corner events are
    disjoint, so this is a 5-cell multinomial with known probabilities
    and 4 degrees of freedom, tested against nothing but geometry.
    """
    w = barycentric(points, vertices)
    n = len(w)
    corner = w > 0.5
    if np.any(corner.sum(axis=1) > 1):
        raise ValueError("two barycentric coordinates above 1/2 is impossible")
    counts = np.concatenate([corner.sum(axis=0), [n - int(corner.sum())]])
    probs = np.array([0.125, 0.125, 0.125, 0.125, 0.5])
    expected = n * probs
    stat = float((((counts - expected) ** 2) / expected).sum())
    # Survival function of chi-square with 4 dof, in closed form:
    # P(X > x) = (1 + x/2) exp(-x/2).
    p = (1.0 + stat / 2.0) * math.exp(-stat / 2.0)
    return {
        "n": n,
        "counts": counts.tolist(),
        "expected": expected.tolist(),
        "chi_square": stat,
        "dof": 4,
        "p_value": p,
        "cell_probabilities": probs.tolist(),
        "basis": "midpoint subdivision volume ratios: 4 x 1/8 plus 1/2",
    }


def volume_ratio_check(points, vertices, thresholds=(0.25, 0.5, 0.75)) -> list:
    """Independent uniformity check: ``P(w_0 >= t) = (1-t)^3``.

    The region ``w_0 >= t`` is a similar tetrahedron scaled by
    ``1 - t``, so its volume ratio is ``(1-t)^3``. Reports the observed
    fraction, the exact expectation and the deviation in binomial
    standard errors.
    """
    w = barycentric(points, vertices)
    n = len(w)
    out = []
    for t in thresholds:
        expected = (1.0 - t) ** 3
        observed = float((w[:, 0] >= t).mean())
        se = math.sqrt(expected * (1.0 - expected) / n)
        out.append({
            "threshold": t,
            "expected_fraction": expected,
            "observed_fraction": observed,
            "sigma": (observed - expected) / se if se > 0 else 0.0,
        })
    return out


# --- the estimator ------------------------------------------------------

@dataclass(frozen=True)
class Moments:
    """Empirical moments, already scaled into vertex-scatter form."""

    n: int
    mean: np.ndarray            # estimate of the centroid mu
    scatter: np.ndarray         # 20 * Cov  ->  sum_i c_i c_i^T
    third: np.ndarray           # 60 * E[(X-mu)^3]  ->  sum_i c_i^3


def empirical_moments(points) -> Moments:
    """Sample moments, scaled by the exact factors 20 and 60."""
    p = np.asarray(points, dtype=float)
    if p.ndim != 2 or p.shape[1] != 3:
        raise ValueError(f"expected an (n,3) point cloud, got {p.shape}")
    if len(p) < 4:
        raise EstimatorFailure(
            f"{len(p)} points cannot determine 4 vertices; the third "
            f"moment tensor alone needs far more")
    mu = p.mean(axis=0)
    c = p - mu
    s = float(SECOND_MOMENT_FACTOR) * (c.T @ c) / len(p)
    t = float(THIRD_MOMENT_FACTOR) * np.einsum(
        "ni,nj,nk->ijk", c, c, c, optimize=True) / len(p)
    return Moments(n=len(p), mean=mu, scatter=s, third=t)


def whitening(scatter) -> tuple[np.ndarray, np.ndarray]:
    """Symmetric ``S^(-1/2)`` and its inverse."""
    s = np.asarray(scatter, dtype=float)
    vals, vecs = np.linalg.eigh(0.5 * (s + s.T))
    if np.min(vals) <= 1e-12 * max(float(np.max(vals)), 1.0):
        raise EstimatorFailure(
            f"scatter matrix is singular (eigenvalues {vals.tolist()}); "
            f"the point cloud is flat and no tetrahedron can be recovered")
    return (vecs @ np.diag(vals ** -0.5) @ vecs.T,
            vecs @ np.diag(vals ** 0.5) @ vecs.T)


def cubic_form(tensor, x) -> float:
    return float(np.einsum("ijk,i,j,k->", tensor, x, x, x))


def _shifted_step(tensor, x):
    g = np.einsum("ijk,j,k->i", tensor, x, x)
    return g + float(np.dot(g, x)) * x


def extract_directions(whitened_third, seed=None, restarts=48,
                       iterations=500, tol=1e-12,
                       cluster_cos=0.9) -> np.ndarray:
    """Find the four whitened vertex directions by shifted iteration.

    Plain tensor power iteration is neutrally stable here (transverse
    derivative exactly ``-1`` at every fixed point) and does not
    converge; the shift by ``f(x) = T(x,x,x)`` cancels that term. See
    the module docstring.

    Raises :class:`EstimatorFailure` rather than guessing if the number
    of distinct converged directions is not four.
    """
    t = np.asarray(whitened_third, dtype=float)
    rng = _rng(seed)
    found: list[np.ndarray] = []
    for _ in range(int(restarts)):
        x = rng.normal(size=3)
        x /= np.linalg.norm(x)
        converged = False
        for _ in range(int(iterations)):
            y = _shifted_step(t, x)
            norm = float(np.linalg.norm(y))
            if norm < 1e-13:
                break
            y /= norm
            if float(np.linalg.norm(y - x)) < tol:
                x, converged = y, True
                break
            x = y
        if not converged:
            continue
        if not any(float(np.dot(x, d)) > cluster_cos for d in found):
            found.append(x)
    if len(found) != 4:
        raise EstimatorFailure(
            f"the cubic form has {len(found)} distinct maxima, not 4; the "
            f"whitened third moment is not a simplex frame, so these "
            f"observations are not uniform samples from a tetrahedron")
    return np.array(found)


@dataclass(frozen=True)
class TetrahedronEstimate:
    """A recovered tetrahedron, with the diagnostics that qualify it."""

    vertices: np.ndarray
    n: int
    #: ||T_w||_F / sqrt(3/2). One for clean uniform data, ~zero when the
    #: observations carry no third-moment signal.
    third_moment_signal: float
    #: |sum_i u_i|, which is exactly zero for a true tetrahedron.
    #: A self-consistency residual the estimator does not get for free.
    closure_residual: float
    evidence_class: str = "SYNTHETIC_RESULT"
    diagnostics: dict = field(default_factory=dict)


def estimate_vertices(points, seed=None, restarts=48,
                      signal_floor=THIRD_MOMENT_SIGNAL_FLOOR
                      ) -> TetrahedronEstimate:
    """Recover four vertices from a point cloud by method of moments.

    Assumes the points are uniform in the interior of a non-degenerate
    tetrahedron. When that assumption fails this function sometimes
    raises and sometimes returns a confident wrong answer; which of the
    two happens is documented in :func:`degradation_report` and is not
    something the caller can infer from the return value alone.
    """
    m = empirical_moments(points)
    wh, wi = whitening(m.scatter)
    t_w = np.einsum("ijk,ia,jb,kc->abc", m.third, wh, wh, wh, optimize=True)
    signal = (float(np.linalg.norm(t_w))
              / math.sqrt(float(CANONICAL_THIRD_NORM_SQ)))
    if signal < signal_floor:
        raise EstimatorFailure(
            f"whitened third-moment signal {signal:.4f} is below the floor "
            f"{signal_floor}: after whitening these observations look "
            f"third-moment-free, which is what a shell, a sphere or a "
            f"fully smeared rotating target looks like. No tetrahedron "
            f"is reported because many tetrahedra fit equally well")
    dirs = extract_directions(t_w, seed=seed, restarts=restarts)
    u = math.sqrt(float(WHITENED_VERTEX_NORM_SQ)) * dirs
    closure = float(np.linalg.norm(u.sum(axis=0)))
    verts = u @ wi.T + m.mean
    return TetrahedronEstimate(
        vertices=verts,
        n=m.n,
        third_moment_signal=signal,
        closure_residual=closure,
        diagnostics={
            "centroid": m.mean.tolist(),
            "scatter_eigenvalues": np.linalg.eigvalsh(m.scatter).tolist(),
            "cubic_maxima": [cubic_form(t_w, d) for d in dirs],
            "canonical_cubic_max": CANONICAL_CUBIC_MAX,
            "what_this_does_not_say": (
                "that the observed object is a tetrahedron. The estimator "
                "returns a tetrahedron for any input it does not refuse, "
                "because a tetrahedron is what it is built to return"),
        })


# --- error metrics ------------------------------------------------------

def vertex_match_error(estimated, truth) -> dict:
    """Best-permutation vertex error. Recovered vertices are unordered."""
    e = _as_vertices(estimated)
    t = _as_vertices(truth)
    best, best_perm = None, None
    for perm in permutations(range(4)):
        d = np.linalg.norm(e[list(perm)] - t, axis=1)
        m = float(np.max(d))
        if best is None or m < best:
            best, best_perm = m, perm
    d = np.linalg.norm(e[list(best_perm)] - t, axis=1)
    scale = tetrahedron_scale(t)
    return {
        "permutation": best_perm,
        "max_error": best,
        "rms_error": float(np.sqrt(np.mean(d ** 2))),
        "scale": scale,
        "relative_max_error": best / scale,
        "centroid_error": float(
            np.linalg.norm(e.mean(axis=0) - t.mean(axis=0))),
        "volume_ratio": (tetrahedron_volume(e) / tetrahedron_volume(t)
                         if tetrahedron_volume(t) > 0 else float("nan")),
    }


# --- how many samples for what accuracy ---------------------------------

def recovery_vs_n(vertices=None, sizes=(1_000, 3_000, 10_000, 30_000,
                                        100_000), trials=5, seed=None) -> list:
    """Relative recovery error against sample size.

    Reported as the median over ``trials`` independent clouds, plus the
    worst trial, because the mean is not the interesting statistic when
    the failure mode is an occasional total miss.
    """
    v = _as_vertices(REFERENCE_TETRAHEDRON if vertices is None else vertices)
    rng = _rng(seed)
    rows = []
    for n in sizes:
        errs, failures = [], 0
        for _ in range(int(trials)):
            pts = sample_uniform(v, n, seed=rng)
            try:
                est = estimate_vertices(pts, seed=rng)
            except EstimatorFailure:
                failures += 1
                continue
            errs.append(vertex_match_error(est.vertices, v)
                        ["relative_max_error"])
        rows.append({
            "n": n,
            "trials": int(trials),
            "failures": failures,
            "median_relative_error": (float(np.median(errs)) if errs
                                      else float("nan")),
            "worst_relative_error": (float(np.max(errs)) if errs
                                     else float("nan")),
        })
    return rows


# --- the generalisation gap ---------------------------------------------

def dirichlet_scale_bias(alpha) -> float:
    """Predicted length bias when the density is Dirichlet(alpha,...).

    For symmetric ``Dirichlet(a,a,a,a)``,
    ``Cov(W) = (4I - J)/(16(4a+1))``, so the scatter matrix the
    estimator infers is the true one times ``5/(4a+1)``. Lengths are
    therefore wrong by ``sqrt(5/(4a+1))``: 0.745 at ``a = 2``, 1.291 at
    ``a = 0.5``. This is a *bias*, not noise. It does not shrink with
    more samples, which is the single most important sentence in this
    module.
    """
    a = float(alpha)
    if a <= 0:
        raise ValueError("concentration must be positive")
    return math.sqrt(5.0 / (4.0 * a + 1.0))


def degradation_nonuniform(vertices=None, alphas=(0.5, 0.75, 1.0, 1.5, 2.0),
                           n=100_000, seed=None) -> list:
    """Error when the interior density is not uniform.

    Symmetric concentrations keep the centroid and the shape and get the
    scale wrong by exactly :func:`dirichlet_scale_bias`; the estimator
    reports a healthy third-moment signal throughout, so nothing in the
    return value warns the caller.
    """
    v = _as_vertices(REFERENCE_TETRAHEDRON if vertices is None else vertices)
    rng = _rng(seed)
    rows = []
    for a in alphas:
        pts = sample_dirichlet(v, n, alpha=a, seed=rng)
        try:
            est = estimate_vertices(pts, seed=rng)
        except EstimatorFailure as exc:
            rows.append({"alpha": a, "refused": True, "reason": str(exc)})
            continue
        err = vertex_match_error(est.vertices, v)
        rows.append({
            "alpha": a,
            "refused": False,
            "relative_max_error": err["relative_max_error"],
            "predicted_scale_bias": dirichlet_scale_bias(a),
            "observed_scale_ratio": (tetrahedron_scale(est.vertices)
                                     / tetrahedron_scale(v)),
            "third_moment_signal": est.third_moment_signal,
        })
    return rows


def degradation_face_weighted(vertices=None, weights=(1.0, 1.0, 1.0, 6.0),
                              n=100_000, seed=None) -> dict:
    """Error when the density piles up against one face.

    An unequal Dirichlet moves the mean off the centroid, so even the
    first moment -- the one part of the estimator that is otherwise
    robust -- is wrong.
    """
    v = _as_vertices(REFERENCE_TETRAHEDRON if vertices is None else vertices)
    rng = _rng(seed)
    pts = sample_dirichlet(v, n, alpha=weights, seed=rng)
    out = {"weights": list(weights), "n": n}
    try:
        est = estimate_vertices(pts, seed=rng)
    except EstimatorFailure as exc:
        out.update(refused=True, reason=str(exc))
        return out
    err = vertex_match_error(est.vertices, v)
    out.update(refused=False,
               relative_max_error=err["relative_max_error"],
               centroid_error=err["centroid_error"],
               relative_centroid_error=err["centroid_error"]
               / tetrahedron_scale(v),
               volume_ratio=err["volume_ratio"],
               third_moment_signal=est.third_moment_signal)
    return out


def degradation_shell(vertices=None,
                      bands=((0.0, 0.9), (0.6, 0.9), (0.85, 0.9)),
                      n=100_000, seed=None) -> list:
    """Error when observations lie in a shell instead of filling the volume.

    The bands run from a solid ball through a thick shell to a thin one,
    all strictly inside the insphere. Every one of them produces a
    distribution that does not depend on the tetrahedron, so the
    expected outcome is a refusal, and the refusal is the correct answer
    rather than a limitation of the method.
    """
    v = _as_vertices(REFERENCE_TETRAHEDRON if vertices is None else vertices)
    rng = _rng(seed)
    rows = []
    for inner, outer in bands:
        pts = sample_shell(v, n, inner_frac=inner, outer_frac=outer,
                           seed=rng)
        row = {"inner_frac": inner, "outer_frac": outer, "n": n}
        try:
            est = estimate_vertices(pts, seed=rng)
        except EstimatorFailure as exc:
            row.update(refused=True, reason=str(exc))
        else:
            err = vertex_match_error(est.vertices, v)
            row.update(refused=False,
                       relative_max_error=err["relative_max_error"],
                       third_moment_signal=est.third_moment_signal)
        rows.append(row)
    return rows


def degradation_rotating(vertices=None,
                         angles=(0.0, math.pi / 8, math.pi / 4,
                                 math.pi / 2, math.pi, 2 * math.pi),
                         axis=(0.0, 0.0, 1.0), n=100_000, seed=None) -> list:
    """Error when the target rotates during acquisition.

    The cloud is a mixture over rotations. Mixing washes out the third
    moment about the rotation axis, so the recovered shape drifts
    towards the rotational average of the true one.
    """
    v = _as_vertices(REFERENCE_TETRAHEDRON if vertices is None else vertices)
    rng = _rng(seed)
    rows = []
    for ang in angles:
        pts = sample_rotating(v, n, total_angle=ang, axis=axis, seed=rng)
        row = {"total_angle_rad": ang, "total_angle_deg": math.degrees(ang),
               "n": n}
        try:
            est = estimate_vertices(pts, seed=rng)
        except EstimatorFailure as exc:
            row.update(refused=True, reason=str(exc))
        else:
            err = vertex_match_error(est.vertices, v)
            row.update(refused=False,
                       relative_max_error=err["relative_max_error"],
                       third_moment_signal=est.third_moment_signal)
        rows.append(row)
    return rows


def degradation_drifting(vertices=None, drift_fracs=(0.0, 0.1, 0.25, 0.5, 1.0),
                         direction=(1.0, 0.0, 0.0), n=100_000, seed=None
                         ) -> list:
    """Error when the target translates during acquisition.

    ``drift_fracs`` are multiples of :func:`tetrahedron_scale`. A drift
    is a convolution with a line segment: it inflates the second moment
    along one axis while leaving the third moment of the shape intact,
    so the estimator sees a stretched tetrahedron and reports it without
    complaint.
    """
    v = _as_vertices(REFERENCE_TETRAHEDRON if vertices is None else vertices)
    scale = tetrahedron_scale(v)
    d = np.asarray(direction, dtype=float)
    d = d / np.linalg.norm(d)
    rng = _rng(seed)
    rows = []
    for frac in drift_fracs:
        pts = sample_rotating(v, n, total_angle=0.0,
                              drift=d * float(frac) * scale, seed=rng)
        row = {"drift_fraction_of_scale": frac, "n": n}
        try:
            est = estimate_vertices(pts, seed=rng)
        except EstimatorFailure as exc:
            row.update(refused=True, reason=str(exc))
        else:
            err = vertex_match_error(est.vertices, v)
            row.update(refused=False,
                       relative_max_error=err["relative_max_error"],
                       volume_ratio=err["volume_ratio"],
                       third_moment_signal=est.third_moment_signal)
        rows.append(row)
    return rows


def degradation_clipped_shell(vertices=None,
                              bands=((1.2, 1.5), (2.0, 2.5), (3.0, 3.5)),
                              n=50_000, seed=None) -> list:
    """Error for a thin shell cut by the tetrahedron's own faces.

    Unlike a shell strictly inside the solid, this one *is* identifiable
    in principle -- the clipping boundary is the faces. It is included
    to keep the shell result honest: the impossibility result of
    :func:`shell_nonidentifiability_example` is about shells inside the
    insphere, not about every conceivable shell geometry. The estimator
    still fails here, but for the ordinary reason that its moment
    identities do not hold, not because information is absent.
    """
    v = _as_vertices(REFERENCE_TETRAHEDRON if vertices is None else vertices)
    rng = _rng(seed)
    rows = []
    for inner, outer in bands:
        pts = sample_shell(v, n, inner_frac=inner, outer_frac=outer,
                           clip=True, seed=rng)
        row = {"inner_frac": inner, "outer_frac": outer, "n": len(pts),
               "clipped": True, "identifiable_in_principle": True}
        try:
            est = estimate_vertices(pts, seed=rng)
        except EstimatorFailure as exc:
            row.update(refused=True, reason=str(exc))
        else:
            err = vertex_match_error(est.vertices, v)
            row.update(refused=False,
                       relative_max_error=err["relative_max_error"],
                       third_moment_signal=est.third_moment_signal)
        rows.append(row)
    return rows


def degradation_report(n=50_000, seed=None) -> dict:
    """Every broken assumption, and which diagnostic (if any) catches it.

    The middle column is the uncomfortable one. Two of the four failure
    modes are caught -- the estimator refuses -- and two are not: the
    estimator returns a wrong tetrahedron with a healthy third-moment
    signal and a small closure residual, and nothing in the return value
    distinguishes it from a good fit.
    """
    rng = _rng(seed)
    return {
        "n": n,
        "non_uniform_density_symmetric": {
            "rows": degradation_nonuniform(n=n, seed=rng),
            "caught_by_a_diagnostic": False,
            "failure_type": "BIAS",
            "note": ("error is set by dirichlet_scale_bias(alpha) and is "
                     "independent of sample size. More data makes the "
                     "wrong answer more precise"),
        },
        "non_uniform_density_towards_a_face": {
            "row": degradation_face_weighted(n=n, seed=rng),
            "caught_by_a_diagnostic": True,
            "failure_type": "REFUSAL",
            "note": "the cubic form stops having four maxima",
        },
        "shell_confined": {
            "rows": degradation_shell(n=n, seed=rng),
            "caught_by_a_diagnostic": True,
            "failure_type": "REFUSAL",
            "note": ("the third-moment signal collapses to ~1% of "
                     "canonical. The refusal is correct and it is also "
                     "the only possible answer: see "
                     "shell_nonidentifiability_example()"),
        },
        "shell_clipped_by_faces": {
            "rows": degradation_clipped_shell(n=n, seed=rng),
            "caught_by_a_diagnostic": True,
            "failure_type": "REFUSAL",
            "note": ("identifiable in principle -- the clipping boundary "
                     "is the faces -- and still refused, because the "
                     "moment identities this estimator inverts do not "
                     "hold for the clipped density. Absence of "
                     "information and absence of a method are different "
                     "failures and this row is the second kind"),
        },
        "rotating_target": {
            "rows": degradation_rotating(n=n, seed=rng),
            "caught_by_a_diagnostic": "ONLY_WHEN_LARGE",
            "failure_type": "BIAS_THEN_REFUSAL",
            "note": ("small rotations produce large errors with no "
                     "warning; large rotations are refused. The "
                     "dangerous regime is the quiet one"),
        },
        "translating_target": {
            "rows": degradation_drifting(n=n, seed=rng),
            "caught_by_a_diagnostic": False,
            "failure_type": "BIAS",
            "note": ("drift inflates one axis of the scatter matrix; the "
                     "estimator reports a stretched tetrahedron and no "
                     "diagnostic objects"),
        },
        "what_this_does_not_say": (
            "that the caught cases are safe. A refusal only means this "
            "estimator noticed. Two of six broken assumptions produce "
            "confident wrong answers, so passing the diagnostics is not "
            "evidence that the assumptions hold"),
    }


# --- identifiability ----------------------------------------------------

def second_moment_twin(vertices, rotation=None, seed=None) -> np.ndarray:
    """A different tetrahedron with identical mean and covariance.

    Closed form. With ``c_i`` the centred vertices and ``S = C C^T``,
    the map ``M = S^(1/2) R S^(-1/2)`` for any ``R`` in ``O(3)`` sends
    ``C`` to ``C' = M C`` with

        C' C'^T = S^(1/2) R S^(-1/2) S S^(-1/2) R^T S^(1/2) = S

    and ``sum_i c'_i = M sum_i c_i = 0``. So mean and covariance are
    preserved exactly while the shape is not, because ``M`` is a general
    linear map, not an isometry. Second moments alone therefore never
    identify a tetrahedron -- the ambiguity is a full 3-parameter
    ``O(3)`` orbit, and it is why the estimator needs the third moment.

    The one exception is the isotropic case: when ``S`` is a multiple of
    the identity, ``M = R`` and the twin is a rigid rotation of the
    original. A regular tetrahedron has no second-moment twin except its
    own rotations.

    ``det M = det R = 1``, so the twin also has exactly the same volume
    as the original. Mean, covariance and volume all agree while the
    shape differs, which is worth stating plainly: three familiar
    summary statistics matching is not identification.
    """
    v = _as_vertices(vertices)
    mu = v.mean(axis=0)
    c = v - mu
    s = c.T @ c
    vals, vecs = np.linalg.eigh(s)
    if np.min(vals) <= 0:
        raise ValueError("degenerate tetrahedron has no whitening")
    root = vecs @ np.diag(vals ** 0.5) @ vecs.T
    inv_root = vecs @ np.diag(vals ** -0.5) @ vecs.T
    if rotation is None:
        q, r = np.linalg.qr(_rng(seed).normal(size=(3, 3)))
        rotation = q @ np.diag(np.sign(np.diag(r)))
    m = root @ np.asarray(rotation, dtype=float) @ inv_root
    return c @ m.T + mu


def shell_nonidentifiability_example(radius=1.0, seed=None) -> dict:
    """Two very different tetrahedra that a shell observer cannot tell apart.

    Both are built by :func:`circumscribing_tetrahedron` from the same
    sphere, so both have exactly that sphere as their insphere. Any
    observation confined to a shell inside that sphere has a
    distribution that depends only on the shell -- not on the
    tetrahedron -- so the two are *exactly* observationally equivalent.
    Not approximately, and not up to sampling error: the likelihood is
    identical for every possible dataset.

    The parameter count makes the scale of the problem plain. A
    tetrahedron has 12 degrees of freedom; a sphere has 4. The map from
    tetrahedra to inspheres has 8-dimensional fibres, so the
    equivalence class of any shell observation is an 8-parameter family
    of tetrahedra of wildly differing shapes and sizes.
    """
    regular = np.array([[1.0, 1.0, 1.0], [1.0, -1.0, -1.0],
                        [-1.0, 1.0, -1.0], [-1.0, -1.0, 1.0]])
    regular = regular / np.linalg.norm(regular, axis=1, keepdims=True)
    # A markedly skewed but still positively-spanning set of normals.
    skewed = np.array([[0.2, 0.1, 1.0], [1.0, -0.3, -0.4],
                       [-0.9, 0.8, -0.2], [-0.4, -1.0, 0.1]])
    skewed = skewed / np.linalg.norm(skewed, axis=1, keepdims=True)
    centre = np.zeros(3)
    a = circumscribing_tetrahedron(regular, centre, radius)
    b = circumscribing_tetrahedron(skewed, centre, radius)
    ca, ra = insphere(a)
    cb, rb = insphere(b)
    return {
        "tetrahedron_a": a.tolist(),
        "tetrahedron_b": b.tolist(),
        "insphere_a": {"centre": ca.tolist(), "radius": ra},
        "insphere_b": {"centre": cb.tolist(), "radius": rb},
        "volume_a": tetrahedron_volume(a),
        "volume_b": tetrahedron_volume(b),
        "volume_ratio": tetrahedron_volume(b) / tetrahedron_volume(a),
        "shared_insphere_radius": radius,
        "observationally_equivalent_for": (
            "any observation supported inside the common insphere, "
            "including any spherical shell about its centre"),
        "equivalence_class_dimension": 8,
        "why": (
            "the distribution of a shell-confined observation is a "
            "function of the shell alone. Two tetrahedra sharing an "
            "insphere induce the same likelihood for every dataset, so "
            "no estimator, no amount of data and no prior-free method "
            "can separate them"),
    }


def refuse_shell_inverse(points=None) -> None:
    """Refuse to invert a tetrahedron from shell-confined observations."""
    raise NotIdentifiable(
        "observations confined to a spherical shell do not identify a "
        "tetrahedron. Every tetrahedron whose insphere contains the "
        "shell induces exactly the same distribution, so the likelihood "
        "is flat over an 8-parameter family. This is a property of the "
        "observation model, not of the estimator: no method recovers "
        "what the data does not encode. See "
        "shell_nonidentifiability_example() for two explicit members of "
        "one such family.")


def identifiability_report() -> dict:
    """Where the inverse problem is well posed and where it is not."""
    return {
        "identified_by_moments_1_and_2": False,
        "second_moment_deficiency": {
            "constraints": 6,
            "degrees_of_freedom": 9,
            "ambiguity": "a 3-parameter O(3) orbit",
            "constructive_witness": "second_moment_twin()",
            "exception": (
                "an isotropic scatter matrix, i.e. a regular "
                "tetrahedron, whose twins are all rigid rotations"),
        },
        "identified_by_moments_1_to_3": {
            "uniform_interior_sampling": True,
            "caveat": (
                "identified up to the labelling of the four vertices, "
                "which no moment can order"),
        },
        "not_identified_at_all": {
            "shell_or_sphere_confined": (
                "flat likelihood over an 8-parameter family; "
                "see shell_nonidentifiability_example()"),
            "unknown_non_uniform_density": (
                "density and shape trade off against each other. A "
                "smaller tetrahedron with an outward-piled density "
                "reproduces the moments of a larger one with a uniform "
                "density; without an independent constraint on the "
                "density the pair is not separable"),
            "target_moving_by_an_unknown_law": (
                "the cloud is a mixture over an unknown group orbit. "
                "Shape and motion are confounded, and a fully smeared "
                "orbit destroys the third moment the method depends on"),
        },
        "what_this_does_not_say": (
            "that the shell and motion cases are hard. They are not "
            "hard, they are impossible: the information is absent from "
            "the observations, so effort and data do not help"),
    }


# --- refusals -----------------------------------------------------------

def refuse_earth_sphere_inverse(*args, **kwargs) -> None:
    """Refuse to carry the reproduction over to the Earth-sphere problem.

    Called with any arguments, and refuses regardless of them, because
    there is no argument that would make the promotion valid.
    """
    raise InverseClaimRefused(
        "reproducing the uniform-tetrahedron moment estimator licenses "
        "exactly one claim: that the estimator works on uniform "
        "interior samples from a static tetrahedron, which is "
        "LITERATURE_REPRODUCTION. It does not license any claim about "
        "the Earth-sphere problem, for five independent reasons, any "
        "one of which is sufficient. "
        "(1) SAMPLING. The method's identifiability rests on "
        "E[(X-mu)^3] = (1/60) sum c_i^3, which holds only for the "
        "uniform interior density. Non-uniform density biases the "
        "recovered scale by a factor that does not shrink with sample "
        "size; see dirichlet_scale_bias(). "
        "(2) SUPPORT. The pack's observations are shell-constrained, "
        "and shell-constrained observations have a flat likelihood over "
        "an 8-parameter family of tetrahedra; see "
        "shell_nonidentifiability_example(). No estimator recovers "
        "information the observation model does not contain. "
        "(3) MOTION. A moving or rotating target makes the cloud a "
        "mixture over an unknown group orbit, confounding shape with "
        "motion and, at full smear, annihilating the third moment "
        "entirely. "
        "(4) MODEL CLASS. The estimator returns four vertices for any "
        "input it does not refuse, because four vertices is what it is "
        "built to return. Fitting a tetrahedron is not a test of "
        "whether the object is one, and the R10.1 claim policy names "
        "this firewall directly: a tetrahedral inverse estimator is not "
        "proof that the hidden object is tetrahedral. "
        "(5) EVIDENCE CLASS. Every number in this module is "
        "SYNTHETIC_RESULT computed from a seeded pseudo-random "
        "generator. Nothing here was measured, so nothing here can be "
        "promoted to BENCH_MEASUREMENT.")


def refuse_tetrahedral_object_claim(estimate=None) -> None:
    """Refuse to read a successful fit as evidence about the object.

    Note that this refusal is deliberately *not* the crude version.
    :func:`model_class_probe` shows the estimator does reject a box, a
    Gaussian and a square pyramid, so a non-refusal is not literally
    vacuous. It is still not evidence, for the reasons below.
    """
    raise InverseClaimRefused(
        "estimate_vertices() returns four vertices, and it rejects some "
        "non-tetrahedral solids -- see model_class_probe(). That falls "
        "well short of evidence that an observed object is tetrahedral. "
        "(1) The alternatives it rejects were chosen by the author from "
        "an unbounded model space; rejecting four is not model "
        "comparison. (2) A goodness-of-fit against one class needs a "
        "likelihood ratio against the classes that were never fitted. "
        "(3) The failure modes the estimator does NOT detect -- biased "
        "density, drift, small rotation -- are exactly the conditions "
        "under which a claim would be made, and under those it returns "
        "a confident wrong tetrahedron with healthy diagnostics. "
        "(4) Nothing here was measured. The R10.1 claim policy states "
        "the firewall directly: a tetrahedral inverse estimator is not "
        "proof that the hidden object is tetrahedral.")


# --- report -------------------------------------------------------------

def inverse_report(seed=None) -> dict:
    """The Q19 summary: what was reproduced, and what it does not buy."""
    rng = _rng(seed)
    v = REFERENCE_TETRAHEDRON
    pts = sample_uniform(v, 100_000, seed=rng)
    est = estimate_vertices(pts, seed=rng)
    err = vertex_match_error(est.vertices, v)
    return {
        "reproduction": {
            "n": est.n,
            "relative_max_error": err["relative_max_error"],
            "third_moment_signal": est.third_moment_signal,
            "closure_residual": est.closure_residual,
            "evidence_class": "LITERATURE_REPRODUCTION",
        },
        "exact_algebra": {
            "second_moment_factor": str(SECOND_MOMENT_FACTOR),
            "third_moment_factor": str(THIRD_MOMENT_FACTOR),
            "third_moment_decomposition": {
                k: str(x) for k, x in third_moment_decomposition().items()},
            "whitened_vertex_norm_sq": str(WHITENED_VERTEX_NORM_SQ),
            "canonical_third_norm_sq": str(CANONICAL_THIRD_NORM_SQ),
        },
        "identifiability": identifiability_report(),
        "prior_art": {
            "described_as": "2018 method-of-moments simplex estimator",
            "source": "operator-supplied",
            "verified": False,
            "note": (
                "the citation could not be checked in this environment, "
                "so no result is attributed to it. The derivation here "
                "is independent and is checked against simulation"),
        },
        "measured_here": "nothing",
        "what_this_is": (
            "a working, tested reproduction of a known estimator, plus "
            "a quantified account of the three assumptions it needs and "
            "a constructive proof that the pack's own observation model "
            "destroys identifiability"),
        "what_this_does_not_say": (
            "that the hidden object is a tetrahedron; that the "
            "Earth-sphere inverse problem is solvable by this or any "
            "moment method; that a fitted vertex set corresponds to "
            "anything physical. The reproduction succeeded and the "
            "generalisation failed, and the second half is the result"),
    }
