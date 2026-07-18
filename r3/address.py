"""P02/P03 (A12-A27) — tetrahedral frequency-key addressing.

Exact hierarchy 1, 8, 64, 512, 4096 (N_d = 8^d = 2^(3d)). A recursive
base-8 codec addresses child tetrahedra; the five typed readings of a
K value (region/subregion, origin/destination, region/phase, operator
entry, digit path) are declared, never guessed; barycentric
coordinates locate points inside a cell.

An ADDRESS is bookkeeping. A physical destination additionally
requires frame, epoch, metric model, ephemeris, uncertainty, and a
calibrated address map — the destination certificate refuses to exist
without them.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import ClaimBoundaryError, refuse_collapse

#: K-value semantics (core/03). A K without a declared semantic is
#: refused — the same integer means five different things.
K_SEMANTICS = ("REGION_SUBREGION", "ORIGIN_DESTINATION",
               "REGION_PHASE", "OPERATOR_ENTRY", "DIGIT_PATH")


def level_count(depth: int) -> int:
    """N_d = 8^d = 2^(3d), exactly."""
    if depth < 0:
        raise ClaimBoundaryError("depth must be non-negative")
    return 8 ** depth


def encode(digits: list) -> int:
    """Base-8 digit path -> address index at depth len(digits)."""
    k = 0
    for d in digits:
        if not (0 <= int(d) <= 7):
            raise ClaimBoundaryError(f"digit {d} outside octal range")
        k = k * 8 + int(d)
    return k


def decode(k: int, depth: int) -> list:
    """Address index -> base-8 digit path of the declared depth."""
    if not (0 <= k < 8 ** depth):
        raise ClaimBoundaryError(
            f"K={k} outside depth-{depth} range [0, {8 ** depth})")
    out = []
    for _ in range(depth):
        out.append(k % 8)
        k //= 8
    return list(reversed(out))


def parent(k: int, depth: int, levels_up: int = 1) -> int:
    """pi^d(K): the ancestor address. pi^depth(K) is always 0 — the
    SYNTHETIC_HIERARCHY_ROOT, guaranteed by the codec, and NOT a
    vacuum origin."""
    if levels_up > depth:
        raise ClaimBoundaryError("cannot go above the hierarchy root")
    return k // (8 ** levels_up)


def split_k(k: int, semantic: str) -> dict:
    """K = 64*A + B under a DECLARED semantic."""
    if semantic not in K_SEMANTICS:
        raise ClaimBoundaryError(
            f"semantic {semantic!r} undeclared; K={k} means nothing "
            "without one (five readings exist)")
    if not (0 <= k < 4096):
        raise ClaimBoundaryError("two-level K must lie in [0, 4096)")
    hi, lo = divmod(k, 64)
    names = {"REGION_SUBREGION": ("region", "subregion"),
             "ORIGIN_DESTINATION": ("origin", "destination"),
             "REGION_PHASE": ("region", "phase"),
             "OPERATOR_ENTRY": ("row", "col"),
             "DIGIT_PATH": ("hi_digits", "lo_digits")}[semantic]
    return {"k": k, "semantic": semantic, names[0]: hi, names[1]: lo}


def barycentric_locate(lambdas: tuple) -> dict:
    """x = sum(lambda_i * v_i), lambdas >= 0 summing to 1 (exact
    check on the caller's rationals/floats with tolerance)."""
    if len(lambdas) != 4:
        raise ClaimBoundaryError("a tetrahedron has four barycentric "
                                 "coordinates")
    if any(v < 0 for v in lambdas):
        raise ClaimBoundaryError("negative barycentric coordinate: "
                                 "point lies outside the cell")
    s = sum(lambdas)
    if abs(s - 1.0) > 1e-12:
        raise ClaimBoundaryError(f"lambdas sum to {s}, not 1")
    return {"lambdas": tuple(lambdas), "inside": True,
            "on_face": any(v == 0 for v in lambdas)}


def route(k_from: int, k_to: int, depth: int = 2) -> dict:
    """64x64 route operator entry: the pair (i, j) as an operator
    index. Routing between ADDRESSES is graph bookkeeping; it moves
    nothing physical."""
    return {"operator_entry": split_k(64 * (k_from % 64) + (k_to % 64),
                                      "OPERATOR_ENTRY"),
            "hierarchy_distance": _tree_distance(k_from, k_to, depth),
            "claim": "address-space routing; not transport"}


def _tree_distance(a: int, b: int, depth: int) -> int:
    da, db = decode(a, depth), decode(b, depth)
    common = 0
    for x, y in zip(da, db):
        if x != y:
            break
        common += 1
    return 2 * (depth - common)


def transition_4096(k_from: int, k_to: int) -> dict:
    """A22: one entry of the 4096-state transition table. Deliberately
    dumb: a transition is a labelled pair, and the compiler's output
    says so."""
    if not (0 <= k_from < 4096 and 0 <= k_to < 4096):
        raise ClaimBoundaryError("states must lie in [0, 4096)")
    return {"from": k_from, "to": k_to,
            "from_digits": decode(k_from, 4),
            "to_digits": decode(k_to, 4),
            "claim": "a labelled pair in a synthetic state space"}


@dataclass(frozen=True)
class DestinationCertificate:
    """A26: what separates an address from a place. Every field is
    required; a certificate cannot be built for bookkeeping alone."""
    address_k: int
    semantic: str
    frame: str
    epoch_utc: str
    metric_model: str
    ephemeris_ref: str
    position_uncertainty_m: float
    address_map_calibration: str
    evidence_class: str = "ANALYTIC_MODEL"

    def __post_init__(self):
        for name in ("frame", "epoch_utc", "metric_model",
                     "ephemeris_ref", "address_map_calibration"):
            if not getattr(self, name):
                raise ClaimBoundaryError(
                    f"destination certificate missing {name}: an "
                    "address without frame/epoch/metric/ephemeris/"
                    "calibration is bookkeeping, not a place")
        if self.position_uncertainty_m <= 0:
            raise ClaimBoundaryError(
                "zero/negative uncertainty refused: a real map has "
                "error bars")
        if self.semantic not in K_SEMANTICS:
            raise ClaimBoundaryError("undeclared K semantic")


def hierarchy_root_is_not_vacuum() -> None:
    """The A85 correction as an executable refusal."""
    refuse_collapse("HIERARCHY_ROOT_IS_VACUUM_ORIGIN")
