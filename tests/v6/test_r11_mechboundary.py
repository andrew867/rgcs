"""P09 — a classical mechanical boundary that changes in time.

The headline is exercised with numbers: a SUDDEN boundary change
scatters one mode's energy across the new modal basis, and a GRADUAL
change with a long ramp time tends to the adiabatic limit where the
mixing matrix is the identity and the mode keeps its identity. The
energy ledger is required to close for both, and deliberately omitting
the boundary-work term is required to break it. Every over-claim the
model invites — energy from nothing, a quantum reading of a classical
mode-mixing number — is refused.
"""

from __future__ import annotations

import inspect
import math
import re

import numpy as np
import pytest

from r11 import mechboundary as MB


# --- fixtures / helpers --------------------------------------------------

def uniform_chain(n: int = 6) -> MB.ChainConfig:
    """A perfectly uniform fixed-fixed chain, with a closed-form spectrum."""
    return MB.ChainConfig(
        n_nodes=n, node_mass=1.0, internal_stiffness=1.0,
        support_stiffness=1.0, boundary_stiffness=1.0,
        electrode_mass=0.0, electrode_stiffness=0.0,
        internal_damping=0.0, support_damping=0.0,
        boundary_damping=0.0, electrode_damping=0.0)


#: Parameters that actually move the undamped modal basis (they touch M
#: or K), with the minimum column-averaged off-diagonal mixing a factor
#: 1 -> 4 sudden change must produce.
MOVING_PARAMETERS = [
    (MB.BoundaryParameter.STIFFNESS, 0.20),
    (MB.BoundaryParameter.SUPPORT_IMPEDANCE, 0.15),
    (MB.BoundaryParameter.ELECTRODE_LOADING, 0.03),
]


# --- (1) modes: ascending frequencies, mass-normalised shapes -----------

def test_uniform_chain_gives_ascending_eigenfrequencies():
    system = MB.build_system(uniform_chain())
    basis = MB.modes(system.M, system.K)
    assert basis.n == 6
    assert np.all(np.diff(basis.omega) > 0.0)
    assert np.all(basis.omega > 0.0)


def test_uniform_chain_matches_the_closed_form_spectrum():
    """omega_j = 2*sqrt(k/m)*sin(j*pi/(2*(N+1))) for a uniform fixed-fixed
    chain. An assembly bug in build_system moves these."""
    n = 6
    system = MB.build_system(uniform_chain(n))
    basis = MB.modes(system.M, system.K)
    expected = np.array([2.0 * math.sin(j * math.pi / (2.0 * (n + 1)))
                         for j in range(1, n + 1)])
    assert basis.omega == pytest.approx(expected, rel=1e-12, abs=1e-12)


def test_modes_are_mass_normalised_and_diagonalise_the_stiffness():
    system = MB.build_system(MB.DEFAULT_CHAIN)
    basis = MB.modes(system.M, system.K)
    n = basis.n
    assert basis.normalisation_defect() < MB.ORTHONORMALITY_TOL
    gram = basis.shapes.T @ system.M @ basis.shapes
    assert gram == pytest.approx(np.eye(n), abs=1e-10)
    stiff = basis.shapes.T @ system.K @ basis.shapes
    assert stiff == pytest.approx(np.diag(basis.omega ** 2), abs=1e-10)


def test_a_heavier_chain_is_slower_and_a_stiffer_one_is_faster():
    base = MB.build_system(uniform_chain())
    slow = MB.build_system(MB.ChainConfig(
        **{**uniform_chain().__dict__, "node_mass": 4.0}))
    fast = MB.build_system(MB.ChainConfig(
        **{**uniform_chain().__dict__, "internal_stiffness": 4.0}))
    assert np.all(MB.modes(slow.M, slow.K).omega
                  < MB.modes(base.M, base.K).omega)
    assert np.all(MB.modes(fast.M, fast.K).omega
                  > MB.modes(base.M, base.K).omega)


def test_modes_refuses_a_non_positive_definite_mass_matrix():
    k = np.array([[2.0, -1.0], [-1.0, 2.0]])
    with pytest.raises(MB.MechBoundaryError):
        MB.modes(np.array([[1.0, 0.0], [0.0, -1.0]]), k)


