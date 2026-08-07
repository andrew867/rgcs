"""Phryll v2 export bundle (05_CAD_GENERATOR/EXPORT_BUNDLE_LAYOUT):

    phryll_design_<design_id>/
      MANIFEST.json  CHECKSUMS.sha256
      inputs/ cad/ flat/ pdf/ receipts/ logs/
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path

from rgcs_core.provenance import json_dumps, sha256_file

from rgcs_desktop.services.export_receipts import (git_commit,
                                                   software_versions)


def export_bundle(design_id: str, bundle_root: str | Path,
                  inputs: dict[str, dict], cad: dict[str, str],
                  flat: dict[str, str], pdf: dict[str, str],
                  receipts: dict[str, dict],
                  backend_notes: list[str]) -> Path:
    """Assemble the bundle directory. ``inputs``/``receipts`` map file
    stems to JSON payloads; ``cad``/``flat``/``pdf`` map target names to
    existing file paths (copied in)."""
    import shutil
    root = Path(bundle_root) / f"phryll_design_{design_id}"
    for sub in ("inputs", "cad", "flat", "pdf", "receipts", "logs"):
        (root / sub).mkdir(parents=True, exist_ok=True)

    for stem, payload in inputs.items():
        (root / "inputs" / f"{stem}.json").write_text(
            json_dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8")
    for sub, mapping in (("cad", cad), ("flat", flat), ("pdf", pdf)):
        for name, src in mapping.items():
            shutil.copy(src, root / sub / name)
    for stem, payload in receipts.items():
        (root / "receipts" / f"{stem}.json").write_text(
            json_dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8")
    (root / "logs" / "backend_status.txt").write_text(
        "\n".join(backend_notes) + "\n", encoding="utf-8")

    manifest = {
        "bundle_kind": "phryll_v2_design",
        "design_id": design_id,
        "software": software_versions(),
        "git_commit": git_commit(),
        "generated_utc": _dt.datetime.now(_dt.timezone.utc)
                            .isoformat(timespec="seconds"),
        "layout": ["inputs", "cad", "flat", "pdf", "receipts", "logs"],
    }
    (root / "MANIFEST.json").write_text(
        json_dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    lines = []
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.name != "CHECKSUMS.sha256":
            rel = p.relative_to(root).as_posix()
            lines.append(f"{sha256_file(str(p))}  {rel}")
    (root / "CHECKSUMS.sha256").write_text("\n".join(lines) + "\n",
                                           encoding="utf-8")
    return root


def verify_bundle(root: str | Path) -> dict:
    root = Path(root)
    recorded = {}
    for line in (root / "CHECKSUMS.sha256").read_text(
            encoding="utf-8").splitlines():
        if line.strip():
            sha, _, rel = line.partition("  ")
            recorded[rel] = sha
    mismatched = [rel for rel, sha in recorded.items()
                  if not (root / rel).is_file()
                  or sha256_file(str(root / rel)) != sha]
    return {"ok": not mismatched, "n_members": len(recorded),
            "mismatched": mismatched}
