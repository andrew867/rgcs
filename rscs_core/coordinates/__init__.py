"""RSCS typed coordinates (RSCS-C.1 .. RSCS-C.14).

Immutable, unit-tagged coordinate records on declared manifolds. Import the
concrete types from here; each maps to exactly one RSCS-C.* registry row.
"""

from __future__ import annotations

from ._base import RSCSCoordinate, require_finite, require_finite_array
from .space import SpatialCoordinate, OrientationFrame
from .spectral import (TimeCoordinate, PhaseCoordinate, AngularFrequency,
                       Wavevector)
from .modal import ModeIndex, ModalState
from .medium import PolarizationState, SelectionCoordinate, GroupDelay
from .meta import Uncertainty, ProvenanceTag
from .memory import MemoryLattice
# RSCS-C.15 HydrogenuineRecord lives in rscs_core.memory (the memory
# application) to avoid a coordinates<->memory import cycle; import it from
# `rscs_core.memory`, not from here.

#: Map RSCS-C.* id -> coordinate class, for registry cross-checks.
COORDINATE_TYPES = {
    "RSCS-C.1": SpatialCoordinate,
    "RSCS-C.2": TimeCoordinate,
    "RSCS-C.3": PhaseCoordinate,
    "RSCS-C.4": AngularFrequency,
    "RSCS-C.5": Wavevector,
    "RSCS-C.6": ModeIndex,
    "RSCS-C.7": ModalState,
    "RSCS-C.8": OrientationFrame,
    "RSCS-C.9": PolarizationState,
    "RSCS-C.10": SelectionCoordinate,
    "RSCS-C.11": GroupDelay,
    "RSCS-C.12": Uncertainty,
    "RSCS-C.13": ProvenanceTag,
    "RSCS-C.14": MemoryLattice,
}

__all__ = [
    "RSCSCoordinate", "require_finite", "require_finite_array",
    "SpatialCoordinate", "OrientationFrame", "TimeCoordinate",
    "PhaseCoordinate", "AngularFrequency", "Wavevector", "ModeIndex",
    "ModalState", "PolarizationState", "SelectionCoordinate", "GroupDelay",
    "Uncertainty", "ProvenanceTag", "MemoryLattice", "COORDINATE_TYPES",
]
