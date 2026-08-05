"""Frozen rgcs-terra RC4 reference for the public workbench cage.

Terra RC4 is a released, verified, external dependency. The workbench
references it read-only as an operational calibrated coordinate
profile. This module is the only place the workbench states Terra
metadata, and it refuses -- by raising, not by warning -- any attempt
to promote the profile to a validated physical endpoint.

This module does frozen metadata and refusal. It does not claim
physical endpoint validation. Independent physical endpoint
validation remains HOLDOUT_REQUIRED.
"""

from __future__ import annotations

from types import MappingProxyType

TERRA_RC4_REPO = "andrew867/rgcs-terra"
TERRA_RC4_TAG = "v1.0.0-rc4"
TERRA_RC4_COMMIT = "4fdee3e7fbdb416d8e4b32dcb422d0977e6f20af"
TERRA_RC4_VERDICT = "GREEN_TERRA_ALIGNMENT_SOLVED_CALIBRATED_V1"

#: Blocker split, exactly as published at RC4. B-numbers are Terra's.
TERRA_RC4_BLOCKERS = MappingProxyType({
    "B01A": "CLOSED",
    "B02A": "CLOSED",
    "B01B": "VALIDATION_PENDING",
    "B02B": "PHYSICAL_VALIDATION_PENDING",
    "B10": "OPEN",
})

#: The one public claim the adapter may make about Terra.
ALLOWED_PUBLIC_CLAIM = (
    "RGCS Terra V1 is done-for-now as an operational calibrated "
    "coordinate workbench. Independent physical endpoint validation "
    "remains HOLDOUT_REQUIRED."
)

PHYSICAL_ENDPOINT_VALIDATED = False
MANUAL_MAP_VERIFICATION = False

#: Evidence kinds the adapter refuses as physical validation.
REFUSED_EVIDENCE_KINDS = ("map_screenshot", "manual_map_verification",
                          "visual_map_match", "source_language")


class PhysicalValidationRefused(RuntimeError):
    """Raised on any attempt to advance a physical claim through Terra."""


def frozen_profile() -> dict:
    """A mutable COPY of the frozen metadata; the module stays frozen."""
    return {
        "repo": TERRA_RC4_REPO,
        "tag": TERRA_RC4_TAG,
        "commit": TERRA_RC4_COMMIT,
        "verdict": TERRA_RC4_VERDICT,
        "blockers": dict(TERRA_RC4_BLOCKERS),
        "status": "OPERATIONAL_CALIBRATED_PROFILE",
        "physical_endpoint_validated": PHYSICAL_ENDPOINT_VALIDATED,
        "holdout": "HOLDOUT_REQUIRED",
    }


def promote_physical_validation(*_args, **_kwargs):
    """The refusal is the feature. There is no code path that flips
    physical validation to true inside the workbench."""
    raise PhysicalValidationRefused(
        "Terra RC4 is an operational calibrated profile. Physical "
        "endpoint validation is HOLDOUT_REQUIRED and cannot be set "
        "from workbench code.")


def accept_validation_evidence(kind: str) -> dict:
    """Only bench-grade evidence kinds may even enter review."""
    if kind in REFUSED_EVIDENCE_KINDS:
        raise PhysicalValidationRefused(
            f"evidence kind '{kind}' is refused as physical validation; "
            f"a map screenshot or source language is not a receipt")
    return {"kind": kind, "status": "REVIEW_ONLY",
            "physical_endpoint_validated": False,
            "note": "review does not advance a physical claim"}


__all__ = ["TERRA_RC4_REPO", "TERRA_RC4_TAG", "TERRA_RC4_COMMIT",
           "TERRA_RC4_VERDICT", "TERRA_RC4_BLOCKERS",
           "ALLOWED_PUBLIC_CLAIM", "PHYSICAL_ENDPOINT_VALIDATED",
           "MANUAL_MAP_VERIFICATION", "REFUSED_EVIDENCE_KINDS",
           "PhysicalValidationRefused", "frozen_profile",
           "promote_physical_validation", "accept_validation_evidence"]
