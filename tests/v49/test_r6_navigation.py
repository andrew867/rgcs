"""P12 — navigation observability and the sovereignty audit."""

from __future__ import annotations

import pytest

from r6 import navigation as N


def test_clock_rate_jacobian_is_rank_one_not_rank_zero():
    """g/c^2 ~ 1e-16 is tiny but real.

    Rounding it to zero would claim a clock carries no position
    information at all, contradicting published optical-clock height
    measurements. The rank tolerance must be relative.
    """
    J = N.clock_rate_jacobian((0.0, 0.0, -9.80665))
    assert N._rank(J) == 1


def test_genuinely_zero_jacobian_is_rank_zero():
    assert N._rank([[0.0, 0.0, 0.0]]) == 0


def test_rank_is_scale_invariant():
    a = [[1e-16, 0.0, 0.0], [0.0, 2e-16, 0.0]]
    b = [[1e16, 0.0, 0.0], [0.0, 2e16, 0.0]]
    assert N._rank(a) == N._rank(b) == 2


def test_clock_alone_leaves_two_dof_unobservable():
    J = N.clock_rate_jacobian((0.0, 0.0, -9.80665))
    r = N.analyze_observability("CLOCK_GEODESY", J)
    assert r.jacobian_rank == 1
    assert r.unobservable_dof == 2
    assert r.status == "POSITION_UNOBSERVABLE"
    assert not r.position_observable


def test_equipotential_note_is_reported():
    J = N.clock_rate_jacobian((0.0, 0.0, -9.80665))
    r = N.analyze_observability("CLOCK_GEODESY", J)
    assert any("equipotential" in n for n in r.notes)


def test_full_rank_measurement_is_bounded():
    J = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    r = N.analyze_observability("CELESTIAL", J)
    assert r.unobservable_dof == 0
    assert r.position_observable


def test_map_aiding_is_labelled_when_a_map_is_used():
    J = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    r = N.analyze_observability("TERRAIN", J, has_map=True)
    assert r.status == "MAP_AIDED_NAVIGATION"


def test_inertial_without_initial_condition_is_dead_reckoning():
    J = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    r = N.analyze_observability("INERTIAL", J,
                                has_initial_condition=False)
    assert r.status == "DEAD_RECKONING"


def test_unknown_method_rejected():
    with pytest.raises(ValueError):
        N.analyze_observability("TELEPATHY", [[1.0, 0.0, 0.0]])


def test_every_status_is_declared():
    J = N.clock_rate_jacobian((0.0, 0.0, -9.80665))
    for m in N.DEPENDENCIES:
        r = N.analyze_observability(m, J)
        assert r.status in N.NAVIGATION_STATUSES


# --- fusion -----------------------------------------------------------

def test_fusion_can_make_position_observable():
    a = N.analyze_observability(
        "CLOCK_GEODESY", N.clock_rate_jacobian((0.0, 0.0, -9.8)))
    b = N.analyze_observability("TERRAIN", [[1.0, 0.0, 0.0]])
    c = N.analyze_observability("GEOMAGNETIC", [[0.0, 1.0, 0.0]])
    f = N.fuse_observability([a, b, c])
    assert f.unobservable_dof == 0
    assert f.status == "POSITION_BOUNDED"


def test_fusion_inherits_the_union_of_dependencies():
    a = N.analyze_observability("CLOCK_GEODESY", [[1.0, 0.0, 0.0]])
    b = N.analyze_observability("CELESTIAL", [[0.0, 1.0, 0.0]])
    f = N.fuse_observability([a, b])
    assert len(f.dependencies) == len(set(f.dependencies))
    for d in a.dependencies:
        assert d in f.dependencies
    for d in b.dependencies:
        assert d in f.dependencies


def test_fusion_says_observability_is_because_of_the_dependencies():
    a = N.analyze_observability("CLOCK_GEODESY", [[1.0, 0.0, 0.0]])
    b = N.analyze_observability("TERRAIN", [[0.0, 1.0, 0.0]])
    c = N.analyze_observability("CELESTIAL", [[0.0, 0.0, 1.0]])
    f = N.fuse_observability([a, b, c])
    assert any("not in spite of them" in n for n in f.notes)


def test_fusion_of_nothing_rejected():
    with pytest.raises(ValueError):
        N.fuse_observability([])


def test_fused_rank_cannot_exceed_position_dof():
    reps = [N.analyze_observability("CELESTIAL",
                                    [[1.0, 0.0, 0.0],
                                     [0.0, 1.0, 0.0],
                                     [0.0, 0.0, 1.0]])
            for _ in range(4)]
    f = N.fuse_observability(reps)
    assert f.jacobian_rank == 3


# --- the sovereignty audit -------------------------------------------

def test_no_method_is_infrastructure_free():
    a = N.sovereignty_audit()
    assert a["methods_infrastructure_free"] == 0
    assert a["status"] == "SOVEREIGN_NAVIGATION_UNSUPPORTED"


def test_every_method_has_at_least_one_dependency():
    for m, deps in N.DEPENDENCIES.items():
        assert deps, f"{m} claims no external dependency"


def test_audit_covers_every_declared_method():
    a = N.sovereignty_audit()
    assert a["methods_examined"] == len(N.DEPENDENCIES)


def test_audit_verdict_names_the_claim():
    a = N.sovereignty_audit()
    assert "R6-C-107" in a["verdict"]


def test_audit_states_a_ceiling_not_just_a_refusal():
    a = N.sovereignty_audit()
    assert "dependencies stated" in a["claim_ceiling"]


def test_position_from_local_metric_is_refused():
    with pytest.raises(RuntimeError) as e:
        N.refuse_position_from_local_metric()
    assert "LOCAL_FIELD_IS_GLOBAL_POSITION" in str(e.value)


def test_inertial_lists_drift_dependency():
    assert any("bound drift" in d for d in N.DEPENDENCIES["INERTIAL"])


def test_celestial_lists_catalogue_dependency():
    assert any("catalogue" in d for d in N.DEPENDENCIES["CELESTIAL"])
