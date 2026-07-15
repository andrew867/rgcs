"""Modal coordinates: RSCS-C.6 mode-index tuple and RSCS-C.7 modal state.

RSCS-C.6 ModeIndex: an integer tuple naming a mode (axial N, compact n,
parity family). The v2 indices are instances.

RSCS-C.7 ModalState: complex modal amplitudes psi in C^n, the occupancy /
analytic-signal state that generalizes v2 z(t) and the modal amplitudes of
RGCS-M.23-28/46. Amplitude |psi_n| and phase arg(psi_n) are carried together
and reported separately (the KOS-03 lesson, inherited from v2).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, Sequence

import numpy as np

from ._base import RSCSCoordinate, require_finite_array

__all__ = ["ModeIndex", "ModalState"]


@dataclass(frozen=True)
class ModeIndex(RSCSCoordinate):
    """RSCS-C.6. An integer index tuple naming a mode."""

    registry_id: ClassVar[str] = "RSCS-C.6"
    indices: tuple[int, ...] = ()
    labels: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        idx = tuple(int(i) for i in self.indices)
        object.__setattr__(self, "indices", idx)
        if self.labels and len(self.labels) != len(idx):
            raise ValueError("labels, if given, must match indices length")
        object.__setattr__(self, "labels", tuple(str(s) for s in self.labels))

    def components(self) -> dict[str, Any]:
        return {"indices": list(self.indices), "labels": list(self.labels)}


@dataclass(frozen=True)
class ModalState(RSCSCoordinate):
    """RSCS-C.7. Complex modal amplitudes psi in C^n.

    ``amplitudes`` is a 1-D complex array. Component fields keep the unit tag
    of the campaign observable X; amplitude and phase are exposed separately.
    """

    registry_id: ClassVar[str] = "RSCS-C.7"
    amplitudes: np.ndarray = ()  # type: ignore[assignment]

    def __post_init__(self) -> None:
        arr = require_finite_array("amplitudes", self.amplitudes,
                                   dtype=complex, ndim=1)
        if arr.size < 1:
            raise ValueError("amplitudes must be non-empty")
        object.__setattr__(self, "amplitudes", arr)

    @property
    def n_modes(self) -> int:
        return int(self.amplitudes.size)

    @property
    def amplitude(self) -> np.ndarray:
        return np.abs(self.amplitudes)

    @property
    def phase_rad(self) -> np.ndarray:
        return np.angle(self.amplitudes)

    @property
    def total_occupancy(self) -> float:
        """sum |psi_n|^2 (a conserved quantity under unitary operators)."""
        return float(np.sum(np.abs(self.amplitudes) ** 2))

    @classmethod
    def from_components(cls, values: Sequence[complex]) -> "ModalState":
        return cls(np.asarray(values, dtype=complex))

    def components(self) -> dict[str, Any]:
        return {"amplitudes": self.amplitudes, "amplitude": self.amplitude,
                "phase_rad": self.phase_rad,
                "total_occupancy": self.total_occupancy}
