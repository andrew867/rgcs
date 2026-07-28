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


def test_intake_frozen_and_reparsed_27_1():
    doc = json.loads((EVA / "R10_11FA_INTAKE_PARSE_RECEIPT.json")
                     .read_text(encoding="utf-8"))
    assert doc["wire_count"] == 28
    assert doc["matches_expected_27_1"] is True
    statuses = [r["status"] for r in doc["independent_parse"]]
    assert statuses.count("PARSED") == 27
    assert statuses.count("WIDTH_OVERFLOW") == 1
    bad = next(r for r in doc["independent_parse"]
               if r["status"] == "WIDTH_OVERFLOW")
    assert bad["wire"] == "1687425419853"


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
