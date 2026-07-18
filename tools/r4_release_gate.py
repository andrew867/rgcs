"""R04/R65 — the no-post-tag-sync release gate.

v4.6, v4.7.0 and v4.7.1 each needed a commit AFTER the tag to sync the
committed workbook and checksum manifest with what was actually
published. That means the tagged tree was never quite the released
tree. R4 forbids it: the tag must already contain every release-owned
artifact.

This gate is run BEFORE tagging and refuses if any committed
release-owned artifact is stale:

- ``release/v45/RGCS_Master_Evidence_Workbook.xlsx`` must byte-match a
  freshly generated public workbook;
- ``release/v45/SHA256SUMS.txt`` must list the Windows assets and the
  workbook with their current hashes.

**Why the committed manifest covers only the Windows assets and the
workbook.** The source archive is ``git archive`` of the tagged commit,
so it CONTAINS the manifest; a committed manifest listing the source
archive's own hash is circular and can never be satisfied. The complete
manifest (standard bundle + Windows assets) is generated at publish
time and uploaded as a release asset — an upload is not repository
content, so it needs no commit and breaks no gate.

    python tools/r4_release_gate.py            # verify (exit 1 on stale)
    python tools/r4_release_gate.py --write    # refresh, then verify
"""

from __future__ import annotations

import hashlib
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

V45 = ROOT / "release" / "v45"
WORKBOOK = V45 / "RGCS_Master_Evidence_Workbook.xlsx"
MANIFEST = V45 / "SHA256SUMS.txt"

#: Artifacts the tag must already contain, with the glob that finds the
#: built Windows assets for the current version.
WINDOWS_GLOBS = ("RGCS-Workbench-*-Windows-x64-portable.zip",
                 "RGCS-Workbench-*-Windows-x64-Setup.exe")


def _version() -> str:
    import re
    m = re.search(r'^version = "([^"]+)"',
                  (ROOT / "pyproject.toml").read_text(encoding="utf-8"),
                  re.M)
    return m.group(1) if m else "0.0.0"


def generate_workbook_bytes(version: str) -> bytes:
    """A freshly generated PUBLIC workbook, as bytes."""
    from rgcs_workbench.workbook import generate
    wb = generate(version=version, include_private=False)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def workbook_is_current(version: str) -> dict:
    """openpyxl embeds no timestamp we control, but zip member order and
    content are deterministic for a deterministic store, so a byte
    comparison is meaningful. Content equality is checked cell-wise as
    the authoritative test, with bytes reported for information."""
    if not WORKBOOK.exists():
        return {"ok": False, "reason": "committed workbook missing"}
    fresh = generate_workbook_bytes(version)
    on_disk = WORKBOOK.read_bytes()
    if _sha(fresh) == _sha(on_disk):
        return {"ok": True, "match": "bytes"}
    # fall back to cell-wise comparison (zip metadata can differ)
    import openpyxl
    a = openpyxl.load_workbook(io.BytesIO(fresh))
    b = openpyxl.load_workbook(io.BytesIO(on_disk))
    if a.sheetnames != b.sheetnames:
        return {"ok": False, "reason": "sheet set differs",
                "fresh_sheets": len(a.sheetnames),
                "committed_sheets": len(b.sheetnames)}
    for name in a.sheetnames:
        va = [[c.value for c in row] for row in a[name].iter_rows()]
        vb = [[c.value for c in row] for row in b[name].iter_rows()]
        if va != vb:
            return {"ok": False,
                    "reason": f"sheet {name!r} content differs"}
    return {"ok": True, "match": "cell-wise"}


def windows_assets(version: str) -> list:
    out = []
    for g in WINDOWS_GLOBS:
        out.extend(sorted(V45.glob(g.replace("*", version))))
    return out


def manifest_is_current(version: str) -> dict:
    if not MANIFEST.exists():
        return {"ok": False, "reason": "committed manifest missing"}
    listed = {}
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        if "  " in line:
            h, n = line.split("  ", 1)
            listed[n.strip()] = h
    required = windows_assets(version) + [WORKBOOK]
    problems = []
    for p in required:
        if p.name not in listed:
            problems.append(f"{p.name}: not listed")
        elif listed[p.name] != _sha(p.read_bytes()):
            problems.append(f"{p.name}: hash stale")
    if not windows_assets(version):
        problems.append(
            f"no Windows assets for {version} found in release/v45 — "
            "build them before the gate")
    return {"ok": not problems, "problems": problems,
            "listed": len(listed)}


def write_release_owned(version: str) -> dict:
    """Refresh the committed artifacts so the tag can contain them."""
    V45.mkdir(parents=True, exist_ok=True)
    WORKBOOK.write_bytes(generate_workbook_bytes(version))
    lines = []
    for p in windows_assets(version) + [WORKBOOK]:
        lines.append(f"{_sha(p.read_bytes())}  {p.name}")
    MANIFEST.write_text("\n".join(lines) + "\n", encoding="utf-8",
                        newline="\n")
    return {"workbook": str(WORKBOOK.relative_to(ROOT)),
            "manifest_entries": len(lines)}


def gate(version: str | None = None) -> dict:
    v = version or _version()
    wb = workbook_is_current(v)
    mf = manifest_is_current(v)
    ok = wb["ok"] and mf["ok"]
    return {
        "version": v,
        "workbook": wb,
        "manifest": mf,
        "ok": ok,
        "verdict": "TAG_MAY_PROCEED" if ok else "REFUSE_TAG",
        "rule": "the tag must already contain every release-owned "
                "artifact; no post-tag synchronization commit is "
                "permitted (R04/R65)",
    }


def main() -> int:
    v = _version()
    if "--write" in sys.argv:
        print("refreshed:", write_release_owned(v))
    rep = gate(v)
    print(f"release gate for v{rep['version']}: {rep['verdict']}")
    print(f"  workbook: {rep['workbook']}")
    print(f"  manifest: {rep['manifest']}")
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
