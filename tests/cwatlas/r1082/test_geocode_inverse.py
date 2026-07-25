"""P22 — inverse source geocoder: map selection -> source-style vector.

Covers: a body click yields a five-token source-style address under a named
frozen profile; forward-then-inverse recovers the source vector for an encodable
click; non-representable clicks return the nearest-encodable point with an
explicit quantization residual (no false exactness); non-uniqueness is surfaced
as aliases; the shell supplies the radius (no altitude missing); a named profile
is required; determinism; schema conformance.
"""

from __future__ import annotations

import pytest

from cwatlas.icosahedron import build_icosahedron
from cwatlas.r1082 import geocode_forward as G
from cwatlas.r1082 import geocode_inverse as I
from cwatlas.r1082.claims import R1082ClaimError
from cwatlas.r1082.route_core import RouteError


@pytest.fixture(scope="module")
def ico():
    return build_icosahedron()


def test_named_profile_required(ico):
    with pytest.raises(RouteError):
        I.inverse_geocode(10.0, 20.0, 3, None, ico=ico)


def test_forward_then_inverse_recovers_source_vector(ico):
    sf = G.single_family_stub("F1_CANONICAL_DIRECT_BE")
    fwd = G.geocode("165876523", sf, shell=3, ico=ico)
    c = fwd.candidates[0]
    inv = I.inverse_geocode(c.latitude_deg, c.longitude_deg, 3, sf, ico=ico)
    assert inv.route == fwd.route                    # exact recovery
    assert inv.representable_exact is True
    assert inv.quantization_residual <= I.local_coord._EXACT_TOL
    assert inv.source_vector == "01|65|87|65|23"


def test_five_token_display_shape(ico):
    sf = G.single_family_stub()
    fwd = G.geocode("1234567890", sf, shell=3, ico=ico)
    c = fwd.candidates[0]
    inv = I.inverse_geocode(c.latitude_deg, c.longitude_deg, 3, sf, ico=ico)
    parts = inv.source_vector.split("|")
    assert len(parts) == 5
    assert all(len(p) == 2 and p.isdigit() for p in parts)


def test_arbitrary_click_nearest_encodable_no_false_exactness(ico):
    sf = G.single_family_stub()
    # A click that is not a route centroid -> nearest encodable + a residual.
    inv = I.inverse_geocode(12.34, -56.78, 3, sf, ico=ico)
    assert inv.representable_exact is False
    assert inv.quantization_residual > 0.0
    # The reported nearest point is itself exactly encodable (round-trips).
    back = I.inverse_geocode(inv.nearest_latitude_deg, inv.nearest_longitude_deg,
                             3, sf, ico=ico)
    assert back.route == inv.route


def test_non_uniqueness_surfaced_as_aliases(ico):
    # Under the un-narrowed ensemble the other families' addresses are shown.
    # Use an addressable click (a real route centroid) so distinct token-order
    # families genuinely disagree on the source vector.
    f1 = G.single_family_stub("F1_CANONICAL_DIRECT_BE")
    fwd = G.geocode("165876523", f1, shell=3, ico=ico)
    c = fwd.candidates[0]
    allp = G.default_frozen_stub()
    inv = I.inverse_geocode(c.latitude_deg, c.longitude_deg, 3, allp,
                            family_name="F1_CANONICAL_DIRECT_BE", ico=ico)
    assert len(inv.aliases) == len(allp.retained_family_names) - 1
    assert inv.non_unique is True                     # families disagree
    for a in inv.aliases:
        assert a["family_name"] != inv.family_name
        assert len(a["source_vector"].split("|")) == 5


def test_family_name_must_be_retained(ico):
    sf = G.single_family_stub("F1_CANONICAL_DIRECT_BE")
    with pytest.raises(RouteError):
        I.inverse_geocode(10.0, 20.0, 3, sf, family_name="F2_REVERSED_DIRECT_BE",
                          ico=ico)


@pytest.mark.parametrize("shell", range(0, 9))
def test_shell_supplies_radius_no_altitude_missing(shell, ico):
    sf = G.single_family_stub()
    inv = I.inverse_geocode(15.0, 25.0, shell, sf, ico=ico)
    assert inv.radius_m is not None
    assert inv.receipt["shell_supplies_radius"] is True
    assert inv.receipt["altitude_missing"] is False
    assert inv.shell == shell


def test_epoch_packet_depth_extends(ico):
    sf = G.single_family_stub()
    shell_only = I.inverse_geocode(10.0, 20.0, 3, sf, ico=ico)
    with_coarse = I.inverse_geocode(10.0, 20.0, 3, sf, coarse_epoch=2, ico=ico)
    full = I.inverse_geocode(10.0, 20.0, 3, sf, coarse_epoch=2, fine_epoch=23,
                             ico=ico)
    assert shell_only.packet_depth == "SHELL_ONLY"
    assert with_coarse.packet_depth == "SHELL_PLUS_COARSE"
    assert full.packet_depth == "FULL"


def test_foreign_body_selection_refused(ico):
    sf = G.single_family_stub()
    with pytest.raises(RouteError):
        I.inverse_geocode(10.0, 20.0, 3, sf, body="MARS", ico=ico)


def test_candidate_not_measured_raises(ico):
    sf = G.single_family_stub()
    inv = I.inverse_geocode(10.0, 20.0, 3, sf, ico=ico)
    with pytest.raises(R1082ClaimError):
        inv.assert_not_measured()
    assert inv.receipt["max_evidence"] == "CALIBRATED_CANDIDATE"


def test_determinism(ico):
    sf = G.single_family_stub()
    a = I.inverse_geocode(10.0, 20.0, 3, sf, ico=ico)
    b = I.inverse_geocode(10.0, 20.0, 3, sf, ico=ico)
    assert a.route == b.route
    assert a.wire_packet == b.wire_packet
    assert a.quantization_residual == b.quantization_residual
    assert a.receipt["receipt_hash"] == b.receipt["receipt_hash"]


def test_serializable(ico):
    import json
    sf = G.single_family_stub()
    inv = I.inverse_geocode(10.0, 20.0, 3, sf, ico=ico)
    ser = inv.to_serializable()
    json.loads(json.dumps(ser))
    assert ser["geometry"]["source_vector"].count("|") == 4
    assert ser["result_type"] == "CANDIDATE_CALIBRATED_POINT"


def test_report_seals_claims():
    r = I.geocode_inverse_report()
    assert r["phase_id"] == "P22"
    assert r["tranche"] == "T06"
    assert r["named_profile_required"] is True
    assert r["nearest_encodable_when_quantized"] is True
    assert r["shell_supplies_radius"] is True
    assert r["measured_here"] == "nothing"
    assert r["source_origin"] == "SOURCE_ORIGIN_NOT_VALIDATED"
    assert r["physical_effects"] == "PHYSICAL_EFFECTS_NOT_CLAIMED"
