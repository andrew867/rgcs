"""P07 — rooted interbody route compiler and causal refusals."""

from __future__ import annotations

import pytest

from r10 import route as RT

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


def test_a_rooted_earth_moon_route_compiles():
    r = RT.compile_route(_earth_moon())
    assert r["verdict"] == "ROUTE_SOFTWARE_VALID"
    assert r["path"][0] == "EARTH_CELL" and r["path"][-1] == "MOON_CELL"


def test_the_route_carries_the_light_time_floor():
    r = RT.compile_route(_earth_moon())
    assert r["total_light_floor_s"] == pytest.approx(1.282, abs=0.01)
    assert r["causal_status"] == "CAUSAL_DELAY_REQUIRED"


def test_zero_time_across_distance_is_refused():
    with pytest.raises(RT.CausalityViolation):
        _hop("EARTH_MOON_ROOT", "MOON_ROOT", D_EM, travel=0.0)


def test_an_unsupported_edge_is_refused():
    with pytest.raises(RT.RouteError):
        _hop("EARTH_CELL", "MARS_ROOT")


def test_incompatible_epochs_are_refused():
    with pytest.raises(RT.RouteError):
        _hop("EARTH_CELL", "EARTH_ROOT", ed="2027")


def test_a_disconnected_route_is_refused():
    with pytest.raises(RT.RouteError):
        RT.compile_route([_hop("EARTH_CELL", "EARTH_ROOT"),
                          _hop("MOON_ROOT", "MOON_CELL")])


def test_local_hops_are_instantaneous_spatial_hops_are_not():
    assert _hop("EARTH_CELL", "EARTH_ROOT").causal_status == \
        "INSTANTANEOUS_LOCAL"
    assert _hop("EARTH_MOON_ROOT", "MOON_ROOT", D_EM).causal_status == \
        "CAUSAL_DELAY_REQUIRED"


def test_zero_time_transit_helper_refuses():
    with pytest.raises(RT.CausalityViolation):
        RT.refuse_zero_time_transit(D_EM)


def test_report_disclaims_gateways():
    r = RT.route_report()
    assert "not a gateway" in r["what_this_does_not_say"]
    assert r["measured_here"] == "nothing"
