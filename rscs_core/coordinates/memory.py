"""Memory coordinate: RSCS-C.14 memory-lattice coordinate (HYP, QUARANTINED).

Seeded from the Arisaka NHT/HAL proposal (EP-07-01/02, concept 13). This is a
Source-claim-derived HYPOTHESIS candidate ONLY. Per the notation ledger
policy 1.5 and the EXCLUSION_MATRIX, it carries NO physical weight: no
consciousness/brain/memory conclusion may be imported into any RGCS physical
claim. Agent 04 must attach an observable, an uncertainty, and a
pre-registered failure condition before this coordinate is used for anything
downstream. Constructing it requires an explicit acknowledgement flag so it
can never be instantiated by accident inside EST/DER code paths.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar

import numpy as np

from ._base import RSCSCoordinate, require_finite_array

__all__ = ["MemoryLattice"]


@dataclass(frozen=True)
class MemoryLattice(RSCSCoordinate):
    """RSCS-C.14. A candidate memory-lattice coordinate on a torus T^n.

    ``orientation_index`` names a lattice site; ``carrier_phase_rad`` is the
    phase stored at that site (space-to-phase encoding). CLASS = HYP.

    The ``acknowledge_hypothesis`` flag MUST be True: it forces any caller to
    state that they are entering the quarantined memory layer, so EST/DER code
    cannot silently depend on it (design principle 4 firewall)."""

    registry_id: ClassVar[str] = "RSCS-C.14"
    orientation_index: tuple[int, ...] = ()
    carrier_phase_rad: np.ndarray = ()  # type: ignore[assignment]
    acknowledge_hypothesis: bool = False

    def __post_init__(self) -> None:
        if self.acknowledge_hypothesis is not True:
            raise ValueError(
                "RSCS-C.14 is a QUARANTINED hypothesis coordinate (NHT/HAL); "
                "construct it only with acknowledge_hypothesis=True and only "
                "after attaching an observable + failure condition "
                "(notation ledger 1.5; EXCLUSION_MATRIX SRC-3-07)")
        idx = tuple(int(i) for i in self.orientation_index)
        object.__setattr__(self, "orientation_index", idx)
        phases = require_finite_array("carrier_phase_rad",
                                      self.carrier_phase_rad, ndim=1)
        if phases.size != len(idx):
            raise ValueError("carrier_phase_rad must match orientation_index")
        object.__setattr__(self, "carrier_phase_rad",
                           np.mod(phases, 2.0 * np.pi))

    @property
    def claim_class(self) -> str:
        return "HYP"

    def components(self) -> dict[str, Any]:
        return {"orientation_index": list(self.orientation_index),
                "carrier_phase_rad": self.carrier_phase_rad,
                "claim_class": "HYP"}
