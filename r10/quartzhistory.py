"""P01/P02 — the verified postwar quartz-growth patent and industry
timeline, and the refusal it exists to make.

The history here is real and checkable from primary patent records:
after the war there was intense industrial effort to grow oscillator-
grade quartz, it ran through Brush, Clevite, and Bell Laboratories, and
those same companies had deep electronics and defense/ordnance business.
Two things are therefore true and are recorded as `HISTORICAL_FACT`:

* **the postwar quartz industrial timeline is verified**, and
* **the defense-company overlap is verified**.

A third thing is tempting and is **refused**: that this overlap proves a
classified or extraterrestrial inheritance behind the technology.
Corporate and defense adjacency is not provenance. Firms that make
oscillators also make ordnance because oscillators go in radios and
radios go in weapons; that is ordinary industrial history, not a hidden
lineage. `CLASSIFIED_TECHNOLOGY_LINK_NOT_ESTABLISHED` is the verdict, and
:func:`refuse_classified_link` enforces it.

Dates and patent numbers are transcribed from the source pack's primary-
record research; they are marked ``HISTORICAL_FACT`` with a
``source_quality`` of ``PRIMARY_RECORD_SECONDHAND`` — sourced from the
research compilation, not independently re-verified against a patent
office in this environment. Chronology is ordering, never causation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum


class HistoryError(RuntimeError):
    """Raised on a malformed record or an overclaim past the evidence."""


class SourceQuality(Enum):
    PRIMARY_RECORD = "PRIMARY_RECORD"                     # verified at the office
    PRIMARY_RECORD_SECONDHAND = "PRIMARY_RECORD_SECONDHAND"  # sourced from research
    SECONDARY = "SECONDARY"


@dataclass(frozen=True)
class CrystalGrowthPatent:
    """One patent/industry record. Dates are HISTORICAL_FACT as sourced."""

    patent_id: str
    jurisdiction: str
    title: str
    inventors: tuple[str, ...]
    assignee_at_filing: str
    priority_date: date | None
    filing_date: date | None
    publication_date: date | None
    grant_date: date | None
    growth_method: str = ""
    seed_type: str = ""
    axis_orientation: str = ""
    industrial_context: str = ""
    defense_context: str = ""
    source_quality: SourceQuality = SourceQuality.PRIMARY_RECORD_SECONDHAND
    excerpts: str = ""

    def __post_init__(self) -> None:
        if not self.patent_id:
            raise HistoryError("patent_id is required")

    @property
    def milestone_date(self) -> date | None:
        """The date this record represents on the timeline: the grant or
        publication for a granted/published patent, the filing/priority for
        a pending application. It is the latest declared date, and it is
        what the verified timeline is ordered by."""
        cands = [d for d in (self.priority_date, self.filing_date,
                             self.publication_date, self.grant_date)
                 if d is not None]
        return max(cands) if cands else None


#: The verified timeline, transcribed from the pack's primary-record
#: research (VERIFIED_PATENT_TIMELINE). Each is HISTORICAL_FACT as sourced.
TIMELINE: tuple[CrystalGrowthPatent, ...] = (
    CrystalGrowthPatent(
        "US-Buehler-CIP-1948", "US", "Bell continuation-in-part (later abandoned)",
        ("Ernest Buehler",), "Bell Laboratories",
        date(1948, 12, 30), date(1948, 12, 30), None, None,
        growth_method="hydrothermal",
        industrial_context="early Bell hydrothermal quartz effort",
        excerpts="a later Bell patent identifies this earlier CIP application, "
                 "later abandoned"),
    CrystalGrowthPatent(
        "BrushDev-priority-1949", "US", "Brush Development hydrothermal quartz process",
        ("Brush Development",), "Brush Development",
        date(1949, 5, 21), date(1949, 5, 21), None, None,
        growth_method="hydrothermal",
        industrial_context="Brush hydrothermal quartz priority"),
    CrystalGrowthPatent(
        "Brush-GB-1950", "GB", "Brush UK filing", ("Brush Development",),
        "Brush Development", None, date(1950, 3, 6), None, None,
        growth_method="hydrothermal"),
    CrystalGrowthPatent(
        "Clevite-SobekHale-app-1950", "US", "Sobek and Hale (Clevite) application",
        ("Sobek", "Hale"), "Clevite", None, date(1950, 4, 11), None, None,
        growth_method="hydrothermal seeded quartz"),
    CrystalGrowthPatent(
        "Bell-Buehler-app-1952", "US", "Buehler (Bell Laboratories) application",
        ("Ernest Buehler",), "Bell Laboratories", None, date(1952, 4, 28),
        None, None, growth_method="hydrothermal"),
    CrystalGrowthPatent(
        "GB682203A", "GB", "Hydrothermal seeded quartz in hot high-pressure "
        "aqueous alkali carbonate/bicarbonate", (), "Brush Development",
        None, None, date(1952, 11, 5), None,
        growth_method="hydrothermal, alkali carbonate/bicarbonate solvent",
        seed_type="seeded"),
    CrystalGrowthPatent(
        "US2675303A", "US", "Sobek and Hale (Clevite), oscillator-grade synthetic quartz",
        ("Sobek", "Hale"), "Clevite", date(1950, 4, 11), date(1950, 4, 11),
        date(1954, 4, 13), date(1954, 4, 13),
        growth_method="hydrothermal seeded", seed_type="seeded",
        axis_orientation="seed growth depends appreciably on exact position "
                         "and orientation",
        industrial_context="high-quality oscillator-grade synthetic quartz",
        defense_context="Clevite electronics/ordnance business"),
    CrystalGrowthPatent(
        "US2785058A", "US", "Buehler (Bell Labs), natural or synthetic seed quartz",
        ("Ernest Buehler",), "Bell Laboratories", date(1952, 4, 28),
        date(1952, 4, 28), date(1957, 3, 12), date(1957, 3, 12),
        growth_method="hydrothermal", seed_type="natural or synthetic seed",
        axis_orientation="growth along the main crystallographic axis, plates "
                         "perpendicular, vertical mounting, minor-rhombohedral "
                         "cut ~38 deg to the bomb axis"),
    CrystalGrowthPatent(
        "US3051558A", "US", "Clevite hydrothermal synthesis", (), "Clevite",
        None, date(1956, 1, 1), date(1962, 1, 1), date(1962, 1, 1),
        growth_method="hydrothermal",
        industrial_context="filed 1956, published 1962"),
)

#: Non-patent industry milestones (context), same HISTORICAL_FACT basis.
INDUSTRY_EVENTS = (
    (date(1952, 1, 1), "Cleveland Graphite Bronze bought Brush Development for "
                       "$7M, entered electronics, adopted the Clevite name"),
    (date(1959, 1, 1), "by 1959 over one-third of Clevite sales were "
                       "electronics, incl. Brush Instruments, components, "
                       "transistors, and ordnance"),
    (date(1961, 1, 1), "second-harmonic generation first observed in a single "
                       "quartz crystal (Franken et al.)"),
    (date(1964, 1, 1), "early organic-material SHG observation"),
)


def timeline_is_ordered() -> bool:
    """The recorded anchor dates are non-decreasing (a checkable fact)."""
    anchors = [p.milestone_date for p in TIMELINE if p.milestone_date]
    return all(a <= b for a, b in zip(anchors, anchors[1:]))


def verify_timeline() -> dict:
    """Return the three verdicts the pack requires, with their basis."""
    return {
        "postwar_quartz_industrial_timeline": "POSTWAR_QUARTZ_INDUSTRIAL_TIMELINE_VERIFIED",
        "defense_company_overlap": "DEFENSE_COMPANY_OVERLAP_VERIFIED",
        "classified_technology_link": "CLASSIFIED_TECHNOLOGY_LINK_NOT_ESTABLISHED",
        "basis": "primary patent records (transcribed) + company history",
        "records": len(TIMELINE),
        "ordered": timeline_is_ordered(),
        "evidence_class": "HISTORICAL_FACT",
    }


def refuse_classified_link(*_args, **_kwargs) -> None:
    """Refuse to promote corporate/defense overlap into a classified or
    extraterrestrial inheritance claim."""
    raise HistoryError(
        "refused: verified corporate and defense overlap does NOT establish "
        "a classified, suppressed, or extraterrestrial technology lineage. "
        "Firms that grew oscillator quartz also had ordnance business because "
        "oscillators go in radios; that is ordinary industrial adjacency, not "
        "provenance. CLASSIFIED_TECHNOLOGY_LINK_NOT_ESTABLISHED.")


def refuse_chronology_as_causation(*_args, **_kwargs) -> None:
    """A precedes B in the timeline does not mean A caused or seeded B."""
    raise HistoryError(
        "refused: chronological order is not causation. That one patent or "
        "event precedes another does not establish that it caused, seeded, or "
        "secretly informed it.")


def quartzhistory_report() -> dict:
    return {
        "what_this_is": (
            "a verified postwar quartz-growth patent and industry timeline "
            "(Brush, Clevite, Bell Labs), from primary patent records"),
        "verdicts": verify_timeline(),
        "records": len(TIMELINE),
        "industry_events": len(INDUSTRY_EVENTS),
        "evidence_class": "HISTORICAL_FACT",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "verdict": "POSTWAR_QUARTZ_INDUSTRIAL_TIMELINE_VERIFIED",
        "what_this_does_not_say": (
            "It does not say the technology has a classified, suppressed, or "
            "extraterrestrial origin, that natural-quartz properties were "
            "hidden, or that industrial adjacency to defense proves a hidden "
            "lineage. It records verified history and refuses to read a "
            "conspiracy into a chronology."),
    }
