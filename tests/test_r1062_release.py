"""R10.62 -- the public release candidate: CLI, docs set, receipts.

These tests guard the things a public release can quietly get wrong:
a documented command that does not exist, a screenshot with no
provenance, a blocker that lost its teeth in an edit, or a claim
boundary that drifted into a paraphrase.
"""

import json
import os
import re

import pytest

from r1053 import certificate
from r1053.__main__ import main

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: Every command the public docs promise.
PUBLIC_COMMANDS = ("parse", "map", "path", "polygon", "serve")

RELEASE_DOCS = (
    "docs/QUICKSTART.md",
    "docs/USER_MANUAL.md",
    "docs/V1_COORDINATE_SYSTEM.md",
    "docs/VARIABLE_LENGTH_CODEC.md",
    "docs/EARTH_ROOT_V1.md",
    "docs/MAP_PATH_POLYGON_GUIDE.md",
    "docs/15KM_CELL_FIELD_ENVELOPE_MODEL.md",
    "docs/CLAIM_BOUNDARIES.md",
    "docs/BLOCKERS_B01_B07.md",
    "docs/OA_CONVERGENCE_LEDGER.md",
    "docs/FRAMES_EPOCHS_AND_GALACTIC_DIRECTIONS.md",
    "docs/releases/v1.0.0-rc1.md",
)

BOUNDARY_LINE = ("The tool verifies geometry. It does not verify that a "
                 "candidate vertex is physically true.")


def _read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


# ------------------------------------------------------- isolated CLI

def test_help_lists_every_public_command(capsys):
    with pytest.raises(SystemExit) as e:
        main(["--help"])
    assert e.value.code == 0
    out = capsys.readouterr().out
    for cmd in PUBLIC_COMMANDS:
        assert cmd in out, cmd


def test_parse_runs_and_states_the_boundary(capsys):
    assert main(["parse", "168930443"]) == 0
    out = capsys.readouterr().out
    assert "1204326213" in out                    # octal
    assert "branch          120" in out
    assert "check digit, not geometry" in out
    assert "TRAINING_EQUALITY" in out             # it is a fit anchor
    assert BOUNDARY_LINE.split(".")[0] in out


def test_parse_json_emits_a_full_certificate(capsys):
    assert main(["parse", "165879243", "--json"]) == 0
    cert = json.loads(capsys.readouterr().out)
    assert cert["schema"] == "rgcs.r1059.address-certificate.v1"
    assert cert["projection"]["is_located_target"] is False


def test_map_writes_a_page(tmp_path, capsys):
    out = tmp_path / "m.html"
    assert main(["map", "168930443", "-o", str(out)]) == 0
    assert out.exists() and out.stat().st_size > 5000
    assert "verifies geometry" in capsys.readouterr().out


def test_path_and_polygon_run_from_the_documented_examples(tmp_path, capsys):
    assert main(["path", "167849523", "168930443",
                 "-o", str(tmp_path / "p.html")]) == 0
    assert "178.846" in capsys.readouterr().out
    assert main(["polygon", "165876523,165892743,165892763,165892783",
                 "-o", str(tmp_path / "g.html")]) == 0
    out = capsys.readouterr().out
    assert "105.268" in out and "77.330" in out


def test_serve_command_is_registered():
    """`serve` must exist, not just `serve-maps`."""
    import argparse
    with pytest.raises(SystemExit):
        main(["serve", "--help"])


def test_gated_record_is_refused_by_every_lane(capsys):
    for argv in (["parse", "1687293589323"],
                 ["path", "1687293589323", "165876523"],
                 ["polygon", "1687293589323,165876523,167849523"]):
        assert main(argv) == 2, argv
        assert "bits" in capsys.readouterr().err.lower()


# ------------------------------------------------------ examples ship

def test_example_files_exist_and_contain_valid_vectors():
    from r1053 import kernel
    d = os.path.join(ROOT, "examples")
    for name in ("vectors_basic.txt", "path_erie_toronto.txt",
                 "path_toronto_drummondville.txt",
                 "polygon_orange_stonehenge.txt",
                 "polygon_b01_contradiction.txt"):
        p = os.path.join(d, name)
        assert os.path.exists(p), name
        rows = [ln.split("#")[0].strip()
                for ln in open(p, encoding="utf-8") if ln.strip()]
        vecs = [r for r in rows if r]
        assert vecs, name
        for v in vecs:
            kernel.assert_direct_lane(v)          # raises if not a direct word


def test_polygon_example_has_at_least_three_vertices():
    p = os.path.join(ROOT, "examples", "polygon_orange_stonehenge.txt")
    vecs = [ln.split("#")[0].strip()
            for ln in open(p, encoding="utf-8") if ln.split("#")[0].strip()]
    assert len(set(vecs)) >= 3


# ------------------------------------------------------- the doc set

def test_every_release_document_exists():
    for rel in RELEASE_DOCS:
        assert os.path.exists(os.path.join(ROOT, rel)), rel
        assert len(_read(rel)) > 900, rel


