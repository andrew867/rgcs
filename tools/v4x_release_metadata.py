"""Phase 7: one source of truth for release metadata.

v4.2.0 shipped release notes saying "expect: 681 passed" while the
test-report asset built from the same commit said 682 (V4X-D-004). The
cause is structural: the count lived in prose, maintained by hand, in
four different files.

This tool derives the count from an ACTUAL pytest run (or from the
built test-report asset) and writes docs/v4/RELEASE_METADATA.json. The
guard test then verifies every document agrees with that file, so a
stale count fails the build instead of shipping.

    python tools/v4x_release_metadata.py --refresh   # run pytest
    python tools/v4x_release_metadata.py             # verify only
"""

from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
META = ROOT / "docs" / "v4" / "RELEASE_METADATA.json"
DESELECT = ("tests/regression/test_generator_determinism.py::"
            "test_generator_deterministic")

# (path, regex with one capture group for the count)
COUNT_SITES = [
    ("README.md", r"expect:\s*(\d+)\s+passed"),
    ("README.md", r"\*\*\s*(\d+)\s+tests\s+passed"),
    # Track the CURRENT release's notes only. Superseded release notes
    # are published assets and are deliberately frozen at the count
    # that was true when they shipped -- v5.1.0's notes still say 2420
    # because 2420 was correct at v5.1.0. Repoint this line at each new
    # release rather than rewriting history to satisfy the guard.
    ("docs/v52/RELEASE_NOTES_V5_9_0.md", r"expect:\s*(\d+)\s+passed"),
    ("CHANGELOG.md", r"Tests:\s*(\d+)\s+passing"),
]


def _pyexe() -> str:
    for c in (ROOT / ".venv/Scripts/python.exe",
              ROOT / ".venv/bin/python"):
        if c.exists():
            return str(c)
    return sys.executable


def measure() -> dict:
    """Run the real suite and parse the summary line."""
    cmd = [_pyexe(), "-m", "pytest", "-q", "--deselect", DESELECT]
    run = subprocess.run(cmd, capture_output=True, text=True,
                         cwd=ROOT, timeout=3600)
    tail = run.stdout.strip().splitlines()[-1] if run.stdout else ""
    m = re.search(r"(\d+)\s+passed", tail)
    if not m:
        raise SystemExit(f"cannot parse pytest summary: {tail!r}")
    passed = int(m.group(1))
    d = re.search(r"(\d+)\s+deselected", tail)
    return {"tests_passed": passed,
            "tests_deselected": int(d.group(1)) if d else 0,
            "summary_line": tail,
            "deselect_node": DESELECT,
            "deselect_reason":
                "byte-equality test requires the archived v2.0.0 build "
                "environment; hosted CI deselects exactly this node id "
                "(policy D-V3-04)",
            "exit_code": run.returncode}


def load() -> dict:
    if not META.exists():
        raise SystemExit("RELEASE_METADATA.json missing; run with "
                         "--refresh")
    return json.loads(META.read_text(encoding="utf-8"))


def verify() -> dict:
    meta = load()
    want = meta["tests_passed"]
    problems = []
    checked = 0
    for rel, pattern in COUNT_SITES:
        p = ROOT / rel
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        matches = list(re.finditer(pattern, text))
        if rel == "CHANGELOG.md":
            # the changelog is chronological: only the NEWEST entry's
            # count is current-facing; older entries carry their own
            # historical counts correctly and must not be "fixed"
            # (a blanket replace once falsified the 4.2.1 history —
            # caught and reverted; this scoping prevents a repeat)
            matches = matches[:1]
        for m in matches:
            checked += 1
            got = int(m.group(1))
            if got != want:
                problems.append(
                    f"{rel}: says {got}, actual is {want}")
    return {"expected": want, "sites_checked": checked,
            "problems": problems, "agree": not problems}


def main() -> int:
    if "--refresh" in sys.argv:
        meta = measure()
        META.write_text(json.dumps(meta, indent=2) + "\n",
                        encoding="utf-8")
        print(f"measured: {meta['tests_passed']} passed, "
              f"{meta['tests_deselected']} deselected")
    rep = verify()
    print(f"metadata: expected {rep['expected']} across "
          f"{rep['sites_checked']} documented sites")
    for p in rep["problems"]:
        print("  MISMATCH:", p)
    return 0 if rep["agree"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
