"""P03 — the natural-geological-quartz source requirement, translated.

The private source hypothesis is that naturally grown Earth quartz may be
*required* — that its geological and environmental growth history is part
of the intended function, described in the source's own terms as a small
part of Earth's global heart. That interpretation is Tier-A private
material and stays private.

This module is the **public translation**, and the translation is the
whole discipline: a source requirement is not a materials-science
finding. Publicly, "natural quartz may be required" becomes exactly one
thing — *geological growth history is an independent experimental
variable* — to be tested against controls (hydrothermal synthetic
alpha-quartz, fused silica, nonquartz glass, multiple localities), on
ordinary endpoints, blinded. Nothing about consciousness, absorption, or
a global heart is published as established science, and
:func:`refuse_publish_consciousness_as_materials_science` enforces that.

Two records are kept distinct and never collapsed:

* the **source requirement** — "the source says natural quartz is
  required" — an attributed claim, evidence status `SOURCE_REQUIREMENT`;
* the **experimental variable** — "geological growth history is an
  independent variable" — a design statement, evidence status
  `EXPERIMENTAL_VARIABLE`.

The requirement is `SOURCE_REQUIRED_EXPERIMENTALLY_UNRESOLVED`: the source
requires it, and no experiment here resolves whether it matters. Synthetic
quartz is not a rival to be dismissed; it is a **mandatory control**.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class NaturalSourceError(RuntimeError):
    """Raised when the private interpretation leaks into a public claim."""


class Lane(Enum):
    """The experimental lanes. Natural is primary; the rest are controls."""

    NATURAL_GEOLOGICAL_QUARTZ = "natural_geological_quartz"        # primary
    HYDROTHERMAL_SYNTHETIC_QUARTZ = "hydrothermal_synthetic_quartz"  # control
    FUSED_SILICA = "fused_silica"                                  # control
    NONQUARTZ_GLASS = "nonquartz_glass"                            # control


#: Control lanes are mandatory: the natural-primary lane is untestable
#: without them, and dropping a control is how a null becomes a false
#: positive.
CONTROL_LANES = (
    Lane.HYDROTHERMAL_SYNTHETIC_QUARTZ,
    Lane.FUSED_SILICA,
    Lane.NONQUARTZ_GLASS,
)

#: Ordinary differentiators to measure before any exotic reading. If a
#: natural/synthetic difference ever appears, these explain it first.
ORDINARY_DIFFERENTIATORS = (
    "trace_elements", "inclusions", "dislocations", "twinning",
    "growth_sectors", "radiation_color_centres", "hydroxyl_water",
    "internal_stress", "acoustic_Q", "dielectric_loss", "absorption",
    "scattering", "piezoelectric_orientation",
)


@dataclass(frozen=True)
class SourceRequirement:
    """The attributed private requirement and its public translation.

    ``private_interpretation`` is PRIVATE_ONLY and must never be emitted
    publicly; only the public translation and the experimental framing are
    shareable.
    """

    requirement_id: str
    public_translation: str = (
        "geological growth history is an independent experimental variable")
    private_interpretation: str = ""            # PRIVATE_ONLY, never emitted
    evidence_status: str = "SOURCE_REQUIREMENT"
    publication_class: str = "PRIVATE_ONLY"

    def public_view(self) -> dict:
        """Emits only the public translation and framing — never the
        private interpretation."""
        return {
            "requirement_id": self.requirement_id,
            "public_translation": self.public_translation,
            "experimental_variable": "geological_growth_history",
            "primary_lane": Lane.NATURAL_GEOLOGICAL_QUARTZ.value,
            "mandatory_controls": [l.value for l in CONTROL_LANES],
            "evidence_status": "SOURCE_REQUIRED_EXPERIMENTALLY_UNRESOLVED",
            "endorsed_as_materials_science": False,
        }


def design_lanes() -> dict:
    """The primary lane plus mandatory controls."""
    return {
        "primary": Lane.NATURAL_GEOLOGICAL_QUARTZ.value,
        "controls": [l.value for l in CONTROL_LANES],
        "ordinary_differentiators": list(ORDINARY_DIFFERENTIATORS),
        "verdict": "SOURCE_REQUIRED_EXPERIMENTALLY_UNRESOLVED",
    }


def refuse_publish_consciousness_as_materials_science(*_args, **_kwargs) -> None:
    """Refuse publishing the private interpretation as established science."""
    raise NaturalSourceError(
        "refused: the source's consciousness/global-heart interpretation is "
        "private Tier-A material and is NOT published as established materials "
        "science. Publicly, natural quartz is source-required but "
        "experimentally unresolved, and geological growth history is only an "
        "independent variable to be tested against controls.")


def refuse_drop_synthetic_control(lane: Lane) -> None:
    """Refuse to run the natural-primary lane without synthetic controls."""
    if lane in CONTROL_LANES:
        raise NaturalSourceError(
            f"refused: {lane.value} is a MANDATORY control, not an optional "
            f"comparison. The natural-primary lane is untestable without the "
            f"synthetic/fused-silica/glass controls; dropping one turns a "
            f"null into a false positive.")


def refuse_natural_superiority_claim(*_args, **_kwargs) -> None:
    """Refuse claiming natural quartz is 'better' absent a measured, matched
    result explained past ordinary differentiators."""
    raise NaturalSourceError(
        "refused: no claim that natural quartz is superior or special. Any "
        "measured difference is attributed to ordinary differentiators "
        "(trace elements, inclusions, water, defects) first, and none has "
        "been measured here.")


def naturalsource_report() -> dict:
    return {
        "what_this_is": (
            "the public translation of a private source requirement: "
            "geological growth history as an independent experimental "
            "variable, with synthetic quartz as a mandatory control"),
        "primary_lane": Lane.NATURAL_GEOLOGICAL_QUARTZ.value,
        "mandatory_controls": [l.value for l in CONTROL_LANES],
        "ordinary_differentiators": list(ORDINARY_DIFFERENTIATORS),
        "evidence_class": "SOURCE_REQUIREMENT translated to EXPERIMENTAL_VARIABLE",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "verdict": "SOURCE_REQUIRED_EXPERIMENTALLY_UNRESOLVED",
        "what_this_does_not_say": (
            "It does not say natural quartz stores consciousness, is a global "
            "heart, or is materially superior. It does not publish the "
            "private interpretation. It says the source requires natural "
            "quartz, that this is unresolved experimentally, and that "
            "synthetic quartz is a mandatory control."),
    }
