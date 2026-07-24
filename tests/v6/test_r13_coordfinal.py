"""P37 — the finalized icosahedral-packet coordinate codec: a symbol-level
bijection, a one-to-many alias set, and the refusals that keep an alias
from being read as a destination."""

from __future__ import annotations

import pytest

from r12 import icosapacket as ip
from r13 import coordfinal as C


# --- the symbol-level bijection is real POWER ----------------------------

def test_raw_packet_encode_decode_round_trip_is_a_bijection():
    for value in ip.REGISTERED_VALUES:
        packet = C.GRAMMAR.encode(value)
        assert C.GRAMMAR.decode(packet) == value
        assert C.round_trip_ok(value)
    # a spread of arbitrary VALID packet words also round-trips exactly
    valid_words = (
        0, 1, 123456,
        ip.encode(0, "00000000000", 0),
        ip.encode(19, "33333333333", 7),   # the largest valid packet word
    )
    for value in valid_words:
        assert C.GRAMMAR.decode(C.GRAMMAR.encode(value)) == value


def test_a_value_that_is_in_range_but_not_a_valid_packet_is_refused():
    # all-ones is in the 30-bit range but its face field is 31, which the
    # icosahedron has no face for: refused, not folded onto a face
    with pytest.raises(C.CoordFinalError):
        C.GRAMMAR.encode(ip.WORD_MODULUS - 1)


def test_encode_from_symbols_round_trips():
    packet = C.GRAMMAR.encode_symbols(4, "33012032222", 3)
    assert packet.as_symbols() == (4, "33012032222", 3)
    assert C.GRAMMAR.decode(packet) == packet.word


def test_an_out_of_range_value_is_refused():
    with pytest.raises(C.CoordFinalError):
        C.GRAMMAR.encode(ip.WORD_MODULUS)
    with pytest.raises(C.CoordFinalError):
        C.GRAMMAR.encode(-1)


# --- the coordinate level is a one-to-many alias set ---------------------

def test_alias_set_has_size_greater_than_one():
    packet = C.GRAMMAR.encode(ip.REGISTERED_VALUES[0])
    aliases = C.GRAMMAR.decode_to_alias_set(packet)
    assert len(aliases) == C.FRAME_COUNT
    assert C.FRAME_COUNT > 1
    # the distinct candidate COORDINATES are also more than one
    assert len(C.GRAMMAR.alias_coordinates(packet)) > 1


def test_true_candidate_is_not_distinguishable_within_the_set():
    packet = C.GRAMMAR.encode(ip.REGISTERED_VALUES[1])
    aliases = C.GRAMMAR.decode_to_alias_set(packet)
    nominal = C.GRAMMAR.nominal_candidate(packet)
    # the nominal ("true") candidate is just one member of the set
    assert nominal in aliases
    assert sum(1 for a in aliases if a.is_nominal) == 1
    # and nothing in the packet distinguishes it from its peers
    assert C.GRAMMAR.true_candidate_is_distinguishable(packet) is False


def test_different_frames_give_different_coordinates():
    packet = C.GRAMMAR.encode(ip.REGISTERED_VALUES[2])
    coords = [a.coordinate for a in C.GRAMMAR.decode_to_alias_set(packet)]
    # a one-to-many map: many frames, many coordinates for one packet
    assert len(set(coords)) > 1


# --- the two load-bearing refusals ---------------------------------------

def test_refuse_alias_as_destination_raises():
    packet = C.GRAMMAR.encode(ip.REGISTERED_VALUES[0])
    aliases = C.GRAMMAR.decode_to_alias_set(packet)
    with pytest.raises(C.CoordFinalError):
        C.refuse_alias_as_destination(aliases)


def test_refuse_numeric_match_as_authentication_raises():
    with pytest.raises(C.CoordFinalError):
        C.refuse_numeric_match_as_authentication(165879123, 165879123)


# --- determinism and hash versioning -------------------------------------

def test_encoding_is_deterministic():
    for value in ip.REGISTERED_VALUES:
        assert C.GRAMMAR.encode(value) == C.GRAMMAR.encode(value)
        assert C.is_deterministic(value)


def test_alias_set_is_deterministic():
    packet = C.GRAMMAR.encode(ip.REGISTERED_VALUES[0])
    first = C.GRAMMAR.decode_to_alias_set(packet)
    second = C.GRAMMAR.decode_to_alias_set(packet)
    assert first == second


def test_grammar_is_versioned_by_a_hash():
    h = C.GRAMMAR.version_hash
    assert isinstance(h, str) and len(h) == 64
    # two grammars with the same parameters share the version hash
    assert C.PacketGrammar().version_hash == h
    # a grammar with a different coordinate space is a different codec
    other = C.PacketGrammar(coord_modulus=C.COORD_MODULUS << 1)
    assert other.version_hash != h


# --- the report ----------------------------------------------------------

def test_report_states_the_verdict_and_mentions_the_alias_set():
    rep = C.coordfinal_report()
    assert rep["verdict"] == "COORDINATE_CODEC_FINALIZED_ALIAS_SET_ONLY"
    assert rep["measured_here"] == "nothing"
    assert rep["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert rep["claim_class"] == "REPOSITORY_COMPUTATIONAL_RESULT"
    assert rep["symbol_round_trip_ok"] is True
    assert rep["deterministic"] is True
    assert rep["alias_set_size"] == C.FRAME_COUNT
    assert rep["true_candidate_distinguishable"] is False
    assert "alias set" in rep["what_this_does_not_say"].lower()


def test_coordfinal_module_imports_from_r13():
    from r13 import coordfinal          # noqa: F401
    assert coordfinal.VERDICT == "COORDINATE_CODEC_FINALIZED_ALIAS_SET_ONLY"
