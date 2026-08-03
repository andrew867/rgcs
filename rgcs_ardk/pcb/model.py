"""Deterministic net and board-variant models."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from rgcs_ardk.params import LOCKS


class BoardVariant(str, Enum):
    BOARD_A = "RGCS_ARDK_001_BoardA_PassiveSensor"
    BOARD_B = "RGCS_ARDK_001_BoardB_ActiveDrive"


@dataclass(frozen=True)
class NetRecord:
    name: str
    net_class: str
    description: str


@dataclass(frozen=True)
class BoardDefinition:
    variant: BoardVariant
    purpose: str
    passive_only: bool
    sector_zone_prefixes: tuple[str, ...]
    sector_access_prefixes: tuple[str, ...]
    global_nets: tuple[str, ...]
    features: tuple[str, ...]


def net_registry() -> tuple[NetRecord, ...]:
    records: list[NetRecord] = []
    roles = (
        ("DRV", "sector_drive", "Drive/load electrode"),
        ("SENSE", "sector_sense", "Phase-position pickup"),
        ("LOAD", "sector_loading", "Configurable capacitive/gap loading"),
        ("KELVIN_P", "kelvin_voltage_current_sense", "Positive Kelvin sense"),
        ("KELVIN_N", "kelvin_voltage_current_sense", "Negative Kelvin sense"),
    )
    for index in range(LOCKS.sector_count):
        for prefix, net_class, description in roles:
            records.append(
                NetRecord(
                    f"{prefix}_{index:02d}",
                    net_class,
                    f"{description} for sector {index:02d}",
                )
            )
    records.extend(
        (
            NetRecord("GUARD_INNER", "guard", "inner guard/reference ring"),
            NetRecord("GUARD_OUTER", "guard", "outer guard/reference ring"),
            NetRecord("CENTER_REF", "reference", "center reference pickup"),
        )
    )
    records.extend(
        NetRecord(f"COMPASS_{index}", "coarse_compass_sense", f"Coarse compass pickup {index}")
        for index in range(8)
    )
    return tuple(records)


def checked_in_net_registry() -> tuple[NetRecord, ...]:
    path = Path(__file__).with_name("net_names.csv")
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(
            NetRecord(row["net_name"], row["class"], row["description"])
            for row in csv.DictReader(handle)
        )


def validate_net_registry() -> None:
    generated = net_registry()
    checked_in = checked_in_net_registry()
    if generated != checked_in:
        raise ValueError("checked-in net registry differs from deterministic registry")
    if len({record.name for record in generated}) != len(generated):
        raise ValueError("net registry contains duplicates")


def board_definition(variant: BoardVariant) -> BoardDefinition:
    if variant is BoardVariant.BOARD_A:
        return BoardDefinition(
            variant=variant,
            purpose="passive sensor, geometry, and calibration board",
            passive_only=True,
            sector_zone_prefixes=("SENSE",),
            sector_access_prefixes=("SENSE",),
            global_nets=(
                "GUARD_INNER",
                "GUARD_OUTER",
                "CENTER_REF",
                *(f"COMPASS_{index}" for index in range(8)),
            ),
            features=(
                "37 sector pickups",
                "8 board-edge compass pickups",
                "fixture-mounted center-reference interface",
                "inner and outer guards",
                "fiducials and shared mounting holes",
            ),
        )
    if variant is BoardVariant.BOARD_B:
        return BoardDefinition(
            variant=variant,
            purpose="active drive and configurable loading board",
            passive_only=False,
            sector_zone_prefixes=("DRV", "LOAD"),
            sector_access_prefixes=("DRV", "LOAD", "SENSE", "KELVIN_P", "KELVIN_N"),
            global_nets=("GUARD_INNER", "GUARD_OUTER"),
            features=(
                "37 drive sectors",
                "37 loading sectors",
                "trim and isolation footprints",
                "sense-net breakout without pickup copper",
                "Kelvin access and shared mounting holes",
            ),
        )
    raise ValueError(f"unsupported board variant: {variant}")