def test_modes_refuses_asymmetric_or_mismatched_input():
    with pytest.raises(MB.MechBoundaryError):
        MB.modes(np.eye(2), np.array([[1.0, 2.0], [0.0, 1.0]]))
    with pytest.raises(MB.MechBoundaryError):
        MB.modes(np.eye(2), np.eye(3))


def test_a_chain_whose_stiffness_is_indefinite_is_refused():
    with pytest.raises(MB.MechBoundaryError):
        MB.build_system(MB.ChainConfig(electrode_stiffness=-50.0))


# --- (2) projection ------------------------------------------------------

def test_projection_round_trips_a_state():
    system = MB.build_system(MB.DEFAULT_CHAIN)
    basis = MB.modes(system.M, system.K)
    rng = np.random.default_rng(11)
    state = MB.State(rng.normal(size=basis.n), rng.normal(size=basis.n))
    back = MB.reconstruct(MB.project(state, basis), basis)
    assert back.u == pytest.approx(state.u, abs=1e-12)
    assert back.v == pytest.approx(state.v, abs=1e-12)


def test_modal_energies_sum_to_the_total_energy():
    system = MB.build_system(MB.DEFAULT_CHAIN)
    basis = MB.modes(system.M, system.K)
    rng = np.random.default_rng(12)
    state = MB.State(rng.normal(size=basis.n), rng.normal(size=basis.n))
    total = MB.energy(state, system.M, system.K)
    modal = MB.project(state, basis)
    assert modal.total_energy == pytest.approx(total, rel=1e-12)
    assert modal.fractions.sum() == pytest.approx(1.0, rel=1e-12)


def test_a_pure_mode_puts_all_its_energy_in_one_slot():
    system = MB.build_system(MB.DEFAULT_CHAIN)
    basis = MB.modes(system.M, system.K)
    state = MB.initial_state(basis, 2)
    modal = MB.project(state, basis)
    assert modal.participation(2) == pytest.approx(1.0, abs=1e-12)
    assert MB.energy(state, system.M, system.K) == pytest.approx(
        0.5 * basis.omega[2] ** 2, rel=1e-12)


def test_energy_splits_into_kinetic_and_potential():
    system = MB.build_system(MB.DEFAULT_CHAIN)
    basis = MB.modes(system.M, system.K)
    at_rest = MB.initial_state(basis, 0, phase=0.0)
    moving = MB.initial_state(basis, 0, phase=math.pi / 2)
    assert MB.kinetic_energy(at_rest, system.M) == pytest.approx(0.0, abs=1e-15)
    assert MB.potential_energy(moving, system.K) == pytest.approx(0.0,
                                                                  abs=1e-15)
    assert MB.energy(at_rest, system.M, system.K) == pytest.approx(
        MB.energy(moving, system.M, system.K), rel=1e-12)
    zero = MB.State(np.zeros(basis.n), np.zeros(basis.n))
    assert MB.energy(zero, system.M, system.K) == 0.0


def test_project_refuses_a_state_of_the_wrong_size():
    system = MB.build_system(MB.DEFAULT_CHAIN)
    basis = MB.modes(system.M, system.K)
    with pytest.raises(MB.MechBoundaryError):
        MB.project(MB.State(np.zeros(3), np.zeros(3)), basis)


# --- (3) the mixing matrix ----------------------------------------------

def test_no_change_gives_the_identity_mixing_matrix():
    system = MB.build_system(MB.DEFAULT_CHAIN)
    basis = MB.modes(system.M, system.K)
    mixing = MB.mode_mixing_matrix(basis, basis)
    assert mixing == pytest.approx(np.eye(basis.n), abs=1e-10)
    assert MB.mixing_offdiagonal_fraction(mixing) == pytest.approx(0.0,
                                                                   abs=1e-18)


