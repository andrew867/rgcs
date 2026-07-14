"""Run-manifest construction helpers for the experiment builder.

Produces dicts that validate against experiments/schemas/run_manifest.schema.json
(validated via services.schemas, which reuses validate.py's registry).
"""
from __future__ import annotations

import datetime as _dt
from typing import Any

from rgcs_core.provenance import MODEL_VERSION, sha256_file

from rgcs_desktop.services.schemas import CURRENT_SCHEMA_VERSION


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def specimen_record_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Map a workspace specimen payload (specimen editor output) to a
    schema-conformant specimen record."""
    kind = payload.get("kind", "crystal")
    spec: dict[str, Any] = {
        "specimen_id": payload.get("specimen_id", "SP-UNSET"),
        "specimen_type": ("quartz_crystal" if kind == "crystal"
                          else "spiral_cone_resonator"),
        "material": {"name": payload.get("material", "alpha-quartz")},
        "provenance": {
            "origin": payload.get("origin", "workspace specimen editor"),
            "classification_note": payload.get(
                "classification",
                "geometry priors Derived; default angles are Source claim"),
        },
    }
    g = payload.get("geometry", {})
    if kind == "crystal" and g:
        spec["material"]["density_g_cm3"] = g.get("density_g_cm3", 2.65)
        spec["geometry"] = {
            "length_mm": g["length_mm"],
            "diameter_wide_mm": g["wide_diameter_mm"],
            "diameter_narrow_mm": g["narrow_diameter_mm"],
            "diameter_mode": g.get("diameter_mode", "across_vertices"),
            "facet_count": g.get("facets", 6),
            "angle_female_deg": g.get("female_angle_deg", 51.843),
            "angle_male_deg": g.get("male_angle_deg", 60.0),
            "angle_mode": g.get("angle_mode", "face_slope"),
        }
        if payload.get("mass_measured_g"):
            spec["mass_measured_g"] = payload["mass_measured_g"]
        if payload.get("mass_predicted_g"):
            spec["mass_predicted_g"] = payload["mass_predicted_g"]
    return spec


def build_run_manifest(*, run_id: str, protocol_branch: str,
                       hypothesis_ids: list[str], operator_id: str,
                       control_role: str, specimen: dict[str, Any],
                       drive_config: dict[str, Any],
                       acquisition: dict[str, Any],
                       environment: dict[str, Any] | None = None,
                       timeseries: list[dict[str, Any]] | None = None,
                       human_loading: dict[str, Any] | None = None,
                       protocol_version: str = "1.0.0",
                       notes: str = "") -> dict[str, Any]:
    manifest: dict[str, Any] = {
        "schema_version": CURRENT_SCHEMA_VERSION,
        "run_id": run_id,
        "protocol_branch": protocol_branch,
        "protocol_version": protocol_version,
        "hypothesis_ids": hypothesis_ids,
        "timestamp": _now_iso(),
        "operator_id": operator_id,
        "control_role": control_role,
        "specimen": specimen,
        "drive_config": drive_config,
        "acquisition": acquisition,
        "environment": environment or {
            "bench_id": "BENCH-UNSET",
            "timestamp_start": _now_iso(),
            "temperature_c_start": 20.0,
        },
        "timeseries": timeseries or [],
        "provenance": {
            "software": {"rgcs_desktop": "2.0.0",
                         "rgcs_core_model_version": MODEL_VERSION},
        },
    }
    if human_loading is not None:
        manifest["human_loading"] = human_loading
    if notes:
        manifest["notes"] = notes
    return manifest


def timeseries_entry_for_csv(csv_path: str, channel_ids: list[str],
                             sample_rate_hz: float,
                             columns: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "file": str(csv_path),
        "format": "csv",
        "sha256": sha256_file(str(csv_path)),
        "channel_ids": channel_ids,
        "sample_rate_hz": sample_rate_hz,
        "columns": columns,
    }
