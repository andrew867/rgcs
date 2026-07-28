"""R10.13 Phases 23/32 — documentation execution gate.

Every release-marked manual command executes here through the real
CLI entry (r1013.cli.main), from clean temp directories, exactly as
the tutorials write them. GUI commands are presence-tested. The gmsh
FEM tutorials run on coarse meshes.
"""

import json
import pathlib
import re

import pytest

from r1013.cli import main

DOCS = pathlib.Path(__file__).resolve().parents[2] / "docs" / "r1013"
EX = pathlib.Path(__file__).resolve().parents[2] / "r1013" / "data" / \
    "examples"


def run(argv, expect=0):
    rc = main(argv)
    assert rc == expect, (argv, rc)
    return rc


@pytest.fixture()
def spec(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    p = tmp_path / "my-crystal.json"
    p.write_text((EX / "crystal_complete.json").read_text(),
                 encoding="utf-8")
    return str(p)


# --------------------------------------------------- quick start flow
def test_quick_start_walkthrough(spec, tmp_path):
    run(["crystal", "new", "fresh.json"])
    run(["crystal", "validate", spec])
    run(["crystal", "estimate", spec,
         "--models", "axial-quarter,axial-half"])
    run(["crystal", "report", spec, "--from", "latest",
         "--out", "rep"])
    assert (tmp_path / "rep" / "REPORT.md").is_file()
    text = (tmp_path / "rep" / "REPORT.md").read_text(encoding="utf-8")
    assert "not a measured resonance" in text


def test_general_commands(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    run(["doctor"])
    run(["schema", "verify"])
    run(["examples", "verify"])
    run(["help", "error", "RGCS-E001"])
    with pytest.raises(SystemExit) as ei:
        main(["--version"])
    assert ei.value.code == 0


def test_crystal_record_commands(spec, tmp_path):
    run(["crystal", "inspect", spec])
    run(["crystal", "hash", spec])
    run(["crystal", "geometry", spec])
    run(["crystal", "density-check", spec])
    run(["crystal", "christoffel", spec,
         "--directions", "0,0,1;1,0,0"])
    run(["crystal", "migrate", spec, "--out",
         str(tmp_path / "mig.json")])
    assert (tmp_path / "mig.json").is_file()


def test_validation_failure_exit_code(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    bad = tmp_path / "bad.json"
    bad.write_text('{"schema_version": "nope"}', encoding="utf-8")
    run(["crystal", "validate", str(bad)], expect=2)
    run(["crystal", "estimate", str(tmp_path / "missing.json")],
        expect=2)


def test_output_formats(spec, tmp_path):
    out = tmp_path / "est.json"
    run(["crystal", "estimate", spec, "--format", "json",
         "--output", str(out), "--quiet"])
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert doc["estimates"][0]["evidence_class"] == "ESTIMATE"
    out2 = tmp_path / "est.csv"
    run(["crystal", "estimate", spec, "--format", "csv",
         "--output", str(out2), "--quiet"])
    header = out2.read_text(encoding="utf-8").splitlines()[0]
    assert "frequency_hz" in header


# ------------------------------------------------- FEM tutorial (gmsh)
def test_full_fem_tutorial_coarse(spec, tmp_path):
    run(["crystal", "mesh", spec, "--clmax-mm", "12",
         "--out", str(tmp_path / "m")])
    run(["crystal", "modes", spec, "--clmax-mm", "12", "--count", "8",
         "--fixture", "free", "--out", str(tmp_path / "res")])
    assert (tmp_path / "res" / "modes.json").is_file()
    run(["crystal", "bundle", spec, "--result",
         str(tmp_path / "res"), "--out", str(tmp_path / "bun")])
    run(["bundle", "verify", str(tmp_path / "bun")])


def test_fixture_comparison_tutorial(spec, tmp_path):
    for fixture in ("free", "end_clamp"):
        run(["crystal", "modes", spec, "--clmax-mm", "14",
             "--count", "10", "--fixture", fixture,
             "--out", str(tmp_path / fixture)])
    free = json.loads((tmp_path / "free" / "modes.json").read_text())
    clamped = json.loads((tmp_path / "end_clamp" /
                          "modes.json").read_text())
    assert free["n_rigid_modes"] == 6
    assert clamped["n_rigid_modes"] == 0


def test_frequency_commands(spec, tmp_path):
    run(["frequency", "list", "--quiet"])
    run(["crystal", "modes", spec, "--clmax-mm", "14", "--count", "6",
         "--fixture", "free", "--out", str(tmp_path / "res")])
    run(["frequency", "compare", str(tmp_path / "res" / "modes.json"),
         "--keys", "4096,528"])


# --------------------------------------------------- codec delegation
def test_codec_commands_delegate_unchanged(capsys):
    run(["wire", "parse", "165876523"])
    out = capsys.readouterr().out
    assert "canonical_bits" in out
    run(["wire", "roundtrip", "168742538943"])
    run(["transition", "candidates", "165876523", "--child", "5"])
    # unknown transition cells refuse typed with exit 3
    rc = main(["transition", "refine", "165876523", "--child", "0"])
    assert rc == 3


def test_research_commands(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for topic in ("timing", "aperture", "ledger", "edge-law"):
        run(["research", topic, "--quiet"])


# ------------------------------------------------- doc integrity gate
def test_command_status_registry_written():
    doc = json.loads((DOCS / "receipts" /
                      "COMMAND_STATUS.json").read_text())
    assert doc["schema"] == "rgcs.r1013.command-status.v1"
    statuses = {v["status"] for v in doc["statuses"].values()}
    assert "TARGET" not in statuses


def test_manual_json_examples_are_valid():
    for f in (DOCS / "manual").rglob("*.json"):
        json.loads(f.read_text(encoding="utf-8"))


def test_manual_internal_paths_exist():
    """Schema/example files referenced by the manual ship for real."""
    for rel in ("schemas/crystal-specimen.schema.json",
                "examples/crystal_minimum.json",
                "examples/crystal_complete.json"):
        assert (DOCS / "manual" / rel).is_file(), rel


def test_gui_entry_points_present():
    """rgcs-workbench / rgcs-workbook: presence-tested (GUI)."""
    import importlib
    assert importlib.import_module("rgcs_desktop.app.main").main
    assert importlib.import_module("rgcs_workbench.workbook").main


def test_desktop_wizard_deferred_wording():
    guide = (DOCS / "manual" / "02_USER_MANUAL" /
             "DESKTOP_APP_GUIDE.md").read_text(encoding="utf-8")
    assert "DEFERRAL NOTE" in guide


def test_no_mock_markers_in_r1013():
    """Phase 33 — no placeholders or fake receipts in shipped code."""
    root = pathlib.Path(__file__).resolve().parents[2] / "r1013"
    pat = re.compile(r"TODO|FIXME|NotImplementedError|placeholder|"
                     r"hardcoded_pass|return True  # stub", re.I)
    hits = []
    for f in root.rglob("*.py"):
        for i, line in enumerate(f.read_text(encoding="utf-8")
                                 .splitlines(), 1):
            if pat.search(line):
                hits.append(f"{f.name}:{i}")
    assert hits == [], hits
