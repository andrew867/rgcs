"""Build provenance for the frozen app (v4.5.2).

A single source of truth for "which source produced this binary". At
freeze time the build tool writes ``_build_stamp.json`` (version, git
commit, source hash, build time) and PyInstaller bundles it; the frozen
app reads it for ``--build-info``. From a source checkout the same
values are computed live.

``compute_source_hash`` is the anti-stale mechanism: it hashes every
packaged ``.py`` file, so the build tool can refuse to package a
``dist/`` whose embedded hash no longer matches the working tree (the
exact failure that shipped a stale binary in v4.5.0/v4.5.1).
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

STAMP_NAME = "_build_stamp.json"

# python packages whose source defines application behaviour; a change
# to any of these must invalidate a previously frozen dist.
#: Packages covered by the anti-stale source hash.
#:
#: R8-D-006: this tuple stopped at ``r4`` and silently omitted r6, r7
#: and r8 -- 30 modules across three programme generations. The
#: consequence was that v4.9.0, v5.0.0 and v5.1.0 all carried a source
#: hash that did not change when their own new code changed, so a
#: stale ``dist/`` from the R4 era would have passed the freshness
#: check. That is precisely the failure the v4.5.2 mechanism was built
#: to prevent, reintroduced by scope drift rather than by a code bug.
#:
#: A test now asserts every top-level package directory containing an
#: ``__init__.py`` is listed here, so the next programme cannot repeat
#: it by omission.
#: R10-D-001: ``r10`` arrived during the R10 programme and was added to
#: neither this tuple nor the packaging ``include`` list -- the R8-D-006
#: and R9-D-004 defects starting over, one generation later, for the
#: same reason (a new research package, added to the tree, not added to
#: the two lists that govern hashing and distribution). The guards
#: caught it this time instead of a release doing so.
SOURCE_ROOTS = ("rgcs_desktop", "rgcs_workbench", "rgcs_core",
                "rscs_core", "rscs2_core", "fkey_instrument",
                "resonator_platform", "cspc", "pmwr", "r3", "r4",
                "r6", "r7", "r8", "r9", "r10", "r11",
                # Q02 / R10-D-004: the inverse of R8-D-006. This lane
                # ships in the wheel and sdist and is importable after
                # pip install, but was outside the freshness hash, so a
                # change to it would not invalidate a frozen dist. The
                # asymmetry was defensible (it is not bundled into the
                # frozen exe) but implicit, and the operator's standing
                # decision is that a publicly shipped package must be
                # hashed unless it is removed from every public
                # artifact. It ships, so it is hashed.
                "consciousness_lane")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def compute_source_hash(repo: Path | None = None) -> str:
    """Deterministic sha256 over every packaged .py file (path +
    content), sorted by repo-relative POSIX path. Excludes caches.

    Line endings are normalised to LF before hashing. Git checkouts on
    Windows (``core.autocrlf=true``) re-materialise files with CRLF, so
    a raw-byte hash reports a spurious mismatch for logically identical
    source after a clone or branch switch — which would fail
    ``--build-info`` verification for a genuinely fresh binary. The
    hash must track logical source content, not checkout line-ending
    policy. (It stays fail-safe either way: a real source change always
    changes the hash.)
    """
    repo = repo or repo_root()
    h = hashlib.sha256()
    for root in sorted(SOURCE_ROOTS):
        base = repo / root
        if not base.exists():
            continue
        for p in sorted(base.rglob("*.py"),
                        key=lambda q: q.relative_to(repo).as_posix()):
            if "__pycache__" in p.parts:
                continue
            rel = p.relative_to(repo).as_posix()
            h.update(rel.encode("utf-8"))
            h.update(b"\0")
            h.update(p.read_bytes().replace(b"\r\n", b"\n"))
            h.update(b"\0")
    return h.hexdigest()


def _pyproject_version(repo: Path) -> str:
    import re
    m = re.search(r'^version = "([^"]+)"',
                  (repo / "pyproject.toml").read_text(encoding="utf-8"),
                  re.M)
    return m.group(1) if m else "0.0.0"


def _git_commit(repo: Path) -> str:
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo,
                           capture_output=True, text=True, timeout=10)
        return r.stdout.strip() or "unknown"
    except Exception:  # noqa: BLE001
        return "unknown"


def _frozen_stamp_path() -> Path | None:
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base) / STAMP_NAME
    return None


def build_info() -> dict:
    """Return the build provenance dict. Frozen: read the bundled stamp;
    source: compute live."""
    if getattr(sys, "frozen", False):
        stamp = _frozen_stamp_path()
        if stamp and stamp.exists():
            data = json.loads(stamp.read_text(encoding="utf-8"))
            data["frozen"] = True
            return data
        return {"frozen": True, "error": "no _build_stamp.json bundled"}
    repo = repo_root()
    return {"frozen": False,
            "version": _pyproject_version(repo),
            "git_commit": _git_commit(repo),
            "source_hash": compute_source_hash(repo),
            "built_at": None}


def write_stamp(repo: Path, version: str, built_at: str | None) -> dict:
    """Write ``_build_stamp.json`` at the repo root for the freeze to
    bundle. Returns the stamp dict."""
    stamp = {"version": version,
             "git_commit": _git_commit(repo),
             "source_hash": compute_source_hash(repo),
             "built_at": built_at}
    (repo / STAMP_NAME).write_text(
        json.dumps(stamp, indent=2) + "\n", encoding="utf-8")
    return stamp
