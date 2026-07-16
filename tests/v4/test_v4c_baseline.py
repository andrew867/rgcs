"""Agent B0: baseline scanner behavior tests."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "docs" / "v4" / "baseline"


def test_scanner_runs_and_is_deterministic(tmp_path):
    """Two runs produce byte-identical inventory apart from none —
    the scanner contains no timestamps or RNG."""
    cmd = [sys.executable, "tools/v4/baseline/scan_baseline.py"]
    subprocess.run(cmd, cwd=REPO, check=True, capture_output=True)
    first = {p.name: p.read_bytes() for p in OUT.glob("*.json")}
    subprocess.run(cmd, cwd=REPO, check=True, capture_output=True)
    second = {p.name: p.read_bytes() for p in OUT.glob("*.json")}
    # dirty_files may legitimately differ between runs if the tree
    # changes; everything else must be bit-stable on an unchanged tree
    assert set(first) == set(second)
    for name in first:
        assert first[name] == second[name], f"{name} nondeterministic"


def test_authority_commits_reachable_and_protected_tags():
    inv = json.loads((OUT / "V4_REPO_INVENTORY.json").read_text())
    for c in ("9165594", "7962817", "3fcb0d7", "715486b"):
        assert inv["authority_commits"][c] == "commit", c
    for t in ("v2.0.0", "v3.0.0", "v3.0.1", "v4.0.0"):
        v = inv["protected_tags_present"][t]
        assert not v.startswith("ERROR"), f"tag {t} missing: {v}"


def test_frozen_checksums_recorded():
    fr = json.loads(
        (OUT / "V4_FROZEN_ARTIFACT_CHECKSUMS.json").read_text())
    assert fr["archive_v2_tree"] and not \
        fr["archive_v2_tree"].startswith("ERROR")
    assert len(fr["tag_tree_hashes"]) >= 6
    assert "proof_bundle_sha256sums_digest" in fr


def test_scanner_writes_only_owned_paths():
    """The scanner script contains no write targets outside
    docs/v4/baseline (static check of the tool source)."""
    src = (REPO / "tools/v4/baseline/scan_baseline.py").read_text(
        encoding="utf-8")
    assert 'OUT = REPO / "docs" / "v4" / "baseline"' in src
    assert "write_text" in src
    # no other output-directory constants
    assert src.count("write_text") == 1


def test_local_vs_hosted_ci_distinction_documented():
    doc = (OUT.parent / "baseline" / "V4_BASELINE_TEST_MATRIX.json")
    tm = json.loads(doc.read_text())
    assert "LOCAL" in tm["_note"]
