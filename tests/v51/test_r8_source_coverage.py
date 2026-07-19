"""R8-D-006 — the anti-stale hash must cover every shipped package.

SOURCE_ROOTS stopped at r4 and omitted r6, r7 and r8, so three
releases carried a source hash that did not respond to their own
code. This file makes that impossible to repeat by omission.
"""

from __future__ import annotations

import pathlib

from rgcs_desktop.build_meta import SOURCE_ROOTS, compute_source_hash

ROOT = pathlib.Path(__file__).resolve().parents[2]

#: Directories that are deliberately not part of the shipped app.
EXCLUDED = {
    "tests", "docs", "tools", "packaging", "archive", "internal-docs",
    "manuscript", "manuscripts", "evidence", "experiments", "release",
    "embedded", "firmware", "references", "schemas", "papers",
    "consciousness_lane",          # quarantined lane, not shipped
    "demo_out", "proof_bundle_110mm", "source_claims",
    # provenance registry, imported by tests only and not shipped in
    # the desktop app; surfaced when the namespace-package hole was
    # closed (R9-D-003)
    "sources",
}


def _package_dirs() -> set[str]:
    """Every top-level directory holding importable source.

    R9-D-003: this used to require ``__init__.py``, which left a hole
    exactly the shape of the defect it was written to prevent. ``r9``
    imports fine as a namespace package (PEP 420) with no
    ``__init__.py``, so it was invisible both to ``SOURCE_ROOTS`` and
    to this guard. A directory of ``.py`` files that Python will
    happily import is a package for hashing purposes whether or not it
    declares itself one.
    """
    out = set()
    for p in ROOT.iterdir():
        if not p.is_dir() or p.name.startswith((".", "_")):
            continue
        if p.name in EXCLUDED or p.name.endswith(".egg-info"):
            continue
        if any(q.name != "__init__.py" and q.suffix == ".py"
               for q in p.rglob("*.py")
               if "__pycache__" not in q.parts):
            out.add(p.name)
    return out


def test_every_package_is_covered_by_the_source_hash():
    missing = _package_dirs() - set(SOURCE_ROOTS)
    assert not missing, (
        f"packages not covered by SOURCE_ROOTS: {sorted(missing)}. "
        f"A package outside the hash means a stale dist/ can pass the "
        f"freshness check after that package changes.")


def test_the_three_previously_missing_packages_are_present():
    for pkg in ("r6", "r7", "r8"):
        assert pkg in SOURCE_ROOTS


def test_r9_is_covered():
    """R9-D-003: r9 shipped as a namespace package with no
    __init__.py, so the original form of this guard could not see it.
    """
    assert "r9" in SOURCE_ROOTS


def test_guard_sees_packages_without_an_init_file():
    """The guard must not depend on __init__.py, or it reopens the
    hole it exists to close."""
    import tempfile
    import pathlib as _pl
    with tempfile.TemporaryDirectory() as td:
        d = _pl.Path(td) / "ghostpkg"
        d.mkdir()
        (d / "mod.py").write_text("x = 1\n")
        assert not (d / "__init__.py").exists()
        found = any(q.suffix == ".py" and q.name != "__init__.py"
                    for q in d.rglob("*.py"))
        assert found, ("the detection rule must treat a directory of "
                       ".py files as a package regardless of "
                       "__init__.py")


def test_source_hash_is_stable_and_well_formed():
    a, b = compute_source_hash(), compute_source_hash()
    assert a == b
    assert len(a) == 64


def test_listed_roots_that_exist_are_real_packages():
    for root in SOURCE_ROOTS:
        p = ROOT / root
        if p.exists():
            assert p.is_dir()
