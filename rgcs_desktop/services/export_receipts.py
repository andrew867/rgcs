"""Export receipts and bundle manifests for Design Studio artifacts.

Every exported artifact gets a receipt carrying: object ID, source object
IDs, software version, git commit (when available), input hash, output
hashes, claim boundary, and timestamp. Receipts are plain dicts so they
serialize with the repo's canonical NaN-free JSON.
"""
from __future__ import annotations

import datetime as _dt
import subprocess
from pathlib import Path

from rgcs_core.provenance import json_dumps, sha256_file, sha256_of_jsonable

import rgcs_desktop


def software_versions() -> dict[str, str]:
    import platform
    return {
        "rgcs_desktop": rgcs_desktop.__version__,
        "python": platform.python_version(),
    }


def git_commit() -> str | None:
    """Current commit hash, or None (frozen builds have no git)."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).resolve().parents[2],
            capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if out.returncode != 0:
        return None
    return out.stdout.strip() or None


def make_receipt(inputs: dict, outputs: list[Path], classification: str,
                 *, object_id: str = "", source_ids: list[str] | None = None,
                 boundary: str = "") -> dict:
    """Receipt for one export action.

    ``inputs`` is hashed canonically (sort_keys, NaN-free); each output
    file is hashed by content. The timestamp records when the export
    happened; determinism claims attach to the input/output hashes, not
    the timestamp.
    """
    return {
        "object_id": object_id,
        "source_ids": list(source_ids or []),
        "classification": classification,
        "claim_boundary": boundary,
        "software": software_versions(),
        "git_commit": git_commit(),
        "input_sha256": sha256_of_jsonable(inputs),
        "outputs": [
            {"path": p.name, "sha256": sha256_file(str(p))}
            for p in outputs
        ],
        "timestamp_utc": _dt.datetime.now(_dt.timezone.utc)
                            .isoformat(timespec="seconds"),
    }


def write_receipt(receipt: dict, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json_dumps(receipt, indent=2, sort_keys=True),
                        encoding="utf-8")
    return out_path


def write_manifest(bundle_dir: Path, receipts: list[dict]) -> Path:
    """Write MANIFEST.json + CHECKSUMS.json for an export bundle
    directory. CHECKSUMS covers every file in the bundle except the
    checksum file itself."""
    bundle_dir = Path(bundle_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "bundle_kind": "design_studio_export",
        "software": software_versions(),
        "git_commit": git_commit(),
        "receipts": receipts,
        "generated_utc": _dt.datetime.now(_dt.timezone.utc)
                            .isoformat(timespec="seconds"),
    }
    manifest_path = bundle_dir / "MANIFEST.json"
    manifest_path.write_text(json_dumps(manifest, indent=2, sort_keys=True),
                             encoding="utf-8")
    checks = {}
    for p in sorted(bundle_dir.rglob("*")):
        if p.is_file() and p.name != "CHECKSUMS.json":
            checks[p.relative_to(bundle_dir).as_posix()] = sha256_file(str(p))
    (bundle_dir / "CHECKSUMS.json").write_text(
        json_dumps(checks, indent=2, sort_keys=True), encoding="utf-8")
    return manifest_path


def verify_manifest(bundle_dir: Path) -> dict:
    """Re-hash a bundle directory against CHECKSUMS.json."""
    import json
    bundle_dir = Path(bundle_dir)
    recorded = json.loads((bundle_dir / "CHECKSUMS.json")
                          .read_text(encoding="utf-8"))
    mismatched = [rel for rel, sha in recorded.items()
                  if not (bundle_dir / rel).is_file()
                  or sha256_file(str(bundle_dir / rel)) != sha]
    return {"ok": not mismatched, "n_members": len(recorded),
            "mismatched": mismatched}
