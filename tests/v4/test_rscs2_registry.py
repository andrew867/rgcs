"""Tests for the RSCS2 registry loader + classification/provenance lint."""
from __future__ import annotations

from rscs2_core.registry import (VALID_CLASSES, VALID_NAMESPACES,
                                 lint_registry, load_registry,
                                 registry_entries)


def test_registry_loads_and_is_clean():
    reg = load_registry()
    assert reg["schema_version"] == 1
    entries = registry_entries(reg)
    assert entries, "registry has no entries"
    # every shipped entry passes the governance lint
    assert lint_registry(reg) == []


def test_every_entry_wellformed():
    for e in registry_entries():
        assert e["id"].rsplit(".", 1)[0] in VALID_NAMESPACES
        assert e["class"] in VALID_CLASSES
        assert e["units"] and e["provenance"] and e["module"] and e["tests"]


def test_lint_catches_violations():
    bad = {"benchmarks": [
        {"id": "RSCS2-X.1", "class": "EST", "units": "Hz",
         "provenance": ["x"], "module": "m", "tests": ["t"]},       # bad ns
        {"id": "RSCS2-V.1", "class": "WRONG", "units": "", "provenance": [],
         "module": "", "tests": []},                                 # many
        {"id": "RSCS2-V.1", "class": "EST", "units": "Hz",
         "provenance": ["SRC-3-01"], "module": "m", "tests": ["t"]},  # dup+SRC
    ]}
    problems = lint_registry(bad)
    joined = " ".join(problems)
    assert "namespace" in joined
    assert "duplicate id" in joined
    assert "class" in joined and "missing units" in joined
    assert "SRC" in joined and "firewall" in joined
