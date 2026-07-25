"""P10 — seven-field semantic expansion.

Expand<->compact POWER round-trip, variable-depth epoch omission, explicit
resolver token counts, determinism, and schema conformance (with the
shell_epoch $ref).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cwatlas.r1082 import route_core as rc
from cwatlas.r1082 import semantic_expand as se

SCHEMA_DIR = Path(__file__).resolve().parents[3] / "cwatlas" / "r1082" / "schemas"


@pytest.fixture(scope="module")
def address_validator():
    jsonschema = pytest.importorskip("jsonschema")
    referencing = pytest.importorskip("referencing")
    from referencing import Registry, Resource

    def load(name):
        return json.loads((SCHEMA_DIR / name).read_text("utf-8"))

    registry = Registry().with_resources([
        ("shell_epoch.schema.json",
         Resource.from_contents(load("shell_epoch.schema.json"))),
    ])
    return jsonschema.Draft202012Validator(
        load("semantic_address.schema.json"), registry=registry)


@pytest.fixture(scope="module")
def shell_epoch_validator():
    jsonschema = pytest.importorskip("jsonschema")
    return jsonschema.Draft202012Validator(
        json.loads((SCHEMA_DIR / "shell_epoch.schema.json").read_text("utf-8")))


# -- seven-field expansion --------------------------------------------------

def test_expand_produces_seven_fields():
    addr = se.expand(rc.parse_five_token("165876523"))
    d = addr.to_dict()
    assert set(d) == {"namespace", "stellar_system", "body", "root_face",
                      "recursive_path", "barycentric", "shell_epoch"}
    assert d["root_face"] == 1
    assert d["recursive_path"] == [1, 0, 1, 1, 2, 7, 1, 0, 1]
    assert d["shell_epoch"]["shell"]["index"] == 5
    assert d["shell_epoch"]["compressed_epoch"]["payload"]["coarse"] == 2


def test_resolver_plan_token_counts_are_explicit():
    counts = {r.field_name: r.token_count for r in se.RESOLVER_PLAN}
    assert counts["namespace"] == 0  # absent in short local address
    assert counts["root_face"] == 1
    assert counts["recursive_path"] == 3  # one token != one field
    assert counts["shell_epoch"] == 1
    assert sum(counts.values()) == rc.FIVE_TOKEN


# -- expand <-> compact round-trip (POWER) ----------------------------------

def test_expand_compact_roundtrip():
    r = rc.parse_five_token("165876523")
    addr = se.expand(r)
    assert se.compact(addr).tokens == r.tokens


@pytest.mark.parametrize("text", ["0165876523", "01|65|89|27|43",
                                  "12|33|07|58|91"])
def test_roundtrip_various(text):
    r = rc.parse(text, expect_tokens=5)
    assert se.compact(se.expand(r)).tokens == r.tokens


# -- variable depth: short packets omit the epoch ---------------------------

def test_short_packet_omits_epoch():
    r = rc.parse("01|65|87|65")  # four tokens: no shell-epoch token
    addr = se.expand(r)
    assert addr.shell_epoch["compressed_epoch"] is None
    assert "shell_epoch.compressed_epoch" in addr.unresolved
    # and it still round-trips
    assert se.compact(addr).tokens == r.tokens


def test_absent_prefixes_recorded_as_unresolved():
    addr = se.expand(rc.parse_five_token("165876523"))
    assert {"namespace", "stellar_system", "body"} <= set(addr.unresolved)


# -- shell supplies the radius ----------------------------------------------

def test_shell_supplies_radius_never_missing():
    addr = se.expand(rc.parse_five_token("165876523"))
    assert addr.shell_epoch["shell"]["radius_m"] is not None
    assert addr.shell_epoch["shell"]["radius_m"] == se.resolve_shell_radius_m(5)


# -- negatives --------------------------------------------------------------

def test_face_out_of_range_refused():
    # token[0]=45 -> face 45 > 19: refused (not a valid icosahedral face)
    with pytest.raises(rc.RouteError):
        se.expand(rc.parse("45|65|87|65|23"))


def test_missing_conventional_epoch_refused():
    with pytest.raises(rc.RouteError):
        se.expand(rc.parse_five_token("165876523"),
                  conventional_epoch={"value": "no-timescale"})


# -- determinism + schema ---------------------------------------------------

def test_determinism():
    r = rc.parse_five_token("165876523")
    assert se.expand(r).to_dict() == se.expand(r).to_dict()


def test_conforms_to_schemas(address_validator, shell_epoch_validator):
    addr = se.expand(rc.parse_five_token("165876523"))
    shell_epoch_validator.validate(addr.shell_epoch)
    address_validator.validate(addr.to_dict())
    # short packet also conforms
    address_validator.validate(se.expand(rc.parse("01|65|87|65")).to_dict())


def test_report_seals_claims():
    r = se.semantic_expand_report()
    assert r["measured_here"] == "nothing"
    assert r["source_origin"] == "SOURCE_ORIGIN_NOT_VALIDATED"
    assert r["total_tokens"] == rc.FIVE_TOKEN
    assert len(r["seven_fields"]) == 7
