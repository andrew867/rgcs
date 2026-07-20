"""S04/S05/S08 — a linear event ledger with the dates kept apart.

The chronology policy is strict about one thing above all: a "date" is
not a single field. An event has a claimed start, an observer-local
time, a timezone, a recording date, a publication date, a repost date,
a retrieval date, a conventional-discovery date, and a project-derivation
date, and collapsing them is how precedence arguments go wrong. This
module keeps them separate and lets only the well-dated items into the
strict timeline.

**This ledger is populated with public conventional-science events
only.** Coblentz's 1912 firefly estimate, the beta-spectrum sequence,
the CEvNS lineage, the tetrahedron paper, the firefly correction --
things with public DOIs and settled dates. The source-corpus chronology,
which would encode private material, is built and kept in the private
repository and never appears here. What is public is the *engine* and
the *conventional timeline*, not anyone's transcripts.

**Chronology is not causality.** Temporal order can establish precedence
and possible access -- who could have read what, and when. It cannot,
by itself, establish causation, secrecy, plagiarism, transfer, or
physical truth. :func:`refuse_causal_claim` enforces that, and the
dependency graph is explicitly labelled *possible access*, not
influence.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict

#: Date roles the policy requires be kept separate.
DATE_ROLES = (
    "event_start",
    "event_end",
    "observer_local",
    "recording",
    "publication",
    "repost",
    "retrieval",
    "conventional_discovery",
    "project_derivation",
)

#: Precision classes, coarsest last.
PRECISION_CLASSES = (
    "EXACT_TIMESTAMP",
    "EXACT_DATE",
    "MONTH_ONLY",
    "YEAR_ONLY",
    "INFERRED_RANGE",
    "UNKNOWN",
)

#: Only these two precisions may enter the strict timeline.
STRICT_PRECISIONS = ("EXACT_TIMESTAMP", "EXACT_DATE")


class ChronologyError(ValueError):
    """Raised on a malformed event or a forbidden promotion."""


class CausalClaimRefused(RuntimeError):
    """Raised when temporal order is offered as causation."""


@dataclass(frozen=True)
class DatedField:
    """One date, with its role and how well it is known."""

    role: str
    value: str            # ISO-8601 where known; free text otherwise
    precision: str

    def __post_init__(self) -> None:
        if self.role not in DATE_ROLES:
            raise ChronologyError(f"unknown date role {self.role!r}")
        if self.precision not in PRECISION_CLASSES:
            raise ChronologyError(
                f"unknown precision {self.precision!r}")

    @property
    def strict(self) -> bool:
        return self.precision in STRICT_PRECISIONS


@dataclass(frozen=True)
class Event:
    """A dated event. Evidence class and public/private are explicit."""

    key: str
    label: str
    dates: tuple[DatedField, ...]
    evidence_class: str
    public: bool
    doi: str = ""
    note: str = ""

    def date(self, role: str) -> DatedField | None:
        for d in self.dates:
            if d.role == role:
                return d
        return None

    @property
    def sort_year(self) -> int | None:
        """Year of the best-dated field, for ordering only."""
        best = None
        for d in self.dates:
            if d.value[:4].isdigit():
                y = int(d.value[:4])
                best = y if best is None else min(best, y)
        return best

    @property
    def enters_strict_timeline(self) -> bool:
        """An event enters only if it has at least one strict date."""
        return any(d.strict for d in self.dates)


def _y(role, year, precision="YEAR_ONLY"):
    return DatedField(role, str(year), precision)


#: The public conventional-science timeline. Every entry has a public
#: source and a settled date. Nothing here is from the private corpus.
CONVENTIONAL_EVENTS = (
    Event(
        "coblentz_1912", "Coblentz estimates firefly light output",
        (_y("publication", 1912),
         _y("conventional_discovery", 1912)),
        "CONVENTIONAL_LITERATURE", True,
        note="the 1e13-1e14 photons/flash figure later found too high"),
    Event(
        "chadwick_1914", "Chadwick: the beta spectrum is continuous",
        (DatedField("publication", "1914", "YEAR_ONLY"),),
        "CONVENTIONAL_LITERATURE", True),
    Event(
        "ellis_wooster_1927",
        "Ellis & Wooster: the continuum is real, not instrumental",
        (_y("publication", 1927),), "CONVENTIONAL_LITERATURE", True),
    Event(
        "pauli_1930", "Pauli postulates the neutrino",
        (DatedField("event_start", "1930-12-04", "EXACT_DATE"),
         DatedField("publication", "1930-12-04", "EXACT_DATE")),
        "CONVENTIONAL_LITERATURE", True,
        note="the letter to the Tuebingen meeting is exactly dated"),
    Event(
        "fermi_1934", "Fermi's theory of beta decay",
        (_y("publication", 1934),), "CONVENTIONAL_LITERATURE", True),
    Event(
        "freedman_1974", "Freedman predicts coherent neutrino scattering",
        (_y("publication", 1974),), "CONVENTIONAL_LITERATURE", True),
    Event(
        "drukier_stodolsky_1984",
        "Drukier & Stodolsky: coherence permits small detectors",
        (_y("publication", 1984),), "CONVENTIONAL_LITERATURE", True),
    Event(
        "coherent_2017", "COHERENT observes CEvNS",
        (_y("publication", 2017),), "CONVENTIONAL_LITERATURE", True,
        doi="10.1126/science.aao0990"),
    Event(
        "vilcu_2018", "Tetrahedron vertex estimator published",
        (_y("publication", 2018),), "CONVENTIONAL_LITERATURE", True,
        doi="10.1007/s10231-017-0688-6"),
    Event(
        "silver_2026", "Firefly brightness overestimate corrected",
        (_y("publication", 2026),), "CONVENTIONAL_LITERATURE", True,
        doi="10.1119/5.0325834",
        note="corrects Coblentz 1912 downward by 2-6 orders"),
)


def strict_timeline(events=CONVENTIONAL_EVENTS) -> list[Event]:
    """Events with at least one exact date, ordered by best year.

    Lower-precision items are searchable elsewhere but must not be
    ordered as if their dates were known -- so they are excluded here.
    """
    strict = [e for e in events if e.enters_strict_timeline]
    return sorted(strict, key=lambda e: (e.sort_year or 9999))


def full_ledger(events=CONVENTIONAL_EVENTS) -> list[Event]:
    return sorted(events, key=lambda e: (e.sort_year or 9999))


# --- S08: possible-access edges, not influence edges -------------------

@dataclass(frozen=True)
class AccessEdge:
    """B was published before A, so A's author COULD have seen it.

    This is a statement about opportunity, never about influence.
    """

    earlier: str
    later: str

    def as_record(self) -> dict:
        return {"earlier": self.earlier, "later": self.later,
                "means": "possible access only, not influence"}


def possible_access_edges(events=CONVENTIONAL_EVENTS) -> list[AccessEdge]:
    """Every strictly-earlier -> later pair, by publication year.

    Deliberately complete and deliberately weak: it says who *could*
    have read what. Turning any edge into an influence claim needs
    evidence this graph does not contain.
    """
    dated = [e for e in events if e.sort_year is not None]
    edges = []
    for a in dated:
        for b in dated:
            if a.sort_year < b.sort_year:
                edges.append(AccessEdge(a.key, b.key))
    return edges


def refuse_causal_claim(earlier: str, later: str) -> None:
    """Temporal order is not causation."""
    raise CausalClaimRefused(
        f"{earlier!r} predates {later!r}, which establishes possible "
        f"access and nothing more. Precedence is not causation, "
        f"plagiarism, secrecy, or transfer. Asserting influence "
        f"requires evidence of the actual path -- a citation, a "
        f"correspondence, a shared source -- that temporal order alone "
        f"cannot supply.")


def chronology_report() -> dict:
    strict = strict_timeline()
    return {
        "date_roles_kept_separate": list(DATE_ROLES),
        "precision_classes": list(PRECISION_CLASSES),
        "strict_precisions": list(STRICT_PRECISIONS),
        "conventional_events": len(CONVENTIONAL_EVENTS),
        "in_strict_timeline": len(strict),
        "strict_timeline": [
            {"key": e.key, "label": e.label, "year": e.sort_year}
            for e in strict],
        "possible_access_edges": len(possible_access_edges()),
        "scope": (
            "public conventional-science events only. The source-corpus "
            "chronology is built in the private repository and never "
            "appears in the public tree"),
        "chronology_is_not_causality": (
            "temporal order establishes precedence and possible access. "
            "It cannot establish causation, secrecy, plagiarism, "
            "transfer, or physical truth on its own"),
        "evidence_class": "DERIVED_MATHEMATICS",
        "measured_here": "nothing",
    }
