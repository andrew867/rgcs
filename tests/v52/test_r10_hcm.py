"""Q13-Q17 — HCM roots, topology, address, shells.

The arithmetic tests are the easy half. The load-bearing ones are the
three refusals: no face/vertex conflation, no retrospective fit sold as
a prediction, and no precision manufactured by unit conversion.
"""

from __future__ import annotations

from fractions import Fraction as F

import pytest

from r10 import hcm as H


# --- the exact arithmetic ----------------------------------------------

def test_the_identity_holds():
    assert 4096 ** 3 == 8 ** 12 == 2 ** 36 == 68_719_476_736


def test_twelve_levels_is_thirty_six_bits():
    assert H.address_bits(12) == 36
    assert H.address_bits(0) == 0
    assert H.address_bits(1) == 3


def test_twelve_levels_reaches_kilometre_scale():
    km = H.linear_scale_km(12)
    assert 1.5 < km < 1.6
    assert km == pytest.approx(6371.0088 / 4096)


def test_cell_count_scales_by_eight():
    t = H.ICOSAHEDRON_FACES
    assert H.cell_count(t, 0) == 20
    assert H.cell_count(t, 1) == 160
    assert H.cell_count(t, 12) == 20 * 8 ** 12


def test_negative_levels_refused():
    with pytest.raises(ValueError):
        H.address_bits(-1)
    with pytest.raises(ValueError):
        H.linear_scale_km(-1)


# --- Q14: the dual ambiguity is not resolved by assumption -------------

def test_twenty_regions_is_ambiguous():
    """20 icosahedral FACES and 20 dodecahedral VERTICES both give
    twenty. Saying "twenty regions" does not pick one."""
    r = H.dual_ambiguity_report()
    assert r["ambiguous"]
    assert len(r["readings_giving_20_regions"]) == 2
    solids = {x["solid"] for x in r["readings_giving_20_regions"]}
    assert solids == {"icosahedron", "dodecahedron"}


def test_both_twenty_region_readings_really_have_twenty():
    for t in H.TWENTY_REGION_READINGS:
        assert t.region_count == 20


def test_the_dual_swaps_faces_and_vertices():
    assert H.ICOSAHEDRON_FACES.faces == H.DODECAHEDRON_FACES.vertices == 20
    assert H.ICOSAHEDRON_FACES.vertices == H.DODECAHEDRON_FACES.faces == 12


def test_ambiguity_is_explained_as_substantive_not_cosmetic():
    r = H.dual_ambiguity_report()
    assert "adjacency graphs differ" in r["why_it_matters"]
    assert "unresolved" in r["resolution"]


def test_every_topology_satisfies_euler():
    for t in (H.ICOSAHEDRON_FACES, H.ICOSAHEDRON_VERTICES,
              H.DODECAHEDRON_FACES, H.DODECAHEDRON_VERTICES):
        assert t.vertices - t.edges + t.faces == 2


def test_a_non_polyhedron_is_refused():
    """The Euler check must be capable of rejecting something."""
    with pytest.raises(H.TopologyError):
        H.Topology("nonsense", 20, 12, 99, "FACE")


def test_unknown_region_element_refused():
    with pytest.raises(H.TopologyError):
        H.Topology("icosahedron", 20, 12, 30, "EDGE")


# --- Q15: the address ---------------------------------------------------

def _addr(levels=12, region=7):
    return H.Address(H.ICOSAHEDRON_FACES, region,
                     tuple(range(8))[:levels] + (0,) * max(0, levels - 8),
                     "ITRF2020", "2026-07-20T00:00:00Z", 1.6)


def test_address_packs_and_unpacks():
    a = _addr()
    b = H.Address.from_int(a.to_int(), 12, a.topology, a.region,
                           a.frame, a.epoch, a.uncertainty_km)
    assert b.path == a.path


def test_thirty_six_bits_is_three_twelve_bit_words():
    a = _addr()
    assert a.bits == 36
    words = a.as_words(12)
    assert len(words) == 3
    assert all(0 <= w < 4096 for w in words)


def test_words_reconstruct_the_packed_value():
    a = _addr()
    w = a.as_words(12)
    assert (w[0] << 24) | (w[1] << 12) | w[2] == a.to_int()


def test_frame_and_epoch_are_required():
    """An address without them is a label, not a position."""
    with pytest.raises(ValueError):
        H.Address(H.ICOSAHEDRON_FACES, 0, (1,), "", "2026", 1.0)
    with pytest.raises(ValueError):
        H.Address(H.ICOSAHEDRON_FACES, 0, (1,), "ITRF2020", "", 1.0)


