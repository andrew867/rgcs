"""Loaders and validators for the cage's machine-readable registries.

Three JSON files ship as package data: the public module registry,
the evidence-class lists, and the H-ME-SSP-001 protocol record. The
loaders read the copies beside this module, so an installed wheel and
a source checkout agree.

This module does registry loading and structural validation. It does
not claim anything about physics. RC1 packaging validation remains
pending.
"""

from __future__ import annotations

import json
import pathlib

_HERE = pathlib.Path(__file__).resolve().parent

EXPECTED_MODULE_IDS = tuple(f"MOD-{i:03d}" for i in range(1, 9))

#: Module id -> exact public status string from the spec pack.
EXPECTED_STATUSES = {
    "MOD-001": "PUBLIC_WORKBENCH",
    "MOD-002": "OPERATIONAL_CALIBRATED_PROFILE_REFERENCE",
    "MOD-003": "MEASUREMENT_HYPOTHESIS_NOT_VALIDATED",
    "MOD-004": "BENCH_PROTOCOL",
    "MOD-005": "PUBLIC_RESEARCH_HYPOTHESIS_NOT_VALIDATED",
    "MOD-006": "HYPOTHESIS_REGISTRY",
    "MOD-007": "PUBLIC_ARCHIVE_RECORD",
    "MOD-008": "RELEASE_GATE",
}

MAPPING_STATUSES = ("MAPPED_EXISTING", "PARTIAL_EXISTING",
                    "CAGE_ONLY_PENDING_IMPORT")


def _load(name: str) -> dict:
    return json.loads((_HERE / name).read_text(encoding="utf-8"))


def load_module_registry() -> dict:
    return _load("module_registry.json")


def load_evidence_classes() -> dict:
    return _load("evidence_classes.json")


def load_h_me_ssp_001_protocol() -> dict:
    return _load("h_me_ssp_001_protocol.json")


def validate_module_registry(repo_root: str | pathlib.Path | None = None
                             ) -> list[str]:
    """Return a list of problems; empty means structurally valid.

    Problems are strings, not booleans, so every failure states its
    reason. Path existence is checked only when a repo root is given,
    because an installed wheel does not carry the whole tree.
    """
    reg = load_module_registry()
    problems: list[str] = []
    mods = {m.get("id"): m for m in reg.get("modules", [])}

    for mod_id in EXPECTED_MODULE_IDS:
        if mod_id not in mods:
            problems.append(f"missing module {mod_id}")
            continue
        mod = mods[mod_id]
        if mod.get("status") != EXPECTED_STATUSES[mod_id]:
            problems.append(
                f"{mod_id} status '{mod.get('status')}' != "
                f"'{EXPECTED_STATUSES[mod_id]}'")
        if mod.get("mapping_status") not in MAPPING_STATUSES:
            problems.append(f"{mod_id} has unknown mapping_status "
                            f"'{mod.get('mapping_status')}'")
        boundary = mod.get("boundary", "")
        if "It does not claim" not in boundary:
            problems.append(f"{mod_id} boundary sentence lacks the "
                            f"'It does not claim' clause")
        if "pending" not in boundary.lower() and "HOLDOUT" not in boundary:
            problems.append(f"{mod_id} boundary sentence lacks a "
                            f"pending/holdout clause")
        if not mod.get("repo_paths"):
            problems.append(f"{mod_id} lists no repo paths")
        elif repo_root is not None:
            root = pathlib.Path(repo_root)
            for rel in mod["repo_paths"]:
                if not (root / rel).exists():
                    problems.append(f"{mod_id} maps to missing path "
                                    f"'{rel}'")

    extra = set(mods) - set(EXPECTED_MODULE_IDS)
    if extra:
        problems.append(f"unexpected module ids: {sorted(extra)}")

    for boundary_flag in ("NO_PHYSICAL_CLAIM_ADVANCED",
                          "TERRA_RC4_PRESERVED"):
        if boundary_flag not in reg.get("hard_boundaries", []):
            problems.append(f"hard boundary '{boundary_flag}' missing")

    return problems


__all__ = ["EXPECTED_MODULE_IDS", "EXPECTED_STATUSES", "MAPPING_STATUSES",
           "load_module_registry", "load_evidence_classes",
           "load_h_me_ssp_001_protocol", "validate_module_registry"]
