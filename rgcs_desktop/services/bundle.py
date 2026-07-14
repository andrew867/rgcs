"""Reproducibility bundle export.

Bundle = zip containing the workspace db, imported sources, artifacts,
manifests, reports, a CHECKSUMS.json (sha256 of every member) and a
VERSIONS.json (software versions). Deterministic member ordering.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import zipfile
from pathlib import Path

from rgcs_core.provenance import MODEL_VERSION, sha256_file

import rgcs_desktop
from rgcs_desktop.workspaces import Workspace

_BUNDLE_DIRS = ("sources", "artifacts", "manifests", "reports")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def export_bundle(ws: Workspace, dest: str | Path | None = None) -> Path:
    """Write the reproducibility zip; records it in export history."""
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = Path(dest) if dest else ws.root / "bundles" / f"bundle-{stamp}.zip"
    dest.parent.mkdir(parents=True, exist_ok=True)

    members: list[tuple[str, Path]] = [("workspace.db",
                                        ws.root / "workspace.db")]
    for sub in _BUNDLE_DIRS:
        base = ws.root / sub
        if base.exists():
            for p in sorted(base.rglob("*")):
                if p.is_file() and not p.name.startswith("."):
                    members.append((str(p.relative_to(ws.root)), p))

    checksums: dict[str, str] = {}
    versions = {
        "rgcs_core_model_version": MODEL_VERSION,
        "rgcs_desktop": rgcs_desktop.__version__,
        "bundle_format": "1.0",
        "created_utc": stamp,
        "workspace_name": ws.name,
        "workspace_schema_version": ws.schema_version,
    }
    try:
        import numpy, scipy, PySide6  # noqa: E401
        versions.update({"numpy": numpy.__version__,
                         "scipy": scipy.__version__,
                         "PySide6": PySide6.__version__})
    except Exception:  # pragma: no cover
        pass

    tmp = dest.with_suffix(".zip.tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zf:
        for arcname, path in members:
            data = path.read_bytes()
            checksums[arcname] = _sha256_bytes(data)
            zf.writestr(arcname, data)
        zf.writestr("CHECKSUMS.json", json.dumps(checksums, indent=2,
                                                 sort_keys=True))
        zf.writestr("VERSIONS.json", json.dumps(versions, indent=2,
                                                sort_keys=True))
    tmp.replace(dest)  # atomic finalize
    ws.record_export("bundle", dest, sha256_file(str(dest)))
    return dest


def verify_bundle(path: str | Path) -> dict:
    """Re-hash every member against CHECKSUMS.json; returns a report."""
    path = Path(path)
    mismatches: list[str] = []
    with zipfile.ZipFile(path) as zf:
        checksums = json.loads(zf.read("CHECKSUMS.json"))
        versions = json.loads(zf.read("VERSIONS.json"))
        for arcname, expected in checksums.items():
            got = _sha256_bytes(zf.read(arcname))
            if got != expected:
                mismatches.append(arcname)
    return {"ok": not mismatches, "mismatches": mismatches,
            "n_members": len(checksums), "versions": versions}
