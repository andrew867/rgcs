"""R10.16C — surface address metric correction tests."""

import pytest

from r1016.addressing import (AddressingError, SurfaceWord,
                              TransportWire, active_split,
                              resolve_surface_word, surface_prefix)


def test_surface_octal10_matches_specified_values():
    for word, expected in ((165876523, "1170611453"),
                           (168500683, "1202616713"),
                           (167849523, "1200227063"),
                           (168930443, "1204326213")):
        assert SurfaceWord(word).surface_octal10 == expected


def test_surface_octal10_is_always_ten_digits():
    for w in (0, 1, 165876523, (1 << 30) - 1):
        assert len(SurfaceWord(w).surface_octal10) >= 10


def test_active_split_refuses_a_surface_word():
    with pytest.raises(AddressingError, match="category error"):
        active_split(SurfaceWord(168500683))
    with pytest.raises(AddressingError):
        active_split("168500683")
    rec = active_split(TransportWire("165876523"))
    assert rec["header"] == "16" and rec["terminal"] == "3"


def test_resolver_returns_a_surface_word_not_a_wire():
    sw = resolve_surface_word(
        {"raw_vector": "165879243",
         "canonical_packet_or_candidate": "168500683",
         "current_status": "CORRECTED_WIRE_TO_CANONICAL_CANDIDATE"})
    assert isinstance(sw, SurfaceWord)
    assert sw.value == 168500683
    assert sw.surface_octal10 == "1202616713"


def test_payload_octal_is_marked_diagnostic_only():
    rec = TransportWire("168500683").record()
    assert rec["payload_octal"] == "3174224"       # the wrong reading
    assert rec["payload_octal_scope"] == \
        "SURFACE_WORD_REPARSED_AS_WIRE_DIAGNOSTIC"


def test_f5_q22_s3_decompose_the_surface_word():
    for w in (165876523, 168500683, 167849523, 168930443):
        s = SurfaceWord(w)
        assert (s.F5 << 25) | (s.Q22 << 3) | s.S3 == w


def test_face_field_separates_the_continents():
    """Independent structural check: the NA trio share a face."""
    assert SurfaceWord(165876523).F5 == 4          # Stonehenge
    for w in (168930443, 168500683, 167849523):    # Toronto/Mtl/Erie
        assert SurfaceWord(w).F5 == 5


def test_surface_hierarchy_is_negative_and_cleanly_separated():
    from r1016.hierarchy import surface_prefix_proximity_test
    r = surface_prefix_proximity_test()
    assert abs(r["spearman_rho_prefix_vs_distance"] + 0.8783) < 1e-4
    assert r["hierarchy_consistent"] is True
    assert r["cleanly_separated_by_prefix_level"] is True
    assert r["verdict"] == "SURFACE_OCTAL10_HIERARCHY_NEGATIVE_RHO"
    assert max(r["levels"]["3"]) < min(r["levels"]["1"])


def test_toronto_erie_share_three_symbols_not_zero():
    """The specific retraction."""
    assert surface_prefix(SurfaceWord(168930443),
                          SurfaceWord(167849523)) == 3


def test_payload_prefix_metric_is_retracted_but_preserved():
    from r1016.hierarchy import payload_prefix_diagnostic
    d = payload_prefix_diagnostic()
    assert d["status"] == "RETRACTED_AS_A_HIERARCHY_METRIC"
    assert d["scope"] == "SURFACE_WORD_REPARSED_AS_WIRE_DIAGNOSTIC"
    assert d["spearman_rho_prefix_vs_distance"] > 0     # the wrong sign


def test_geometric_gate_is_unchanged_by_the_metric_fix():
    """The projector already consumed surface words numerically."""
    from r1016.search import run
    res = run(contexts=("TRAINED",))
    assert res["survivor_count"] == 0
    assert res["best"]["rms_km"] > 1000