def test_region_must_exist_in_the_chosen_topology():
    """Region 15 exists among 20 faces and not among 12 vertices --
    the ambiguity has teeth."""
    H.Address(H.ICOSAHEDRON_FACES, 15, (0,), "f", "e", 1.0)
    with pytest.raises(ValueError):
        H.Address(H.ICOSAHEDRON_VERTICES, 15, (0,), "f", "e", 1.0)


def test_refinement_digits_are_octal():
    with pytest.raises(ValueError):
        H.Address(H.ICOSAHEDRON_FACES, 0, (8,), "f", "e", 1.0)


def test_negative_uncertainty_refused():
    with pytest.raises(ValueError):
        H.Address(H.ICOSAHEDRON_FACES, 0, (0,), "f", "e", -1.0)


def test_out_of_range_packed_value_refused():
    with pytest.raises(ValueError):
        H.Address.from_int(8 ** 12, 12, H.ICOSAHEDRON_FACES, 0,
                           "f", "e", 1.0)


# --- Q15: and it is a fit, not a prediction ----------------------------

def test_the_address_size_is_labelled_a_retrospective_fit():
    """The honest core of this phase."""
    p = H.address_provenance()
    assert p["status"] == "RETROSPECTIVE_FIT"
    assert "fitted to a known answer" in p["why"]


def test_provenance_says_what_would_make_it_evidence():
    p = H.address_provenance()
    w = p["what_would_make_it_evidence"]
    assert "in advance" in w
    assert "whichever way it came out" in w


def test_elegance_is_explicitly_not_evidence():
    p = H.address_provenance()
    assert "tidiness is not evidence" in p["elegance_warning"]
    assert "property of the radix" in p["elegance_warning"]


def test_neighbouring_level_counts_would_also_have_been_available():
    """The fit is visible: 11 and 13 bracket the target, so 12 was
    chosen, not discovered."""
    assert H.linear_scale_km(11) > 3.0
    assert H.linear_scale_km(13) < 0.8
    assert 1.0 < H.linear_scale_km(12) < 2.0


# --- Q17: precision is not created by conversion -----------------------

def test_the_statute_mile_is_exact_by_definition():
    assert H.METRES_PER_STATUTE_MILE == F(1609344, 1000)


def test_exact_conversion_is_computed_exactly():
    assert H.NOMINAL_SHELL.to_km_exact() == F(2500) * F(1609344, 1000) / 1000
    assert float(H.NOMINAL_SHELL.to_km_exact()) == pytest.approx(4023.36)


def test_but_it_is_only_reportable_to_two_significant_figures():
    """2500 is a round nominal figure. 4023.36 km would claim six
    significant figures from an input carrying about two."""
    assert H.NOMINAL_SHELL.significant_figures == 2
    assert H.NOMINAL_SHELL.to_km_reported() == "4000"


def test_more_significant_figures_would_report_more():
    """The rounding must actually track the declared precision, or it
    is a hardcoded string."""
    precise = H.Shell("measured", F(2500), "STATUTE_MILE", 5,
                      "hypothetical instrument reading")
    assert precise.to_km_reported() == "4023.4"


def test_precision_report_names_where_the_exactness_lives():
    r = H.NOMINAL_SHELL.precision_report()
    assert "belongs to the definition" in r["warning"]
    assert r["honestly_reportable_km"] == "4000"


def test_precise_shell_claim_is_refused():
    with pytest.raises(H.PrecisionError) as e:
        H.refuse_precise_shell()
    assert "nominal round figure" in str(e.value)
    assert "4000" in str(e.value)


def test_invalid_shell_inputs_refused():
    with pytest.raises(ValueError):
        H.Shell("x", F(1), "STATUTE_MILE", 0, "b")
    with pytest.raises(ValueError):
        H.Shell("x", F(1), "PARSEC", 2, "b")


# --- firewalls ----------------------------------------------------------

def test_graph_distance_is_not_spacetime_distance():
    with pytest.raises(H.MetricPromotionRefused) as e:
        H.refuse_metric_promotion()
    msg = str(e.value)
    assert "property of the construction" in msg
    assert "stress-energy budget" in msg


def test_report_states_what_this_is_not():
    r = H.hcm_report()
    n = r["what_this_is_not"]
    assert "evidence that Earth has twenty regions" in n
    assert "bookkeeping" in n
    assert r["measured_here"] == "nothing"
    assert r["evidence_class"] == "DERIVED_MATHEMATICS"
