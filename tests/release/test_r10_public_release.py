"""Release-control tests for the local R10 public candidate."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path

from tools import r10_public_release as release


REQUIRED_TERMS = (
    "crabwood",
    "cnt",
    "carbon nanotube",
    "ascii",
    "plaintext",
    "message decode",
    "decoded message",
    "glyph message",
    "private comms",
    "deuterium",
    "tritium",
    "heavy water",
    "neutron",
    "fusion",
    "transmutation",
    "helium generation",
    "reactor",
    "UHV gas fill",
)


def blob(path: str, content: str = "") -> release.BlobRecord:
    return release.BlobRecord(path, "test", content.encode("utf-8"))


def test_normalize_preserves_dotfiles() -> None:
    assert release.normalize(".gitattributes") == ".gitattributes"
    assert release.normalize("./docs/file.md") == "docs/file.md"
    assert release.normalize(r".\docs\file.md") == "docs/file.md"


def test_release_directory_replacement_handles_readonly_entries(
    tmp_path: Path,
) -> None:
    target = tmp_path / "dist" / "releases" / release.RC_NAME
    nested = target / "source" / "fixtures"
    nested.mkdir(parents=True)
    payload = nested / "receipt.json"
    payload.write_text("{}\n", encoding="utf-8")
    os.chmod(payload, stat.S_IREAD)
    os.chmod(nested, stat.S_IREAD)

    release._replace_release_directory(tmp_path, target)

    assert target.is_dir()
    assert list(target.iterdir()) == []


def test_every_required_term_is_an_exclusion() -> None:
    for term in REQUIRED_TERMS:
        row = release.classify_blob(blob("docs/workbench/public.md", term))
        assert row["classification"] == release.CLASS_PRIVATE, term
        assert row["content_excluded_terms"], term


def test_exclusion_beats_explicit_public_inclusion() -> None:
    row = release.classify_blob(
        blob("rgcs_coordinate/codecs/public.py", "decoded message")
    )
    assert row["public_rule"]
    assert row["classification"] == release.CLASS_PRIVATE


def test_unmatched_goes_to_review() -> None:
    row = release.classify_blob(blob("misc/unmatched.bin", "ordinary data"))
    assert row["classification"] == release.CLASS_REVIEW


def test_archive_and_private_lane_prefixes_never_publish() -> None:
    assert (
        release.classify_blob(blob("archive/old/public-map.md"))["classification"]
        == release.CLASS_QUARANTINE
    )
    assert (
        release.classify_blob(blob("r1011/public-looking-codec.py"))["classification"]
        == release.CLASS_QUARANTINE
    )


def test_public_coordinate_file_requires_no_exclusion_hit() -> None:
    row = release.classify_blob(
        blob("rgcs_coordinate/codecs/public.py", "structural vector parser")
    )
    assert row["classification"] == release.CLASS_PUBLIC


def test_public_workbench_hub_and_lab_examples_are_explicit() -> None:
    for path in (
        "workbench/index.html",
        "static/hub/index.html",
        "examples/rgcs_lab/claim_yellow.json",
    ):
        row = release.classify_blob(blob(path, "bounded public artifact"))
        assert row["classification"] == release.CLASS_PUBLIC, path


def test_mixed_r1073_branch_is_quarantined() -> None:
    classification = release.classify_branch(
        "claude/rgcs-r10-62-terminal-vertex-4aca40",
        ahead=37,
        subject="R10.73",
    )
    assert classification.value == release.CLASS_QUARANTINE


def test_pinned_engineering_commits_are_the_only_default_overlays() -> None:
    assert release.SAFE_OVERLAY_COMMITS == (
        "35312e29c8db1b164975991b1df07a8c8653cd47",
        "4e762851d083c31238f582b4b29497943a1a0407",
        "a10a3bb11a1c05fd6f7676a97ac12b3417d877ec",
        "710e5947c80ea7a2299dc0a40fd63a4262891e39",
        "dfab636c4bf5e165103d7ebc72a693ef828b9987",
    )


def test_generated_report_has_no_public_exclusion_leak() -> None:
    path = Path("docs/release/r10_release_filter_report.json")
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["result"] == "PASS"
    assert report["counts"]["excluded_term_public_leaks"] == 0


def test_public_package_registry_pins_authority_and_holds() -> None:
    from rgcs_desktop.build_meta import SOURCE_ROOTS

    registry = json.loads(
        Path("docs/release/r10_public_package_registry.json").read_text(
            encoding="utf-8"
        )
    )
    commits = registry["source_commits"]
    assert commits["r10_73_authority"] == (
        "710e5947c80ea7a2299dc0a40fd63a4262891e39"
    )
    assert commits["r10_74_source"] == (
        "dfab636c4bf5e165103d7ebc72a693ef828b9987"
    )
    assert set(registry["source_roots"]).issubset(SOURCE_ROOTS)
    assert registry["authority"]["seed_status"] == "NOT_AUTHORITY"
    assert registry["ardk"]["fabrication_readiness"] == "REFUSED"
    assert registry["ardk"]["publication_hold"] is True
    assert registry["release_resolution"]["ardk_fabrication_hold"] == (
        "REMAINS_ASSERTED"
    )


def test_registered_proof_packages_and_hold_exist() -> None:
    registry = json.loads(
        Path("docs/release/r10_public_package_registry.json").read_text(
            encoding="utf-8"
        )
    )
    assert all(Path(path).is_dir() for path in registry["proof_packages"].values())
    assert Path(registry["ardk"]["publication_hold_path"]).is_file()
    seed_files = list(Path(registry["authority"]["seed_root"]).iterdir())
    assert seed_files
    assert all("NOT_AUTHORITY" in path.name for path in seed_files)


def test_performance_path_modules_remain_review_only() -> None:
    for path in (
        "rgcs_phyrll_v06/resonance.py",
        "rgcs_phyrll_v07/force_boundary.py",
        "rgcs_phyrll_v07/resonator.py",
    ):
        row = release.classify_blob(blob(path, "bounded implementation"))
        assert row["classification"] == release.CLASS_REVIEW


def test_namespace_audit_detects_wall_power_path(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "bad.py").write_text(
        "def ring_power_from_wall(): return 1\n"
        "def candidate_force(): return ring_power_from_wall()\n",
        encoding="utf-8",
    )
    audit = release._namespace_and_power_audit(source)
    assert audit["force_thrust_namespace_leak_count"] == 1
    assert audit["wall_power_path_count"] == 1


def test_namespace_audit_allows_explicit_firewall(tmp_path: Path) -> None:
    path = tmp_path / "rgcs_ardk" / "reports" / "firewall.py"
    path.parent.mkdir(parents=True)
    path.write_text(
        "def ring_power_from_wall(): return 1\n"
        "def candidate_force(): return ring_power_from_wall()\n",
        encoding="utf-8",
    )
    audit = release._namespace_and_power_audit(tmp_path)
    assert audit["force_thrust_namespace_leak_count"] == 0
    assert audit["wall_power_path_count"] == 0
