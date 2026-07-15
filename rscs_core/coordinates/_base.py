"""Base class and validation helpers for RSCS typed coordinates.

Every RSCS coordinate is an immutable (frozen) dataclass carrying named,
unit-tagged components on a declared manifold (docs/RSCS_NOTATION_LEDGER.md
policy 2: typed coordinates, never bare vectors). The base class provides
finiteness/shape validation, deterministic JSON serialization, and a
``registry_id`` hook so a coordinate can be traced back to its RSCS-C.* row.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, ClassVar, Sequence

import numpy as np

__all__ = ["RSCSCoordinate", "require_finite", "require_finite_array"]


def require_finite(name: str, value: float) -> float:
    """Return ``value`` as a float or raise if it is NaN/inf/non-numeric."""
    if not (isinstance(value, (int, float)) and math.isfinite(float(value))):
        raise ValueError(f"{name} must be a finite real number; got {value!r}")
    return float(value)


def require_finite_array(name: str, value: Any, *, dtype: Any = float,
                         ndim: int | None = None,
                         shape: tuple[int, ...] | None = None) -> np.ndarray:
    """Coerce to a finite numpy array of the given dtype/shape or raise."""
    arr = np.asarray(value, dtype=dtype)
    if ndim is not None and arr.ndim != ndim:
        raise ValueError(f"{name} must be {ndim}-D; got {arr.ndim}-D")
    if shape is not None and arr.shape != shape:
        raise ValueError(f"{name} must have shape {shape}; got {arr.shape}")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} contains non-finite values (NaN/inf)")
    return arr


@dataclass(frozen=True)
class RSCSCoordinate:
    """Base for all RSCS-C.* typed coordinate records.

    Subclasses set the ``registry_id`` class var (e.g. ``"RSCS-C.1"``) and
    implement :meth:`components` returning an ordered, unit-tagged mapping for
    deterministic serialization. Instances are immutable; equality and
    serialization are structural.
    """

    registry_id: ClassVar[str] = ""

    def components(self) -> dict[str, Any]:
        """Ordered mapping of component name -> value (override)."""
        raise NotImplementedError

    def to_dict(self) -> dict[str, Any]:
        """Deterministic, JSON-ready dict including the registry id."""
        out: dict[str, Any] = {"rscs_id": self.registry_id}
        for key, val in self.components().items():
            if isinstance(val, np.ndarray):
                out[key] = val.tolist()
            elif isinstance(val, complex):
                out[key] = {"re": val.real, "im": val.imag}
            else:
                out[key] = val
        return out

    @staticmethod
    def _seq(name: str, value: Sequence[float], n: int) -> tuple[float, ...]:
        arr = require_finite_array(name, value, ndim=1, shape=(n,))
        return tuple(float(v) for v in arr)
