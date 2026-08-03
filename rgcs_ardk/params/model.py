"""Typed access to the locked RevA geometry and control parameters."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import json
import math
from pathlib import Path
from typing import Any

import yaml


class ParameterLockError(ValueError):
    """Raised when a parameter file contradicts an R10.74 design lock."""


@dataclass(frozen=True)
class LockedParameters:
    sector_count: int = 37
    active_count: int = 33
    run_count: int = 35
    active_floor: float = 0.5
    winner_min_active_amplitude: float = 0.544
    modulation: float = 0.5
    lag_rad: float = math.pi
    d_eff_magnitude: float = 0.4124
    direction_offset_deg: float = 12.46
    carrier_hz: int = 1_683_456
    envelope_hz: int = 4_096
    outer_diameter_mm: float = 288.0
    inner_diameter_mm: float = 188.0
    outer_radius_mm: float = 144.0
    inner_radius_mm: float = 94.0
    mean_radius_mm: float = 119.0
    publication_hold: bool = True

    @property
    def sector_pitch_deg(self) -> Fraction:
        return Fraction(360, self.sector_count)

    @property
    def inner_outer_ratio(self) -> Fraction:
        return Fraction(int(self.inner_diameter_mm), int(self.outer_diameter_mm))

    def validate(self) -> None:
        expected = LockedParameters()
        exact_fields = (
            "sector_count",
            "active_count",
            "run_count",
            "carrier_hz",
            "envelope_hz",
            "outer_diameter_mm",
            "inner_diameter_mm",
            "outer_radius_mm",
            "inner_radius_mm",
            "mean_radius_mm",
        )
        for name in exact_fields:
            if getattr(self, name) != getattr(expected, name):
                raise ParameterLockError(f"locked parameter changed: {name}")
        if self.active_floor < 0.5:
            raise ParameterLockError("active amplitude floor must be at least 0.5")
        if self.modulation != 0.5 or not math.isclose(self.lag_rad, math.pi):
            raise ParameterLockError("constrained recipe must remain mod=0.5, lag=pi")
        if not math.isclose(self.d_eff_magnitude, 0.4124, abs_tol=1e-12):
            raise ParameterLockError("locked d_eff magnitude changed")
        if not math.isclose(self.direction_offset_deg, 12.46, abs_tol=1e-12):
            raise ParameterLockError("locked direction offset changed")
        if self.inner_outer_ratio != Fraction(47, 72):
            raise ParameterLockError("ID/OD ratio must equal 47/72")
        if not self.publication_hold:
            raise ParameterLockError("PUBLICATION_HOLD must remain true")


LOCKS = LockedParameters()


def _data_path(name: str) -> Path:
    return Path(__file__).with_name(name)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_locked_parameters() -> LockedParameters:
    """Load the checked-in files and refuse any disagreement with the locks."""
    constants = _load_json(_data_path("constants_revA.json"))
    desktop = _load_yaml(_data_path("desktop_288mm_revA.yaml"))
    geometry = desktop["geometry"]
    recipe = desktop["r1073_recipe"]
    frequencies = desktop["frequencies"]
    params = LockedParameters(
        sector_count=constants["N_sectors"],
        active_count=constants["active_count_steering"],
        run_count=constants["run_count"],
        active_floor=recipe["active_floor"],
        winner_min_active_amplitude=recipe["winner_min_active_amplitude"],
        modulation=recipe["modulation"],
        lag_rad=recipe["lag_rad"],
        d_eff_magnitude=recipe["d_eff_magnitude"],
        direction_offset_deg=recipe["direction_offset_deg"],
        carrier_hz=frequencies["carrier_hz"],
        envelope_hz=frequencies["envelope_reference_hz"],
        outer_diameter_mm=geometry["outer_diameter"],
        inner_diameter_mm=geometry["inner_diameter"],
        outer_radius_mm=geometry["outer_radius"],
        inner_radius_mm=geometry["inner_radius"],
        mean_radius_mm=geometry["mean_radius"],
        publication_hold=desktop["status"] == "PUBLICATION_HOLD",
    )
    params.validate()
    if Fraction(geometry["inner_outer_ratio_exact"]) != Fraction(47, 72):
        raise ParameterLockError("parameter file ratio declaration changed")
    return params