def test_mixing_columns_are_unit_vectors_when_the_mass_does_not_change():
    change = MB.BoundaryChange(MB.BoundaryParameter.STIFFNESS,
                               MB.ChangeProfile.SUDDEN, 1.0, 4.0)
    before, after = change.systems(MB.DEFAULT_CHAIN)
    mixing = MB.mode_mixing_matrix(MB.system_modes(before),
                                   MB.system_modes(after))
    assert np.sum(mixing ** 2, axis=0) == pytest.approx(
        np.ones(mixing.shape[1]), abs=1e-10)


@pytest.mark.parametrize("parameter,floor", MOVING_PARAMETERS)
def test_a_sudden_change_mixes_the_modes(parameter, floor):
    """The bases are not the same, so a sudden change spreads each old
    mode over several new ones."""
    change = MB.BoundaryChange(parameter, MB.ChangeProfile.SUDDEN, 1.0, 4.0)
    before, after = change.systems(MB.DEFAULT_CHAIN)
    mixing = MB.mode_mixing_matrix(MB.system_modes(before),
                                   MB.system_modes(after))
    assert MB.mixing_offdiagonal_fraction(mixing) > floor
    assert np.max(np.abs(mixing - np.eye(mixing.shape[0]))) > 0.05


def test_a_damping_change_moves_no_undamped_mode_shape():
    """C does not enter K v = omega**2 M v, so the basis is untouched and
    the mixing matrix is exactly the identity. That is a result about
    which matrix the parameter lives in, not a gap."""
    change = MB.BoundaryChange(MB.BoundaryParameter.DAMPING,
                               MB.ChangeProfile.SUDDEN, 1.0, 6.0)
    before, after = change.systems(MB.DISSIPATIVE_CHAIN)
    assert np.any(after.C != before.C)
    assert after.K == pytest.approx(before.K)
    assert after.M == pytest.approx(before.M)
    mixing = MB.mode_mixing_matrix(MB.system_modes(before),
                                   MB.system_modes(after))
    assert mixing == pytest.approx(np.eye(mixing.shape[0]), abs=1e-10)
    assert MB.mixing_offdiagonal_fraction(mixing) == pytest.approx(0.0,
                                                                   abs=1e-18)


def test_mixing_offdiagonal_fraction_rejects_bad_input():
    with pytest.raises(MB.MechBoundaryError):
        MB.mixing_offdiagonal_fraction(np.zeros((2, 3)))
    with pytest.raises(MB.MechBoundaryError):
        MB.mixing_offdiagonal_fraction(np.eye(3), index=7)


# --- (4) the headline: sudden scatters, gradual goes adiabatic ----------

@pytest.mark.parametrize("parameter,_floor", MOVING_PARAMETERS)
def test_participation_rises_monotonically_with_ramp_time(parameter, _floor):
    """THE headline. Sweep tau and the target mode keeps more and more of
    its energy, tending to the adiabatic limit of one."""
    sweep = MB.tau_sweep(MB.DEFAULT_CHAIN, parameter)
    assert sweep["basis_moves"] is True
    assert sweep["monotone_increasing"] is True
    assert sweep["participation"][0] < sweep["participation"][-1]
    assert sweep["adiabatic_participation"] > 0.98
    assert sweep["verdict"] == "ADIABATIC_LIMIT_PRESERVES_MODAL_IDENTITY"
    assert sweep["ledgers_close"] is True


@pytest.mark.parametrize("parameter,_floor", MOVING_PARAMETERS)
def test_a_sudden_change_keeps_strictly_less_than_the_adiabatic_limit(
        parameter, _floor):
    sweep = MB.tau_sweep(MB.DEFAULT_CHAIN, parameter)
    assert sweep["sudden_participation"] < 0.99
    assert (sweep["adiabatic_participation"]
            > sweep["sudden_participation"] + 0.01)
    assert sweep["gain_over_sudden"][-1] > 0.0


def test_the_shortest_ramp_reproduces_the_sudden_case():
    """A ramp far shorter than a period is the sudden limit, and the
    integrator has to agree with the closed-form jump."""
    sweep = MB.tau_sweep(MB.DEFAULT_CHAIN, MB.BoundaryParameter.STIFFNESS,
                         taus=(0.02, 0.5, 5.0, 40.0))
    assert sweep["participation"][0] == pytest.approx(
        sweep["sudden_participation"], abs=2e-3)


