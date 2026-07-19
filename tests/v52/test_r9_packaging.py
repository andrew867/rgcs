"""R9-D-004 — the research packages must actually be installed.

``SOURCE_ROOTS`` governs the build-freshness hash. The packaging
``include`` list governs what ``pip install`` puts on disk. They are
different lists, and nothing was checking that they agreed.

They did not. v4.9.0, v5.0.0 and v5.1.0 all shipped an ``include``
list that stopped at ``r4``, so ``pip install rgcs`` from any of those
releases installed none of r6, r7 or r8 -- the headline research
packages of those very releases. Working from a clone hid it
completely, because ``pythonpath = ["."]`` makes the source tree
importable whether or not packaging agrees.

This file makes the two lists agree by test rather than by memory.
"""

from __future__ import annotations

import pathlib
import tomllib

import pytest

from rgcs_desktop.build_meta import SOURCE_ROOTS

# R9-D-020: this module imported setuptools at top level. setuptools is
# a build-system requirement, not a runtime or test one, and it is
# absent from CI's portable job -- so the whole module failed to
# collect on every platform while passing locally, where the venv
# happens to have it. A packaging guard that cannot run in CI is not a
# guard. Declared in the dev extra now, and imported defensively so a
# missing build tool skips this file instead of erroring collection.
find_packages = pytest.importorskip(
    "setuptools", reason="setuptools needed for package-discovery parity"
).find_packages

ROOT = pathlib.Path(__file__).resolve().parents[2]

#: Hashed for build freshness but deliberately not distributed.
NOT_DISTRIBUTED: set[str] = set()


def _include_patterns() -> list[str]:
    cfg = tomllib.loads((ROOT / "pyproject.toml").read_text())
    return cfg["tool"]["setuptools"]["packages"]["find"]["include"]


def _top_level_packages() -> set[str]:
    found = find_packages(where=str(ROOT), include=_include_patterns())
    return {p for p in found if "." not in p}


def test_every_hashed_package_is_also_distributed():
    """The defect, stated as an assertion."""
    expected = {r for r in SOURCE_ROOTS
                if (ROOT / r).exists()} - NOT_DISTRIBUTED
    missing = expected - _top_level_packages()
    assert not missing, (
        f"packages in SOURCE_ROOTS but not installed by pip: "
        f"{sorted(missing)}. A clone hides this because pythonpath "
        f"makes the tree importable; an install does not.")


def test_the_research_packages_are_installable():
    shipped = _top_level_packages()
    for pkg in ("r3", "r4", "r6", "r7", "r8", "r9"):
        assert pkg in shipped, f"{pkg} would not be installed"


def test_r9_is_importable():
    import r9
    assert set(r9.__all__) == {
        "betadecay", "carrier", "cwdecode", "octave", "vortex"}


def test_every_r9_module_named_in_all_exists():
    import importlib
    import r9
    for name in r9.__all__:
        importlib.import_module(f"r9.{name}")
