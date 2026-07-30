"""R10.11F / F-A acceptance — intake, revocation, analytic solve."""

from __future__ import annotations

import json
import pathlib

import pytest

from r1011 import e3_frame as e3

EVF = pathlib.Path(__file__).resolve().parents[2] / "docs" / "r1011" / \
    "evidence" / "r1011f"
EVA = pathlib.Path(__file__).resolve().parents[2] / "docs" / "r1011" / \
    "evidence" / "r1011fa"


def test_intake_v2_corrected_28_of_28():
    doc = json.loads((EVA / "R10_11FA_INTAKE_PARSE_RECEIPT.json")
                     .read_text(encoding="utf-8"))
    assert doc["schema"].endswith("intake-freeze.v2")
    assert doc["wire_count"] == 28
    assert doc["parsed"] == 28 and doc["failures"] == 0
    # A2 correction ledger: malformed value preserved, superseded
    led = doc["correction_ledger"]
    assert led["malformed_transcription_preserved"] == "1687425419853"
    assert led["superseded_by"] == "168742538943"
    assert led["v1_status_line_deleted"] == "ONE_WIDTH_OVERFLOW_UNRESOLVED"
    cw = doc["corrected_wire_verification"]
    assert (cw["e3"], tuple(cw["states"]), tuple(cw["children"]),
            cw["terminal"], cw["depth"]) == (6, (32, 56, 7), (1, 0, 6), 3, 3)


def test_corrected_wire_parses_and_roundtrips():
    p = e3.parse(168742538943)
    assert p.e3 == 6 and p.states == (32, 56, 7)
    assert p.children == (1, 0, 6) and p.terminal == 3
    assert e3.encode(p) == 168742538943


def test_a2_reclassifications_registered():
    reg = json.loads((EVA / "R10_11FA2_CORRECTIONS.json")
                     .read_text(encoding="utf-8"))
    assert "PRIMED_RETROSPECTIVE" in reg["reclassification_144000"]["status"]
    assert "CANNOT support" in reg["reclassification_144000"]["consequence"]
    sub = reg["subtitle_chronology"]
    assert "NOT independent confirmation" in sub["classification"]
    assert set(sub["not_named"]) == {"QAnon", "Project 2025",
                                     "US military-industrial complex"}
    assert "144000_RECLASSIFIED_AS_PRIMED_RETROSPECTIVE_MATCH" in         reg["verdict_lines"]


def test_overflow_wire_refused_never_truncated():
    with pytest.raises(e3.E3FrameError, match="width family"):
        e3.parse(1687425419853)


def test_627_operator_revoked_in_authority():
    auth = json.loads((EVA / "CURRENT_T_PROJECTION_AUTHORITY.json")
                      .read_text(encoding="utf-8"))
    assert "REVOKED" in auth["revoked"]["action"]
    assert "627" in auth["revoked"]["id"]
    assert "ANALYTIC" in auth["active_target"]
    assert "10/9" in auth["ratio_authority"]


def test_exact_t_edge_inferences_all_rejected():
    import csv
    rows = list(csv.DictReader(open(EVF / "EXACT_EDGE_ODDS.csv",
                                    encoding="utf-8")))
    assert len(rows) == 4
    assert all(r["usable_under_150km_crosstrack"] == "False" for r in rows)


def test_analytic_compensation_no_law_wins():
    import csv
    import math
    rows = list(csv.DictReader(open(
        EVA / "R10_11FA_ANALYTIC_COMPENSATION_CHECK.csv", encoding="utf-8")))
    by = {r["law"]: r for r in rows}

    def rms4(r):
        ks = ("STONEHENGE", "ERIE", "TORONTO", "ORANGE_A")
        return math.sqrt(sum(float(r[k]) ** 2 for k in ks) / 4)
    r1, r109 = rms4(by["1"]), rms4(by["10/9"])
    # the whole family sits within a narrow band and r=1 is not beaten
    assert abs(r1 - 13.902) < 0.05
    assert r109 > r1                      # 10/9 does not improve anchors
    assert abs(r109 - r1) < 0.5           # law nearly inert
    # Montreal reported separately and remains codec-tension dominated
    assert float(by["10/9"]["MONTREAL_DIRECT"]) > 40


def test_pi_equation_registered_not_selected():
    doc = json.loads((EVA / "R10_11FA_PI_EQUATION_REGISTRY.json")
                     .read_text(encoding="utf-8"))
    assert doc["selection"].startswith("NONE")
    assert set(doc["sq_r_readings_tested"]) == {"sqrt(r)", "r^2"}
    assert doc["prime_pair_tokens_registered"] == {"2937": "29|37",
                                                   "8937": "89|37"}
    assert doc["first_fraction_candidate_registered"] == "33/35"
