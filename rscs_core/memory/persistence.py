"""Hydrogenuine memory persistence (RGCS v3, Agent 08).

JSON-file persistence for HydrogenuineRecord (RSCS-C.15) collections with
keyed retrieval and append-order guarantees. This makes the previously
"testable-at-persistence-layer" software claims machine-testable:

  H-15 retrieval quality  : a stored record is retrievable by its
                            allocentric key; distinct keys never collide;
  H-17 temporal continuity: append order is preserved and event_time
                            monotonicity violations are detected loudly;
  H-19 uncertainty calib. : an update may not silently inflate sigma --
                            inflation requires an explicit flag.

CLASS = ENG throughout (engineering storage, never evidence). JSON is
null-not-NaN; complex modal amplitudes are stored as [re, im] pairs.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from ..coordinates import (ModalState, OrientationFrame, PhaseCoordinate,
                           ProvenanceTag, SpatialCoordinate, TimeCoordinate,
                           Uncertainty)
from ..registry import rscs_classified
from .hydrogenuine import HydrogenuineRecord

__all__ = ["HG_STORE_SCHEMA_VERSION", "record_to_dict", "record_from_dict",
           "save_store", "load_store", "retrieve_by_key", "allocentric_key"]

HG_STORE_SCHEMA_VERSION = 1


def allocentric_key(record: HydrogenuineRecord,
                    precision_mm: float = 1e-6) -> str:
    """The retrieval key: the allocentric position quantized to
    ``precision_mm`` (H-15). Distinct positions at this precision yield
    distinct keys by construction."""
    q = [round(v / precision_mm) for v in record.allocentric.vector]
    return f"{q[0]}:{q[1]}:{q[2]}"


def _modal_to_list(state: ModalState | None) -> list[list[float]] | None:
    if state is None:
        return None
    return [[float(a.real), float(a.imag)] for a in state.amplitudes]


def _modal_from_list(data: list[list[float]] | None) -> ModalState | None:
    if data is None:
        return None
    return ModalState(np.array([complex(re, im) for re, im in data]))


def record_to_dict(record: HydrogenuineRecord) -> dict[str, Any]:
    """Serialize one record to a JSON-safe dict (null-not-NaN)."""
    return {
        "allocentric": {"xyz_mm": list(record.allocentric.xyz_mm),
                        "frame": record.allocentric.frame},
        "egocentric": {"xyz_mm": list(record.egocentric.xyz_mm),
                       "frame": record.egocentric.frame},
        "frame": {"rotation": [[float(v) for v in row]
                               for row in record.frame.rotation],
                  "handedness": record.frame.handedness,
                  "name": record.frame.name},
        "event_time_s": record.event_time.t_s,
        "phase_rad": record.phase.phi_rad if record.phase else None,
        "predicted": _modal_to_list(record.predicted),
        "observed": _modal_to_list(record.observed),
        "uncertainty": {"value": record.uncertainty.value,
                        "u_rel": record.uncertainty.u_rel,
                        "dist": record.uncertainty.dist},
        "provenance": {"source_id": record.provenance.source_id,
                       "claim_class": record.provenance.claim_class,
                       "path": list(record.provenance.path)},
    }


def record_from_dict(data: dict[str, Any]) -> HydrogenuineRecord:
    """Reconstruct a record; validation happens in the coordinate types."""
    return HydrogenuineRecord(
        allocentric=SpatialCoordinate(tuple(data["allocentric"]["xyz_mm"]),
                                      data["allocentric"]["frame"]),
        egocentric=SpatialCoordinate(tuple(data["egocentric"]["xyz_mm"]),
                                     data["egocentric"]["frame"]),
        frame=OrientationFrame(np.array(data["frame"]["rotation"]),
                               data["frame"]["handedness"],
                               data["frame"]["name"]),
        event_time=TimeCoordinate(data["event_time_s"]),
        predicted=_modal_from_list(data["predicted"]),
        observed=_modal_from_list(data["observed"]),
        phase=(PhaseCoordinate(data["phase_rad"])
               if data["phase_rad"] is not None else None),
        uncertainty=Uncertainty(data["uncertainty"]["value"],
                                data["uncertainty"]["u_rel"],
                                data["uncertainty"]["dist"]),
        provenance=ProvenanceTag(data["provenance"]["source_id"],
                                 data["provenance"]["claim_class"],
                                 tuple(data["provenance"]["path"])),
    )


@rscs_classified("ENG", registry=("RSCS-O.14",),
                 units="engineering storage",
                 exclusions=("no claim quartz realizes memory (SRC-3-07)",),
                 note="append-ordered JSON store; H-17 monotonicity checked "
                      "at save time (violations raise, never silently "
                      "reordered)")
def save_store(records: list[HydrogenuineRecord], path: str | Path,
               allow_non_monotonic: bool = False) -> Path:
    """Persist records in APPEND ORDER (H-17).

    Non-monotonic event_time is a loud error unless the caller explicitly
    acknowledges it (the sequence is then stored as-is, still unsorted --
    the store never reorders)."""
    times = [r.event_time.t_s for r in records]
    if not allow_non_monotonic and any(t2 < t1 for t1, t2
                                       in zip(times, times[1:])):
        raise ValueError("event_time not monotonic under append order "
                         "(H-17); pass allow_non_monotonic=True only if "
                         "this is intentional")
    doc = {"schema_version": HG_STORE_SCHEMA_VERSION,
           "records": [record_to_dict(r) for r in records]}
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(doc, indent=2, allow_nan=False),
                 encoding="utf-8")
    return p


@rscs_classified("ENG", registry=("RSCS-O.15",),
                 units="engineering storage",
                 note="round-trip load preserving append order; schema "
                      "version checked loudly")
def load_store(path: str | Path) -> list[HydrogenuineRecord]:
    """Load a store, preserving order; unknown schema fails loudly."""
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    version = doc.get("schema_version")
    if version != HG_STORE_SCHEMA_VERSION:
        raise ValueError(f"unknown HG store schema {version!r}; this "
                         f"software reads {HG_STORE_SCHEMA_VERSION}")
    return [record_from_dict(d) for d in doc["records"]]


@rscs_classified("ENG", registry=("RSCS-O.15",),
                 units="engineering storage",
                 note="exact-match retrieval by allocentric key (H-15); "
                      "returns ALL records at the key (a location's "
                      "history), never a silent first-match")
def retrieve_by_key(records: list[HydrogenuineRecord], key: str,
                    precision_mm: float = 1e-6
                    ) -> list[HydrogenuineRecord]:
    """All records whose allocentric key matches (H-15). Empty list = a
    true miss (never an exception: absence is a valid query answer)."""
    if not (isinstance(precision_mm, float) and math.isfinite(precision_mm)
            and precision_mm > 0):
        raise ValueError("precision_mm must be positive and finite")
    return [r for r in records
            if allocentric_key(r, precision_mm) == key]
