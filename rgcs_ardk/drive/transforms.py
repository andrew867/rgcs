"""Exact table transforms used as field-asymmetry controls."""

from __future__ import annotations

import cmath
import math
from typing import Any, Sequence

from rgcs_ardk.params import LOCKS


def table_weights(rows: Sequence[dict[str, Any]]) -> list[complex]:
    if len(rows) != LOCKS.sector_count:
        raise ValueError("expected 37 authority rows")
    return [
        cmath.rect(float(row["amplitude_weight"]), float(row["phase_offset_rad"]))
        for row in rows
    ]


def effective_asymmetry(weights: Sequence[complex]) -> complex:
    if len(weights) != LOCKS.sector_count:
        raise ValueError("expected 37 sector weights")
    return sum(
        weight * cmath.exp(1j * 2.0 * math.pi * index / LOCKS.sector_count)
        for index, weight in enumerate(weights)
    ) / LOCKS.sector_count


def rotate_weights(weights: Sequence[complex], cells: int) -> list[complex]:
    if len(weights) != LOCKS.sector_count:
        raise ValueError("expected 37 sector weights")
    shift = cells % LOCKS.sector_count
    values = list(weights)
    return values[-shift:] + values[:-shift] if shift else values


def mirror_weights(weights: Sequence[complex]) -> list[complex]:
    if len(weights) != LOCKS.sector_count:
        raise ValueError("expected 37 sector weights")
    return [complex(weights[(-index) % LOCKS.sector_count]).conjugate() for index in range(LOCKS.sector_count)]


def reverse_lag_weights(null_masks: dict[str, Any]) -> list[complex]:
    pairs = (null_masks.get("weight_tables") or {}).get("reversed_phase_lag")
    if not isinstance(pairs, list) or len(pairs) != LOCKS.sector_count:
        raise ValueError("reversed-lag authority table is missing")
    return [complex(float(pair[0]), float(pair[1])) for pair in pairs]


def angle_delta_deg(value: complex, reference: complex) -> float:
    return math.degrees(cmath.phase(value / reference)) % 360.0
