from __future__ import annotations

import cmath
import math

import pytest

from rgcs_ardk.drive import load_authority
from rgcs_ardk.firmware import (
    ControlRefused,
    Frame,
    Operation,
    ReferenceControlLoop,
    ReferenceRuntime,
    RuntimeRefused,
    decode_frame,
    encode_frame,
)
from rgcs_ardk.params import LOCKS
from rgcs_ardk.sense import estimate_compass, estimate_delta_b


def _spatial_samples(value: complex, count: int, common: complex = 0j) -> list[complex]:
    return [
        common + value * cmath.exp(-1j * 2.0 * math.pi * index / count)
        for index in range(count)
    ]


def test_sector_estimator_recovers_complex_delta_b_and_removes_common_mode():
    target = cmath.rect(0.3, math.radians(27.0))
    estimate = estimate_delta_b(_spatial_samples(target, 37, 2.0 + 0.5j))
    assert estimate.delta_b == pytest.approx(target, abs=1e-12)
    assert estimate.magnitude == pytest.approx(0.3, abs=1e-12)
    assert estimate.direction_deg == pytest.approx(27.0, abs=1e-12)
    assert estimate.sample_count == 37


def test_compass_estimator_requires_eight_pickups():
    target = cmath.rect(0.2, math.radians(315.0))
    assert estimate_compass(_spatial_samples(target, 8)).direction_deg == pytest.approx(315.0)
    with pytest.raises(ValueError, match="expected 8"):
        estimate_compass([0j] * 7)


def test_control_loop_clamps_mod_and_lag_and_preserves_floor():
    loop = ReferenceControlLoop(load_authority())
    command = loop.step(
        command_angle_rad=math.pi,
        command_magnitude=10.0,
        sector_samples=_spatial_samples(0.1 + 0j, 37),
        modulation=10.0,
        lag_rad=10.0,
    )
    assert 0.0 <= command.modulation <= 0.5
    assert -math.pi <= command.lag_rad <= math.pi
    active = [value for value in command.active_amplitudes if value > 0]
    assert len(active) == 33
    assert min(active) >= 0.5


def test_unsafe_derating_disarms_by_refusal_instead_of_lowering_floor():
    loop = ReferenceControlLoop(load_authority())
    with pytest.raises(ControlRefused, match="active amplitude floor"):
        loop.step(
            command_angle_rad=0.0,
            command_magnitude=0.1,
            sector_samples=_spatial_samples(0.1 + 0j, 37),
            thermal_derating=0.8,
        )


def test_runtime_is_default_off_hash_gated_and_heartbeat_gated():
    runtime = ReferenceRuntime(load_authority())
    assert runtime.enabled is False
    with pytest.raises(RuntimeRefused, match="hash"):
        runtime.arm(
            supplied_config_hash="bad",
            now_s=0.0,
            enclosure_closed=True,
            sensors_valid=True,
            hardware_limit_present=True,
        )
    runtime.arm(
        supplied_config_hash=runtime.config_hash,
        now_s=0.0,
        enclosure_closed=True,
        sensors_valid=True,
        hardware_limit_present=True,
    )
    assert runtime.enabled is True
    runtime.tick(now_s=runtime.heartbeat_timeout_s + 0.01)
    assert runtime.enabled is False
    assert "HEARTBEAT_TIMEOUT" in runtime.fault_flags


def test_spi_reference_frame_round_trip_and_checksum_refusal():
    frame = Frame(Operation.WRITE_REG, 0x20, b"abcd")
    encoded = encode_frame(frame)
    assert decode_frame(encoded) == frame
    corrupted = encoded[:-1] + bytes([encoded[-1] ^ 0x01])
    with pytest.raises(ValueError, match="checksum"):
        decode_frame(corrupted)


def test_frequency_locks_are_exact():
    assert LOCKS.carrier_hz == LOCKS.envelope_hz * 411
