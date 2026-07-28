"""R10.11D acceptance — E3 octal frame + affine transition envelope."""

from __future__ import annotations

import pytest

from r1011 import e3_frame as e3
from r1011 import segmented_codec as sc
from r1011.affine_envelope import (
    AffineEnvelopeError,
    HYPOTHESIS_STATUS,
    PROBES,
    envelope_lookup,
)

REQUIRED_PARSES = {
    1687209343: {"e3": 4, "states": (10, 9, 4), "children": (6,),
                 "terminal": 3},
    16752349783: {"e3": 4, "states": (30, 63, 58), "children": (4, 2),
                  "terminal": 3},
    16782953437: {"e3": 4, "states": (42, 43, 4), "children": (5, 7),
                  "terminal": 7},
}


def test_required_parses_exact():
    for wire, exp in REQUIRED_PARSES.items():
        p = e3.parse(wire)
        assert p.e3 == exp["e3"]
        assert p.states == exp["states"]
        assert p.children == exp["children"]
        assert p.terminal == exp["terminal"]
        assert e3.encode(p) == wire                    # exact inverse


def test_e3_preserves_r1011c_states_and_transitions():
    # every R10.11C pair state triple reappears with E3 = 0b0 + E2
    pairs = [(165876523, 1643789253, 5), (168930443, 1672875493, 5),
             (165892733, 1658274383, 6), (165823973, 1658729343, 6)]
    for c, r, child in pairs:
        pc, pr = e3.parse(c), e3.parse(r)
        assert pc.states == sc.decode_compact(c).states
        assert pr.states == sc.decode_refined(r).states
        assert pr.children == (child,)
        assert pc.e3 == int(sc.decode_compact(c).e2, 2)   # leading zero
        assert pr.e3 == pc.e3
        # transitions still hold slot-by-slot
        assert tuple(sc.T_SPARSE[(s, child)] for s in pc.states) == pr.states


def test_e3_semantics_guard():
    assert "2 bits" in e3.E3_SEMANTICS
    assert "UNRESOLVED" in e3.E3_SEMANTICS


def test_terminal_guard_never_conflates():
    p = e3.parse(16782953437)
    assert p.terminal == 7
    assert p.terminal_is_surface_class is False
    assert e3.parse(1687209343).terminal_is_surface_class is True


def test_width_family_covers_entire_decimal_corpus():
    # the E3 width family (21 + 3*depth bits) contains every decimal
    # payload for the CURRENT corpus depths 0..3; the 8-vs-10 per-level
    # ratio erodes coverage from depth 4 (10-digit payloads), which is
    # exactly why the parser refuses oversized payloads instead of
    # truncating them
    for depth in range(0, 4):
        assert 10 ** (6 + depth) <= 2 ** (21 + 3 * depth)
    assert 10 ** (6 + 4) > 2 ** (21 + 3 * 4)      # erosion begins
    with pytest.raises(e3.E3FrameError, match="width family"):
        e3.parse(int("16" + "9999999999" + "3"))   # depth-4 overflow
    # and the previous E2 frame demonstrably did NOT cover the corpus
    assert 8720934 >= 2 ** 23           # the 1687209343 payload overflow


def test_affine_envelope_typed_lookup():
    known = envelope_lookup(15, 5)
    assert known["evidence_status"] == "SOURCE_KNOWN"
    assert known["output"] == 5
    cons = envelope_lookup(0, 5)
    assert cons["evidence_status"] == "AFFINE_FAMILY_CONDITIONAL_CONSENSUS"
    assert "CONDITIONAL" in cons["caveat"]
    und = envelope_lookup(2, 5)
    assert und["evidence_status"] == "UNDERDETERMINED"
    assert len(und["possible_outputs"]) == 32
    assert "not the recovered source table" in HYPOTHESIS_STATUS


def test_children_other_than_5_6_refused():
    for child in (0, 1, 2, 3, 4, 7):
        with pytest.raises(AffineEnvelopeError):
            envelope_lookup(10, child)


def test_probes_recorded_and_consistent_with_envelope():
    p5 = PROBES[(165872393, 5)]
    assert p5["position_1_output"] == 5 and p5["pos2_xor_pos3"] == 58
    p6 = PROBES[(165879633, 6)]
    assert p6["position_1_output"] == 49 and p6["pos2_xor_pos3"] == 48
    # position-1 states of the probe compacts are 15 in both cases,
    # whose child-5/6 outputs are SOURCE_KNOWN 5 and 49 — consistent
    assert e3.parse(165872393).states[0] == 15
    assert e3.parse(165879633).states[0] == 15
    assert envelope_lookup(15, 5)["output"] == 5
    assert envelope_lookup(15, 6)["output"] == 49


def test_firewalls_no_geography_no_lunar_selection():
    import inspect
    from r1011 import affine_envelope as ae
    src = inspect.getsource(ae) + inspect.getsource(e3)
    for banned in ("latitude", "longitude", "Ohio", "gazetteer"):
        assert banned not in src
