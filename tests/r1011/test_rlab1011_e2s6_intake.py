"""R10.11 late-intake acceptance — E2|S6 frame, table search, reveal."""

from __future__ import annotations

import pytest

from r1011 import e2s6_intake as it


def test_new_vectors_registered():
    raws = {r.raw for r in it.intake_records()}
    assert raws == {1658729343, 165823973, 165652893, 165879633,
                    165778933, 165872393}
    slash = [r for r in it.intake_records() if "slash pair" in r.note]
    assert len(slash) == 2
    for r in slash:
        assert "probable" in r.note.lower()      # never assumed confirmed


def test_header_16_radix_unresolved():
    h = it.HEADER_16_READINGS
    assert h["decimal_integer"]["binary"] == "10000"
    assert h["two_octal_symbols"]["binary"] == "001|110"
    assert "NOT locked" in h["two_octal_symbols"]["status"]


def test_candidate_frame_parses_and_e2_not_face():
    p = it.parse_e2s6_compact(165872393)
    assert p["header"] == "165"
    assert len(p["states"]) == 3
    assert all(0 <= s <= 63 for s in p["states"])
    # E2 is two raw bits; nothing maps it to a face anywhere
    import inspect
    src = inspect.getsource(it)
    assert "face_class" not in src


def test_middle_state_23_claim_recorded_as_unresolved():
    r = it.FRAME_SCAN_RESULT
    assert "NO reading yields 23" in r["result"]
    assert "UNRESOLVED" in r["conclusion"]
    # verify the exhaustive negative computationally (spot check: no
    # aligned window in the 30-bit frame equals 23)
    b = format(165872393, "030b")
    assert all(int(b[i:i + 6], 2) != 23 for i in range(25))


def test_table_search_recorded_and_ring_fails():
    t = it.TABLE_SEARCH_RESULT
    assert any("rgcs_lab/lattice.py" in s for s in t["found_in_repo"])
    assert any("6X6" in s or "6x6" in s for s in t["found_in_archives"])
    assert "NO k works" in t["tests_run"][0]
    # live re-check on one pair: no ring offset maps compact->refined
    def st(v, w):
        b = format(v, f"0{w}b")
        return [int(b[i:i + 6], 2) for i in range(0, 30, 6)]
    sc, sr = st(165876523, 30), st(1643789253, 33)
    assert all([(x + k) % 64 for x in sc] != sr for k in range(64))


def test_holdout_reveal_scored_without_retuning():
    r = it.HOLDOUT_167854923_REVEAL
    assert r["revealed_label"] == "historical lunar-surface location"
    assert r["evidence_class"] == "SOURCE_REPORTED"
    assert "WRONG_BODY" in r["score"]
    assert "NO RETUNING" in r["score"]
    # frozen prediction values unchanged from the R10.9/R10.10 receipts
    assert r["frozen_predictions"]["v1"] == (41.730063, -80.833659)
    # the Erie tension is preserved, not repaired
    assert any("Erie" in n or "167849523" in n
               for n in r["consistency_notes"])


def test_no_geographic_selection_of_tables():
    import inspect
    src = inspect.getsource(it)
    # table testing references only the exact pairs / slash pair;
    # British outputs and sealed unlabelled holdouts never appear
    for banned in ("Stafford", "Wrexham", "Chester", "Andover",
                   "165892323", "168724343", "165829473"):
        assert banned not in src
