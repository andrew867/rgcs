"""Markdown report generation for a workspace."""
from __future__ import annotations

import datetime as _dt
import platform
from pathlib import Path
from typing import Any

from rgcs_core.provenance import MODEL_VERSION, sha256_file

import rgcs_desktop
from rgcs_desktop.services.formatting import format_node_mm, format_uncertain
from rgcs_desktop.workspaces import Workspace
from rgcs_desktop.workspaces.workspace import atomic_write_text


def _versions() -> dict[str, str]:
    import numpy
    import scipy
    versions = {
        "rgcs_core_model_version": MODEL_VERSION,
        "rgcs_desktop": rgcs_desktop.__version__,
        "python": platform.python_version(),
        "numpy": numpy.__version__,
        "scipy": scipy.__version__,
    }
    try:
        import PySide6
        versions["PySide6"] = PySide6.__version__
    except Exception:  # pragma: no cover
        pass
    return versions


def generate_report(ws: Workspace, title: str | None = None) -> Path:
    """Write a markdown summary of the workspace; returns the report path."""
    now = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
    lines: list[str] = []
    lines.append(f"# {title or ws.name} — workspace report")
    lines.append("")
    lines.append(f"Generated {now} by rgcs_desktop {rgcs_desktop.__version__} "
                 f"(rgcs_core model version {MODEL_VERSION}).")
    lines.append("")
    lines.append("Classification policy: every claim in this report keeps the "
                 "label recorded with the underlying object "
                 "(Established / Derived / Hypothesis / Source claim). "
                 "Derived analysis outputs and merit scores are NOT evidence "
                 "of any physical hypothesis.")
    lines.append("")

    lines.append("## Software versions")
    lines.append("")
    for k, v in _versions().items():
        lines.append(f"- {k}: {v}")
    lines.append("")

    for kind, heading in (("specimen", "Specimens"), ("model", "Models"),
                          ("experiment", "Experiments"),
                          ("source", "Sources"), ("result", "Results")):
        objs = ws.list_objects(kind)
        lines.append(f"## {heading} ({len(objs)})")
        lines.append("")
        for o in objs:
            full = ws.get_object(o["object_id"])
            payload = full["payload"]
            lines.append(f"### {o['name']}  `{o['object_id']}`")
            lines.append("")
            cls = payload.get("classification") or payload.get(
                "classification_note")
            if cls:
                lines.append(f"- classification: **{cls}**")
            if kind == "specimen":
                derived = payload.get("derived", {})
                nodes = derived.get("node_positions", {})
                if nodes:
                    lines.append(
                        f"- selected node: "
                        f"{format_node_mm(nodes.get('selected_node_mm'))} "
                        f"(measured: "
                        f"{format_node_mm(nodes.get('measured_node_mm'))})")
                f_ax = derived.get("axial_half_wave")
                if f_ax:
                    lines.append(f"- axial half-wave: "
                                 f"{format_uncertain(f_ax, 'Hz')}")
            if kind == "result":
                lines.append(f"- artifact: {payload.get('artifact_id')}")
                lines.append(f"- sha256: {payload.get('sha256')}")
            lines.append(f"- content sha256: {o['content_sha256']}")
            lines.append("")

    jobs = ws.list_jobs()
    lines.append(f"## Jobs ({len(jobs)})")
    lines.append("")
    for j in jobs:
        lines.append(f"- {j['job_id']} {j['name']}: **{j['status']}** "
                     f"(progress {j['progress']:.0%})"
                     + (f" — error artifact preserved" if j["error"] else ""))
    lines.append("")

    exports = ws.list_exports()
    lines.append(f"## Export history ({len(exports)})")
    lines.append("")
    for e in exports:
        lines.append(f"- {e['created_at']} {e['kind']}: {e['path']} "
                     f"(sha256 {e['sha256'][:16]}…)")
    lines.append("")

    stamp = now.replace(":", "").replace("+0000", "Z")
    path = ws.root / "reports" / f"report-{stamp}.md"
    atomic_write_text(path, "\n".join(lines))
    ws.record_export("report", path, sha256_file(str(path)))
    return path
