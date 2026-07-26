"""RCW P03 — machine-readable claim classes and the standing claims.

Every result object the workbench emits carries a claim class from
this registry and the standing claims block. The classes make the
difference between "the arithmetic is exact" and "this is physically
validated" machine-checkable, so no UI, API, doc or receipt can blur a
training equality into an independent validation by accident.
"""

from __future__ import annotations

from enum import Enum


class ClaimClass(str, Enum):
    """What kind of statement a value is allowed to be."""

    EXACT_STRUCTURAL = "EXACT_STRUCTURAL"
    #: arithmetic on the packet itself; bit-for-bit checkable

    TRAINING_EQUALITY = "TRAINING_EQUALITY"
    #: a supplied calibration pairing (e.g. 165876523 = Stonehenge);
    #: it trains profiles and can never validate them

    HOLDOUT = "HOLDOUT"
    #: reserved evaluation data, never used to fit anything

    DERIVED_CANDIDATE = "DERIVED_CANDIDATE"
    #: computed under named profiles; only as good as the profiles

    CONVENTIONAL_MODEL = "CONVENTIONAL_MODEL"
    #: established public physics/geodesy carried as a model input

    OPERATOR_CORRECTION = "OPERATOR_CORRECTION"
    #: a registered data correction with raw provenance retained

    SOURCE_CLAIM = "SOURCE_CLAIM"
    #: what a source reported; recorded, not endorsed

    UNDERDETERMINED = "UNDERDETERMINED"
    #: the declared profiles do not justify a unique answer

    BLOCKED_MISSING_DATA = "BLOCKED_MISSING_DATA"
    #: honest refusal: a required input does not exist here


#: The standing claims block (authority lock). Every trace embeds it.
STANDING_CLAIMS = {
    "SOURCE_ORIGIN_VALIDATED": "no",
    "STONEHENGE_INDEPENDENTLY_DECODED":
        "no, until the corrected transform passes",
    "OCTAL_PACKET_STRUCTURE_RECOVERED": "yes",
    "PHYSICAL_PROJECTION":
        "underdetermined unless a later receipt proves otherwise",
}

#: The sole active long-origin epoch reference (authority lock). Other
#: isotope roots are not reopened; conventional time scales remain
#: reproducibility metadata.
ACTIVE_LONG_ORIGIN_EPOCH_REFERENCE = "BA_130"


class ClaimBoundaryError(ValueError):
    """Raised when code tries to cross a claim boundary."""


def refuse_promotion(from_class: ClaimClass, to_class: ClaimClass) -> None:
    """Refuse promoting training/source/candidate material to validation.

    There is no validated class to promote into on purpose: validation
    would arrive as a new receipted result, not a relabel.
    """
    raise ClaimBoundaryError(
        f"refused: a {from_class.value} value cannot be relabelled "
        f"{to_class.value}. Validation is a new receipted result, "
        f"never a promotion of existing material.")


def trace_claims() -> dict:
    """The claims block embedded in every emitted trace."""
    return {
        "source_origin_validated": False,
        "stonehenge_independently_decoded": False,
        "octal_packet_structure_recovered": True,
        "physical_projection": "UNDERDETERMINED",
        "standing": dict(STANDING_CLAIMS),
    }
