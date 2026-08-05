"""MOD-008 release manifest and SHA256SUMS for the public workbench.

Builds the spec-pack manifest fields over an explicit file list, and
validates that a manifest and its sums cover every artifact. The
caller supplies created_at and any report hashes, so the builder
stays deterministic and testable.

This module does manifest arithmetic. It does not claim anything
about physics. The packaged public RC1 and its fresh-clone gate use
this module at packaging time.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess

PENDING = "PENDING"


def sha256_of_file(path: str | pathlib.Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_of_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_sha256sums(root: str | pathlib.Path, files) -> str:
    """Classic two-space format, paths posix-relative to root, sorted."""
    root = pathlib.Path(root)
    lines = []
    for f in sorted(pathlib.Path(p) for p in files):
        rel = f.relative_to(root).as_posix()
        lines.append(f"{sha256_of_file(f)}  {rel}")
    return "\n".join(lines) + "\n"


def _git(root: pathlib.Path, *args: str) -> str:
    try:
        out = subprocess.run(["git", *args], cwd=root, capture_output=True,
                             text=True, timeout=30)
        return out.stdout.strip() if out.returncode == 0 else PENDING
    except OSError:
        return PENDING


def build_manifest(root: str | pathlib.Path, files, *, release_id: str,
                   created_at: str, tag: str = PENDING,
                   test_report_hash: str = PENDING,
                   claim_scan_hash: str = PENDING,
                   public_scope_hash: str = PENDING) -> dict:
    """Every spec manifest field, computed or explicitly PENDING."""
    root = pathlib.Path(root)
    files = sorted(pathlib.Path(p) for p in files)
    sums_text = build_sha256sums(root, files)
    registry_path = (root / "rgcs_workbench" / "public_cage"
                     / "module_registry.json")
    return {
        "release_id": release_id,
        "commit": _git(root, "rev-parse", "HEAD"),
        "branch": _git(root, "rev-parse", "--abbrev-ref", "HEAD"),
        "tag": tag,
        "created_at": created_at,
        "module_registry_hash": (sha256_of_file(registry_path)
                                 if registry_path.is_file() else PENDING),
        "file_count": len(files),
        "files": [f.relative_to(root).as_posix() for f in files],
        "sha256sums": sums_text,
        "sha256sums_hash": sha256_of_text(sums_text),
        "test_report_hash": test_report_hash,
        "claim_scan_hash": claim_scan_hash,
        "public_scope_hash": public_scope_hash,
    }


def validate_manifest(manifest: dict, root: str | pathlib.Path,
                      files) -> list[str]:
    """Problems, with reasons: coverage both ways, sums, counts."""
    root = pathlib.Path(root)
    expected = {pathlib.Path(p).relative_to(root).as_posix()
                for p in files}
    listed = set(manifest.get("files", ()))
    problems = [f"file missing from manifest: '{path}'"
                for path in sorted(expected - listed)]
    problems += [f"manifest lists unknown file: '{path}'"
                 for path in sorted(listed - expected)]
    if manifest.get("file_count") != len(listed):
        problems.append("file_count does not match the file list")
    sums = manifest.get("sha256sums", "")
    summed = {line.split("  ", 1)[1] for line in sums.splitlines()
              if "  " in line}
    problems += [f"artifact missing from SHA256SUMS: '{path}'"
                 for path in sorted(listed - summed)]
    if manifest.get("sha256sums_hash") != sha256_of_text(sums):
        problems.append("sha256sums_hash does not match the sums text")
    for field in ("release_id", "commit", "branch", "created_at"):
        if not manifest.get(field):
            problems.append(f"manifest field '{field}' is empty")
    return problems


def write_release_files(root: str | pathlib.Path, out_dir, manifest: dict
                        ) -> dict:
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    sums_path = out / "SHA256SUMS.txt"
    manifest_path = out / "workbench_manifest.json"
    sums_path.write_text(manifest["sha256sums"], encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2),
                             encoding="utf-8")
    return {"sha256sums": str(sums_path), "manifest": str(manifest_path)}


__all__ = ["PENDING", "sha256_of_file", "sha256_of_text",
           "build_sha256sums", "build_manifest", "validate_manifest",
           "write_release_files"]
