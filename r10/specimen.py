"""P04 — specimen ontology and chain of custody for the natural-vs-
synthetic quartz study.

A crystal specimen carries dozens of describable attributes -- handedness,
twin law, cut angles, dimensions, mass, inclusions, trace elements -- and
none of them is the load-bearing field. The two fields that decide whether
a specimen means anything to this study are its **verified origin** and its
**chain of custody**. Everything else is measurable *after* the specimen is
in hand; provenance is the one thing that cannot be recovered later if it
was never established.

The whole point of the study is to distinguish natural geological quartz
from hydrothermal synthetic quartz *by measurement*. That makes two labels
worthless as evidence:

**A seller's "natural" label is not provenance.** Origin is ``VERIFIED``
only when a documented, append-only chain of custody backs it. A purchase
from a seller -- however reputable -- with no custody record is
``ORIGIN_UNVERIFIED``. A specimen tagged NATURAL with an empty custody
chain is, by construction, ``ORIGIN_UNVERIFIED``.

**A material-class label is not a measurement.** You cannot confirm that a
specimen is natural quartz (rather than synthetic quartz, fused silica, or
non-quartz glass) from what it was sold as. Confirming material class
requires measurement -- that is the study, not an input to it. This module
refuses both shortcuts explicitly.

Nothing here is a physical result. This is typed bookkeeping: it records
what is claimed, tracks custody, hashes for integrity, and redacts private
locality and seller in any public projection. No specimen is measured by
any function in this file.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum


class SpecimenError(RuntimeError):
    """Raised on a malformed specimen record or a refused provenance claim."""


# --- controlled vocabularies -------------------------------------------

class MaterialClass(Enum):
    """What the specimen is made of. Confirmed only by measurement."""

    NATURAL_QUARTZ = "NATURAL_QUARTZ"
    HYDROTHERMAL_SYNTHETIC_QUARTZ = "HYDROTHERMAL_SYNTHETIC_QUARTZ"
    FUSED_SILICA = "FUSED_SILICA"
    NONQUARTZ_GLASS = "NONQUARTZ_GLASS"
    UNKNOWN = "UNKNOWN"


class Handedness(Enum):
    """Optical handedness of the quartz, or its absence/ignorance."""

    LEFT = "LEFT"
    RIGHT = "RIGHT"
    UNTWINNED_UNKNOWN = "UNTWINNED_UNKNOWN"


class OriginStatus(Enum):
    """Whether the specimen's origin is backed by custody. Never a label."""

    VERIFIED = "VERIFIED"
    ORIGIN_UNVERIFIED = "ORIGIN_UNVERIFIED"


#: The material classes that are quartz proper (natural or synthetic).
QUARTZ_CLASSES = frozenset({
    MaterialClass.NATURAL_QUARTZ,
    MaterialClass.HYDROTHERMAL_SYNTHETIC_QUARTZ,
})

#: Token used wherever a private field is redacted in a public view.
REDACTED = "WITHHELD_PRIVATE"


# --- chain of custody --------------------------------------------------

@dataclass(frozen=True)
class CustodyEvent:
    """One transfer of custody. Immutable, hashable, append-only in use.

    ``evidence`` names the documentation backing the transfer (a receipt,
    an export permit, a lab intake form). An event with no ``from_party``,
    ``to_party``, ``date`` or ``evidence`` is malformed.
    """

    from_party: str
    to_party: str
    date: str
    evidence: str

    def __post_init__(self) -> None:
        if not (self.from_party and self.to_party and self.date
                and self.evidence):
            raise SpecimenError(
                "a custody event needs from_party, to_party, date and "
                "documentary evidence; an undocumented transfer is not "
                "custody")


