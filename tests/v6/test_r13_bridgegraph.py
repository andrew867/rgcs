"""P06 — a certificate-gated coupling graph and its path search."""

from __future__ import annotations

import pytest

from r12.bridge import CouplingCertificate, Domain
from r13 import bridgegraph as B

A = Domain.ATOMIC_LATTICE_PHONON
Bd = Domain.MACROSCOPIC_ELASTIC
Cd = Domain.ELECTRICAL_BVD
Dd = Domain.OPTICAL_CAVITY


def make_cert(cid: str, source: Domain, target: Domain,
              measurement_performed: bool = False) -> CouplingCertificate:
    """A COMPLETE certificate for a directed pair (all nine declarations)."""
    return CouplingCertificate(
        certificate_id=cid, source=source, target=target,
        state_variables=("x",), units=("unit",),
        coupling_operator="declared operator", overlap_factor=0.5,
        detuning=0.0, damping=1.0,
        phase_matching="matched", symmetry_allowed=True,
        energy_in="in", energy_out="out",
        uncertainty="declared", null_model="declared",
        falsifying_measurement="measure the coupling",
        measurement_performed=measurement_performed)


def make_incomplete_cert() -> CouplingCertificate:
    """A certificate with no declared state variables -> incomplete.

    The constructor forbids an empty phase-matching string, so the
    reachable incompleteness is a missing state-variable declaration:
    ``missing_declarations`` flags it and the graph must refuse it.
    """
    return CouplingCertificate(
        certificate_id="incomplete", source=A, target=Bd,
        state_variables=(), units=(),
        coupling_operator="op", overlap_factor=0.5,
        detuning=0.0, damping=1.0,
        phase_matching="matched", symmetry_allowed=True,
        energy_in="in", energy_out="out",
        uncertainty="u", null_model="n",
        falsifying_measurement="m")


# --- edges form a path ----------------------------------------------------

def test_certificated_edges_form_a_path():
    g = B.CouplingGraph()
    g.add_edge(make_cert("ab", A, Bd))
    g.add_edge(make_cert("bc", Bd, Cd))
    path = g.path(A, Cd)
    assert path is not None
    assert path.domains == (A, Bd, Cd)
    assert path.n_edges == 2
    assert path.is_composite
    assert path.needs_end_to_end_certificate
    assert path.status == B.REQUIRES_END_TO_END_CERTIFICATE


def test_a_single_edge_is_a_path_that_is_its_own_certificate():
    g = B.CouplingGraph()
    g.add_edge(make_cert("ab", A, Bd))
    path = g.path(A, Bd)
    assert path is not None
    assert path.n_edges == 1
    assert not path.is_composite
    assert not path.needs_end_to_end_certificate


def test_a_missing_edge_gives_none():
    g = B.CouplingGraph()
    g.add_edge(make_cert("ab", A, Bd))
    # no B -> C edge, so no route from A to C
    assert g.path(A, Cd) is None
    assert not g.reachable(A, Cd)


def test_an_uncertified_pair_is_not_an_edge():
    g = B.CouplingGraph()
    assert not g.has_edge(A, Bd)
    assert g.path(A, Bd) is None


def test_an_incomplete_certificate_is_refused_as_an_edge():
    g = B.CouplingGraph()
    with pytest.raises(B.BridgeGraphError):
        g.add_edge(make_incomplete_cert())
    assert g.n_edges == 0


def test_a_same_domain_path_is_refused():
    g = B.CouplingGraph()
    with pytest.raises(B.BridgeGraphError):
        g.path(A, A)


# --- the claim class of a composed path -----------------------------------

def test_path_claim_class_is_engineering_candidate_never_measurement():
    certs = [make_cert("ab", A, Bd), make_cert("bc", Bd, Cd)]
    assert B.path_claim_class(certs) == "ENGINEERING_CANDIDATE"
    assert B.path_claim_class(certs) not in B.MEASUREMENT_CLASSES


def test_a_measured_link_does_not_make_a_measured_path():
    # even if a single edge claims BENCH_MEASUREMENT, the composite never does
    measured = make_cert("ab", A, Bd, measurement_performed=True)
    assert measured.claim_class == "BENCH_MEASUREMENT"
    certs = [measured, make_cert("bc", Bd, Cd)]
    assert B.path_claim_class(certs) == "ENGINEERING_CANDIDATE"
    assert B.path_claim_class(certs) not in B.MEASUREMENT_CLASSES


def test_an_empty_path_has_no_claim_class():
    with pytest.raises(B.BridgeGraphError):
        B.path_claim_class([])


# --- refusals -------------------------------------------------------------

def test_refuse_path_as_measured_raises():
    g = B.CouplingGraph()
    g.add_edge(make_cert("ab", A, Bd))
    g.add_edge(make_cert("bc", Bd, Cd))
    path = g.path(A, Cd)
    with pytest.raises(B.BridgeGraphError):
        B.refuse_path_as_measured(path)
    with pytest.raises(B.BridgeGraphError):
        B.refuse_path_as_measured()


def test_refuse_automatic_composition_raises():
    with pytest.raises(B.BridgeGraphError):
        B.refuse_automatic_composition(make_cert("ab", A, Bd),
                                       make_cert("bc", Bd, Cd))


# --- candidate bridges are hypotheses -------------------------------------

def test_search_candidate_bridges_returns_hypotheses_all_requiring_certificate():
    candidates = B.search_candidate_bridges(A, Cd)
    assert len(candidates) > 1
    for cand in candidates:
        assert cand.status == B.REQUIRES_CERTIFICATE
        assert cand.source is A
        assert cand.target is Cd
        assert cand.as_dict()["status"] == "REQUIRES_CERTIFICATE"
    # the direct hypothesis and at least one one-intermediate hypothesis
    assert any(c.n_intermediate == 0 for c in candidates)
    assert any(c.n_intermediate == 1 for c in candidates)


def test_a_candidate_bridge_cannot_claim_an_established_status():
    with pytest.raises(B.BridgeGraphError):
        B.CandidateBridge(A, Cd, (A, Cd), status="ESTABLISHED_COUPLING")


def test_search_over_the_same_domain_is_refused():
    with pytest.raises(B.BridgeGraphError):
        B.search_candidate_bridges(A, A)


# --- report ---------------------------------------------------------------

def test_report_verdict_and_no_measurement():
    r = B.bridgegraph_report()
    assert r["verdict"] == "COUPLING_GRAPH_SEARCH_CERTIFICATE_GATED"
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["claim_class"] == "ENGINEERING_CANDIDATE"
    assert "what_this_does_not_say" in r
