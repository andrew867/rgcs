#!/usr/bin/env python3
"""Validate RGCS experiment JSON instances against the schema set.

Usage:
    python3 experiments/schemas/validate.py                 # validate everything known
    python3 experiments/schemas/validate.py FILE SCHEMA     # validate one instance

Schemas use $id "rgcs://schemas/<name>.schema.json" with relative $refs;
this script registers all schemas so cross-file references resolve offline.
Intended consumers: Agent 05 (desktop experiment builder) and Agent 08 (QA gates).
"""
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

SCHEMA_DIR = Path(__file__).resolve().parent
REPO = SCHEMA_DIR.parent.parent

SCHEMA_FILES = [
    "specimen.schema.json",
    "drive_config.schema.json",
    "acquisition.schema.json",
    "environment.schema.json",
    "timeseries_channel.schema.json",
    "control_matrix.schema.json",
    "run_manifest.schema.json",
    "analysis_result.schema.json",
    "optical_probe.schema.json",
    "timing_program.schema.json",
]

# instance path (relative to repo root) -> schema file
DEFAULT_TARGETS = {
    "experiments/templates/specimen.example.json": "specimen.schema.json",
    "experiments/templates/drive_config.example.json": "drive_config.schema.json",
    "experiments/templates/acquisition.example.json": "acquisition.schema.json",
    "experiments/templates/environment.example.json": "environment.schema.json",
    "experiments/templates/timeseries_channel.example.json": "timeseries_channel.schema.json",
    "experiments/templates/control_matrix.example.json": "control_matrix.schema.json",
    "experiments/templates/run_manifest.example.json": "run_manifest.schema.json",
    "experiments/templates/analysis_result.example.json": "analysis_result.schema.json",
    "experiments/templates/branch_01_modal_survey.template.json": "run_manifest.schema.json",
    "experiments/templates/branch_02_electrode_pulse.template.json": "run_manifest.schema.json",
    "experiments/templates/branch_03_sound_key.template.json": "run_manifest.schema.json",
    "experiments/templates/branch_04_opposed_coil.template.json": "run_manifest.schema.json",
    "experiments/templates/branch_05_human_loading.template.json": "run_manifest.schema.json",
    "experiments/templates/branch_06_spiral_cone.template.json": "run_manifest.schema.json",
    "experiments/templates/branch_07_water.template.json": "run_manifest.schema.json",
    "experiments/templates/branch_08_spatial_mapping.template.json": "run_manifest.schema.json",
    "experiments/templates/optical_probe.example.json": "optical_probe.schema.json",
    "experiments/templates/timing_program.example.json": "timing_program.schema.json",
    "experiments/controls/control_matrix.example.json": "control_matrix.schema.json",
    "experiments/sample_data/modal_survey_run_manifest.json": "run_manifest.schema.json",
    "experiments/sample_data/opposed_coil_run_manifest.json": "run_manifest.schema.json",
}


def build_registry():
    resources = []
    for name in SCHEMA_FILES:
        schema = json.loads((SCHEMA_DIR / name).read_text())
        res = Resource.from_contents(schema)
        resources.append((schema["$id"], res))
        # also register under the bare relative name used by $refs
        # (the custom rgcs:// scheme does not URL-join like http)
        resources.append((name, res))
    return Registry().with_resources(resources)


def validate_file(instance_path: Path, schema_name: str, registry) -> list:
    schema = json.loads((SCHEMA_DIR / schema_name).read_text())
    validator = Draft202012Validator(schema, registry=registry)
    instance = json.loads(instance_path.read_text())
    # A top-level JSON array = a collection of instances (e.g. the full
    # per-branch control matrix); validate each element.
    items = instance if isinstance(instance, list) else [instance]
    errors = []
    for item in items:
        errors.extend(validator.iter_errors(item))
    return sorted(errors, key=lambda e: list(e.absolute_path))


def main() -> int:
    registry = build_registry()
    if len(sys.argv) == 3:
        targets = {sys.argv[1]: sys.argv[2]}
    else:
        targets = DEFAULT_TARGETS
    failures = 0
    for rel, schema_name in targets.items():
        path = (REPO / rel) if not Path(rel).is_absolute() else Path(rel)
        if not path.exists():
            print(f"SKIP (missing): {rel}")
            continue
        errors = validate_file(path, schema_name, registry)
        if errors:
            failures += 1
            print(f"FAIL: {rel} vs {schema_name}")
            for e in errors[:5]:
                loc = "/".join(str(p) for p in e.absolute_path) or "<root>"
                print(f"    at {loc}: {e.message}")
        else:
            print(f"OK:   {rel} vs {schema_name}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
