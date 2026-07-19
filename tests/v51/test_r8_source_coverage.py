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
}


def _package_dirs() -> set[str]:
    out = set()
    for p in ROOT.iterdir():
        if not p.is_dir() or p.name.startswith((".", "_")):
            continue
        if p.name in EXCLUDED or p.name.endswith(".egg-info"):
            continue
        if (p / "__init__.py").exists():
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


def test_source_hash_is_stable_and_well_formed():
    a, b = compute_source_hash(), compute_source_hash()
    assert a == b
    assert len(a) == 64


def test_listed_roots_that_exist_are_real_packages():
    for root in SOURCE_ROOTS:
        p = ROOT / root
        if p.exists():
            assert p.is_dir()
