"""P12 — navigation observability and the dependency audit.

The claim under test is "sovereign navigation": positioning with no
external infrastructure, derived from a locally measured metric.

The refutation is not rhetorical, it is linear algebra. Position is
observable only when the measurement Jacobian has full column rank
over the position block. A local scalar clock rate does not: it maps
a three-dimensional position to one number, and on a spherical
equipotential it maps a whole surface to the *same* number. The
Jacobian is rank 1 at best, so two of three position degrees of
freedom are unobservable no matter how good the clock is.

The second refutation is bookkeeping. Every candidate signal-denied
method is listed in :data:`DEPENDENCIES` with what it actually
requires from outside. Star trackers need catalogues, gravity aiding
needs maps, inertial navigation needs an initial condition and drifts
without bound. "Infrastructure-free" describes none of them.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict

from . import NAVIGATION_STATUSES

#: What each candidate method needs supplied from outside. The point
#: of the table is that no row is empty.
DEPENDENCIES: dict[str, tuple[str, ...]] = {
    "INERTIAL": (
        "initial position and velocity",
        "initial attitude",
        "gravity model for specific-force compensation",
        "periodic external fix to bound drift",
    ),
    "CLOCK_GEODESY": (
        "a second clock to compare against",
        "a phase-coherent transfer link",
        "a geopotential model",
        "traceable frequency standard",
    ),
    "GRAVITY_GRADIENT": (
        "a gravity gradient map",
        "survey data at map resolution",
        "attitude reference",
    ),
    "GEOMAGNETIC": (
        "a field model such as IGRF or WMM",
        "secular variation updates",
        "crustal anomaly map",
        "space-weather state",
    ),
    "CELESTIAL": (
        "a star catalogue",
        "planetary ephemerides",
        "accurate time",
        "clear line of sight",
    ),
    "TERRAIN": (
        "a terrain elevation map",
        "an altimeter",
    ),
    "OPTICAL_FLOW": (
        "a visual map or landmark database",
        "scale from another sensor",
    ),
}


@dataclass
class NavState:
    """x = (r, v, t, clock bias, clock drift, frame, uncertainty)."""

    position_m: tuple[float, float, float]
    velocity_ms: tuple[float, float, float]
    time_s: float
    clock_bias_s: float
    clock_drift_s_per_s: float
    frame: str
    position_uncertainty_m: float

    def as_record(self) -> dict:
        return asdict(self)


# --------------------------------------------------------------------
# Observability
# --------------------------------------------------------------------

def _rank(rows: list[list[float]], rtol: float = 1e-12) -> int:
    """Gaussian-elimination rank, with a *relative* tolerance.

    An absolute tolerance is wrong here and dangerously so. A clock
    rate Jacobian entry is g/c^2 ~ 1e-16 per metre: physically
    meaningful, and the entire basis of relativistic geodesy, but
    below any plausible absolute epsilon. Treating it as zero would
    report that a clock carries *no* position information, which
    overstates the refutation and contradicts published height
    measurements by optical clocks. Tolerance therefore scales with
    the largest entry in the matrix.
    """
    m = [list(map(float, r)) for r in rows]
    if not m:
        return 0
    scale = max((abs(x) for row in m for x in row), default=0.0)
    if scale == 0.0:
        return 0
    tol = rtol * scale
    rank = 0
    ncols = len(m[0])
    for col in range(ncols):
        pivot = None
        for r in range(rank, len(m)):
            if abs(m[r][col]) > tol:
                pivot = r
                break
        if pivot is None:
            continue
        m[rank], m[pivot] = m[pivot], m[rank]
        pv = m[rank][col]
        m[rank] = [x / pv for x in m[rank]]
        for r in range(len(m)):
            if r != rank and abs(m[r][col]) > tol:
                f = m[r][col]
                m[r] = [a - f * b for a, b in zip(m[r], m[rank])]
        rank += 1
        if rank == len(m):
            break
    return rank


@dataclass(frozen=True)
class ObservabilityReport:
    method: str
    jacobian_rank: int
    position_dof: int
    unobservable_dof: int
    status: str
    dependencies: tuple[str, ...]
    notes: tuple[str, ...] = ()

    @property
    def position_observable(self) -> bool:
        return self.unobservable_dof == 0

    def as_record(self) -> dict:
        d = asdict(self)
        d["dependencies"] = list(self.dependencies)
        d["notes"] = list(self.notes)
        d["position_observable"] = self.position_observable
        return d


def clock_rate_jacobian(g_vector: tuple[float, float, float],
                        c: float = 299_792_458.0) -> list[list[float]]:
    """d(df/f)/dr for a local clock-rate measurement.

    The rate depends on the gravitational potential, so the gradient
    with respect to position is g/c^2 — a single row. One measurement,
    three unknowns.
    """
    return [[gi / (c * c) for gi in g_vector]]


def analyze_observability(method: str,
                          jacobian: list[list[float]],
                          *,
                          position_dof: int = 3,
                          has_map: bool = False,
                          has_initial_condition: bool = False,
                          ) -> ObservabilityReport:
    """Classify a navigation method by what its Jacobian supports."""
    if method not in DEPENDENCIES:
        raise ValueError(f"unknown navigation method {method!r}")
    r = _rank(jacobian)
    unobs = max(position_dof - r, 0)
    notes: list[str] = []

    if unobs == position_dof:
        status = "POSITION_UNOBSERVABLE"
        notes.append("the measurement carries no position information")
    elif unobs > 0:
        status = "POSITION_UNOBSERVABLE"
        notes.append(
            f"rank {r} of {position_dof}: {unobs} position degrees of "
            f"freedom are unobservable from this measurement alone")
    else:
        status = "POSITION_BOUNDED"

    if method == "CLOCK_GEODESY" and unobs > 0:
        notes.append(
            "a scalar clock rate is constant over an equipotential "
            "surface, so it cannot distinguish points on it")
    if method == "INERTIAL" and not has_initial_condition:
        status = "DEAD_RECKONING"
        notes.append("no initial condition: position is relative only")
    if has_map and unobs == 0:
        status = "MAP_AIDED_NAVIGATION"

    assert status in NAVIGATION_STATUSES
    return ObservabilityReport(
        method=method, jacobian_rank=r, position_dof=position_dof,
        unobservable_dof=unobs, status=status,
        dependencies=DEPENDENCIES[method], notes=tuple(notes))


def fuse_observability(reports: list[ObservabilityReport],
                       *, position_dof: int = 3) -> ObservabilityReport:
    """Combine methods by stacking their Jacobian ranks.

    Fusion is how position actually becomes observable: several
    partial measurements together can span the space that none spans
    alone. The fused report inherits the *union* of dependencies,
    which is the honest cost of doing it.
    """
    if not reports:
        raise ValueError("nothing to fuse")
    total_rank = min(sum(r.jacobian_rank for r in reports), position_dof)
    deps: list[str] = []
    for r in reports:
        for d in r.dependencies:
            if d not in deps:
                deps.append(d)
    unobs = max(position_dof - total_rank, 0)
    status = "POSITION_BOUNDED" if unobs == 0 else "POSITION_UNOBSERVABLE"
    notes = [
        f"fused {len(reports)} methods: "
        f"{', '.join(r.method for r in reports)}",
        f"union of external dependencies: {len(deps)} items",
    ]
    if unobs == 0:
        notes.append(
            "position is observable, and it is observable *because* "
            "of the external inputs listed, not in spite of them")
    return ObservabilityReport(
        method="FUSED", jacobian_rank=total_rank,
        position_dof=position_dof, unobservable_dof=unobs,
        status=status, dependencies=tuple(deps), notes=tuple(notes))


# --------------------------------------------------------------------
# The sovereignty audit
# --------------------------------------------------------------------

def sovereignty_audit(methods: tuple[str, ...] = tuple(DEPENDENCIES)
                      ) -> dict:
    """The headline P12 result, computed rather than asserted.

    For each candidate method, count what it needs from outside. The
    verdict is ``SOVEREIGN_NAVIGATION_UNSUPPORTED`` whenever any
    method retains a dependency — which is always, because every row
    of :data:`DEPENDENCIES` is non-empty by construction of physics,
    not by choice of table.
    """
    rows = []
    for m in methods:
        deps = DEPENDENCIES[m]
        rows.append({
            "method": m,
            "external_dependencies": len(deps),
            "dependencies": list(deps),
            "infrastructure_free": len(deps) == 0,
        })
    free = [r for r in rows if r["infrastructure_free"]]
    return {
        "methods_examined": len(rows),
        "methods_infrastructure_free": len(free),
        "rows": rows,
        "status": ("SOVEREIGN_NAVIGATION_UNSUPPORTED" if not free
                   else "REVIEW_REQUIRED"),
        "verdict": (
            "No examined method is infrastructure-free. Every "
            "signal-denied technique substitutes a different external "
            "dependency -- a catalogue, a map, a model, a second "
            "clock, or an initial condition -- for the radio signal it "
            "avoids. 'Sovereign navigation' is therefore unsupported "
            "as an absolute claim (claim R6-C-107)."
        ),
        "claim_ceiling": (
            "documented signal-denied navigation with its actual "
            "dependencies stated and its performance measured"
        ),
    }


def refuse_position_from_local_metric(*args, **kwargs):
    """Always refuses: a local field does not fix a global position."""
    raise RuntimeError(
        "global position may not be inferred from a locally measured "
        "clock rate or uniform gravitational field. The measurement "
        "Jacobian has rank 1 against three position unknowns, and is "
        "identically constant over an equipotential surface "
        "(r6 FORBIDDEN_COLLAPSES: LOCAL_FIELD_IS_GLOBAL_POSITION). "
        "Use analyze_observability() and fuse_observability().")
