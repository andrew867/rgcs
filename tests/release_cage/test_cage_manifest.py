"""MOD-008 manifest and SHA256SUMS -- the six spec tests.

Generated artifacts go to pytest tmp_path; nothing is written into
the repository by tests.
"""

from __future__ import annotations

import pathlib

from rgcs_workbench.public_cage import claim_firewall as CF
from rgcs_workbench.public_cage import manifest as MF

ROOT = pathlib.Path(__file__).resolve().parents[2]

CREATED_AT = "2026-08-05T00:00:00Z"


def _surface():
    return CF.cage_public_surface(ROOT)


def _manifest():
    return MF.build_manifest(
        ROOT, _surface(), release_id="RGCS_WORKBENCH_PUBLIC_RC1_CAGE",
        created_at=CREATED_AT)


def test_1_manifest_includes_every_public_file():
    manifest = _manifest()
    assert MF.validate_manifest(manifest, ROOT, _surface()) == []
    assert manifest["file_count"] == len(_surface())


def test_2_sha256sums_covers_every_artifact():
    manifest = _manifest()
    summed = {line.split("  ", 1)[1]
              for line in manifest["sha256sums"].splitlines()}
    assert summed == set(manifest["files"])


def test_3_claim_scan_hash_slot_exists_and_scan_is_clean():
    report = CF.firewall_report(CF.scan_paths(_surface()))
    assert report["verdict"] == "RELEASE_FILTER_CLEAN"
    manifest = MF.build_manifest(
        ROOT, _surface(), release_id="x", created_at=CREATED_AT,
        claim_scan_hash=MF.sha256_of_text(str(report)))
    assert manifest["claim_scan_hash"] != MF.PENDING


def test_4_validation_catches_missing_and_unknown_files():
    manifest = _manifest()
    extra = list(_surface()) + [ROOT / "pyproject.toml"]
    problems = MF.validate_manifest(manifest, ROOT, extra)
    assert any("missing from manifest" in p for p in problems)
    manifest["files"].append("ghost/not_real.md")
    manifest["file_count"] += 1
    problems = MF.validate_manifest(manifest, ROOT, _surface())
    assert any("unknown file" in p for p in problems)
    assert any("missing from SHA256SUMS" in p for p in problems)


def test_5_tampered_sums_are_detected():
    # Flip the first hex digit deterministically. The old form used
    # str.replace on whatever digit happened to be first, which was a
    # no-op when that digit was already "0" -- and the first digit
    # differs across platforms because checkout line endings change
    # the file hashes (caught on CI).
    manifest = _manifest()
    first = manifest["sha256sums"][0]
    swapped = "1" if first == "0" else "0"
    manifest["sha256sums"] = swapped + manifest["sha256sums"][1:]
    problems = MF.validate_manifest(manifest, ROOT, _surface())
    assert any("sha256sums_hash" in p for p in problems)


def test_6_release_files_are_written_and_reload_clean(tmp_path):
    manifest = _manifest()
    out = MF.write_release_files(ROOT, tmp_path / "release", manifest)
    sums = pathlib.Path(out["sha256sums"]).read_text(encoding="utf-8")
    assert sums == manifest["sha256sums"]
    import json
    reloaded = json.loads(pathlib.Path(out["manifest"]).read_text(
        encoding="utf-8"))
    assert MF.validate_manifest(reloaded, ROOT, _surface()) == []


def test_manifest_records_git_commit_and_branch():
    manifest = _manifest()
    assert manifest["commit"] and len(manifest["commit"]) >= 7
    assert manifest["branch"]
