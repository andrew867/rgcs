"""R10.16B — semantic profile recovery tests (spec items 1-12)."""

import math

import pytest

from r1016.hierarchy import (REFERENCE_POINTS, prefix_proximity_test,
                             shared_prefix, stonehenge_avebury_relation)


# 1. decimal payload to octal exactness
def test_payload_decimal_to_octal_exact():
    assert format(587652, "o") == "2173604"
    assert format(4701217, "o") == "21736041"
    assert int("2173604", 8) == 587652


# 2. leading grouped zero preservation for octal-digit binary
def test_grouped_binary_preserves_leading_zeros():
    o = format(587652, "o")
    grouped = " ".join(format(int(d), "03b") for d in o)
    assert grouped == "010 001 111 011 110 000 100"
    assert all(len(g) == 3 for g in grouped.split())
    # regrouping must recover the value exactly
    assert int(grouped.replace(" ", ""), 2) == 587652


# 3 + 4. the two payload values
def test_stonehenge_and_avebury_payloads():
    assert REFERENCE_POINTS["Stonehenge"][0] == "587652"
    assert REFERENCE_POINTS["Avebury"][0] == "4701217"


# 5. Avebury = Stonehenge right-append child 1
def test_avebury_is_stonehenge_right_append_child_1():
    sa = stonehenge_avebury_relation()
    assert sa["right_append_preserved"] is True
    assert sa["right_append_child"] == "1"
    assert sa["avebury_payload_decimal"] == \
        sa["stonehenge_payload_decimal"] * 8 + 1
    assert sa["avebury_payload_octal"].startswith(
        sa["stonehenge_payload_octal"])
    # and it must be labelled as construction, not confirmation
    assert "CONSTRUCTED" in sa["what_it_does_NOT_establish"] or \
        "constructed" in sa["what_it_does_NOT_establish"]


# 6. fixed RGCS30 available but not privileged
def test_fixed_rgcs30_is_control_not_privileged():
    from r1016.search import FROZEN_BASELINE_VIEW, view_word_maps
    from r1016.project import STRICT_ANCHORS
    views = {m["view"] for m in view_word_maps(list(STRICT_ANCHORS))}
    assert FROZEN_BASELINE_VIEW in views          # still available
    assert len(views) > 1                          # not the only one


# 7. no profile silently drops leftover/control bits
def test_octal_fold_rules_preserve_a_control_bit():
    from r1016.profiles import FOLD_RULES
    for name, f in FOLD_RULES.items():
        for d in range(8):
            q = f(d)
            assert 0 <= q <= 3, (name, d)
    # every octal digit carries 3 bits: 2 of child + 1 of control,
    # so the fold must be 2-to-1 and the control bit recoverable
    for name, f in FOLD_RULES.items():
        counts = {}
        for d in range(8):
            counts.setdefault(f(d), []).append(d)
        assert all(len(v) == 2 for v in counts.values()), name


# 8. no place-name enrichment before geometric scoring
def test_no_place_enrichment_precedes_scoring():
    from r1016.atlas import PLACE_ENRICHMENT_STATUS
    assert "DEFERRED" in PLACE_ENRICHMENT_STATUS
    assert "coordinates" in PLACE_ENRICHMENT_STATUS.lower()


# 9. no mesh warp
def test_no_mesh_warp_anywhere_in_r1016():
    import pathlib
    root = pathlib.Path(__file__).resolve().parents[2] / "r1016"
    banned = ("warp", "nonlinear_fit", "curve_fit", "least_squares")
    for f in root.rglob("*.py"):
        low = f.read_text(encoding="utf-8").lower()
        for b in banned:
            for line in low.splitlines():
                if b in line:
                    assert ("no " + b in line or "not" in line
                            or "#" in line or '"' in line
                            or "never" in line), (f.name, b, line[:70])


# 10. strict anchor gate enforced
def test_strict_gate_constant_and_enforcement():
    """The R10.18 authority retains exactly three strict anchors."""
    from r1016.project import (RAW_TRANSPORT_ANCHORS, STRICT_ANCHORS,
                               STRICT_GATE_RMS_KM)
    assert STRICT_GATE_RMS_KM == 25.0
    expected = {"165876523", "168930443", "167849523"}
    assert set(STRICT_ANCHORS) == expected
    assert set(RAW_TRANSPORT_ANCHORS) == expected


# 11. path-vector compact/refined relationships detected
def test_path_structure_degrades_honestly_without_input(monkeypatch):
    """No operator data in the tree: it must SAY so, not fabricate."""
    from r1016.run_r1016b import (STRUCTURE_INPUT_ENV,
                                  path_structure_report)
    monkeypatch.delenv(STRUCTURE_INPUT_ENV, raising=False)
    rows = path_structure_report()
    assert len(rows) == 1
    assert rows[0]["relation"].startswith("NOT_SUPPLIED_SET_")


