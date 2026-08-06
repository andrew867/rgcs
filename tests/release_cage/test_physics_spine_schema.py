"""Group B: physics-spine and ledger schema validity."""

from __future__ import annotations

from rgcs_workbench.public_cage import physics_spine as PS


def test_spine_validates_with_zero_problems():
    assert PS.validate_spine() == []


def test_every_entry_has_lane_class_anchor_observables_and_refusals():
    for entry in PS.load_spine()["entries"]:
        assert entry["lane"]
        assert entry["source_class"] in PS.SOURCE_CLASSES
        assert entry["external_anchor"]
        assert entry["forbidden_claims"]
        if entry["public_status"] == "PUBLIC_RESEARCH" \
                and entry["observables"]:
            assert entry["controls"], entry["id"]


def test_positron_and_dce_lanes_are_analogy_only():
    entries = {e["lane"]: e for e in PS.load_spine()["entries"]}
    for lane in PS.ANALOGY_ONLY_LANES:
        entry = entries[lane]
        assert entry["public_status"] == "LONG_TERM_ANALOGY_ONLY"
        assert entry["bench_priority"] == 0


def test_ledger_validates_and_agrees_across_formats():
    assert PS.validate_ledger() == []
    ids = [r["id"] for r in PS.load_ledger_json()]
    assert len(ids) == 17
    assert ids == [r["id"] for r in PS.load_ledger_csv()]


def test_every_ledger_row_has_claim_boundary_and_quality():
    for row in PS.load_ledger_json():
        assert row["claim_boundary"]
        assert row["source_quality"] in ("high", "medium-high", "medium")


def test_required_anchors_from_the_pack_are_present():
    blob = " ".join(r["identifier_or_url"] + " " + r["title"]
                    for r in PS.load_ledger_json())
    for anchor in ("US9405136B2", "nphys3134", "ph400058y",
                   "US7561759B2", "s41467-024-51171-6",
                   "s41566-018-0259-4", "479 376-379", "US7894125B2",
                   "WO2021069873A1", "1905.13252", "US12028960B2",
                   "US5617443A", "AEgIS", "PB97123947"):
        assert anchor in blob, anchor


def test_schema_rejects_a_broken_entry(monkeypatch):
    spine = PS.load_spine()
    spine["entries"][0] = dict(spine["entries"][0],
                               source_class="MADE_UP",
                               forbidden_claims=[])
    monkeypatch.setattr(PS, "load_spine", lambda: spine)
    problems = PS.validate_spine()
    assert any("source_class" in p for p in problems)
    assert any("forbidden_claims" in p for p in problems)
