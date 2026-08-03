"""Hash-pinned loader for the committed R10.73 design authority."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from rgcs_ardk.params import LOCKS


class AuthorityRefused(RuntimeError):
    """Raised when the required R10.73 inputs are absent or untrusted."""


@dataclass(frozen=True)
class AuthorityBundle:
    root: Path
    drive_table: dict[str, Any]
    probe_plan: dict[str, Any]
    null_masks: dict[str, Any]
    bench_protocol: str
    source_commit: str
    hashes: dict[str, str]

    @property
    def rows(self) -> list[dict[str, Any]]:
        return self.drive_table["rows"]


def _canonical_bytes(path: Path) -> bytes:
    text = path.read_text(encoding="utf-8")
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(_canonical_bytes(path)).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AuthorityRefused(f"unreadable authority file: {path.name}") from exc
    if not isinstance(value, dict):
        raise AuthorityRefused(f"authority file must contain an object: {path.name}")
    return value


def _complex_pairs(values: list[Any]) -> list[complex]:
    converted: list[complex] = []
    for value in values:
        if not isinstance(value, list) or len(value) != 2:
            raise AuthorityRefused("null table contains a malformed complex pair")
        converted.append(complex(float(value[0]), float(value[1])))
    return converted


def _validate_drive_table(table: dict[str, Any]) -> None:
    rows = table.get("rows")
    if not isinstance(rows, list) or len(rows) != LOCKS.sector_count:
        raise AuthorityRefused("drive table must contain exactly 37 rows")
    indices = [row.get("cell_index") for row in rows]
    if indices != list(range(LOCKS.sector_count)):
        raise AuthorityRefused("drive table cell indices are not canonical")
    active = [row for row in rows if row.get("active_floor_status") == "OK"]
    blanked = [row for row in rows if row.get("active_floor_status") == "BLANKED"]
    if len(active) != LOCKS.active_count or len(blanked) != 4:
        raise AuthorityRefused("drive table active/blanked counts violate the lock")
    if any(row.get("active_floor_status") not in {"OK", "BLANKED"} for row in rows):
        raise AuthorityRefused("drive table contains a floor violation")
    minimum = min(float(row["amplitude_weight"]) for row in active)
    if minimum < LOCKS.active_floor or minimum < LOCKS.winner_min_active_amplitude:
        raise AuthorityRefused("drive table active amplitude floor is not authoritative")
    if not math.isclose(float(table.get("mod", -1)), LOCKS.modulation, abs_tol=1e-12):
        raise AuthorityRefused("drive table modulation lock changed")
    if not math.isclose(float(table.get("lag_rad", 0)), LOCKS.lag_rad, abs_tol=1e-12):
        raise AuthorityRefused("drive table lag lock changed")
    prediction = table.get("predicted_d_eff") or {}
    if not math.isclose(
        float(prediction.get("magnitude", -1)), LOCKS.d_eff_magnitude, abs_tol=2e-3
    ):
        raise AuthorityRefused("drive table d_eff magnitude is outside the locked tolerance")
    if not math.isclose(
        float(prediction.get("offset_from_blank_axis_deg", 999)),
        LOCKS.direction_offset_deg,
        abs_tol=0.1,
    ):
        raise AuthorityRefused("drive table direction offset is outside tolerance")


def _validate_probe_plan(plan: dict[str, Any]) -> None:
    probes = plan.get("probes")
    if not isinstance(probes, list) or len(probes) != 54 or plan.get("n_probes") != 54:
        raise AuthorityRefused("probe authority must contain exactly 54 probes")
    counts: dict[str, int] = {}
    for probe in probes:
        counts[probe["kind"]] = counts.get(probe["kind"], 0) + 1
    expected = {
        "center": 1,
        "perimeter": 37,
        "compass": 8,
        "above_plane": 4,
        "below_plane": 4,
    }
    if counts != expected:
        raise AuthorityRefused("probe authority geometry is incomplete")
    if plan.get("lock_in_reference_hz") != LOCKS.carrier_hz:
        raise AuthorityRefused("probe carrier lock changed")
    if plan.get("envelope_reference_hz") != LOCKS.envelope_hz:
        raise AuthorityRefused("probe envelope lock changed")


def _validate_null_masks(nulls: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    tables = nulls.get("weight_tables") or {}
    required = {
        "all_active_symmetric",
        "binary_blanking_best",
        "reversed_phase_lag",
        "rotated_mask_k7",
        "mirrored_mask",
    }
    if set(tables) != required:
        raise AuthorityRefused("null table registry is incomplete or unexpected")
    for name, values in tables.items():
        if len(values) != LOCKS.sector_count:
            raise AuthorityRefused(f"null table has wrong length: {name}")
        _complex_pairs(values)
    baseline = sorted(round(float(row["amplitude_weight"]), 12) for row in rows)
    randomized = nulls.get("equal_resource_randomized") or []
    if len(randomized) != 8:
        raise AuthorityRefused("eight equal-resource randomized controls are required")
    for item in randomized:
        values = _complex_pairs(item.get("weights") or [])
        magnitudes = sorted(round(abs(value), 12) for value in values)
        if not item.get("equal_resource") or magnitudes != baseline:
            raise AuthorityRefused("randomized control changed the resource distribution")
    conditions = {item.get("name") for item in nulls.get("bench_conditions") or []}
    if not {"dummy_resistive_load", "no_crystal", "dummy_crystal"} <= conditions:
        raise AuthorityRefused("bench-condition controls are incomplete")


def load_authority(root: str | Path | None = None) -> AuthorityBundle:
    """Load and validate the only input allowed to feed design generators."""
    authority_root = Path(root) if root is not None else Path(__file__).with_name("authority")
    manifest_path = Path(__file__).with_name("authority_manifest.json")
    if "seed" in authority_root.name.lower() or "not_authority" in str(authority_root).lower():
        raise AuthorityRefused("seed data cannot be selected as design authority")
    manifest = _read_json(manifest_path)
    if manifest.get("status") != "R10_73_AUTHORITY" or manifest.get("seed_is_authority"):
        raise AuthorityRefused("authority manifest status is invalid")
    hashes: dict[str, str] = {}
    for name, record in manifest["files"].items():
        path = authority_root / name
        if not path.is_file():
            raise AuthorityRefused(f"required R10.73 artifact missing: {name}")
        actual = _sha256(path)
        if actual != record["sha256"]:
            raise AuthorityRefused(f"stale or modified R10.73 artifact: {name}")
        hashes[name] = actual
    drive_table = _read_json(authority_root / "drive_table.json")
    probe_plan = _read_json(authority_root / "probe_plan.json")
    null_masks = _read_json(authority_root / "null_masks.json")
    _validate_drive_table(drive_table)
    _validate_probe_plan(probe_plan)
    _validate_null_masks(null_masks, drive_table["rows"])
    return AuthorityBundle(
        root=authority_root.resolve(),
        drive_table=drive_table,
        probe_plan=probe_plan,
        null_masks=null_masks,
        bench_protocol=(authority_root / "bench_protocol.md").read_text(encoding="utf-8"),
        source_commit=manifest["source_commit"],
        hashes=hashes,
    )
