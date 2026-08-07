"""Shared helpers for Design Studio panels: export locations, the
cross-panel studio state (selected specimen/design), and safe export
recording."""
from __future__ import annotations

from pathlib import Path

from rgcs_core.provenance import sha256_file


def studio_state(context) -> dict:
    """Mutable cross-panel state (last validated specimen, last design).
    Lives on the AppContext so panels stay decoupled from each other."""
    if not hasattr(context, "design_studio_state"):
        context.design_studio_state = {}
    return context.design_studio_state


def export_dir(context) -> Path:
    """Where Design Studio artifacts land: inside the workspace when one
    is open, else a local folder."""
    ws = getattr(context, "workspace", None)
    if ws is not None:
        return Path(ws.root) / "exports" / "design_studio"
    return Path.cwd() / "design_studio_exports"


def record_export_safe(context, kind: str, path: Path) -> None:
    """Record an export in the workspace ledger; never let ledger
    trouble break the export itself."""
    ws = getattr(context, "workspace", None)
    if ws is None:
        return
    try:
        ws.record_export(kind, Path(path), sha256_file(str(path)))
        context.notify_workspace_changed()
    except Exception:   # ledger is best-effort; the artifact exists
        pass


#: Built-in demo specimen (mirrors the repo example template) so the
#: golden path is walkable before any workspace objects exist.
EXAMPLE_SPECIMEN = {
    "schema_version": "1.0.0",
    "specimen_id": "CRY-EXAMPLE-001",
    "material_family": "quartz",
    "dimensions": {
        "length_mm": 110.0,
        "diameter_mm": 32.0,
        "facet_count": 6,
        "termination_angle_deg": 51.7,
    },
    "mass_g": 232.0,
    "measured_nodes_mm": [27.5, 55.0, 82.5],
    "uncertainty": {"length_mm": 0.5, "width_mm": 0.5, "angle_deg": 1.0},
    "supplier": "example supplier",
    "operator": "example operator",
    "provenance": {"entered_by": "example operator",
                   "method": "calipers + protractor"},
    "classification": "MEASURED_INPUT",
}
