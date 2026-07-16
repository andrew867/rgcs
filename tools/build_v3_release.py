#!/usr/bin/env python3
"""Build the v3 release package under release/ (Agent 11).

Artifacts:
  rgcs-v<VERSION>-source.zip            git archive of the release commit
  rgcs_v3_manuscripts.zip           4 PDFs + TeX/tables/figures/checksums
  rgcs_v3_sample_experiments.zip    schemas + templates + sample data
  SHA256SUMS.txt                    checksums of everything above
  PROVENANCE.json                   commit, environment, test evidence
  RELEASE_NOTES.md                  written separately (hashed here)

Usage: python tools/build_v3_release.py <release_commit_sha>
"""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REL = REPO / "release"
VERSION = "3.0.1"


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _zip_tree(dest: Path, pairs: list[tuple[str, Path]]) -> None:
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
        for arcname, path in sorted(pairs):
            zf.write(path, arcname)
    print(f"built {dest.name} ({dest.stat().st_size} bytes, "
          f"{len(pairs)} members)")


def main() -> int:
    commit = sys.argv[1]
    REL.mkdir(exist_ok=True)

    # 1. source archive from the release commit (POSIX names by design)
    src = REL / f"rgcs-v{VERSION}-source.zip"
    subprocess.run(["git", "archive", "--format=zip", "-o", str(src),
                    commit], cwd=REPO, check=True)
    print(f"built {src.name} ({src.stat().st_size} bytes)")

    # 2. manuscript bundle
    pairs: list[tuple[str, Path]] = []
    for name in ("rscs_foundations", "rgcs_crystal_application",
                 "software_hardware_plan", "historical_source_companion"):
        d = REPO / "manuscripts" / name
        for p in list(d.glob(f"{name}.*")) + list(
                (d / "tables").glob("*.tex")) + list(
                (d / "figures").glob("*.pdf")) + [
                d / "CHECKSUMS.json", d / "VERSIONS.json", d / "BUILD.md"]:
            if p.exists() and p.suffix not in (".aux", ".log", ".out",
                                               ".bbl", ".blg", ".toc",
                                               ".fls", ".xdv"):
                pairs.append((f"{name}/{p.relative_to(d).as_posix()}", p))
    for shared in (REPO / "manuscripts" / "common").glob("*"):
        pairs.append((f"common/{shared.name}", shared))
    _zip_tree(REL / "rgcs_v3_manuscripts.zip", pairs)

    # 3. sample experiments bundle (schemas + validated examples + samples)
    pairs = []
    for sub in ("schemas", "templates", "sample_data", "controls"):
        base = REPO / "experiments" / sub
        if base.exists():
            for p in base.rglob("*"):
                if p.is_file() and not p.name.startswith("."):
                    pairs.append(
                        (p.relative_to(REPO / "experiments").as_posix(), p))
    _zip_tree(REL / "rgcs_v3_sample_experiments.zip", pairs)

    # 4. provenance
    def _v(cmd: list[str]) -> str:
        try:
            out = subprocess.run(cmd, capture_output=True, text=True,
                                 timeout=60).stdout.splitlines()
            return out[0].strip() if out else "unknown"
        except Exception:
            return "unavailable"

    import numpy
    prov = {
        "version": VERSION,
        "release_commit": commit,
        "baseline": {"tag": "v2.0.0", "commit": "f9fd2c2",
                     "frozen_path": "archive/v2.0.0/"},
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "numpy": numpy.__version__,
            "xelatex": _v(["xelatex", "--version"]),
        },
        "test_evidence": {
            "suite": "377 portable tests pass on every platform; the "
                     "golden byte-equality test is scoped to the archived "
                     "v2 build environment (NR3-001/D-V3-04) and replaced "
                     "everywhere else by a tolerance-aware regeneration "
                     "test",
            "hosted_ci": "GitHub Actions: ubuntu/windows/macos x "
                         "Python 3.11/3.13 portable matrix + pinned "
                         "ubuntu reference job, all green",
            "schema_validation": "12/12 targets OK",
            "cep_battery": "all_ok",
            "generated_artifacts": "byte-stable across regenerations",
        },
        "registries": {"rgcs_m": "61 ids, schema 1, frozen",
                       "rscs": "40 ids (17 coordinates + 23 operators)"},
        "qa": {"report": "docs/QA_REPORT_V3.md",
               "defects_fixed": ["D-V3-01", "D-V3-02", "D-V3-03",
                                 "D-V3-04"],
               "open_non_blocking": ["QA-D-19 (v2 tooling, frozen)"]},
    }
    (REL / "PROVENANCE.json").write_text(
        json.dumps(prov, indent=2, sort_keys=True), encoding="utf-8")
    print("built PROVENANCE.json")

    # 5. checksums over everything in release/ (incl. RELEASE_NOTES.md if
    # already written)
    sums = []
    for p in sorted(REL.iterdir()):
        if p.is_file() and p.name != "SHA256SUMS.txt":
            sums.append(f"{_sha(p)}  {p.name}")
    (REL / "SHA256SUMS.txt").write_text("\n".join(sums) + "\n",
                                        encoding="utf-8")
    print("built SHA256SUMS.txt")
    for line in sums:
        print("  " + line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
