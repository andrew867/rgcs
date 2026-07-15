"""Metadata coordinates: RSCS-C.12 uncertainty descriptor and
RSCS-C.13 provenance tag.

C.12 wraps the v2 ``UncertainValue`` (RGCS-M.10) so RSCS uncertainty is the
SAME object the frozen core uses -- the Conservative Extension Property for
uncertainty propagation is then exact by construction. C.13 is the
provenance/receipt coordinate that travels with any state: source id, claim
class, and an optional process/fabrication path (EP-03-01).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, ClassVar

from rgcs_core.uncertainty import UncertainValue

from ..registry import VALID_CLASSES
from ._base import RSCSCoordinate, require_finite

__all__ = ["Uncertainty", "ProvenanceTag"]


@dataclass(frozen=True)
class Uncertainty(RSCSCoordinate):
    """RSCS-C.12. An uncertain scalar: (value, relative 1-sigma, dist type).

    Backed by the frozen v2 ``UncertainValue`` so propagation matches v2
    exactly (RSCS-O.11). ``dist`` names the distribution family (default
    'normal') for downstream propagation choices."""

    registry_id: ClassVar[str] = "RSCS-C.12"
    value: float = 0.0
    u_rel: float = 0.0
    dist: str = "normal"

    def __post_init__(self) -> None:
        require_finite("value", self.value)
        # Delegate range validation to the frozen v2 dataclass.
        UncertainValue(self.value, self.u_rel)
        if not isinstance(self.dist, str) or not self.dist:
            raise ValueError("dist must be a non-empty string")

    @property
    def uncertain_value(self) -> UncertainValue:
        return UncertainValue(self.value, self.u_rel)

    @property
    def sigma(self) -> float:
        return self.uncertain_value.sigma

    def components(self) -> dict[str, Any]:
        return {"value": self.value, "u_rel": self.u_rel, "sigma": self.sigma,
                "dist": self.dist}


@dataclass(frozen=True)
class ProvenanceTag(RSCSCoordinate):
    """RSCS-C.13. A provenance/receipt coordinate carried with a state.

    ``source_id`` is a SRC-3-*/EP-* id or an internal origin; ``claim_class``
    is one of EST/DER/HYP/SRC/ENG; ``path`` is an optional ordered process/
    fabrication history (e.g. the spiral-helix write path, EP-03-01)."""

    registry_id: ClassVar[str] = "RSCS-C.13"
    source_id: str = "internal"
    claim_class: str = "DER"
    path: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, str) or not self.source_id:
            raise ValueError("source_id must be a non-empty string")
        if self.claim_class not in VALID_CLASSES:
            raise ValueError(f"claim_class must be one of {VALID_CLASSES}")
        object.__setattr__(self, "path", tuple(str(p) for p in self.path))

    def extend_path(self, step: str) -> "ProvenanceTag":
        """Return a new tag with ``step`` appended to the process path."""
        return ProvenanceTag(self.source_id, self.claim_class,
                             (*self.path, str(step)))

    def components(self) -> dict[str, Any]:
        return {"source_id": self.source_id, "claim_class": self.claim_class,
                "path": list(self.path)}