def test_a_damping_sweep_is_flat_because_the_basis_never_moves():
    """No basis scattering at all from a C-only change. The residual
    departure from one is non-proportional damping coupling ringing the
    other modes, which is a different mechanism and two orders of
    magnitude smaller than the stiffness scattering above."""
    sweep = MB.tau_sweep(MB.DISSIPATIVE_CHAIN, MB.BoundaryParameter.DAMPING)
    assert sweep["basis_moves"] is False
    assert sweep["verdict"] == "BASIS_UNMOVED_NO_MODAL_SCATTERING"
    assert sweep["sudden_participation"] == pytest.approx(1.0, abs=1e-12)
    assert min(sweep["participation"]) > 0.99
    stiffness = MB.tau_sweep(MB.DEFAULT_CHAIN, MB.BoundaryParameter.STIFFNESS)
    assert (1.0 - min(sweep["participation"])
            < 0.05 * (1.0 - stiffness["sudden_participation"]))


def test_a_sudden_change_at_zero_displacement_scatters_less():
    """Phase matters: a stiffness change made while the structure is
    passing through zero does no work and disturbs the mode far less
    than the same change made at the turning point."""
    turning = MB.simulate_change(
        MB.DEFAULT_CHAIN,
        MB.BoundaryChange(MB.BoundaryParameter.STIFFNESS,
                          MB.ChangeProfile.SUDDEN, 1.0, 4.0),
        phase=0.0)
    crossing = MB.simulate_change(
        MB.DEFAULT_CHAIN,
        MB.BoundaryChange(MB.BoundaryParameter.STIFFNESS,
                          MB.ChangeProfile.SUDDEN, 1.0, 4.0),
        phase=math.pi / 2)
    assert turning.boundary_work > 0.0
    assert crossing.boundary_work == pytest.approx(0.0, abs=1e-15)
    assert crossing.participation > turning.participation + 0.1


def test_tau_sweep_rejects_a_degenerate_sweep():
    with pytest.raises(MB.MechBoundaryError):
        MB.tau_sweep(MB.DEFAULT_CHAIN, MB.BoundaryParameter.STIFFNESS,
                     taus=(1.0,))
    with pytest.raises(MB.MechBoundaryError):
        MB.tau_sweep(MB.DEFAULT_CHAIN, MB.BoundaryParameter.STIFFNESS,
                     taus=(5.0, 1.0))
    with pytest.raises(MB.MechBoundaryError):
        MB.tau_sweep(MB.DEFAULT_CHAIN, MB.BoundaryParameter.STIFFNESS,
                     taus=(0.0, 1.0))


# --- (5) the energy ledger ----------------------------------------------

@pytest.mark.parametrize("parameter", list(MB.BoundaryParameter))
def test_the_ledger_closes_for_a_sudden_change(parameter):
    result = MB.simulate_change(
        MB.DISSIPATIVE_CHAIN,
        MB.BoundaryChange(parameter, MB.ChangeProfile.SUDDEN, 1.0, 4.0))
    ledger = result.ledger()
    assert ledger["closes"] is True
    assert ledger["dissipated"] == 0.0          # nothing is lost in zero time
    assert ledger["relative_residual"] < MB.LEDGER_TOL


@pytest.mark.parametrize("parameter", list(MB.BoundaryParameter))
def test_the_ledger_closes_for_a_gradual_change(parameter):
    result = MB.simulate_change(
        MB.DISSIPATIVE_CHAIN,
        MB.BoundaryChange(parameter, MB.ChangeProfile.GRADUAL, 1.0, 4.0, 3.0))
    ledger = result.ledger()
    assert ledger["closes"] is True
    assert ledger["relative_residual"] < MB.LEDGER_TOL
    assert ledger["dissipated"] > 0.0           # the dashpots are working


@pytest.mark.parametrize("profile,tau", [(MB.ChangeProfile.SUDDEN, 0.0),
                                         (MB.ChangeProfile.GRADUAL, 3.0)])
