"""P09 — five-token base-100 parser, reconstruction, prefix tree.

POWER round-trip (five-token + variable depth), negatives (malformed refused),
determinism, and schema conformance.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cwatlas.r1082 import route_core as rc

SCHEMA_DIR = Path(__file__).resolve().parents[3] / "cwatlas" / "r1082" / "schemas"


@pytest.fixture(scope="module")
def route_validator():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(
        (SCHEMA_DIR / "source_route_core.schema.json").read_text("utf-8"))
    return jsonschema.Draft202012Validator(schema)


# -- exact five-token parse -------------------------------------------------

def test_parse_bare_digits_five_tokens():
    r = rc.parse_five_token("165876523")
    assert r.tokens == (1, 65, 87, 65, 23)
    assert r.depth == 5


def test_parse_pipe_form_matches_bare():
    a = rc.parse("165876523", expect_tokens=5)
    b = rc.parse("01|65|87|65|23")
    assert a.tokens == b.tokens == (1, 65, 87, 65, 23)


def test_leading_zero_preserved_in_canonical_raw():
    r = rc.parse_five_token("165876523")
    # odd-length input is left-padded to even; the leading zero is preserved
    assert r.raw == "0165876523"
    assert r.to_wire() == "01|65|87|65|23"
    assert r.leading_zero_policy == rc.POLICY_LEFT_PAD


# -- POWER round-trip -------------------------------------------------------

def test_roundtrip_raw_and_wire():
    r = rc.parse_five_token("165876523")
    assert rc.parse(rc.reconstruct(r)).tokens == r.tokens
    assert rc.parse(rc.reconstruct(r, wire=True)).tokens == r.tokens
    assert r.to_raw() == "0165876523"


@pytest.mark.parametrize("text,depth", [
    ("01", 1), ("0102", 2), ("010203", 3), ("0102030405", 5),
    ("010203040506", 6),
])
def test_variable_depth_roundtrip(text, depth):
    r = rc.parse(text)
    assert r.depth == depth
    assert rc.parse(r.to_raw()).tokens == r.tokens


# -- prefix tree ------------------------------------------------------------

def test_prefix_tree_lookup_and_common_prefix():
    routes = [rc.parse(f"01|65|89|27|{t}").tokens for t in ("43", "63", "83")]
    tree = rc.RoutePrefixTree()
    for r in routes:
        tree.insert(r)
    assert all(tree.contains(r) for r in routes)
    assert not tree.contains((1, 65, 89, 27, 99))
    assert tree.longest_common_prefix() == (1, 65, 89, 27)
    assert tree.has_prefix((1, 65, 89))
    assert tree.descendants((1, 65, 89, 27)) == 3


def test_ancestry_siblings_compare():
    a = (1, 65, 89, 27, 43)
    b = (1, 65, 89, 27, 63)
    assert rc.common_prefix(a, b) == (1, 65, 89, 27)
    assert rc.common_prefix_length(a, b) == 4
    assert rc.is_ancestor((1, 65, 89, 27), a)
    assert not rc.is_ancestor(a, a)  # strict prefix only
    assert rc.are_siblings(a, b)
    assert not rc.are_siblings(a, (1, 65, 89, 27))
    assert rc.compare(a, b) == -1 and rc.compare(b, a) == 1
    assert rc.compare(a, a) == 0


def test_line_like_terminal_progression():
    routes = [rc.parse(f"01|65|89|27|{t}").tokens for t in ("43", "63", "83")]
    assert rc.is_line_like_terminal_progression(routes)  # step 20
    # a non-linear terminal set is not line-like
    broken = [rc.parse(f"01|65|89|27|{t}").tokens for t in ("43", "63", "90")]
    assert not rc.is_line_like_terminal_progression(broken)
    # a different prefix breaks the shared-prefix requirement
    mixed = [rc.parse("01|65|89|27|43").tokens, rc.parse("02|65|89|27|63").tokens]
    assert not rc.is_line_like_terminal_progression(mixed)


# -- negatives (malformed refused) ------------------------------------------

def test_wrong_token_count_refused():
    with pytest.raises(rc.RouteError):
        rc.parse_five_token("0102")  # only two tokens
    with pytest.raises(rc.RouteError):
        rc.parse("010203", expect_tokens=5)


def test_non_digit_refused():
    with pytest.raises(rc.RouteError):
        rc.parse("01|6x|87|65|23")


def test_odd_length_refused_under_explicit_policy():
    with pytest.raises(rc.RouteError):
        rc.parse("165876523", leading_zero_policy=rc.POLICY_EXPLICIT)
    # but LEFT_PAD_TO_EVEN accepts the same odd-length string
    assert rc.parse("165876523").tokens == (1, 65, 87, 65, 23)


def test_empty_and_bad_policy_refused():
    with pytest.raises(rc.RouteError):
        rc.parse("||")
    with pytest.raises(rc.RouteError):
        rc.parse("0102", leading_zero_policy="NOPE")


# -- determinism + schema ---------------------------------------------------

def test_determinism():
    a = rc.parse_five_token("165876523").to_dict()
    b = rc.parse_five_token("165876523").to_dict()
    assert a == b


def test_conforms_to_schema(route_validator):
    route_validator.validate(rc.parse_five_token("165876523").to_dict())
    route_validator.validate(rc.parse("0102030405").to_dict())


def test_report_seals_claims():
    r = rc.route_core_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_effects"] == "PHYSICAL_EFFECTS_NOT_CLAIMED"
    assert r["source_origin"] == "SOURCE_ORIGIN_NOT_VALIDATED"
    assert r["claim_class"] == "MATHEMATICAL_TRANSLATION"
    assert r["evidence_class"] == "DERIVED_MATHEMATICS"
