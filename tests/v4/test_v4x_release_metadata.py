"""Phase 7 guard: documented test counts must match a real run.

v4.2.0 shipped "expect: 681 passed" while the test-report asset built
from the same commit said 682 (V4X-D-004). The count lived in prose, by
hand, in four files. It now derives from an actual pytest run into
docs/v4/RELEASE_METADATA.json, and this test fails the build if any
document drifts from it."""

import importlib.util
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "v4x_release_metadata", ROOT / "tools" / "v4x_release_metadata.py")
meta_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(meta_mod)


def test_metadata_file_exists_and_is_sane():
    m = json.loads((ROOT / "docs/v4/RELEASE_METADATA.json")
                   .read_text(encoding="utf-8"))
    assert m["tests_passed"] > 600
    assert m["tests_deselected"] == 1
    assert "D-V3-04" in m["deselect_reason"]
    assert m["deselect_node"].endswith("test_generator_deterministic")


def test_every_documented_count_agrees():
    """The 681-vs-682 defect, made impossible."""
    rep = meta_mod.verify()
    assert rep["agree"], rep["problems"]
    assert rep["sites_checked"] >= 3, \
        "guard is not actually checking any document"


def test_version_is_consistent_everywhere():
    ver = "5.8.0"
    assert f'version = "{ver}"' in (ROOT / "pyproject.toml").read_text(
        encoding="utf-8")
    cff = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    assert f"version: {ver}" in cff
    assert f"releases/tag/v{ver}" in cff
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert f"releases/tag/v{ver}" in readme
    ch = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"[{ver}]" in ch