def test_omitting_the_boundary_work_breaks_the_ledger(profile, tau):
    """POWER: the ledger only closes because W_boundary is in it."""
    result = MB.simulate_change(
        MB.DEFAULT_CHAIN,
        MB.BoundaryChange(MB.BoundaryParameter.STIFFNESS, profile,
                          1.0, 4.0, tau))
    assert abs(result.boundary_work) > 1e-3
    assert result.ledger()["closes"] is True
    broken = result.ledger(include_boundary_work=False)
    assert broken["closes"] is False
    assert broken["boundary_work_included"] is False
    assert broken["residual"] == pytest.approx(result.boundary_work,
                                               rel=1e-4, abs=1e-9)


def test_energy_ledger_is_the_stated_identity():
    ledger = MB.energy_ledger(1.0, 1.5, 0.75, 0.25)
    assert ledger["closes"] is True
    assert ledger["predicted_energy_after"] == pytest.approx(1.5)
    assert MB.energy_ledger(1.0, 1.5, 0.75, 0.30)["closes"] is False
    assert MB.energy_ledger(1.0, 1.5, 0.50, 0.25)["closes"] is False


def test_energy_ledger_refuses_negative_dissipation_and_bad_tolerance():
    with pytest.raises(MB.MechBoundaryError):
        MB.energy_ledger(1.0, 1.0, 0.0, dissipated=-1.0)
    with pytest.raises(MB.MechBoundaryError):
        MB.energy_ledger(1.0, 1.0, 0.0, tol=0.0)


def test_work_done_by_boundary_is_computed_from_the_change_not_the_residual():
    """W = 0.5*u^T dK u for a stiffening at the turning point, exactly."""
    change = MB.BoundaryChange(MB.BoundaryParameter.STIFFNESS,
                               MB.ChangeProfile.SUDDEN, 1.0, 4.0)
    before, after = change.systems(MB.DEFAULT_CHAIN)
    start = MB.initial_state(MB.system_modes(before), 0)
    end = MB.apply_sudden(start, before, after)
    work = MB.work_done_by_boundary(MB.Snapshot(before, start),
                                    MB.Snapshot(after, end))
    expected = 0.5 * float(start.u @ ((after.K - before.K) @ start.u))
    assert work == pytest.approx(expected, rel=1e-12)
    assert work > 0.0
    assert MB.Snapshot(after, end).energy == pytest.approx(
        MB.Snapshot(before, start).energy + work, rel=1e-12)


def test_a_softening_boundary_does_negative_work():
    """Electrode loading here softens and mass-loads; the agent takes
    energy out rather than putting it in, and the ledger still closes."""
    result = MB.simulate_change(
        MB.DEFAULT_CHAIN,
        MB.BoundaryChange(MB.BoundaryParameter.ELECTRODE_LOADING,
                          MB.ChangeProfile.SUDDEN, 1.0, 4.0))
    assert result.boundary_work < 0.0
    assert result.energy_after < result.energy_before
    assert result.ledger()["closes"] is True


def test_momentum_not_velocity_is_continuous_through_a_mass_change():
    change = MB.BoundaryChange(MB.BoundaryParameter.ELECTRODE_LOADING,
                               MB.ChangeProfile.SUDDEN, 1.0, 4.0)
    before, after = change.systems(MB.DEFAULT_CHAIN)
    start = MB.initial_state(MB.system_modes(before), 0, phase=math.pi / 2)
    end = MB.apply_sudden(start, before, after)
    assert end.u == pytest.approx(start.u)
    assert end.momentum(after.M) == pytest.approx(start.momentum(before.M),
                                                  abs=1e-12)
    assert not np.allclose(end.v, start.v)


# --- (6) damping strictly dissipates ------------------------------------

def test_damping_strictly_dissipates_with_no_drive():
    system = MB.build_system(MB.DISSIPATIVE_CHAIN)
    basis = MB.system_modes(system)
    run = MB.free_response(system, MB.initial_state(basis, 0), 30.0)
    assert run["is_damped"] is True
    assert run["dissipated"] > 0.0
    assert run["energy_after"] < run["energy_before"]
    assert run["monotone_decreasing"] is True
    assert run["boundary_work"] == pytest.approx(0.0, abs=1e-15)
    assert run["ledger"]["closes"] is True


