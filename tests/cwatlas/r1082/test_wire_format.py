"""P11 — packed shell-epoch composite and variable-depth wire format.

Encode/decode POWER round-trip at every depth, shell-supplied radius, the
explicit 8<->0 transition flag, ambiguous-legacy alias set, mandatory
conventional epoch, determinism, and schema conformance.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cwatlas.codec_base100 import encode as b100_encode
from cwatlas.r1082 import wire_format as wf
from cwatlas.r1082.route_core import RouteError

SCHEMA_DIR = Path(__file__).resolve().parents[3] / "cwatlas" / "r1082" / "schemas"
_UTC = {"timescale": "UTC", "value": "2000-01-01T00:00:00Z"}


@pytest.fixture(scope="module")
def shell_epoch_validator():
    jsonschema = pytest.importorskip("jsonschema")
    return jsonschema.Draft202012Validator(
        json.loads((SCHEMA_DIR / "shell_epoch.schema.json").read_text("utf-8")))


# -- encode/decode round-trip at every depth --------------------------------

def test_shell_only_roundtrip():
    p = wf.make_packet(wf.PacketDepth.SHELL_ONLY, 3)
    assert wf.decode(wf.encode(p)) == p
    assert p.coarse_epoch is None and p.fine_epoch is None


def test_shell_plus_coarse_roundtrip():
    p = wf.make_packet(wf.PacketDepth.SHELL_PLUS_COARSE, 5, coarse_epoch=2)
    d = wf.decode(wf.encode(p))
    assert d == p and d.coarse_epoch == 2 and d.fine_epoch is None


def test_full_roundtrip():
    p = wf.make_packet(wf.PacketDepth.FULL, 8, coarse_epoch=2, fine_epoch=23)
    d = wf.decode(wf.encode(p))
    assert d == p and d.coarse_epoch == 2 and d.fine_epoch == 23


@pytest.mark.parametrize("shell", range(0, 9))
def test_all_shells_roundtrip(shell):
    p = wf.make_packet(wf.PacketDepth.SHELL_PLUS_COARSE, shell, coarse_epoch=1)
    assert wf.decode(wf.encode(p)).shell == shell


# -- shell supplies radius --------------------------------------------------

def test_shell_supplies_radius():
    d = wf.decode(wf.encode(wf.make_packet(wf.PacketDepth.SHELL_ONLY, 6)))
    assert d.radius_m is not None
    assert d.radius_m == wf.resolve_shell_radius_m(6)


# -- 8<->0 explicit transition flag (not integer equality) ------------------

def test_eight_zero_is_flag_not_equality():
    eight = wf.make_packet(wf.PacketDepth.SHELL_ONLY, 8)
    zero = wf.make_packet(wf.PacketDepth.SHELL_ONLY, 0)
    assert eight.shell_closure_transition is True
    assert zero.shell_closure_transition is False
    # shell 8 is NOT treated as equal to shell 0
    assert eight.shell != zero.shell
    assert eight != zero


# -- ambiguous legacy packets -> typed alias set ----------------------------

def test_ambiguous_legacy_returns_alias_set():
    # a single token v<=8 is both a SHELL_ONLY and a SHELL_PLUS_COARSE(coarse=0)
    res = wf.decode_legacy(b100_encode([5]))
    assert res.status == "CANDIDATE_ALIAS_SET"
    assert len(res.candidates) == 2
    depths = {c.depth for c in res.candidates}
    assert wf.PacketDepth.SHELL_ONLY in depths
    assert wf.PacketDepth.SHELL_PLUS_COARSE in depths


def test_unambiguous_legacy_is_single_point():
    # a single token v>8 admits only the SHELL_PLUS_COARSE reading
    res = wf.decode_legacy(b100_encode([50]))
    assert res.status == "CANONICAL_EXACT_POINT"
    assert len(res.candidates) == 1


# -- to_shell_epoch: mandatory conventional epoch + schema ------------------

def test_to_shell_epoch_requires_conventional(shell_epoch_validator):
    p = wf.make_packet(wf.PacketDepth.FULL, 3, coarse_epoch=1, fine_epoch=9)
    se = wf.to_shell_epoch(p, _UTC)
    shell_epoch_validator.validate(se)
    assert se["conventional_epoch"]["timescale"] == "UTC"
    assert se["shell"]["radius_m"] is not None
    with pytest.raises(RouteError):
        wf.to_shell_epoch(p, {})


def test_shell_only_to_shell_epoch_omits_compressed(shell_epoch_validator):
    p = wf.make_packet(wf.PacketDepth.SHELL_ONLY, 2)
    se = wf.to_shell_epoch(p, _UTC)
    shell_epoch_validator.validate(se)
    assert se["compressed_epoch"] is None


# -- negatives --------------------------------------------------------------

def test_bad_shell_refused():
    with pytest.raises(RouteError):
        wf.make_packet(wf.PacketDepth.SHELL_ONLY, 9)


def test_depth_field_mismatch_refused():
    with pytest.raises(RouteError):
        wf.make_packet(wf.PacketDepth.SHELL_ONLY, 3, coarse_epoch=1)
    with pytest.raises(RouteError):
        wf.make_packet(wf.PacketDepth.FULL, 3, coarse_epoch=1)  # missing fine


def test_unknown_depth_code_refused():
    with pytest.raises(RouteError):
        wf.decode(b100_encode([9, 3]))  # depth code 9 is unknown


# -- determinism ------------------------------------------------------------

def test_determinism():
    p = wf.make_packet(wf.PacketDepth.FULL, 8, coarse_epoch=2, fine_epoch=23)
    assert wf.encode(p) == wf.encode(p)


def test_report_seals_claims():
    r = wf.wire_format_report()
    assert r["measured_here"] == "nothing"
    assert r["eight_zero_transition_is_flag_not_equality"] is True
    assert r["shell_supplies_radius"] is True
    assert len(r["packet_depths"]) == 3
