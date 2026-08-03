"""First-spatial-harmonic estimators for the stationary pickup rings."""

from __future__ import annotations

import cmath
from dataclasses import dataclass
import math
from typing import Sequence

from rgcs_ardk.params import LOCKS


@dataclass(frozen=True)
class FieldEstimate:
    delta_b: complex
    magnitude: float
    direction_deg: float
    common_mode: complex
    sample_count: int


def _estimate(samples: Sequence[complex], expected: int, center_reference: complex) -> FieldEstimate:
    if len(samples) != expected:
        raise ValueError(f"expected {expected} complex samples")
    corrected = [complex(sample) - center_reference for sample in samples]
    common_mode = sum(corrected) / expected
    delta_b = sum(
        (sample - common_mode) * cmath.exp(1j * 2.0 * math.pi * index / expected)
        for index, sample in enumerate(corrected)
    ) / expected
    return FieldEstimate(
        delta_b=delta_b,
        magnitude=abs(delta_b),
        direction_deg=math.degrees(cmath.phase(delta_b)) % 360.0,
        common_mode=common_mode,
        sample_count=expected,
    )


def estimate_delta_b(
    sector_samples: Sequence[complex], center_reference: complex = 0j
) -> FieldEstimate:
    return _estimate(sector_samples, LOCKS.sector_count, center_reference)


def estimate_compass(
    compass_samples: Sequence[complex], center_reference: complex = 0j
) -> FieldEstimate:
    return _estimate(compass_samples, 8, center_reference)


class SenseRingEstimator:
    """Applies complex gain calibration before estimating the first harmonic."""

    def __init__(self, calibration: Sequence[complex] | None = None) -> None:
        gains = [1 + 0j] * LOCKS.sector_count if calibration is None else list(calibration)
        if len(gains) != LOCKS.sector_count:
            raise ValueError("expected 37 complex calibration gains")
        if any(abs(gain) == 0 for gain in gains):
            raise ValueError("calibration gains must be nonzero")
        self._gains = tuple(complex(gain) for gain in gains)

    def estimate(
        self, sector_samples: Sequence[complex], center_reference: complex = 0j
    ) -> FieldEstimate:
        if len(sector_samples) != LOCKS.sector_count:
            raise ValueError("expected 37 complex samples")
        calibrated = [sample / gain for sample, gain in zip(sector_samples, self._gains)]
        return estimate_delta_b(calibrated, center_reference)