def test_an_undamped_chain_conserves_energy_and_dissipates_nothing():
    system = MB.build_system(MB.DEFAULT_CHAIN)
    basis = MB.system_modes(system)
    run = MB.free_response(system, MB.initial_state(basis, 0), 30.0)
    assert run["is_damped"] is False
    assert run["dissipated"] == pytest.approx(0.0, abs=1e-15)
    assert run["energy_after"] == pytest.approx(run["energy_before"],
                                                rel=1e-8)


def test_more_damping_dissipates_more():
    basis_ref = MB.system_modes(MB.build_system(MB.DEFAULT_CHAIN))
    losses = []
    for scale in (0.5, 1.0, 2.0):
        system = MB.build_system(MB.ChainConfig().dissipative(scale))
        state = MB.State(basis_ref.shapes[:, 0].copy(),
                         np.zeros(basis_ref.n))
        losses.append(MB.free_response(system, state, 20.0)["dissipated"])
    assert losses[0] < losses[1] < losses[2]


def test_free_response_refuses_a_non_positive_duration():
    system = MB.build_system(MB.DEFAULT_CHAIN)
    basis = MB.system_modes(system)
    with pytest.raises(MB.MechBoundaryError):
        MB.free_response(system, MB.initial_state(basis, 0), 0.0)


# --- (7) typing of the change itself ------------------------------------

def test_the_four_parameters_touch_different_matrices():
    base = MB.build_system(MB.DISSIPATIVE_CHAIN)
    touched = {}
    for parameter in MB.BoundaryParameter:
        after = MB.build_system(
            MB.with_boundary(MB.DISSIPATIVE_CHAIN, parameter, 4.0))
        touched[parameter] = (bool(np.any(after.M != base.M)),
                              bool(np.any(after.K != base.K)),
                              bool(np.any(after.C != base.C)))
    assert touched[MB.BoundaryParameter.STIFFNESS] == (False, True, False)
    assert touched[MB.BoundaryParameter.DAMPING] == (False, False, True)
    assert touched[MB.BoundaryParameter.SUPPORT_IMPEDANCE] == (False, True,
                                                               True)
    assert touched[MB.BoundaryParameter.ELECTRODE_LOADING] == (True, True,
                                                               True)
    assert len(set(touched.values())) == len(MB.BoundaryParameter)


def test_a_sudden_change_may_not_carry_a_ramp_time():
    with pytest.raises(MB.MechBoundaryError):
        MB.BoundaryChange(MB.BoundaryParameter.STIFFNESS,
                          MB.ChangeProfile.SUDDEN, 1.0, 4.0, 2.0)


def test_a_gradual_change_needs_a_positive_ramp_time():
    with pytest.raises(MB.MechBoundaryError):
        MB.BoundaryChange(MB.BoundaryParameter.STIFFNESS,
                          MB.ChangeProfile.GRADUAL, 1.0, 4.0, 0.0)
    with pytest.raises(MB.MechBoundaryError):
        MB.BoundaryChange(MB.BoundaryParameter.STIFFNESS,
                          MB.ChangeProfile.GRADUAL, 1.0, 4.0, -1.0)


def test_with_boundary_refuses_a_parameter_it_does_not_know():
    with pytest.raises(MB.MechBoundaryError):
        MB.with_boundary(MB.DEFAULT_CHAIN, "STIFFNESS", 2.0)
    with pytest.raises(MB.MechBoundaryError):
        MB.with_boundary(MB.DEFAULT_CHAIN, MB.BoundaryParameter.STIFFNESS,
                         float("inf"))


def test_the_ramp_is_smooth_at_both_ends_and_spans_zero_to_one():
    assert MB.ramp(0.0, 5.0) == (0.0, 0.0)
    assert MB.ramp(5.0, 5.0) == (1.0, 0.0)
    assert MB.ramp(2.5, 5.0)[0] == pytest.approx(0.5)
    assert MB.ramp(2.5, 5.0)[1] > 0.0
    # a sudden change has no ramp: it is a step
    assert MB.ramp(-1.0, 0.0) == (0.0, 0.0)
    assert MB.ramp(1.0, 0.0) == (1.0, 0.0)
    taus = np.linspace(0.0, 4.0, 41)
    values = [MB.ramp(t, 4.0)[0] for t in taus]
    assert np.all(np.diff(values) >= 0.0)


