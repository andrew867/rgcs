"""Phi ladders and actual sale-crystal triage -- comparison lanes only.

Three source-reported arithmetic ladders from the 2026-08-06 V3 pack
(golden-ratio gravity paper review plus the Dan Winter phi-Schumann
cascade), and the scoring loader for ACTUAL sale-dataset crystal
candidates. Classification is contractual:

    SOURCE_REPORTED_ARITHMETIC   the ladder formulas and constants
    CANDIDATE_BRIDGE             a near-neighbor pairing, never a merge
    NOT_RGCS_VALIDATION          nothing here validates the source's
                                 physical interpretation

The source paper's claim that phi fractality and phase conjugation
cause gravity stays source language. RGCS reproduces the arithmetic,
compares frequencies, and stops there.

Near-neighbor discipline (locked): 4079.44 Hz is not 4096 Hz,
20.4992 Hz is not 20.48 Hz, 13.563688 MHz is not 13.18359375 MHz.
The phi ladder and the RGCS octave ladder are different families and
never merge without an explicit correction rule.

Purchase and test ranking uses actual sale-dataset candidates and
their estimated modes, never ideal-only calculated crystals, and the
sale-list estimate stays separate from any future measured result.
"""

from __future__ import annotations

import csv
import json
import math
import pathlib

_HERE = pathlib.Path(__file__).resolve().parent

PHI = (1.0 + math.sqrt(5.0)) / 2.0

#: Source-paper constants, preserved verbatim for arithmetic
#: reproduction (SOURCE_REPORTED_ARITHMETIC; deliberately not CODATA).
SOURCE_PLANCK_LENGTH_M = 1.616252e-35
SOURCE_PLANCK_TIME_S = 1.35125e-43
SCHUMANN_BASE_HZ = 7.83

CLASSIFICATIONS = ("SOURCE_REPORTED_ARITHMETIC", "CANDIDATE_BRIDGE",
                   "NOT_RGCS_VALIDATION")

#: (phi-family value, RGCS-family value, note) -- distinct, never merged.
NEAR_NEIGHBOR_PAIRS = (
    (4079.445028735422, 4096.0,
     "phi-Schumann n=13 vs RGCS phase authority"),
    (20.499206131911677, 20.48,
     "phi-Schumann n=2 in Hz vs RGCS 20.48 (kHz-lane numeral)"),
    (13563688.592484437, 13183593.75,
     "phi Planck-time n=171 vs RGCS craft carrier candidate"),
)


def phi_schumann_hz(n: int) -> float:
    return SCHUMANN_BASE_HZ * PHI ** n


def phi_planck_frequency_hz(n: int) -> float:
    return 1.0 / (SOURCE_PLANCK_TIME_S * PHI ** n)


def phi_planck_length_angstrom(n: int) -> float:
    return SOURCE_PLANCK_LENGTH_M * PHI ** n * 1.0e10


def offset_percent(value: float, target: float) -> float:
    return 100.0 * (value - target) / target


def near_neighbor_receipts() -> list[dict]:
    """Each pair stated with its offset; families stay separate."""
    receipts = []
    for phi_value, rgcs_value, note in NEAR_NEIGHBOR_PAIRS:
        receipts.append({
            "phi_family_value": phi_value,
            "rgcs_family_value": rgcs_value,
            "offset_percent": offset_percent(phi_value, rgcs_value),
            "note": note,
            "distinct": phi_value != rgcs_value,
            "rule": "FAMILIES_NEVER_MERGE_WITHOUT_CORRECTION_RULE",
            "classification": "CANDIDATE_BRIDGE",
        })
    return receipts


def _load(name: str):
    return json.loads((_HERE / name).read_text(encoding="utf-8"))


def load_phi_schumann_ladder() -> list[dict]:
    return _load("phi_schumann_ladder.json")


def load_phi_planck_frequency_ladder() -> list[dict]:
    return _load("phi_planck_time_frequency_ladder_selected.json")


def load_phi_planck_hydrogen_radii() -> list[dict]:
    return _load("phi_planck_length_hydrogen_radii.json")


def load_scored_modes() -> list[dict]:
    return _load("actual_sale_crystal_phi_rgcs_scored_modes.json")


def load_scored_modes_csv() -> list[dict]:
    with open(_HERE / "actual_sale_crystal_phi_rgcs_scored_modes.csv",
              encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_scored_modes() -> list[str]:
    """Every row is sale-derived and carries BOTH score lanes."""
    problems: list[str] = []
    for row in load_scored_modes():
        rid = f"{row.get('crystal_id')}:{row.get('mode')}"
        if not str(row.get("crystal_id", "")).startswith("SALE_"):
            problems.append(f"{rid} is not a sale-dataset candidate; "
                            f"ideal-only crystals are not rankable")
        for field in ("mode_hz", "nearest_phi_key", "nearest_phi_hz",
                      "phi_offset_percent", "nearest_rgcs_key",
                      "nearest_rgcs_hz", "rgcs_offset_percent",
                      "primary_lane"):
            if row.get(field) in (None, ""):
                problems.append(f"{rid} missing {field}")
    return problems


def rank_candidates() -> dict:
    """Two score columns over ACTUAL sale modes; smallest absolute
    offset wins its lane. Sale-list estimates, not measurements."""
    rows = load_scored_modes()
    # The RGCS score column is the 4096 multiple family. A row whose
    # nearest key is the annular-resonance-derived 1683456/100 scores
    # in that other lane, not here; without this filter the rutilated
    # shear mode would wrongly take the octave championship.
    rgcs_family = [r for r in rows if "4096" in r["nearest_rgcs_key"]]
    best_rgcs = min(rgcs_family,
                    key=lambda r: abs(r["rgcs_offset_percent"]))
    best_phi = min(rows, key=lambda r: abs(r["phi_offset_percent"]))
    multi = {}
    for row in rows:
        if abs(row["phi_offset_percent"]) <= 3.5:
            multi.setdefault(row["crystal_id"], []).append(row["mode"])
    best_multi = max(multi.items(), key=lambda kv: len(kv[1]),
                     default=(None, []))
    return {
        "score_rgcs_4096_family": {
            "crystal_id": best_rgcs["crystal_id"],
            "mode": best_rgcs["mode"],
            "offset_percent": best_rgcs["rgcs_offset_percent"],
        },
        "score_phi_schumann_family": {
            "crystal_id": best_phi["crystal_id"],
            "mode": best_phi["mode"],
            "offset_percent": best_phi["phi_offset_percent"],
        },
        "best_multi_hit_phi": {
            "crystal_id": best_multi[0],
            "modes_within_3p5_percent": sorted(best_multi[1]),
        },
        "basis": "SALE_LIST_ESTIMATES_NOT_MEASUREMENTS",
        "classification": "NOT_RGCS_VALIDATION",
    }


__all__ = ["PHI", "SOURCE_PLANCK_LENGTH_M", "SOURCE_PLANCK_TIME_S",
           "SCHUMANN_BASE_HZ", "CLASSIFICATIONS", "NEAR_NEIGHBOR_PAIRS",
           "phi_schumann_hz", "phi_planck_frequency_hz",
           "phi_planck_length_angstrom", "offset_percent",
           "near_neighbor_receipts", "load_phi_schumann_ladder",
           "load_phi_planck_frequency_ladder",
           "load_phi_planck_hydrogen_radii", "load_scored_modes",
           "load_scored_modes_csv", "validate_scored_modes",
           "rank_candidates"]
