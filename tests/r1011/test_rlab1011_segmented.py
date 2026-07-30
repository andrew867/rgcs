"""R10.11C acceptance — locked segmented codec for the 16...3 family."""

from __future__ import annotations

import pytest

from r1011 import segmented_codec as sc

PAIRS = [(165876523, 1643789253, 5), (168930443, 1672875493, 5),
         (165892733, 1658274383, 6), (165823973, 1658729343, 6)]


def test_all_four_pairs_transition_exactly():
    for compact_raw, refined_raw, child in PAIRS:
        c = sc.decode_compact(compact_raw)
        r = sc.decode_refined(refined_raw)
        assert r.child == child
        assert r.e2 == c.e2                       # E2 preserved
        assert sc.child_apply(c, child) == r      # forward through T
        assert sc.parent_reduce(r) == c           # inverse through T^-1


def test_round_trips_exact():
    for compact_raw, refined_raw, _ in PAIRS:
        assert sc.encode_compact(sc.decode_compact(compact_raw)) == compact_raw
        assert sc.encode_refined(sc.decode_refined(refined_raw)) == refined_raw


def test_middle_state_23_checksum():
    seg = sc.decode_compact(165872393)
    assert seg.states[1] == 23


def test_sparse_table_and_refusals():
    assert len(sc.T_SPARSE) == 12
    assert len(sc.T_INVERSE) == 12                # per-child injective
    assert "UNDERDETERMINED" in sc.TABLE_STATUS
    # unknown cells refuse, never guess
    c = sc.decode_compact(165652893)              # states [10, 0, 41]
    with pytest.raises(sc.SegmentedCodecError, match="UNKNOWN cell"):
        sc.child_apply(c, 5)
    with pytest.raises(sc.SegmentedCodecError, match="UNKNOWN cell"):
        sc.parent_reduce(sc.RefinedSeg("10", (0, 1, 2), 5))


def test_family_gate_and_field_semantics():
    with pytest.raises(sc.SegmentedCodecError, match="16...3 family"):
        sc.decode_compact(683742917)              # not 16...3
    seg = sc.decode_compact(165876523)
    assert seg.e2 in ("00", "01", "10", "11")     # epoch/shell bits, no face map
    assert sc.HEADER_OCTAL_BITS == ("001", "110")  # Sol|Terra, locked


def test_monolithic_profile_preserved_as_historical():
    m = sc.MONOLITHIC_COMPATIBILITY
    assert m["status"] == "FIELDS_DO_NOT_CORRESPOND"
    assert "EXACT_OLD_STRUCTURAL_PROFILE" in m["disposition"]
    # the old reading still round-trips (nothing was deleted)
    from rgcs_coordinate.codecs import federation_terra_30 as t10
    tr = t10.decode(165876523)
    assert t10.encode(tr.face_id, tr.q22_path, tr.extracted_shell) == 165876523


def test_no_geographic_or_holdout_selection():
    import inspect
    src = inspect.getsource(sc)
    for banned in ("Stafford", "Wrexham", "lat", "lon", "Ohio",
                   "165892323", "165829473"):
        assert banned not in src