def test_a_bad_chain_configuration_is_refused():
    with pytest.raises(MB.MechBoundaryError):
        MB.ChainConfig(n_nodes=1)
    with pytest.raises(MB.MechBoundaryError):
        MB.ChainConfig(node_mass=0.0)
    with pytest.raises(MB.MechBoundaryError):
        MB.ChainConfig(boundary_damping=-1.0)
    with pytest.raises(MB.MechBoundaryError):
        MB.ChainConfig(electrode_node=99)
    with pytest.raises(MB.MechBoundaryError):
        MB.ChainConfig(node_mass=1.0, electrode_mass=-1.0)


# --- (8) the refusals ----------------------------------------------------

def test_refuse_energy_from_nothing_raises():
    with pytest.raises(MB.MechBoundaryError) as excinfo:
        MB.refuse_energy_from_nothing(0.068, "the boundary itself")
    assert "BOUNDARY_WORK_REQUIRED" in str(excinfo.value)


def test_refuse_quantum_claim_raises_and_points_at_the_other_lane():
    with pytest.raises(MB.MechBoundaryError) as excinfo:
        MB.refuse_quantum_claim("photons were created by the moving support")
    message = str(excinfo.value)
    assert "dynboundary" in message
    assert "CLASSICAL_MODEL_ESTABLISHES_NOTHING_QUANTUM" in message


def test_the_refusals_have_no_non_raising_path():
    for refusal in (MB.refuse_energy_from_nothing, MB.refuse_quantum_claim):
        with pytest.raises(MB.MechBoundaryError):
            refusal()


# --- (9) the report ------------------------------------------------------

def test_report_declares_what_it_measured_and_what_it_concluded():
    report = MB.mechboundary_report()
    assert report["measured_here"] == "nothing"
    assert report["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert report["evidence_class"] in ("ANALYTIC_MODEL",
                                        "NUMERICAL_SIMULATION")
    assert set(report["evidence_classes"]) == {"ANALYTIC_MODEL",
                                               "NUMERICAL_SIMULATION"}
    assert report["verdict"] == "CLASSICAL_DYNAMIC_BOUNDARY_MODEL_IMPLEMENTED"
    assert report["verdict"] == MB.DEFAULT_VERDICT
    assert report["verdict"] in report["verdicts"]
    assert len(report["what_this_does_not_say"]) > 200
    assert report["parameters"] == [p.value for p in MB.BoundaryParameter]
    assert report["profiles"] == [p.value for p in MB.ChangeProfile]
    assert "dynboundary" in report["distinct_from_the_quantum_lane"]


def test_the_headline_helper_reports_sudden_against_adiabatic():
    headline = MB.mixing_headline()
    assert headline["measured_here"] == "nothing"
    assert headline["monotone_increasing"] is True
    assert headline["adiabatic_participation"] > headline[
        "sudden_participation"]
    assert headline["adiabatic_participation"] > 0.98


def test_every_result_carries_its_ledger():
    result = MB.simulate_change(
        MB.DEFAULT_CHAIN,
        MB.BoundaryChange(MB.BoundaryParameter.STIFFNESS,
                          MB.ChangeProfile.GRADUAL, 1.0, 4.0, 2.0))
    payload = result.as_dict()
    assert payload["measured_here"] == "nothing"
    assert payload["ledger"]["closes"] is True
    assert payload["profile"] == "GRADUAL"
    assert payload["parameter"] == "STIFFNESS"
    assert sum(payload["modal_energy_fractions"]) == pytest.approx(1.0)


def test_the_module_carries_no_private_content():
    source = inspect.getsource(MB)
    for forbidden in ("C:\\", "C:/", "OneDrive", "Users\\", "andrew"):
        assert forbidden not in source
    assert re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", source) is None
