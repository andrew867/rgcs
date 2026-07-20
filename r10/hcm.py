"""Q13-Q17 — Hedron Coordinate Mapping: roots, topology, address, shells.

A recursive addressing scheme over nested barycentric roots, with the
Earth sphere partitioned by a polyhedral topology and refined 1-to-8.

The arithmetic is exact and pleasing:

    4096**3 == 8**12 == 2**36 == 68_719_476_736

Twelve levels of one-to-eight refinement is exactly thirty-six bits,
which is exactly three 12-bit words. Starting from a mean Earth radius
of 6371.0088 km, twelve levels reach a linear scale of **1.5554 km**.

Three things this module refuses to do, each of which would be easy
and wrong.

**It does not conflate faces with vertices.** An icosahedron has 20
faces and 12 vertices; its dual, the dodecahedron, has 12 faces and 20
vertices. "20" and "12" appear in both, swapped. A scheme that says
"20 regions" without saying *20 of what* is not specified, and the two
readings give different neighbour relations, different gate semantics
and different addresses. Both are implemented; neither is assumed.

**It does not present 20 and 36 as predictions.** They were selected
*after* the target scale was known. Twelve levels reaches kilometre
scale, and kilometre scale is what was wanted -- so twelve is a
retrospective fit, and ``address_provenance()`` says so. A parameter
chosen to land on a known answer is not evidence about the world. It
would become one only if fixed in advance and then tested against
something it was not fitted to.

**It does not manufacture precision from nominal figures.** A shell
quoted as "2500 statute miles" converts to 4023.36 km *exactly*, but
the exactness belongs to the conversion factor, not the measurement.
"2500" carries about two significant figures; reporting 4023.36 km
implies six. ``Shell`` tracks significant figures through the
conversion and refuses to report more than it was given.

Nothing here is measured. No physical claim is made about gates,
nodes, pinches, or any correspondence between graph distance and
spacetime distance -- see :func:`refuse_metric_promotion`.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

# --- constants, with provenance ---------------------------------------

#: IUGG mean Earth radius, km. A defined mean, not a measurement of
#: any particular direction; Earth is not a sphere.
EARTH_MEAN_RADIUS_KM = 6371.0088

#: Exact by international agreement since 1959.
METRES_PER_STATUTE_MILE = Fraction(1_609_344, 1000)

#: Refinement: each cell splits into eight.
REFINEMENT_FACTOR = 8

#: Twelve levels. See address_provenance() for why this number is a
#: retrospective fit and not a prediction.
DEFAULT_LEVELS = 12


class TopologyError(ValueError):
    """Raised when face and vertex semantics are conflated."""


class PrecisionError(ValueError):
    """Raised when a result would claim more precision than its input."""


class MetricPromotionRefused(RuntimeError):
    """Raised when graph structure is offered as physical geometry."""


# --- Q14: topology, without conflating the dual pair -------------------

@dataclass(frozen=True)
class Topology:
    """A convex regular polyhedron, with its counts stated separately."""

    name: str
    faces: int
    vertices: int
    edges: int
    #: Which element carries a region address. This is the field that
    #: the "20 regions" phrasing leaves undetermined.
    region_element: str          # "FACE" or "VERTEX"

    def __post_init__(self) -> None:
        if self.region_element not in ("FACE", "VERTEX"):
            raise TopologyError(
                f"region_element must be FACE or VERTEX, got "
                f"{self.region_element!r}")
        if self.vertices - self.edges + self.faces != 2:
            raise TopologyError(
                f"{self.name}: V - E + F = "
                f"{self.vertices - self.edges + self.faces}, not 2; "
                f"this is not a valid convex polyhedron")

    @property
    def region_count(self) -> int:
        return self.faces if self.region_element == "FACE" else self.vertices


ICOSAHEDRON_FACES = Topology("icosahedron", 20, 12, 30, "FACE")
ICOSAHEDRON_VERTICES = Topology("icosahedron", 20, 12, 30, "VERTEX")
DODECAHEDRON_FACES = Topology("dodecahedron", 12, 20, 30, "FACE")
DODECAHEDRON_VERTICES = Topology("dodecahedron", 12, 20, 30, "VERTEX")

#: Every reading that yields twenty regions. There is more than one,
#: which is the point.
TWENTY_REGION_READINGS = (ICOSAHEDRON_FACES, DODECAHEDRON_VERTICES)


def dual_ambiguity_report() -> dict:
    """Why "twenty regions" does not specify a topology."""
    return {
        "readings_giving_20_regions": [
            {"solid": t.name, "element": t.region_element,
             "faces": t.faces, "vertices": t.vertices}
            for t in TWENTY_REGION_READINGS],
        "readings_giving_12_regions": [
            {"solid": t.name, "element": t.region_element}
            for t in (ICOSAHEDRON_VERTICES, DODECAHEDRON_FACES)],
        "ambiguous": True,
        "why_it_matters": (
            "the two readings are not cosmetic relabelling. Twenty "
            "icosahedral faces meet three at a vertex and share edges "
            "with three neighbours; twenty dodecahedral vertices meet "
            "three faces and have three edge-neighbours. The adjacency "
            "graphs differ, so neighbour queries, gate semantics and "
            "any address that encodes 'next region' differ too."),
        "resolution": (
            "unresolved by the source material, and left unresolved "
            "here. Both are constructible; the caller must state which "
            "one, and Address records it."),
    }


# --- Q15: the address ---------------------------------------------------

def address_bits(levels: int = DEFAULT_LEVELS) -> int:
    """Bits needed for `levels` levels of 1-to-8 refinement."""
    if levels < 0:
        raise ValueError("levels must be non-negative")
    return 3 * levels


def cell_count(topology: Topology, levels: int = DEFAULT_LEVELS) -> int:
    return topology.region_count * REFINEMENT_FACTOR ** levels


def linear_scale_km(levels: int = DEFAULT_LEVELS,
                    radius_km: float = EARTH_MEAN_RADIUS_KM) -> float:
    """Characteristic cell size after `levels` refinements.

    Each 1-to-8 split halves the linear scale. This is a scale
    estimate, not a cell diameter: cells on a subdivided polyhedron
    are not congruent, and the spread grows with distance from a
    vertex.
    """
    if levels < 0:
        raise ValueError("levels must be non-negative")
    return radius_km / (2 ** levels)


@dataclass(frozen=True)
class Address:
    """A region plus a refinement path. Frame and epoch are required.

    An address is a *label*. It is not a position until a frame, an
    epoch and an uncertainty accompany it, which is why those fields
    have no defaults.
    """

    topology: Topology
    region: int
    path: tuple[int, ...]        # each entry 0..7
    frame: str
    epoch: str
    uncertainty_km: float

    def __post_init__(self) -> None:
        if not 0 <= self.region < self.topology.region_count:
            raise ValueError(
                f"region {self.region} outside 0.."
                f"{self.topology.region_count - 1} for "
                f"{self.topology.name} {self.topology.region_element}s")
        for i, d in enumerate(self.path):
            if not 0 <= d < REFINEMENT_FACTOR:
                raise ValueError(
                    f"refinement digit {d} at level {i} outside 0..7")
        if self.uncertainty_km < 0:
            raise ValueError("uncertainty cannot be negative")
        if not self.frame or not self.epoch:
            raise ValueError(
                "frame and epoch are required: an address without them "
                "is a label, not a position")

    @property
    def levels(self) -> int:
        return len(self.path)

    @property
    def bits(self) -> int:
        return address_bits(self.levels)

    def to_int(self) -> int:
        """Pack the refinement path into an integer (region excluded)."""
        v = 0
        for d in self.path:
            v = (v << 3) | d
        return v

    @classmethod
    def from_int(cls, packed: int, levels: int, topology: Topology,
                 region: int, frame: str, epoch: str,
                 uncertainty_km: float) -> "Address":
        if packed < 0 or packed >= REFINEMENT_FACTOR ** levels:
            raise ValueError(
                f"packed value {packed} outside 0..8**{levels}-1")
        path = tuple((packed >> (3 * (levels - 1 - i))) & 0b111
                     for i in range(levels))
        return cls(topology, region, path, frame, epoch, uncertainty_km)

    def as_words(self, word_bits: int = 12) -> tuple[int, ...]:
        """Split into fixed-width words. 36 bits = three 12-bit words."""
        if self.bits % word_bits:
            raise ValueError(
                f"{self.bits} bits does not divide into {word_bits}-bit "
                f"words")
        n = self.bits // word_bits
        v = self.to_int()
        mask = (1 << word_bits) - 1
        return tuple((v >> (word_bits * (n - 1 - i))) & mask
                     for i in range(n))


def address_provenance(levels: int = DEFAULT_LEVELS) -> dict:
    """Are twenty regions and thirty-six bits predictions? No.

    This is the honest core of Q15. The numbers are correct and the
    arithmetic is elegant; that is not the same as being evidence.
    """
    return {
        "levels": levels,
        "bits": address_bits(levels),
        "identity": "4096**3 == 8**12 == 2**36",
        "identity_holds": 4096 ** 3 == 8 ** levels == 2 ** address_bits(levels)
                          if levels == 12 else None,
        "linear_scale_km": linear_scale_km(levels),
        "status": "RETROSPECTIVE_FIT",
        "why": (
            "twelve levels was selected because twelve levels reaches "
            "kilometre scale, and kilometre scale was the target. The "
            "parameter was fitted to a known answer. Choosing eleven "
            "or thirteen would have given 3.1 km or 0.78 km, and "
            "whichever matched the desired resolution would have been "
            "the one adopted."),
        "what_would_make_it_evidence": (
            "fixing the topology, level count and orientation in "
            "advance, then testing them against an observable they "
            "were not fitted to -- and reporting the result whichever "
            "way it came out"),
        "elegance_warning": (
            "8**12 == 2**36 == 4096**3 is a true and tidy identity, "
            "and tidiness is not evidence. Any power-of-two refinement "
            "produces identities like this at every level; they are a "
            "property of the radix, not a discovery about Earth."),
    }


# --- Q17: shells, without manufacturing precision ----------------------

@dataclass(frozen=True)
class Shell:
    """A candidate shell altitude, carrying its significant figures."""

    label: str
    value: Fraction
    unit: str                    # "STATUTE_MILE" | "KM"
    significant_figures: int
    basis: str                   # how the figure was obtained

    def __post_init__(self) -> None:
        if self.significant_figures < 1:
            raise ValueError("significant_figures must be >= 1")
        if self.unit not in ("STATUTE_MILE", "KM"):
            raise ValueError(f"unknown unit {self.unit!r}")

    def to_km_exact(self) -> Fraction:
        """The exact converted value. Correct, and misleading alone."""
        if self.unit == "KM":
            return self.value
        return self.value * METRES_PER_STATUTE_MILE / 1000

    def to_km_reported(self) -> str:
        """The value rounded to the significant figures actually held.

        The conversion factor is exact by definition, so the arithmetic
        is exact -- but exactness of a conversion does not create
        precision that the input never had (Q17).
        """
        exact = float(self.to_km_exact())
        if exact == 0:
            return "0"
        from math import floor, log10
        digits = self.significant_figures - 1 - floor(log10(abs(exact)))
        return f"{round(exact, digits):.{max(digits, 0)}f}"

    def precision_report(self) -> dict:
        return {
            "label": self.label,
            "as_given": f"{float(self.value):g} {self.unit}",
            "significant_figures": self.significant_figures,
            "exact_conversion_km": str(self.to_km_exact()),
            "honestly_reportable_km": self.to_km_reported(),
            "basis": self.basis,
            "warning": (
                "the exact conversion is exact because the statute "
                "mile is defined as exactly 1609.344 m. That exactness "
                "belongs to the definition, not to the measurement. "
                "Quoting the full converted figure would claim "
                "precision the source never supplied."),
        }


#: The candidate shell from the source material. Two significant
#: figures: "2500" is a round nominal number, not a measurement to the
#: nearest mile, and nothing in the record says otherwise.
NOMINAL_SHELL = Shell(
    label="candidate shell, nominal source distance",
    value=Fraction(2500),
    unit="STATUTE_MILE",
    significant_figures=2,
    basis=("stated as a round figure in source material; no "
           "instrument, method, or error bar accompanies it"),
)


def refuse_precise_shell() -> None:
    """Refuse to treat the nominal shell as a precise altitude."""
    raise PrecisionError(
        f"the candidate shell is a nominal round figure "
        f"({float(NOMINAL_SHELL.value):g} statute miles, ~2 significant "
        f"figures). It converts to "
        f"{NOMINAL_SHELL.to_km_exact()} km exactly, but that exactness "
        f"is a property of the defined conversion factor, not of the "
        f"source. Reportable as "
        f"{NOMINAL_SHELL.to_km_reported()} km and no better.")


# --- firewalls ----------------------------------------------------------

def refuse_metric_promotion(*args, **kwargs) -> None:
    """Graph adjacency is not spacetime geometry."""
    raise MetricPromotionRefused(
        "an address identifies a cell in a synthetic partition. "
        "Adjacency in that partition is a property of the "
        "construction, not of spacetime, and no shortcut through the "
        "graph corresponds to a shortened physical path. Promoting "
        "graph distance to metric distance would require a mechanism, "
        "a stress-energy budget, and a measurement -- none of which "
        "exists here.")


def hcm_report() -> dict:
    return {
        "topology": dual_ambiguity_report(),
        "address": address_provenance(),
        "shell": NOMINAL_SHELL.precision_report(),
        "cells_at_12_levels": cell_count(ICOSAHEDRON_FACES, 12),
        "evidence_class": "DERIVED_MATHEMATICS",
        "measured_here": "nothing",
        "what_this_is": (
            "a well-defined synthetic addressing scheme over a sphere, "
            "with exact arithmetic and explicit frames. It is "
            "reusable infrastructure."),
        "what_this_is_not": (
            "evidence that Earth has twenty regions, that a polyhedral "
            "partition is physically privileged, that gates or nodes "
            "exist, or that anything about the scheme constrains "
            "physics. A partition is a choice of bookkeeping."),
    }
