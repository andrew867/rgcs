"""Reference control loop whose sole feedback variable is DeltaB."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

from rgcs_ardk.drive import AuthorityBundle
from rgcs_ardk.params import LOCKS
from rgcs_ardk.sense import FieldEstimate, SenseRingEstimator


class ControlRefused(RuntimeError):
    """Raised when a command would violate a control or safety lock."""


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _wrap_rad(value: float) -> float:
    return (value + math.pi) % (2.0 * math.pi) - math.pi


@dataclass
class PID:
    kp: float
    ki: float = 0.0
    kd: float = 0.0
    integral_limit: float = 1.0
    _integral: float = 0.0
    _previous: float | None = None

    def update(self, error: float, dt_s: float) -> float:
        if dt_s <= 0:
            raise ValueError("dt_s must be positive")
        self._integral = _clamp(
            self._integral + error * dt_s,
            -self.integral_limit,
            self.integral_limit,
        )
        derivative = 0.0 if self._previous is None else (error - self._previous) / dt_s
        self._previous = error
        return self.kp * error + self.ki * self._integral + self.kd * derivative


@dataclass(frozen=True)
class ControlCommand:
    delta_b: complex
    direction_error_rad: float
    magnitude_error: float
    modulation: float
    lag_rad: float
    active_amplitudes: tuple[float, ...]
    enabled: bool


class ReferenceControlLoop:
    """PID reference with hard clamps and authority-derived sector amplitudes."""

    def __init__(
        self,
        authority: AuthorityBundle,
        *,
        direction_pid: PID | None = None,
        magnitude_pid: PID | None = None,
        estimator: SenseRingEstimator | None = None,
    ) -> None:
        self._authority = authority
        self._direction_pid = direction_pid or PID(kp=0.05, integral_limit=math.pi)
        self._magnitude_pid = magnitude_pid or PID(kp=0.05, integral_limit=0.5)
        self._estimator = estimator or SenseRingEstimator()

    def step(
        self,
        *,
        command_angle_rad: float,
        command_magnitude: float,
        sector_samples: Sequence[complex],
        center_reference: complex = 0j,
        modulation: float = LOCKS.modulation,
        lag_rad: float = LOCKS.lag_rad,
        group_balance: Sequence[float] | None = None,
        thermal_derating: float = 1.0,
        dt_s: float = 1.0 / LOCKS.envelope_hz,
    ) -> ControlCommand:
        if command_magnitude < 0:
            raise ControlRefused("command magnitude must be nonnegative")
        if not 0.0 < thermal_derating <= 1.0:
            raise ControlRefused("thermal derating must be in (0, 1]")
        estimate: FieldEstimate = self._estimator.estimate(sector_samples, center_reference)
        direction_error = _wrap_rad(command_angle_rad - math.radians(estimate.direction_deg))
        magnitude_error = command_magnitude - estimate.magnitude
        next_lag = _clamp(
            lag_rad + self._direction_pid.update(direction_error, dt_s),
            -math.pi,
            math.pi,
        )
        next_modulation = _clamp(
            modulation + self._magnitude_pid.update(magnitude_error, dt_s),
            0.0,
            LOCKS.modulation,
        )
        balances = [1.0] * LOCKS.sector_count if group_balance is None else list(group_balance)
        if len(balances) != LOCKS.sector_count:
            raise ControlRefused("group balance must contain 37 values")
        if any(not 0.9 <= value <= 1.1 for value in balances):
            raise ControlRefused("group-balance values must remain within 0.9..1.1")
        amplitudes: list[float] = []
        for row, balance in zip(self._authority.rows, balances):
            if row["active_floor_status"] == "BLANKED":
                amplitudes.append(0.0)
                continue
            amplitude = float(row["amplitude_weight"]) * balance * thermal_derating
            if amplitude < LOCKS.active_floor:
                raise ControlRefused("derating would violate the active amplitude floor; disarm")
            amplitudes.append(amplitude)
        return ControlCommand(
            delta_b=estimate.delta_b,
            direction_error_rad=direction_error,
            magnitude_error=magnitude_error,
            modulation=next_modulation,
            lag_rad=next_lag,
            active_amplitudes=tuple(amplitudes),
            enabled=True,
        )
