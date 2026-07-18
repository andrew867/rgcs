"""A00: capture the v4.6 programme baseline (RELEASE_EVIDENCE).

Records the state the programme starts from so later claims can be
traced to a reproducible checkout: commit, version, tags, branch,
declared test command, source digest, and — explicitly — whether the
frozen Windows binary is fresh or stale.

The binary-freshness field exists because v4.5.0/v4.5.1 shipped a
stale PyInstaller executable (built before the code it claimed to
contain). The baseline records the honest answer; it does not fix
unrelated packaging work.

    python tools/cspc_baseline.py            # write + print
    python tools/cspc_baseline.py --check    # verify, exit 1 on drift
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "docs" / "v4" / "cspc" / "BASELINE_V4_6.json"

TEST_COMMAND = ("python -m pytest -q --deselect "
                "tests/regression/test_generator_determinism.py::"
                "test_generator_deterministic")


def _git(*args: str) -> str:
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                       text=True, timeout=60)
    return r.stdout.strip()


def _version() -> str:
    import re
    m = re.search(r'^version = "([^"]+)"',
                  (ROOT / "pyproject.toml").read_text(encoding="utf-8"),
                  re.M)
    return m.group(1) if m else "unknown"


def binary_freshness() -> dict:
    """Is a frozen dist/ present, and does it match current source?

    Reuses the v4.5.2 anti-stale mechanism rather than inventing a
    second one."""
    from rgcs_desktop.build_meta import compute_source_hash
    stamp = ROOT / "dist" / "RGCSWorkbench" / "_internal" / "_build_stamp.json"
    cur = compute_source_hash(ROOT)
    if not stamp.exists():
        return {"frozen_build_present": False,
                "state": "ABSENT",
                "current_source_hash": cur,
                "note": "no frozen build in this checkout; the "
                        "programme does not require one until "
                        "packaging (A35)"}
    d = json.loads(stamp.read_text(encoding="utf-8"))
    fresh = d.get("source_hash") == cur
    return {"frozen_build_present": True,
            "state": "FRESH" if fresh else "STALE",
            "frozen_source_hash": d.get("source_hash"),
            "current_source_hash": cur,
            "frozen_git_commit": d.get("git_commit"),
            "frozen_version": d.get("version"),
            "note": "FRESH means the frozen exe was built from this "
                    "exact source (v4.5.2 guard)."}


def capture() -> dict:
    from rgcs_desktop.build_meta import compute_source_hash
    meta_path = ROOT / "docs" / "v4" / "RELEASE_METADATA.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) \
        if meta_path.exists() else {}
    return {
        "programme": "RGCS-V4.6-CSCP",
        "evidence_class": "RELEASE_EVIDENCE",
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "head_commit": _git("rev-parse", "HEAD"),
        "base_commit": _git("rev-parse", "origin/main"),
        "package_version": _version(),
        "latest_release_tag": _git("describe", "--tags", "--abbrev=0"),
        "frozen_tags": sorted(t for t in _git("tag").split()
                              if t and "-rc" not in t),
        "test_command": TEST_COMMAND,
        "baseline_tests_passed": meta.get("tests_passed"),
        "baseline_tests_deselected": meta.get("tests_deselected"),
        "source_hash": compute_source_hash(ROOT),
        "binary_freshness": binary_freshness(),
        "physical_status": "UNTESTED",
        "claim_boundary":
            "Baseline is RELEASE_EVIDENCE about software state only. "
            "It asserts nothing about any physical hypothesis.",
    }


def main() -> int:
    data = capture()
    if "--check" in sys.argv:
        if not OUT.exists():
            print("baseline missing; run without --check")
            return 1
        old = json.loads(OUT.read_text(encoding="utf-8"))
        drift = [k for k in ("package_version", "source_hash")
                 if old.get(k) != data.get(k)]
        print(f"baseline drift: {drift or 'none'}")
        return 1 if drift else 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in data.items()
                      if k != "frozen_tags"}, indent=2))
    print(f"\nwrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