def test_path_vector_structure_detected(tmp_path, monkeypatch):
    """Detection works on SYNTHETIC wires; no operator path-vector
    value is stored in this test or anywhere in the tracked tree."""
    import json

    from r1016.run_r1016b import (STRUCTURE_INPUT_ENV,
                                  path_structure_report)
    # synthetic: payload 2173604 octal, child right-append of 1
    compact = "16" + str(int("2173604", 8)) + "3"
    refined = "16" + str(int("21736041", 8)) + "3"
    cfg = tmp_path / "s.json"
    cfg.write_text(json.dumps({
        "pairs": [[compact, refined]],
        "prefix_families": {"synthetic": [compact, refined]}}),
        encoding="utf-8")
    monkeypatch.setenv(STRUCTURE_INPUT_ENV, str(cfg))
    rows = path_structure_report()
    pair = [r for r in rows if r["compact"] == compact][0]
    assert pair["relation"] == "RIGHT_APPEND_CHILD"
    assert pair["appended_symbols"] == "1"
    fam = [r for r in rows
           if r["relation"].startswith("SHARED_OCTAL")][0]
    assert int(fam["relation"].split("_")[3]) == 7


# 12. no private personal records beyond authorised vectors
def test_no_private_personal_records_in_r1016_source():
    import pathlib

    from rgcs_surface_wave.privacy import (FORBIDDEN_PHRASES,
                                           WIRE_SIGNATURE,
                                           public_wire_allowlist)
    allow = public_wire_allowlist()
    root = pathlib.Path(__file__).resolve().parents[2] / "r1016"
    for f in root.rglob("*.py"):
        text = f.read_text(encoding="utf-8")
        for m in WIRE_SIGNATURE.finditer(text):
            assert m.group(0) in allow, (f.name, "unknown wire")
        for p in FORBIDDEN_PHRASES:
            assert p.lower() not in text.lower(), (f.name, p)


# --- the decisive geometry-free result -------------------------------
def test_prefix_proximity_contradiction_is_the_controlling_result():
    r = prefix_proximity_test()
    assert r["geometry_free"] is True
    assert r["hierarchy_consistent"] is False
    assert r["spearman_rho_prefix_vs_distance"] > 0, \
        "a hierarchy needs a strongly NEGATIVE correlation"
    assert r["verdict"] == "PREFIX_PROXIMITY_CONTRADICTION"
    w = r["sharpest_contradiction"]
    assert w is not None and w["distance_excess_km"] > 1000


def test_prefix_test_excludes_the_constructed_point_by_default():
    """Avebury is constructed from Stonehenge; including it would be
    circular."""
    r = prefix_proximity_test()
    assert all("Avebury" not in row["pair"] for row in r["rows"])
    r2 = prefix_proximity_test(exclude_constructed=False)
    assert any("Avebury" in row["pair"] for row in r2["rows"])


def test_shared_prefix_helper():
    assert shared_prefix("2173604", "21736041") == 7
    assert shared_prefix("2173604", "3320164") == 0


# --- canonical surface word bridge (R10.16B patch) -------------------
def test_resolver_matches_specification():
    from r1016.surface_word import ANCHOR_RECORDS, resolve_surface_word
    expect = {"Stonehenge": (165876523, "raw_vector"),
              "Toronto": (168930443, "canonical_packet_or_candidate"),
              "Erie": (167849523, "canonical_packet_or_candidate")}
    assert set(ANCHOR_RECORDS) == set(expect)
    for name, (word, src) in expect.items():
        got_word, got_src = resolve_surface_word(ANCHOR_RECORDS[name])
        assert got_word == word, name
        assert got_src == src, name


def test_resolver_falls_back_to_raw_without_status():
    from r1016.surface_word import resolve_surface_word
    w, src = resolve_surface_word(
        {"raw_vector": "165876523",
         "canonical_packet_or_candidate": "999999999",
         "current_status": "SOMETHING_ELSE"})
    assert (w, src) == (165876523, "raw_vector")


def test_removed_anchor_is_absent_from_current_authority():
    from r1016.surface_word import ANCHOR_RECORDS, resolution_report
    assert "Montreal" not in ANCHOR_RECORDS
    report = resolution_report()
    assert report["anchors_rebound"] == 0
    assert report["rebound"] == []


def test_strict_anchors_use_resolved_surface_words():
    from r1016.project import RAW_TRANSPORT_ANCHORS, STRICT_ANCHORS
    assert STRICT_ANCHORS == RAW_TRANSPORT_ANCHORS
    assert len(STRICT_ANCHORS) == 3


def test_surface_metric_uses_only_current_authority():
    from r1016.hierarchy import SURFACE_ANCHORS
    assert set(SURFACE_ANCHORS) == {"Stonehenge", "Toronto", "Erie"}
