"""RSCS-O.13 memory-lattice store/recall operator (HYP, QUARANTINED).

Store/recall on the RSCS-C.14 MemoryLattice, seeded from the Arisaka NHT/HAL
proposal (EP-07-02). CLASS = HYP. Carries NO physical claim: this is a
candidate mechanism only. Every entry point requires acknowledge_hypothesis
so EST/DER code cannot depend on it by accident, and Agent 04 must supply an
observable + pre-registered failure condition before any downstream use
(notation ledger 1.5; EXCLUSION_MATRIX SRC-3-07). Provided here so Agent 04
has a stable, typed API surface -- not a working memory model.
"""

from __future__ import annotations

import numpy as np

from ..coordinates import MemoryLattice, ModalState
from ..registry import rscs_classified

from .hydrogenuine import (HydrogenuineRecord, store as hg_store,
                           replay as hg_replay, update as hg_update)

__all__ = ["store", "recall", "HydrogenuineRecord", "hg_store", "hg_replay",
           "hg_update"]


@rscs_classified("HYP", registry=("RSCS-O.13",), provenance=("EP-07-02",),
                 units="candidate (rad phases on a torus)",
                 exclusions=("NHT/HAL: no consciousness/brain/memory import "
                             "into RGCS physics (SRC-3-07)",),
                 note="candidate store: writes modal phases to lattice sites; "
                      "HYP only, requires observable + failure condition")
def store(state: ModalState, orientation_index: tuple[int, ...],
          acknowledge_hypothesis: bool = False) -> MemoryLattice:
    """Candidate store: encode the phases of a ModalState onto lattice sites.

    QUARANTINED. Requires acknowledge_hypothesis=True. Makes no physical
    claim; Agent 04 owns the observable and failure condition."""
    if state.n_modes != len(orientation_index):
        raise ValueError("orientation_index must match the number of modes")
    return MemoryLattice(orientation_index, state.phase_rad,
                         acknowledge_hypothesis=acknowledge_hypothesis)


@rscs_classified("HYP", registry=("RSCS-O.13",), provenance=("EP-07-01",),
                 units="candidate (rad)",
                 exclusions=("NHT/HAL: no consciousness/brain/memory import "
                             "into RGCS physics (SRC-3-07)",),
                 note="candidate recall: read stored carrier phases; HYP only")
def recall(lattice: MemoryLattice) -> np.ndarray:
    """Candidate recall: return the stored carrier phases (rad). QUARANTINED."""
    if not isinstance(lattice, MemoryLattice):
        raise TypeError("lattice must be a MemoryLattice (RSCS-C.14)")
    return np.asarray(lattice.carrier_phase_rad, dtype=float)
