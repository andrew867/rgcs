"""P15 — Recursive eight-way spatialization families (bounded candidate set).

The locked source route core is a **five-token base-100** representation
(Locked Decision 13), e.g. ``165876523 -> 01|65|87|65|23``. This module maps
such a route into the recursive **one-to-eight** icosahedral refinement of the
reused engine (:mod:`cwatlas.addressing` / :mod:`cwatlas.subdivision`), giving,
for each route, an address ``(face, octal path)`` and its deterministic cell
polygon and centroid.

The *exact* token-to-geometric-path semantics are **inferred, not locked**
(System Contract, "locked versus inferred"). So instead of guessing one, this
module enumerates a **bounded, finite family of candidate mappings** — the
ensemble the later calibration selects among. There are exactly **four**
families (the architecture spec), differing only in deterministic, invertible
conventions:

* ``token_order`` — the significance ordering of the five base-100 tokens;
* ``face_entry`` — ``DIRECT`` face numbering vs. ``ROOT_RELATIVE`` numbering
  offset by the locked root face;
* ``digit_order`` — ``BIG_ENDIAN`` vs. ``LITTLE_ENDIAN`` emission of the octal
  refinement digits.

Each family is a pure arithmetic bijection ``route <-> (face, octal path)`` —
**no hash and no destination catalogue** (required work #3). Each is invertible,
has a fixed path depth, and a counted search-space size for the ledger. Planted
route->point mappings are provided so the recovery power of the inverse pipeline
(P16) can be measured (required work #4).

A candidate mapping is a ``CALIBRATED_CANDIDATE`` at most — never a measured
fact, and it asserts no source origin. See :mod:`cwatlas.r1082.claims`.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from cwatlas.addressing import path_cell
from cwatlas.icosahedron import Icosahedron, build_icosahedron
from cwatlas.localize import cell_centroid
from cwatlas.r1082 import claims as r1082_claims
from cwatlas.r1082.partition import IcosahedralPartition, build_partition

FAMILY_CODEC_ID = "CW-R1082-SPATIALIZE"
FAMILY_CODEC_VERSION = "1.0.0"

#: The locked five-token base-100 route core (Locked Decision 13).
ROUTE_TOKENS = 5
TOKEN_BASE = 100
TOKEN_MIN = 0
TOKEN_MAX = TOKEN_BASE - 1

#: The one-to-eight (octal) recursive refinement of the reused engine.
OCTAL_BASE = 8

#: Number of icosahedral faces (partition cardinality).
FACE_COUNT = 20

#: Fixed refinement depth. The route carries ``TOKEN_BASE ** ROUTE_TOKENS``
#: (= 10**10) states; a face (20) plus ``PATH_DEPTH`` octal digits must cover
#: the route integer divided across the face, i.e. ``8 ** PATH_DEPTH`` must
#: exceed ``10**10 / 20``. Depth 10 gives ``8**10 = 1.07e9 > 5e8``: the mapping
#: is injective and every route round-trips exactly.
PATH_DEPTH = 10

#: The default root face used by ROOT_RELATIVE families. Bound once from the
#: partition's own canonical model (face 0 as a deterministic, public default);
#: a real deployment binds it via ``partition.select_root(direction)``. It only
#: shifts the face numbering and is inverted exactly, so it never breaks the
#: round-trip.
DEFAULT_ROOT_FACE = 0


class SpatializationError(ValueError):
    """Raised on a malformed route, face id, or path under a family."""


def _validate_route(route) -> tuple[int, ...]:
    """Coerce and validate a five-token base-100 route."""
    seq = tuple(route)
    if len(seq) != ROUTE_TOKENS:
        raise SpatializationError(
            f"route must have exactly {ROUTE_TOKENS} base-100 tokens, got "
            f"{len(seq)}")
    out: list[int] = []
    for i, t in enumerate(seq):
        if isinstance(t, bool) or not isinstance(t, (int, np.integer)):
            raise SpatializationError(
                f"route token {i} must be an int, got {t!r}")
        t = int(t)
        if not TOKEN_MIN <= t <= TOKEN_MAX:
            raise SpatializationError(
                f"route token {i}={t} out of range [{TOKEN_MIN}, {TOKEN_MAX}]")
        out.append(t)
    return tuple(out)


@dataclass(frozen=True)
class Spatialization:
    """The result of mapping one route under one family.

    Attributes
    ----------
    family_name, route:
        The family and the (validated) five-token route.
    face_id, path:
        The address the route maps to: icosa face ``0..19`` and an octal path
        of length :data:`PATH_DEPTH`.
    centroid:
        ``(3,)`` unit direction of the terminal cell centroid — the route's
        representative point, not a decoded destination.
    polygon:
        ``(3, 3)`` unit corners of the terminal spherical-triangle cell
        (deterministic cell polygon, required work #5).
    depth:
        Refinement depth (== ``len(path)``).
    """

    family_name: str
    route: tuple[int, ...]
    face_id: int
    path: tuple[int, ...]
    centroid: np.ndarray
    polygon: np.ndarray
    depth: int


@dataclass(frozen=True)
class SpatializationFamily:
    """A single bounded, invertible candidate mapping.

    A family is a pure arithmetic bijection between the ``10**10`` five-token
    routes and a subset of the ``(face, octal path)`` address space. It uses no
    hash and no destination catalogue.

    Attributes
    ----------
    name:
        Stable family identifier.
    token_order:
        Permutation of ``(0..4)`` giving the base-100 token significance,
        most-significant first.
    face_entry:
        ``"DIRECT"`` or ``"ROOT_RELATIVE"``.
    digit_order:
        ``"BIG_ENDIAN"`` or ``"LITTLE_ENDIAN"`` octal-digit emission.
    root_face:
        The root face offset used when ``face_entry == "ROOT_RELATIVE"``.
    """

    name: str
    token_order: tuple[int, ...]
    face_entry: str
    digit_order: str
    root_face: int = DEFAULT_ROOT_FACE

    # -- route <-> integer (token significance) ---------------------------
    def route_to_int(self, route) -> int:
        """Fold a five-token route into an integer in ``[0, 10**10)``."""
        toks = _validate_route(route)
        n = 0
        for pos in self.token_order:
            n = n * TOKEN_BASE + toks[pos]
        return n

    def int_to_route(self, n: int) -> tuple[int, ...]:
        """Inverse of :meth:`route_to_int`."""
        if not 0 <= n < TOKEN_BASE ** ROUTE_TOKENS:
            raise SpatializationError(f"route integer out of range: {n!r}")
        digits: list[int] = []
        x = n
        for _ in range(ROUTE_TOKENS):
            digits.append(x % TOKEN_BASE)
            x //= TOKEN_BASE
        digits.reverse()  # most-significant first, matching route_to_int
        toks = [0] * ROUTE_TOKENS
        for slot, pos in enumerate(self.token_order):
            toks[pos] = digits[slot]
        return tuple(toks)

    # -- integer <-> (face, octal path) -----------------------------------
    def _face_raw_and_quotient(self, n: int) -> tuple[int, int]:
        return n % FACE_COUNT, n // FACE_COUNT

    def _apply_face_entry(self, face_raw: int) -> int:
        if self.face_entry == "ROOT_RELATIVE":
            return (face_raw + self.root_face) % FACE_COUNT
        return face_raw

    def _invert_face_entry(self, face_id: int) -> int:
        if self.face_entry == "ROOT_RELATIVE":
            return (face_id - self.root_face) % FACE_COUNT
        return face_id

    def _quotient_to_path(self, q: int) -> tuple[int, ...]:
        if not 0 <= q < OCTAL_BASE ** PATH_DEPTH:
            raise SpatializationError(
                f"quotient {q} exceeds octal capacity at depth {PATH_DEPTH}")
        digits: list[int] = []
        x = q
        for _ in range(PATH_DEPTH):
            digits.append(x % OCTAL_BASE)
            x //= OCTAL_BASE
        digits.reverse()  # natural big-endian (most-significant refinement first)
        if self.digit_order == "LITTLE_ENDIAN":
            digits.reverse()
        return tuple(digits)

    def _path_to_quotient(self, path) -> int:
        digits = list(int(d) for d in path)
        if len(digits) != PATH_DEPTH:
            raise SpatializationError(
                f"path must have depth {PATH_DEPTH}, got {len(digits)}")
        if self.digit_order == "LITTLE_ENDIAN":
            digits = list(reversed(digits))
        q = 0
        for d in digits:
            if not 0 <= d < OCTAL_BASE:
                raise SpatializationError(f"octal digit out of range: {d!r}")
            q = q * OCTAL_BASE + d
        return q

    def address_of_route(self, route) -> tuple[int, tuple[int, ...]]:
        """Route -> ``(face_id, octal path)`` under this family."""
        n = self.route_to_int(route)
        face_raw, q = self._face_raw_and_quotient(n)
        return self._apply_face_entry(face_raw), self._quotient_to_path(q)

    def route_of_address(self, face_id: int, path) -> tuple[int, ...]:
        """Inverse: ``(face_id, octal path)`` -> route under this family."""
        face_raw = self._invert_face_entry(int(face_id))
        q = self._path_to_quotient(path)
        n = q * FACE_COUNT + face_raw
        return self.int_to_route(n)

    # -- geometry ---------------------------------------------------------
    def map_route(self, route, *,
                 partition: IcosahedralPartition | None = None,
                 ico: Icosahedron | None = None) -> Spatialization:
        """Map a route to its address, cell polygon, and centroid."""
        if ico is None:
            ico = (partition or build_partition()).ico
        toks = _validate_route(route)
        face_id, path = self.address_of_route(toks)
        cell = path_cell(ico, face_id, path)
        return Spatialization(
            family_name=self.name,
            route=toks,
            face_id=face_id,
            path=path,
            centroid=cell_centroid(cell),
            polygon=cell.corners(),
            depth=len(path),
        )

    def search_space_size(self) -> int:
        """Number of distinct routes this family can represent (the ledger)."""
        return TOKEN_BASE ** ROUTE_TOKENS

    def descriptor(self) -> dict:
        """Parameters, invertibility, depth, and search-space size (work #2)."""
        return {
            "name": self.name,
            "token_order": list(self.token_order),
            "face_entry": self.face_entry,
            "digit_order": self.digit_order,
            "root_face": self.root_face,
            "invertible": True,
            "path_depth": PATH_DEPTH,
            "route_space": self.search_space_size(),
            "address_capacity": FACE_COUNT * OCTAL_BASE ** PATH_DEPTH,
            "uses_hash_or_catalogue": False,
        }


#: The bounded, finite family ensemble — exactly four (architecture spec).
FAMILIES: tuple[SpatializationFamily, ...] = (
    SpatializationFamily(
        name="F1_CANONICAL_DIRECT_BE",
        token_order=(0, 1, 2, 3, 4),
        face_entry="DIRECT",
        digit_order="BIG_ENDIAN",
    ),
    SpatializationFamily(
        name="F2_REVERSED_DIRECT_BE",
        token_order=(4, 3, 2, 1, 0),
        face_entry="DIRECT",
        digit_order="BIG_ENDIAN",
    ),
    SpatializationFamily(
        name="F3_CANONICAL_ROOTREL_BE",
        token_order=(0, 1, 2, 3, 4),
        face_entry="ROOT_RELATIVE",
        digit_order="BIG_ENDIAN",
    ),
    SpatializationFamily(
        name="F4_ROTATED_DIRECT_LE",
        token_order=(2, 3, 4, 0, 1),
        face_entry="DIRECT",
        digit_order="LITTLE_ENDIAN",
    ),
)

#: Number of candidate spatializations in the bounded ensemble.
FAMILY_COUNT = len(FAMILIES)

#: The family registry, by name.
FAMILY_BY_NAME: dict[str, SpatializationFamily] = {f.name: f for f in FAMILIES}


def get_family(name: str) -> SpatializationFamily:
    """Look up a family by name; refuse an unknown name."""
    try:
        return FAMILY_BY_NAME[name]
    except KeyError:
        raise SpatializationError(
            f"unknown spatialization family {name!r}; the bounded ensemble is "
            f"{sorted(FAMILY_BY_NAME)}") from None


#: Synthetic, public planted routes — no private narrative, just five-token
#: base-100 vectors used to measure the inverse pipeline's recovery power.
PLANTED_ROUTES: tuple[tuple[int, ...], ...] = (
    (1, 65, 87, 65, 23),   # the sanitized 165876523 route shape (public)
    (0, 0, 0, 0, 0),
    (99, 99, 99, 99, 99),
    (12, 34, 56, 78, 90),
    (7, 7, 7, 7, 7),
    (50, 0, 50, 0, 50),
)


def planted_mappings(family: SpatializationFamily, *,
                    ico: Icosahedron | None = None,
                    ) -> tuple[tuple[tuple[int, ...], np.ndarray], ...]:
    """Planted ``(route, centroid point)`` pairs under ``family`` (work #4).

    These are the ground-truth pairs the recovery test (P16) inverts: mapping
    each planted route forward yields a synthetic point; the inverse pipeline
    must recover the exact planted route. This measures recovery power without
    any hash or catalogue.
    """
    if ico is None:
        ico = build_partition().ico
    out = []
    for route in PLANTED_ROUTES:
        sp = family.map_route(route, ico=ico)
        out.append((sp.route, sp.centroid))
    return tuple(out)


def spatialization_report() -> dict:
    """Governance report for the bounded family ensemble."""
    return {
        "phase": "P15",
        "tranche": "T04",
        "what_this_is": (
            "the bounded ensemble of candidate spatialization families mapping "
            "five-token base-100 routes into the recursive one-to-eight "
            "icosahedral refinement; each family is a pure arithmetic bijection "
            "route <-> (face, octal path) with a deterministic cell polygon and "
            "centroid"),
        "codec_id": FAMILY_CODEC_ID,
        "codec_version": FAMILY_CODEC_VERSION,
        "family_count": FAMILY_COUNT,
        "families": [f.descriptor() for f in FAMILIES],
        "route_tokens": ROUTE_TOKENS,
        "token_base": TOKEN_BASE,
        "octal_base": OCTAL_BASE,
        "path_depth": PATH_DEPTH,
        "route_space_per_family": TOKEN_BASE ** ROUTE_TOKENS,
        "address_capacity_per_family": FACE_COUNT * OCTAL_BASE ** PATH_DEPTH,
        "uses_hash_or_catalogue": False,
        "planted_route_count": len(PLANTED_ROUTES),
        "reused_engine": "cwatlas.addressing / cwatlas.subdivision (NOT reimplemented)",
        "evidence_class": r1082_claims.EvidenceClass.CALIBRATED_CANDIDATE.value,
        "max_evidence": r1082_claims.MAX_CANDIDATE_EVIDENCE.value,
        "level": "SOFTWARE",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "physical_effects": "PHYSICAL_EFFECTS_NOT_CLAIMED",
        "source_origin": "SOURCE_ORIGIN_NOT_VALIDATED",
        "verdict": "R1082_SPATIALIZATION_FAMILIES_BOUNDED_INVERTIBLE_NO_CATALOGUE",
        "what_this_does_not_say": (
            "A spatialization is a CALIBRATED_CANDIDATE at most: one member of "
            "a bounded candidate ensemble, not a measured location, not a "
            "decoded destination, and no validation of the source origin. The "
            "correct family, if any, is selected only by sealed-anchor "
            "calibration, never by result shopping."),
    }
