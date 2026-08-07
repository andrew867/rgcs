#!/usr/bin/env python3
"""Generate a release build manifest conforming to
schemas/release/release_manifest.schema.json.

Usage:
    python tools/packaging/release_manifest.py \
        --platform linux --build-command "..." \
        --smoke-command "rgcs-workbench --smoke-check" \
        --smoke-status passed \
        --artifact dist/rgcs-workbench/rgcs-workbench \
        --out release/release_manifest.json
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def git_commit() -> str:
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                             capture_output=True, text=True, timeout=10)
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return "unknown"


def build_manifest(platform: str, build_command: str, smoke_command: str,
                   smoke_status: str, artifacts: list[Path]) -> dict:
    return {
        "platform": platform,
        "commit": git_commit(),
        "build_command": build_command,
        "artifacts": [
            {"path": str(p.as_posix()), "sha256": sha256_file(p),
             "bytes": p.stat().st_size}
            for p in artifacts
        ],
        "smoke": {"status": smoke_status, "command": smoke_command},
        "generated_utc": _dt.datetime.now(_dt.timezone.utc)
                            .isoformat(timespec="seconds"),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--platform", required=True)
    ap.add_argument("--build-command", default="")
    ap.add_argument("--smoke-command", required=True)
    ap.add_argument("--smoke-status", required=True,
                    choices=["passed", "failed", "skipped"])
    ap.add_argument("--artifact", action="append", required=True,
                    type=Path, help="artifact path (repeatable)")
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args(argv)

    for p in args.artifact:
        if not p.is_file():
            print(f"missing artifact: {p}", file=sys.stderr)
            return 1
    manifest = build_manifest(args.platform, args.build_command,
                              args.smoke_command, args.smoke_status,
                              args.artifact)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, indent=2, sort_keys=True),
                        encoding="utf-8")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
