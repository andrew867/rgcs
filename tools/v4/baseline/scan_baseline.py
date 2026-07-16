"""Agent B0: deterministic repository baseline scanner (read-only).

    python tools/v4/baseline/scan_baseline.py

Writes docs/v4/baseline/ artifacts:
  V4_REPO_INVENTORY.json          head/branch/tags/dirty/worktrees/remotes
  V4_FROZEN_ARTIFACT_CHECKSUMS.json  protected-ref tree hashes + release
                                     checksum files
  V4_BASELINE_TEST_MATRIX.json    per-directory collected test counts
  V4_MODULE_STATUS.json           rscs2_core/rgcs_core/rscs_core module map

The scanner never writes outside docs/v4/baseline/ and never mutates
repository state. Local test evidence is labeled LOCAL; hosted CI
evidence must come from the GitHub API and is recorded separately.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "docs" / "v4" / "baseline"

AUTHORITY_COMMITS = ["9165594", "7962817", "3fcb0d7", "715486b"]
PROTECTED_TAGS = ["v2.0.0", "v3.0.0", "v3.0.1", "v4.0.0",
                  "v4.0.0-alpha", "v4.0.0-rc1"]


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True,
                          text=True, cwd=REPO, check=True).stdout.strip()


def try_git(*args: str):
    try:
        return git(*args)
    except subprocess.CalledProcessError as e:
        return f"ERROR: {e.stderr.strip()[:200]}"


def repo_inventory() -> dict:
    dirty = [ln for ln in git("status", "--porcelain").splitlines() if ln]
    return {
        "head": git("rev-parse", "HEAD"),
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "remotes": git("remote", "-v").splitlines(),
        "worktrees": git("worktree", "list").splitlines(),
        "tags": sorted(git("tag", "--list").splitlines()),
        "dirty_files": sorted(dirty),
        "authority_commits": {
            c: try_git("cat-file", "-t", c) for c in AUTHORITY_COMMITS},
        "protected_tags_present": {
            t: try_git("rev-parse", f"{t}^{{commit}}")
            for t in PROTECTED_TAGS},
    }


def frozen_checksums() -> dict:
    out: dict = {"tag_tree_hashes": {}, "archive_v2_tree": None,
                 "release_checksum_files": {}}
    for t in PROTECTED_TAGS:
        out["tag_tree_hashes"][t] = try_git(
            "rev-parse", f"{t}^{{tree}}")
    out["archive_v2_tree"] = try_git(
        "rev-parse", "HEAD:archive/v2.0.0")
    for p in sorted(REPO.glob("release/**/SHA256SUMS*")):
        rel = p.relative_to(REPO).as_posix()
        out["release_checksum_files"][rel] = hashlib.sha256(
            p.read_bytes()).hexdigest()
    pb = REPO / "proof_bundle_110mm" / "SHA256SUMS.txt"
    if pb.exists():
        out["proof_bundle_sha256sums_digest"] = hashlib.sha256(
            pb.read_bytes()).hexdigest()
    return out


def test_matrix() -> dict:
    out = {}
    for d in sorted((REPO / "tests").iterdir()):
        if not d.is_dir():
            continue
        files = sorted(p.name for p in d.glob("test_*.py"))
        n_tests = 0
        for p in d.glob("test_*.py"):
            n_tests += sum(1 for ln in p.read_text(
                encoding="utf-8", errors="ignore").splitlines()
                if ln.startswith("def test_")
                or ln.lstrip().startswith("def test_"))
        out[d.name] = {"files": files, "test_functions": n_tests}
    out["_note"] = ("static function count; authoritative counts come "
                    "from pytest runs (LOCAL evidence only)")
    return out


def module_status() -> dict:
    """Heuristic implementation map: implemented (has tests referencing
    it), interface_only markers, or absent."""
    mods = {}
    for pkg in ("rscs2_core", "rgcs_core", "rscs_core"):
        pdir = REPO / pkg
        if not pdir.exists():
            continue
        for p in sorted(pdir.rglob("*.py")):
            rel = p.relative_to(REPO).as_posix()
            txt = p.read_text(encoding="utf-8", errors="ignore")
            markers = []
            low = txt.lower()
            if "interface_tested" in low or "interface_only" in low:
                markers.append("interface_only_markers")
            if "notimplementederror" in low:
                markers.append("raises_notimplemented")
            if "todo" in low or "fixme" in low:
                markers.append("todo_markers")
            mods[rel] = {
                "bytes": p.stat().st_size,
                "def_count": txt.count("\ndef ") + txt.count("\nclass "),
                "markers": markers,
            }
    return mods


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "V4_REPO_INVENTORY.json": repo_inventory(),
        "V4_FROZEN_ARTIFACT_CHECKSUMS.json": frozen_checksums(),
        "V4_BASELINE_TEST_MATRIX.json": test_matrix(),
        "V4_MODULE_STATUS.json": module_status(),
    }
    for name, obj in artifacts.items():
        (OUT / name).write_text(
            json.dumps(obj, indent=2, sort_keys=True) + "\n",
            encoding="utf-8")
        print(f"wrote {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