class ChainOfCustody:
    """An ordered, append-only list of custody events.

    Events are only ever appended; there is no edit or delete. An empty
    chain is a valid object -- it just means the origin is unverified.
    """

    def __init__(self, events: tuple[CustodyEvent, ...] = ()) -> None:
        self._events: list[CustodyEvent] = list(events)

    def append(self, event: CustodyEvent) -> None:
        if not isinstance(event, CustodyEvent):
            raise SpecimenError("only CustodyEvent may be appended")
        self._events.append(event)

    def refuse_overwrite(self, index: int) -> None:
        raise SpecimenError(
            "the chain of custody is append-only; a correction is a new "
            "appended event that references the earlier one, never an "
            "overwrite of history")

    @property
    def events(self) -> tuple[CustodyEvent, ...]:
        return tuple(self._events)

    @property
    def documented(self) -> bool:
        """True iff at least one documented custody event is present."""
        return len(self._events) > 0

    def __len__(self) -> int:
        return len(self._events)


# --- the specimen schema ----------------------------------------------

@dataclass(frozen=True)
class Specimen:
    """A single crystal specimen in the natural-vs-synthetic quartz study.

    ``verified_origin`` and ``chain_of_custody`` are the load-bearing
    fields. ``material_class`` records what is *claimed or measured*, but a
    claim from a label carries no weight -- see
    ``refuse_material_class_without_measurement``. ``locality`` and
    ``seller`` are private and are redacted by ``public_view``.
    """

    specimen_id: str
    material_class: MaterialClass = MaterialClass.UNKNOWN
    verified_origin: OriginStatus = OriginStatus.ORIGIN_UNVERIFIED
    locality: str = ""                      # private; redacted publicly
    geological_context: str = ""
    estimated_age: str = ""
    seller: str = ""                        # private; redacted publicly
    chain_of_custody: ChainOfCustody = field(default_factory=ChainOfCustody)
    growth_method: str = "UNKNOWN"
    seed_origin: str = "UNKNOWN"
    handedness: Handedness = Handedness.UNTWINNED_UNKNOWN
    twins: str = "UNKNOWN"
    c_axis: str = ""
    x_axes: str = ""
    cut_angles: tuple[float, ...] = ()
    dimensions: tuple[float, ...] = ()
    mass: float | None = None
    density: float | None = None
    inclusions: tuple[str, ...] = ()
    fractures: tuple[str, ...] = ()
    coatings: tuple[str, ...] = ()
    treatments: tuple[str, ...] = ()
    irradiation: str = "NONE_DECLARED"
    heat_history: str = "NONE_DECLARED"
    defect_proxies: tuple[str, ...] = ()
    trace_elements: tuple[str, ...] = ()
    optical: tuple[str, ...] = ()
    electrical: tuple[str, ...] = ()
    acoustic: tuple[str, ...] = ()
    photos: tuple[str, ...] = ()
    hashes: tuple[str, ...] = ()
    uncertainty: str = ""
    publication_class: str = "PRIVATE_ONLY"

    def __post_init__(self) -> None:
        if not self.specimen_id:
            raise SpecimenError("specimen_id is required")
        if not isinstance(self.material_class, MaterialClass):
            raise SpecimenError("material_class must be a MaterialClass")
        if not isinstance(self.handedness, Handedness):
            raise SpecimenError("handedness must be a Handedness")
        if not isinstance(self.chain_of_custody, ChainOfCustody):
            raise SpecimenError("chain_of_custody must be a ChainOfCustody")


# --- origin status: custody, not label --------------------------------

def origin_status(specimen: Specimen) -> OriginStatus:
    """Origin is VERIFIED only with a documented chain of custody.

    A seller label -- and therefore any ``material_class``, including
    NATURAL_QUARTZ -- proves nothing on its own. With no documented
    custody event the status is ORIGIN_UNVERIFIED, whatever the label says.
    """
    if specimen.chain_of_custody.documented:
        return OriginStatus.VERIFIED
    return OriginStatus.ORIGIN_UNVERIFIED


# --- refusals ----------------------------------------------------------

def refuse_natural_claim_without_custody(specimen: Specimen) -> None:
    """Refuse to assert a specimen is natural geological quartz with no
    chain of custody. A purchase from a seller is not provenance."""
    if not specimen.chain_of_custody.documented:
        raise SpecimenError(
            f"refused: cannot assert {specimen.specimen_id!r} is natural "
            f"geological quartz without a documented chain of custody. A "
            f"purchase from a seller, and a 'natural' label, are not "
            f"provenance. Origin stays ORIGIN_UNVERIFIED until custody is "
            f"documented.")


