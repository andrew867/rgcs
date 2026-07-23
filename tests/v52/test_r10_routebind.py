"""P14 — handshake address binding to rooted routes, and its refusals."""

from __future__ import annotations

import pytest

from r10 import route as RT
from r10 import routebind as RB

E = "2026-07-22T00:00Z"
D_EM = 384400000.0


def _hop(a, b, dist=0.0, travel=None, es=E, ed=E):
    travel = dist / RT.C_M_PER_S if travel is None else travel
    return RT.RouteHop(a, b, es, ed, dist, travel, "D3", "OMEGA", "MATH")


def _earth_moon():
    return [_hop("EARTH_CELL", "EARTH_ROOT"),
            _hop("EARTH_ROOT", "EARTH_MOON_ROOT"),
            _hop("EARTH_MOON_ROOT", "MOON_ROOT", D_EM),
            _hop("MOON_ROOT", "MOON_CELL")]


def test_preregistered_address_binds_and_carries_light_floor():
    b = RB.bind_address(_earth_moon(), "MOON_CELL@root", preregistered=True)
    assert b.verdict == "ROUTE_BINDING_SOFTWARE_VALID"
    assert b.preregistered is True
    assert b.route_path[0] == "EARTH_CELL"
    assert b.route_path[-1] == "MOON_CELL"
    assert b.light_floor_s == pytest.approx(1.282, abs=0.01)


def test_unpreregistered_token_is_refused_as_retrofit():
    with pytest.raises(RB.RouteBindError):
        RB.bind_address(_earth_moon(), "1604/1644", preregistered=False)


def test_refuse_retrofit_helper_raises():
    with pytest.raises(RB.RouteBindError):
        RB.refuse_retrofit("post-hoc-token", ["EARTH_CELL", "MOON_CELL"])


def test_refuse_vector_to_coordinate_raises():
    with pytest.raises(RB.RouteBindError):
        RB.refuse_vector_to_coordinate((1604, 1644), "route_index")


def test_disconnected_route_gives_no_binding():
    with pytest.raises(RT.RouteError):
        RB.bind_address([_hop("EARTH_CELL", "EARTH_ROOT"),
                         _hop("MOON_ROOT", "MOON_CELL")],
                        "MOON_CELL@root", preregistered=True)


def test_unsupported_edge_gives_no_binding():
    with pytest.raises(RT.RouteError):
        RB.bind_address([_hop("EARTH_CELL", "MARS_ROOT")],
                        "MARS_CELL@root", preregistered=True)


def test_zero_time_transit_still_raises_causality_through_binding():
    with pytest.raises(RT.CausalityViolation):
        RB.bind_address(
            [_hop("EARTH_CELL", "EARTH_ROOT"),
             _hop("EARTH_ROOT", "EARTH_MOON_ROOT"),
             _hop("EARTH_MOON_ROOT", "MOON_ROOT", D_EM, travel=0.0),
             _hop("MOON_ROOT", "MOON_CELL")],
            "MOON_CELL@root", preregistered=True)


def test_preregistered_binding_is_better_than_chance():
    good = RB.binding_is_better_than_chance(preregistered=True)
    bad = RB.binding_is_better_than_chance(preregistered=False)
    assert good["power"] == "BETTER_THAN_CHANCE"
    assert bad["power"] == "NO_BETTER_THAN_CHANCE"


def test_report_measures_nothing_and_disclaims():
    r = RB.routebind_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["verdict"] == "ROUTE_BINDING_SOFTWARE_VALID"
    assert r["evidence_class"] == "DERIVED_MATHEMATICS"


def test_binding_dataclass_records_provenance():
    b = RB.bind_address(_earth_moon(), "MOON_CELL@root", preregistered=True,
                        provenance="TIER_A_DECLARATION")
    assert b.provenance == "TIER_A_DECLARATION"
    assert b.handshake_field == "rooted_address"
