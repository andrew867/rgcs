"""P37 -- route prefixes: label-only round-trip, malformed refused, determinism."""

from __future__ import annotations

import pytest

from cwatlas import route_prefix as rp
from cwatlas.claims import ClaimClass

VECTOR = "v=1.0.0;codec=CW-GEO-1;body=EARTH;frame=WGS84;epoch=2020.0;lat=5;lon=7"


# --- round-trip -------------------------------------------------------------

def test_prefix_format_parse_round_trip():
    p = rp.make_prefix("terra", "uk", "wiltshire", "site")
    text = p.format()
    assert text == "terra:d3/uk/wiltshire/site"
    assert rp.parse_prefix(text) == p


def test_depth_zero_round_trip():
    p = rp.make_prefix("sol")
    assert p.format() == "sol:d0"
    assert p.depth == 0
    assert rp.parse_prefix("sol:d0") == p


def test_wrap_split_round_trip():
    p = rp.make_prefix("terra", "a", "b")
    routed = rp.wrap(VECTOR, p)
    got_prefix, got_vector = rp.split(routed)
    assert got_prefix == p
    assert got_vector == VECTOR


# --- POWER: a namespace/route never changes the numeric address -------------

def test_strip_returns_untouched_vector():
    routed = rp.wrap(VECTOR, rp.make_prefix("terra", "deep", "path", "here"))
    assert rp.strip(routed) == VECTOR


def test_rewrap_preserves_numeric_address_across_namespaces():
    routed = rp.wrap(VECTOR, rp.make_prefix("terra", "x"))
    moved = rp.rewrap(routed, "sol", "y", "z")
    # The namespace and route changed; the numbers did not.
    assert rp.strip(moved) == rp.strip(routed) == VECTOR
    assert rp.split(moved)[0].namespace == "sol"


def test_all_known_namespaces_preserve_address():
    for ns in sorted(rp.KNOWN_NAMESPACES):
        routed = rp.wrap(VECTOR, rp.make_prefix(ns, "seg"))
        assert rp.strip(routed) == VECTOR


# --- determinism ------------------------------------------------------------

def test_format_is_deterministic():
    p = rp.make_prefix("terra", "a", "b", "c")
    assert p.format() == p.format() == rp.parse_prefix(p.format()).format()


# --- negative: malformed refused --------------------------------------------

def test_unknown_namespace_refused_by_default():
    with pytest.raises(rp.RoutePrefixError):
        rp.make_prefix("moon", "x")


def test_custom_namespace_allowed_with_flag():
    p = rp.make_prefix("luna", "x", allow_custom=True)
    assert p.namespace == "luna"


def test_uppercase_namespace_refused():
    with pytest.raises(rp.RoutePrefixError):
        rp.make_prefix("Terra", allow_custom=True)


def test_depth_mismatch_refused():
    # Declared d3 but only two segments present.
    with pytest.raises(rp.RoutePrefixError):
        rp.parse_prefix("terra:d3/a/b")


def test_missing_colon_refused():
    with pytest.raises(rp.RoutePrefixError):
        rp.parse_prefix("terra/d0")


def test_missing_depth_token_refused():
    with pytest.raises(rp.RoutePrefixError):
        rp.parse_prefix("terra:")


def test_bad_depth_token_refused():
    with pytest.raises(rp.RoutePrefixError):
        rp.parse_prefix("terra:x2/a/b")


def test_bad_segment_refused():
    with pytest.raises(rp.RoutePrefixError):
        rp.make_prefix("terra", "has space")


def test_wrap_rejects_delimiter_in_vector():
    with pytest.raises(rp.RoutePrefixError):
        rp.wrap("bad|vector", rp.make_prefix("terra"))


def test_split_requires_delimiter():
    with pytest.raises(rp.RoutePrefixError):
        rp.split("terra:d0-no-delimiter")


# --- governance report ------------------------------------------------------

def test_report_shape():
    r = rp.route_prefix_report()
    assert r["claim_class"] == ClaimClass.MATHEMATICAL_TRANSLATION.value
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"
    assert "verdict" in r
