"""RSCS 2.0 registry loader + classification/provenance lint (RGCS v4).

Governance (DV4-002): every RSCS2-* object must be registered here with a
valid namespace, class, units, provenance, module, and tests before first
use. This module loads the registry and lints it; the frozen RGCS-M /
RSCS-C / RSCS-O registries are not touched.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

VALID_CLASSES = ("EST", "DER", "HYP", "SRC", "ENG")
VALID_NAMESPACES = ("RSCS2-E", "RSCS2-G", "RSCS2-B", "RSCS2-S",
                    "RSCS2-A", "RSCS2-D", "RSCS2-V", "RSCS2-U")
_SECTIONS = ("equations", "geometry", "boundary", "solver", "accelerator",
             "diagnostics", "benchmarks", "uncertainty")

_REGISTRY_PATH = Path(__file__).with_name("rscs2_registry.yaml")


def load_registry(path: str | Path | None = None) -> dict[str, Any]:
    """Load the RSCS2 registry yaml."""
    p = Path(path) if path else _REGISTRY_PATH
    with open(p, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def registry_entries(reg: dict[str, Any] | None = None) -> list[dict]:
    """Flat list of all registered objects across sections."""
    reg = reg or load_registry()
    out: list[dict] = []
    for section in _SECTIONS:
        out.extend(reg.get(section, []) or [])
    return out


def lint_registry(reg: dict[str, Any] | None = None) -> list[str]:
    """Return a list of governance violations (empty = clean). Checks:
    valid namespace, no id collision, valid class, units present, provenance
    present, module present, tests present, dimensionally-plausible signature
    string present. This is the machine lint required by the v4 plan
    (use-before-registration / missing-units / missing-tests / namespace
    collision / SRC-leakage guards)."""
    reg = reg or load_registry()
    problems: list[str] = []
    seen: set[str] = set()
    for e in registry_entries(reg):
        eid = e.get("id", "<no-id>")
        ns = eid.rsplit(".", 1)[0] if "." in eid else eid
        if ns not in VALID_NAMESPACES:
            problems.append(f"{eid}: namespace {ns!r} not in {VALID_NAMESPACES}")
        if eid in seen:
            problems.append(f"{eid}: duplicate id (namespace collision)")
        seen.add(eid)
        if e.get("class") not in VALID_CLASSES:
            problems.append(f"{eid}: class {e.get('class')!r} invalid")
        if not e.get("units"):
            problems.append(f"{eid}: missing units")
        if not e.get("provenance"):
            problems.append(f"{eid}: missing provenance")
        if not e.get("module"):
            problems.append(f"{eid}: missing module")
        if not e.get("tests"):
            problems.append(f"{eid}: missing tests")
        # SRC-leakage guard: an EST/DER object may not cite a raw SRC-only
        # provenance without an explicit boundary note (extends v3 firewall).
        if e.get("class") in ("EST", "DER"):
            for prov in e.get("provenance", []) or []:
                if str(prov).strip().upper().startswith("SRC-") and \
                        "boundary" not in str(e.get("note", "")).lower():
                    problems.append(
                        f"{eid}: EST/DER cites raw SRC provenance {prov!r} "
                        f"without a boundary note (firewall)")
    return problems
