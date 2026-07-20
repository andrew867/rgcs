"""R10 P20 — build-artifact parity: what SOURCE_ROOTS says, what a
wheel and an sdist actually carry, and what a fresh install can import.

``tests/v52/test_r9_packaging.py`` closed the in-tree half of this: it
asserts that every package in ``SOURCE_ROOTS`` is matched by the
packaging ``include`` list. That guard is necessary and it is not
sufficient. It reasons about *configuration*, and the defect it exists
to prevent (v4.9.0, v5.0.0 and v5.1.0 shipping none of r6, r7, r8)
was only ever visible in the *artifact* -- a clone imports the tree
regardless, because ``pythonpath = ["."]``.

This file adds the artifact-facing half in two tiers.

Tier 1 (always runs, needs only setuptools) checks the properties that
determine artifact contents before any build happens:

* the wheel package set covers every existing ``SOURCE_ROOTS`` entry,
  at every level of nesting, not just top level;
* the sdist package set is the same set, and no ``MANIFEST.in``
  exclusion quietly narrows it;
* no package would be dropped for want of an ``__init__.py`` (R9-D-003:
  ``r9`` shipped as a PEP 420 namespace package, which
  ``find_packages`` cannot see and a wheel therefore would not carry);
* every ``.py`` file under a source root lands inside some discovered
  package, so none is silently left out of both artifacts;
* every non-``.py`` file under a source root is declared in
  ``[tool.setuptools.package-data]``, or the installed copy loads code
  that reads a file that is not there.

Tier 2 (opt-in) actually builds a wheel and an sdist and reads their
manifests. It is off by default because it needs the ``build`` package
and writes ``build/`` and ``*.egg-info`` into the checkout; set
``RGCS_R10_BUILD_PARITY=1`` to run it. The full build-plus-fresh-venv
transcript that this tier automates is recorded in
``docs/v52/R10_INSTALL_PARITY.md``.

R9-D-020 governs the import style here: this module must never fail
*collection* on a machine without build tooling. setuptools is a
build-system requirement, absent from CI's portable job, and importing
it at module level once broke collection on all three CI platforms
while passing locally. Everything optional is imported through
``importorskip`` or behind a ``skipif``.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import tarfile
import tomllib
import zipfile

import pytest

from rgcs_desktop.build_meta import SOURCE_ROOTS

setuptools = pytest.importorskip(
    "setuptools", reason="setuptools needed for package-discovery parity")
find_packages = setuptools.find_packages
find_namespace_packages = setuptools.find_namespace_packages

ROOT = pathlib.Path(__file__).resolve().parents[2]

#: Packages distributed but deliberately outside the build-freshness
#: hash. **Empty since Q02** -- see R10-D-004 below.
#:
#: ``consciousness_lane`` is the quarantined theory lane. It is matched
#: by the packaging ``include`` list, so ``pip install rgcs`` does put
#: it on disk and it is importable from the wheel -- but it is not in
#: ``SOURCE_ROOTS`` and is not bundled into the frozen desktop app,
#: whose provenance is what that hash exists to protect. The asymmetry
#: is intentional, and it is named here rather than left implicit so
#: that a *second* such package cannot appear unnoticed. Note that the
#: comment on the ``EXCLUDED`` entry in
#: ``tests/v51/test_r8_source_coverage.py`` describes this lane as "not
#: shipped", which is true of the frozen app and false of the wheel.
#: Q02 / R10-D-004 resolved this. The operator's standing decision is
#: that a publicly shipped package must be hashed unless it is removed
#: from every public artifact. consciousness_lane ships, so it is now
#: in SOURCE_ROOTS and this set is empty. An entry added here in future
#: needs an explicit operator decision recorded alongside it.
DISTRIBUTED_NOT_HASHED: set[str] = set()

BUILD_PARITY_ENV = "RGCS_R10_BUILD_PARITY"


# --------------------------------------------------------------- helpers

def _config() -> dict:
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def _include_patterns() -> list[str]:
    return _config()["tool"]["setuptools"]["packages"]["find"]["include"]


def _discovered() -> set[str]:
    """The package set setuptools hands to both the wheel and the sdist."""
    return set(find_packages(where=str(ROOT), include=_include_patterns()))


def _existing_roots() -> set[str]:
    return {r for r in SOURCE_ROOTS if (ROOT / r).is_dir()}


def _py_files(pkg: str) -> list[pathlib.Path]:
    return [p for p in sorted((ROOT / pkg).rglob("*.py"))
            if "__pycache__" not in p.parts]


def _non_py_files(pkg: str) -> list[pathlib.Path]:
    return [p for p in sorted((ROOT / pkg).rglob("*"))
            if p.is_file() and p.suffix != ".py"
            and "__pycache__" not in p.parts]


# ------------------------------------------------- tier 1: configuration

def test_wheel_package_set_covers_every_source_root():
    """Top-level coverage: the R9 assertion, restated against the set
    that actually reaches the wheel."""
    missing = _existing_roots() - {p for p in _discovered() if "." not in p}
    assert not missing, (
        f"in SOURCE_ROOTS but absent from the wheel package set: "
        f"{sorted(missing)}")


def test_every_subpackage_of_every_source_root_is_discovered():
    """Coverage must hold at every level of nesting.

    A top-level package can be present in the wheel while a subpackage
    of it is missing -- the import of the parent still succeeds, so the
    gap surfaces only when someone imports the child. Nothing was
    checking below the first level.
    """
    found = _discovered()
    missing: list[str] = []
    for root in sorted(_existing_roots()):
        for d in sorted((ROOT / root).rglob("*")):
            if not d.is_dir() or "__pycache__" in d.parts:
                continue
            if not any(q.suffix == ".py" for q in d.iterdir() if q.is_file()):
                continue
            dotted = d.relative_to(ROOT).as_posix().replace("/", ".")
            if dotted not in found:
                missing.append(dotted)
    assert not missing, (
        f"subpackages holding .py files that no artifact would carry: "
        f"{missing}")


def test_no_package_is_dropped_for_want_of_an_init_file():
    """R9-D-003, as an artifact property rather than a hash property.

    ``find_packages`` ignores a directory with no ``__init__.py``;
    ``find_namespace_packages`` does not. Any directory in the
    difference imports fine from a clone (PEP 420) and is simply absent
    from the wheel -- the exact shape of the original defect. This is
    the check that would catch a future ``r10`` added the way ``r9``
    was.
    """
    inc = _include_patterns()
    regular = set(find_packages(where=str(ROOT), include=inc))
    namespace = set(find_namespace_packages(where=str(ROOT), include=inc))
    dropped = {p for p in namespace - regular
               if any(q.suffix == ".py"
                      for q in (ROOT / p.replace(".", "/")).iterdir()
                      if q.is_file())}
    assert not dropped, (
        f"namespace packages that a wheel would silently omit: "
        f"{sorted(dropped)}. Add an __init__.py, or the installed "
        f"copy will not contain them even though a clone imports them.")


def test_every_py_file_lands_inside_a_discovered_package():
    """File-level coverage. Package-level agreement can still leave an
    individual module out of both artifacts if it sits in a directory
    that is not itself a package."""
    found = _discovered()
    orphans: list[str] = []
    for root in sorted(_existing_roots()):
        for p in _py_files(root):
            dotted = p.parent.relative_to(ROOT).as_posix().replace("/", ".")
            if dotted not in found:
                orphans.append(p.relative_to(ROOT).as_posix())
    assert not orphans, (
        f".py files in no discovered package, so shipped by neither "
        f"wheel nor sdist: {orphans}")


def test_every_non_py_file_under_a_source_root_is_declared_package_data():
    """Wheels carry ``.py`` files automatically and data files only on
    request. An undeclared data file leaves an installed copy that
    imports cleanly and fails at first read."""
    declared = _config()["tool"]["setuptools"].get("package-data", {})
    undeclared: list[str] = []
    for root in sorted(_existing_roots()):
        pats = declared.get(root, [])
        for p in _non_py_files(root):
            rel = p.relative_to(ROOT / root)
            if not any(rel.match(pat) for pat in pats):
                undeclared.append(p.relative_to(ROOT).as_posix())
    assert not undeclared, (
        f"data files under a source root that no artifact would carry: "
        f"{undeclared}. Declare them in "
        f"[tool.setuptools.package-data] or the install breaks on "
        f"first read.")


def test_sdist_is_governed_by_the_same_package_set_as_the_wheel():
    """Both artifacts must be built from one list, not two.

    Without a ``MANIFEST.in`` setuptools derives the sdist file list
    from the same ``packages`` discovery the wheel uses, so parity is
    structural. If a ``MANIFEST.in`` is ever added it can prune a
    package out of the sdist while leaving the wheel intact -- a
    divergence that no configuration test would otherwise see.
    """
    manifest = ROOT / "MANIFEST.in"
    if not manifest.exists():
        return
    roots = _existing_roots()
    offending = [
        line.strip()
        for line in manifest.read_text(encoding="utf-8").splitlines()
        if line.strip().split(" ")[:1]
        and line.strip().split(" ")[0] in {
            "exclude", "prune", "recursive-exclude", "global-exclude"}
        and any(r in line for r in roots)]
    assert not offending, (
        f"MANIFEST.in excludes packaged source from the sdist while "
        f"the wheel keeps it: {offending}")


def test_distribution_beyond_the_freshness_hash_is_explicit():
    """The mirror of the original defect.

    R8-D-006 was a package that shipped but was not hashed. Everything
    distributed and outside ``SOURCE_ROOTS`` must be named in
    ``DISTRIBUTED_NOT_HASHED`` with a reason, so the next one is a
    decision rather than an oversight.
    """
    top = {p for p in _discovered() if "." not in p}
    unexplained = top - set(SOURCE_ROOTS) - DISTRIBUTED_NOT_HASHED
    assert not unexplained, (
        f"packages shipped to users but outside the build-freshness "
        f"hash: {sorted(unexplained)}. Either add them to "
        f"SOURCE_ROOTS, or record why not in DISTRIBUTED_NOT_HASHED. "
        f"An unhashed shipped package means a stale dist/ passes the "
        f"freshness check after that package changes.")


def test_the_research_packages_are_in_both_artifact_configurations():
    """Named explicitly, because these are the ones that were missing."""
    found = _discovered()
    for pkg in ("r3", "r4", "r6", "r7", "r8", "r9"):
        assert pkg in found, (
            f"{pkg} is in neither the wheel nor the sdist package set")


# ------------------------------------------------------ tier 2: real build

_build_available = True
try:  # noqa: SIM105 - importorskip would skip the whole module
    import build as _build_mod  # noqa: F401
except Exception:  # noqa: BLE001
    _build_available = False

needs_build = pytest.mark.skipif(
    not (_build_available and os.environ.get(BUILD_PARITY_ENV)),
    reason=(f"opt-in artifact build; needs the 'build' package and "
            f"{BUILD_PARITY_ENV}=1 (it writes build/ and *.egg-info "
            f"into the checkout)"))


def _wheel_and_sdist(outdir: pathlib.Path) -> tuple[pathlib.Path,
                                                    pathlib.Path]:
    subprocess.run(
        [sys.executable, "-m", "build", "--no-isolation",
         "--outdir", str(outdir), str(ROOT)],
        check=True, capture_output=True, text=True, timeout=900)
    return (next(outdir.glob("*.whl")), next(outdir.glob("*.tar.gz")))


@needs_build
def test_built_wheel_and_sdist_carry_every_source_root(tmp_path):
    """The assertion the three broken releases would have failed."""
    whl, sdist = _wheel_and_sdist(tmp_path)

    wheel_names = zipfile.ZipFile(whl).namelist()
    with tarfile.open(sdist) as tf:
        raw = tf.getnames()
    prefix = raw[0].split("/")[0] + "/"
    sdist_names = [n[len(prefix):] for n in raw if n.startswith(prefix)]

    def n_py(names: list[str], pkg: str) -> int:
        return sum(1 for n in names
                   if n.startswith(pkg + "/") and n.endswith(".py"))

    for pkg in sorted(_existing_roots()):
        on_disk = len(_py_files(pkg))
        assert n_py(wheel_names, pkg) == on_disk, (
            f"{pkg}: wheel carries {n_py(wheel_names, pkg)} of "
            f"{on_disk} .py files")
        assert n_py(sdist_names, pkg) == on_disk, (
            f"{pkg}: sdist carries {n_py(sdist_names, pkg)} of "
            f"{on_disk} .py files")


@needs_build
def test_built_wheel_declares_every_source_root_as_top_level(tmp_path):
    whl, _ = _wheel_and_sdist(tmp_path)
    zf = zipfile.ZipFile(whl)
    name = next(n for n in zf.namelist() if n.endswith("top_level.txt"))
    declared = set(zf.read(name).decode("utf-8").split())
    missing = _existing_roots() - declared
    assert not missing, f"absent from wheel top_level.txt: {sorted(missing)}"


# --- Q02: the inverse defect (R10-D-004) ------------------------------

def test_every_distributed_package_is_also_hashed():
    """R10-D-004, the mirror of R8-D-006.

    R8-D-006 was "hashed but not shipped". This is "shipped but not
    hashed": consciousness_lane reached the wheel, the sdist and
    top_level.txt, and was importable after pip install, while sitting
    outside SOURCE_ROOTS -- so changing it could not invalidate a
    frozen dist.

    The operator's standing decision is that a publicly shipped
    package must be hashed unless it is removed from every public
    artifact. This asserts that direction, which the pre-existing
    test_every_hashed_package_is_also_distributed does not.
    """
    shipped = {q for q in _discovered() if "." not in q}
    missing = shipped - set(SOURCE_ROOTS)
    assert not missing, (
        f"packages distributed by pip but absent from SOURCE_ROOTS: "
        f"{sorted(missing)}. A shipped package outside the freshness "
        f"hash means changing it cannot invalidate a frozen dist.")


def test_the_two_lists_are_now_exactly_equal():
    """Neither direction may drift again."""
    shipped = {q for q in _discovered() if "." not in q}
    hashed = {r for r in SOURCE_ROOTS if (ROOT / r).exists()}
    assert shipped == hashed, {
        "shipped_not_hashed": sorted(shipped - hashed),
        "hashed_not_shipped": sorted(hashed - shipped),
    }
