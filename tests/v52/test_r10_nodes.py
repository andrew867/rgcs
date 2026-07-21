"""P08/P13 — node registry and the look-elsewhere null.

The load-bearing tests: LOCATION_UNKNOWN cannot be silently located,
gateway/stargate status cannot be positive, and the alignment test has
BOTH the right null result on random sites AND demonstrated power on
planted structure.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from r10 import nodes as N


# --- registry discipline -----------------------------------------------

def test_public_registry_holds_only_public_coordinates():
    for n in N.located_nodes():
        assert n.provenance_class in ("PUBLIC_HERITAGE", "GEODETIC")
        assert n.coordinate_authority != "none"


def test_antarctica_and_the_crystal_sphere_stay_unlocated():
    unlocated = {n.node_id for n in N.PUBLIC_NODES if not n.located}
    assert unlocated == {"antarctic_candidate", "bahamas_crystal_sphere"}


def test_location_unknown_cannot_be_assigned_a_coordinate_freely():
    unknown = [n for n in N.PUBLIC_NODES if not n.located][0]
    with pytest.raises(N.NodeStatusError) as e:
        N.refuse_location_for_unknown(unknown)
    assert "cited survey or heritage authority" in str(e.value)


def test_a_positive_gateway_status_is_refused():
    with pytest.raises(N.NodeStatusError):
        N.Node("x", "X", 10.0, 10.0, "auth", 1.0, "GEODETIC",
               gateway_status="CONFIRMED")
    with pytest.raises(N.NodeStatusError):
        N.Node("x", "X", 10.0, 10.0, "auth", 1.0, "GEODETIC",
               stargate_status="ACTIVE")


def test_an_unlocated_node_must_be_location_unknown():
    with pytest.raises(N.NodeStatusError):
        N.Node("x", "X", None, None, "none", math.inf, "UNKNOWN",
               evidence_status="CONVENTIONAL_REFERENCE")


def test_every_gateway_and_stargate_status_is_negative():
    for n in N.PUBLIC_NODES:
        assert n.gateway_status in ("UNSUPPORTED", "UNKNOWN")
        assert n.stargate_status in ("UNSUPPORTED", "UNKNOWN")


# --- geometry -----------------------------------------------------------

def test_latlon_to_unit_is_a_unit_vector():
    v = N.latlon_to_unit(29.9792, 31.1342)
    assert np.linalg.norm(v) == pytest.approx(1.0)


def test_the_north_pole_points_up():
    assert np.allclose(N.latlon_to_unit(90, 0), [0, 0, 1], atol=1e-9)


def test_all_five_polyhedra_have_the_right_vertex_counts():
    counts = {k: len(v) for k, v in N.POLYHEDRA.items()}
    assert counts == {"tetrahedron": 4, "octahedron": 6, "cube": 8,
                      "icosahedron": 12, "dodecahedron": 20}


def test_polyhedron_vertices_are_unit_vectors():
    for v in N.POLYHEDRA.values():
        assert np.allclose(np.linalg.norm(v, axis=1), 1.0)


# --- the null: random sites do NOT beat chance -------------------------

def test_random_sites_do_not_beat_chance():
    """The whole point. A few random sites fit a polyhedron about as
    well as other random sites, so p is unremarkable."""
    rng = np.random.default_rng(3)
    sites = N._random_sites(4, rng)
    r = N.alignment_pvalue(sites, rotations=150, null_trials=150)
    assert r["verdict"] == "NO_BETTER_THAN_CHANCE"
    assert r["p_value"] > 0.05


def test_the_observed_fit_is_tight_but_meaningless():
    """A small residual is not the evidence -- the null median is just
    as small, which is exactly why residual alone proves nothing."""
    rng = np.random.default_rng(5)
    sites = N._random_sites(4, rng)
    r = N.alignment_pvalue(sites, rotations=150, null_trials=150)
    # the fit is tight in absolute terms...
    assert r["observed_residual_deg"] < 25
    # ...and so is the null, within a few degrees
    assert abs(r["observed_residual_deg"]
               - r["null_median_residual_deg"]) < 8


# --- power: planted polyhedral structure IS detected -------------------

def test_the_test_has_power_on_planted_structure():
    """If genuine polyhedral sites did NOT score low, the test would be
    worthless. Eight sites placed exactly on a rotated cube must beat
    chance.

    Note the meaningful quantity is the p-value, not the absolute
    residual: a random-orientation search of a few hundred rotations
    only aligns even an exact cube to a handful of degrees, but the
    null runs the SAME search, so the exact cube still sits far below
    the null median (5.9 deg vs 18 deg) and scores p ~ 0.003.
    """
    rng = np.random.default_rng(7)
    q, _ = np.linalg.qr(rng.standard_normal((3, 3)))
    planted = N.POLYHEDRA["cube"] @ q.T          # exact cube, rotated
    r = N.alignment_pvalue(planted, rotations=300, null_trials=300)
    assert r["observed_residual_deg"] < \
        r["null_median_residual_deg"] - 5        # far below the null
    assert r["p_value"] < 0.05
    assert r["verdict"] == "TIGHTER_THAN_CHANCE"


def test_planted_and_random_give_opposite_verdicts():
    """The two must actually differ, or the machine is not measuring."""
    rng = np.random.default_rng(11)
    q, _ = np.linalg.qr(rng.standard_normal((3, 3)))
    planted = N.POLYHEDRA["icosahedron"] @ q.T
    rand = N._random_sites(12, rng)
    rp = N.alignment_pvalue(planted, rotations=250, null_trials=250)
    rr = N.alignment_pvalue(rand, rotations=250, null_trials=250)
    assert rp["p_value"] < rr["p_value"]


def test_only_two_public_sites_are_located():
    """An honest structural limit: two points cannot test a
    polyhedron. Named private-origin sites are not public."""
    assert len(N.located_nodes()) == 2


# --- claim discipline --------------------------------------------------

def test_report_states_the_trap_and_the_test():
    r = N.node_report()
    assert "fit something almost always" in r["the_trap"]
    assert "beating random sites counts" in r["the_test"]
    assert r["measured_here"] == "nothing"


def test_report_disclaims_gateways_and_discoveries():
    r = N.node_report()
    n = r["what_this_does_not_say"]
    assert "gateway, or a\nstargate" in n or "gateway, or a stargate" in n
    assert "random points achieve tight fits" in n
