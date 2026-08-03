from __future__ import annotations

import copy

import pytest

from rgcs_ardk.bench import REQUIRED_CONTROLS


@pytest.fixture
def complete_result() -> dict:
    return {
        "primary_observable": "DeltaB",
        "uncertainty": {"angular_deg": 1.0, "amplitude_norm": 0.02},
        "controls": {name: True for name in REQUIRED_CONTROLS},
        "raw_data_hashes": ["a" * 64],
        "instrument_calibration_ids": ["CAL-001"],
        "angle_tracks": True,
        "magnitude_beats_nulls": True,
        "transforms_pass": True,
        "artifacts_bounded": True,
        "claim_language": "CONTROLLED_FIELD_ASYMMETRY_OBSERVED_WITHIN_THIS_BUDGET",
    }


@pytest.fixture
def result_copy(complete_result):
    def factory() -> dict:
        return copy.deepcopy(complete_result)

    return factory