def refuse_material_class_without_measurement(
        claimed: MaterialClass, measured: bool = False) -> None:
    """Refuse to confirm material class from a label alone.

    Distinguishing natural quartz from hydrothermal synthetic quartz (or
    from fused silica or non-quartz glass) requires measurement -- that is
    the entire study. A label, a seller's word, or an assumption cannot
    confirm the class.
    """
    if not measured:
        raise SpecimenError(
            f"refused: cannot confirm material class {claimed.value!r} from "
            f"a label alone. Distinguishing natural from synthetic quartz "
            f"requires measurement; that is the study, not an input to it. "
            f"Without measurement the class stays UNKNOWN.")


# --- integrity ---------------------------------------------------------

def _custody_fingerprint(chain: ChainOfCustody) -> str:
    return "\x1e".join(
        "\x1d".join((e.from_party, e.to_party, e.date, e.evidence))
        for e in chain.events)


def content_hash(specimen: Specimen) -> str:
    """Stable content hash over the schema (integrity, tamper-evidence).

    Deterministic for equal specimens and sensitive to any field change,
    including a change anywhere in the chain of custody.
    """
    parts = (
        specimen.specimen_id,
        specimen.material_class.value,
        specimen.verified_origin.value,
        specimen.locality,
        specimen.geological_context,
        specimen.estimated_age,
        specimen.seller,
        _custody_fingerprint(specimen.chain_of_custody),
        specimen.growth_method,
        specimen.seed_origin,
        specimen.handedness.value,
        specimen.twins,
        specimen.c_axis,
        specimen.x_axes,
        repr(specimen.cut_angles),
        repr(specimen.dimensions),
        repr(specimen.mass),
        repr(specimen.density),
        repr(specimen.inclusions),
        repr(specimen.fractures),
        repr(specimen.coatings),
        repr(specimen.treatments),
        specimen.irradiation,
        specimen.heat_history,
        repr(specimen.defect_proxies),
        repr(specimen.trace_elements),
        repr(specimen.optical),
        repr(specimen.electrical),
        repr(specimen.acoustic),
        repr(specimen.photos),
        repr(specimen.hashes),
        specimen.uncertainty,
        specimen.publication_class,
    )
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


# --- public projection: redact private locality and seller ------------

def public_view(specimen: Specimen) -> dict:
    """A privacy-safe projection. Never emits the private locality or the
    seller; emits structure, origin status, and the integrity hash.

    The custody chain is summarised (event count and evidence presence)
    rather than reproduced, since it can name private parties.
    """
    return {
        "specimen_id": specimen.specimen_id,
        "material_class": specimen.material_class.value,
        "origin_status": origin_status(specimen).value,
        "locality": REDACTED,
        "seller": REDACTED,
        "geological_context": specimen.geological_context,
        "growth_method": specimen.growth_method,
        "handedness": specimen.handedness.value,
        "custody_event_count": len(specimen.chain_of_custody),
        "custody_documented": specimen.chain_of_custody.documented,
        "publication_class": specimen.publication_class,
        "hash": content_hash(specimen),
        "endorsed": False,
    }


# --- report ------------------------------------------------------------

def specimen_report() -> dict:
    return {
        "what_this_is": (
            "a typed specimen ontology for the natural-vs-synthetic quartz "
            "study: it records provenance, tracks an append-only chain of "
            "custody, hashes for integrity, and redacts private locality "
            "and seller in any public view"),
        "material_classes": [m.value for m in MaterialClass],
        "handedness_values": [h.value for h in Handedness],
        "origin_statuses": [s.value for s in OriginStatus],
        "load_bearing_fields": ["verified_origin", "chain_of_custody"],
        "evidence_class": "DERIVED_MATHEMATICS",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "verdict": "SPECIMEN_ONTOLOGY_SOFTWARE_ONLY",
        "what_this_does_not_say": (
            "It does not confirm any specimen's material class -- natural "
            "versus synthetic quartz is decided by measurement, not by a "
            "label -- and it does not treat a seller's word as provenance. "
            "Origin is VERIFIED only with a documented chain of custody; "
            "otherwise it is ORIGIN_UNVERIFIED. No specimen is measured "
            "here."),
    }