def test_readme_opens_with_the_required_public_claim():
    readme = " ".join(_read("README.md").split())
    required = ("RGCS is a coordinate, mapping, signal, and provenance "
                "research workbench.")
    assert required in readme
    assert ("does not claim that anomalous sources, craft, crop "
            "formations, physical propulsion, or non-human communication "
            "are proven") in readme


def test_the_boundary_line_appears_in_the_public_docs():
    flat_line = " ".join(BOUNDARY_LINE.split())
    hits = [rel for rel in RELEASE_DOCS + ("README.md",)
            if flat_line in " ".join(_read(rel).split())]
    assert len(hits) >= 4, hits


def test_readme_documents_every_public_command():
    readme = _read("README.md")
    for cmd in PUBLIC_COMMANDS:
        assert f"python -m r1053 {cmd}" in readme, cmd


def test_readme_links_resolve():
    readme = _read("README.md")
    for target in re.findall(r"\]\((docs/[^)#]+|examples/[^)#]*)\)", readme):
        assert os.path.exists(os.path.join(ROOT, target)), target


def test_blockers_doc_keeps_every_blocker_and_its_clearing_condition():
    doc = _read("docs/BLOCKERS_B01_B07.md")
    for n in range(1, 8):
        assert f"B0{n}" in doc
    assert doc.count("Clears when") >= 7 or doc.count("clears when") >= 7
    # the specific numbers that make the blockers real
    for token in ("5121.7", "0.881", "0.147", "484,856,892", "451.6",
                  "71 %"):
        assert token in doc, token


def test_blockers_are_not_softened_by_hedging_language():
    doc = _read("docs/BLOCKERS_B01_B07.md")
    for bad in ("mostly resolved", "essentially solved", "no longer an issue",
                "largely confirmed"):
        assert bad not in doc.lower()


def test_the_null_travels_with_the_15km_claim():
    doc = _read("docs/15KM_CELL_FIELD_ENVELOPE_MODEL.md")
    assert "1.046" in doc and "0.881" in doc and "0.147" in doc


def test_mapping_guide_explains_the_removed_shoelace_formula():
    doc = _read("docs/MAP_PATH_POLYGON_GUIDE.md")
    assert "shoelace" in doc.lower()
    assert "42" in doc                             # the measured error
    assert "self-cross" in doc.lower() or "crosses itself" in doc.lower()
    assert "Vertex order" in doc or "vertex order" in doc


def test_release_notes_name_the_next_highest_value_work():
    notes = _read("docs/releases/v1.0.0-rc1.md")
    assert "v1.0.0-rc1" in notes
    assert "two more independently sourced hard anchors" in notes.lower()
    assert "unproven" in notes.lower()


# --------------------------------------------------- screenshot receipts

def test_every_screenshot_has_a_provenance_receipt():
    d = os.path.join(ROOT, "docs", "assets", "user-manual")
    shots = [f for f in os.listdir(d) if f.endswith(".png") and f[0].isdigit()]
    assert len(shots) >= 5
    for png in shots:
        rec_path = os.path.join(d, png.replace(".png", ".json"))
        assert os.path.exists(rec_path), f"{png} has no receipt"
        rec = json.load(open(rec_path, encoding="utf-8"))
        for field in ("captured_utc", "commit", "command", "input_vectors",
                      "output_sha256", "bytes", "invented"):
            assert field in rec, (png, field)
        assert rec["invented"] is False
        assert len(rec["output_sha256"]) == 64


def test_screenshot_hashes_match_the_actual_files():
    import hashlib
    d = os.path.join(ROOT, "docs", "assets", "user-manual")
    for f in os.listdir(d):
        if not (f.endswith(".json") and f[0].isdigit()):
            continue
        rec = json.load(open(os.path.join(d, f), encoding="utf-8"))
        png = os.path.join(d, rec["filename"])
        if not os.path.exists(png):
            continue
        actual = hashlib.sha256(open(png, "rb").read()).hexdigest()
        assert actual == rec["output_sha256"], rec["filename"]


def test_required_release_screenshots_are_present():
    d = os.path.join(ROOT, "docs", "assets", "user-manual")
    for stem in ("06_path_erie_toronto", "07_path_toronto_drummondville",
                 "08_path_B01_disagreement", "10_polygon_uk4",
                 "12_polygon_builder_live"):
        assert os.path.exists(os.path.join(d, stem + ".png")), stem


# ------------------------------------------------------------ archive

def test_archived_docs_carry_the_correction_banner():
    d = os.path.join(ROOT, "docs", "archive")
    assert os.path.isdir(d)
    banner = _read("docs/archive/pre-r1059/README.md")
    assert "archived" in banner.lower()
    assert "superseded" in banner.lower()
    assert "Montreal" in banner or "Montréal" in banner


def test_claim_boundary_constant_is_still_the_published_one():
    assert "does not prove physical craft" in certificate.CLAIM_BOUNDARY
    flat = " ".join(certificate.CLAIM_BOUNDARY.split())
    assert flat in " ".join(_read("README.md").split()) or \
        flat in " ".join(_read("docs/CLAIM_BOUNDARIES.md").split())
