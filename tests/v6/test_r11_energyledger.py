"""P15 — energy accounting for interrupted phonon and photon-like states.

The damping convention is pinned down with numbers: the energy decays at
``omega/Q`` and the amplitude at ``omega/(2Q)``, and the factor of two
between them is computed rather than asserted. A basis switch is required
to preserve displacement and momentum, to place every joule of the
post-switch state somewhere in the post-switch eigenbasis, and to close
``E_after == E_before + W_switching``. The electromagnetic ledger is
required to close exactly on a synthetic case, to leave a residual
exactly equal to the switching work when that term is dropped, and — as
it actually stands, with no bench data — to report ``E_unclosed`` as an
interval that includes zero. All four red-team refusals must raise.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from r11 import energyledger as EL
from r11.mechboundary import State


# --- helpers ---------------------------------------------------------------

def chain(k_end: float = 1.0, m_extra: float = 0.0):
    """A 3-node grounded chain, with one tunable end spring and mass."""
    M = np.diag([1.0, 1.0 + m_extra, 1.0])
    K = np.array([[2.0, -1.0, 0.0],
                  [-1.0, 2.0, -1.0],
                  [0.0, -1.0, 1.0 + k_end]])
    return EL.make_system(M, K)


def turning_point_state(system, mode_index: int = 0) -> State:
    """All the energy in strain: u is one mode shape, v is zero."""
    basis = EL.system_basis(system)
    return State(basis.shapes[:, mode_index].copy(), np.zeros(3))


def moving_state(system, mode_index: int = 0) -> State:
    """All the energy kinetic: u is zero, v is one mode shape scaled."""
    basis = EL.system_basis(system)
    omega = float(basis.omega[mode_index])
    return State(np.zeros(3), omega * basis.shapes[:, mode_index].copy())


# --- (1) modal energy ------------------------------------------------------

def test_mode_energy_is_kinetic_plus_potential():
    assert EL.mode_energy(2.0, 0.0, 8.0, 3.0) == pytest.approx(36.0)
    assert EL.mode_energy(2.0, 5.0, 8.0, 0.0) == pytest.approx(25.0)
    assert EL.mode_energy(2.0, 5.0, 8.0, 3.0) == pytest.approx(61.0)


def test_turning_point_energy_matches_the_omega_form():
    """0.5*k*q^2 == 0.5*m*(omega*q)^2 because k = m*omega^2."""
    m, k, q = 2.0, 8.0, 3.0
    omega = EL.mode_omega(m, k)
    assert omega == pytest.approx(2.0)
    assert EL.mode_energy(m, 0.0, k, q) == pytest.approx(
        0.5 * m * (omega * q) ** 2)


def test_mode_energy_guards():
    with pytest.raises(EL.EnergyLedgerError):
        EL.mode_energy(0.0, 1.0, 1.0, 1.0)
    with pytest.raises(EL.EnergyLedgerError):
        EL.mode_energy(1.0, 1.0, -1.0, 1.0)
    with pytest.raises(EL.EnergyLedgerError):
        EL.mode_omega(1.0, 0.0)


# --- (2) the damping convention, and the factor of two --------------------

def test_energy_and_amplitude_decay_rates_differ_by_exactly_two():
    """The load-bearing convention check."""
    for omega, q in ((1.0, 100.0), (7.5, 3.0), (2.0 * math.pi * 4096.0, 1e5)):
        assert EL.energy_decay_rate(omega, q) == pytest.approx(
            2.0 * EL.amplitude_decay_rate(omega, q), rel=1e-15)
        assert EL.decay_rate_ratio(omega, q) == pytest.approx(2.0, rel=1e-15)


def test_energy_decay_is_the_square_of_the_amplitude_decay():
    omega, q = 3.0, 40.0
    for t in (0.0, 1.0, 5.0, 50.0):
        e = EL.damped_mode_energy(1.0, omega, q, t)
        a = EL.damped_amplitude(1.0, omega, q, t)
        assert e == pytest.approx(a ** 2, rel=1e-12)


def test_the_two_time_constants_differ_by_the_factor_two():
    omega, q = 5.0, 20.0
    tau_energy = q / omega
    tau_amplitude = 2.0 * q / omega
    assert tau_amplitude == pytest.approx(2.0 * tau_energy)
    assert EL.damped_mode_energy(1.0, omega, q, tau_energy) == pytest.approx(
        1.0 / math.e, rel=1e-12)
    assert EL.damped_amplitude(1.0, omega, q, tau_amplitude) == pytest.approx(
        1.0 / math.e, rel=1e-12)


def test_using_the_wrong_convention_loses_half_the_energy():
    """Reading omega/Q as an AMPLITUDE rate halves the ringdown, and the
    resulting energy is the square of the correct one -- the factor-2
    error the convention exists to prevent."""
    omega, q, t = 2.0, 10.0, 3.0
    correct = EL.damped_mode_energy(1.0, omega, q, t)
    wrong = math.exp(-omega * t / q) ** 2          # omega/Q on the amplitude
    assert wrong == pytest.approx(correct ** 2, rel=1e-12)
    assert wrong < correct


def test_damping_convention_report():
    conv = EL.damping_convention()
    assert conv["energy_law"] == "E(t) = E0 * exp(-omega*t/Q)"
    assert conv["amplitude_law"] == "a(t) = a0 * exp(-omega*t/(2*Q))"
    assert conv["rate_ratio_energy_over_amplitude"] == pytest.approx(2.0)
    assert conv["rate_ratio_is_two"] is True
    assert conv["energy_is_amplitude_squared"] is True
    assert conv["lightly_damped"] is True
    assert conv["claim_class"] == "SOURCE_ESTABLISHED_PHYSICS"
    assert conv["measured_here"] == "nothing"


def test_damping_guards():
    with pytest.raises(EL.EnergyLedgerError):
        EL.damped_mode_energy(1.0, 1.0, 0.0, 1.0)
    with pytest.raises(EL.EnergyLedgerError):
        EL.damped_mode_energy(1.0, -1.0, 10.0, 1.0)
    with pytest.raises(EL.EnergyLedgerError):
        EL.damped_amplitude(1.0, 1.0, 10.0, -1.0)


# --- (3) basis switching ---------------------------------------------------

def test_projection_places_every_joule_in_the_post_switch_basis():
    """sum(modal energies) == the physical energy after the switch."""
    before, after = chain(1.0), chain(4.0)
    result = EL.switch_basis(turning_point_state(before), before, after)
    assert result.modal_total == pytest.approx(result.energy_after, rel=1e-12)
    assert result.projection_defect < EL.ENERGY_TOL


def test_modal_fractions_sum_to_one():
    before, after = chain(1.0), chain(4.0)
    result = EL.switch_basis(turning_point_state(before), before, after)
    fractions = result.fractions
    assert fractions.size == 3
    assert float(np.sum(fractions)) == pytest.approx(1.0, abs=1e-12)
    assert EL.refuse_hidden_basis_energy(fractions) == pytest.approx(1.0)


def test_the_mechanical_ledger_closes_across_the_switch():
    """E_after == E_before + W_switching, with W evaluated independently."""
    before, after = chain(1.0), chain(4.0)
    result = EL.switch_basis(turning_point_state(before), before, after)
    assert result.energy_after == pytest.approx(
        result.energy_before + result.switching_work, rel=1e-12)
    assert result.closes is True
    assert result.switching_work != 0.0


def test_a_stiffness_switch_scatters_the_mode_across_the_new_basis():
    """The energy that left mode 0 is in the other modes, not gone."""
    before, after = chain(1.0), chain(4.0)
    result = EL.switch_basis(turning_point_state(before), before, after)
    fractions = result.fractions
    assert fractions[0] < 1.0 - 1e-6
    assert float(np.sum(fractions[1:])) > 1e-6
    assert float(np.sum(fractions)) == pytest.approx(1.0, abs=1e-12)


def test_a_mass_switch_does_work_on_a_moving_structure():
    before, after = chain(1.0, 0.0), chain(1.0, 0.5)
    result = EL.switch_basis(moving_state(before), before, after)
    assert result.energy_after < result.energy_before
    assert result.switching_work < 0.0
    assert result.energy_after == pytest.approx(
        result.energy_before + result.switching_work, rel=1e-12)
    assert float(np.sum(result.fractions)) == pytest.approx(1.0, abs=1e-12)


def test_a_null_switch_moves_nothing():
    system = chain(1.0)
    result = EL.switch_basis(turning_point_state(system), system, system)
    assert result.switching_work == pytest.approx(0.0, abs=1e-12)
    assert result.energy_after == pytest.approx(result.energy_before)
    assert result.fractions[0] == pytest.approx(1.0, abs=1e-9)
    assert result.closes is True


def test_switch_basis_report_is_self_consistent():
    before, after = chain(1.0), chain(4.0)
    d = EL.switch_basis(turning_point_state(before), before, after).as_dict()
    assert d["modal_fractions_sum"] == pytest.approx(1.0, abs=1e-12)
    assert d["mechanical_identity"] == "E_after == E_before + W_switching"
    assert d["closes"] is True
    assert d["measured_here"] == "nothing"
    assert len(d["modal_energies"]) == 3


def test_switch_basis_guards():
    with pytest.raises(EL.EnergyLedgerError):
        EL.switch_basis("not a state", chain(), chain())
    with pytest.raises(EL.EnergyLedgerError):
        EL.make_system(np.eye(3), np.eye(2))


# --- (4) the two basis refusals -------------------------------------------

def test_refuse_transferred_energy_as_loss_always_raises():
    """Attack 9: energy that moved to another mode is not a loss."""
    with pytest.raises(EL.EnergyLedgerError) as exc:
        EL.refuse_transferred_energy_as_loss(0, (1, 2), 0.37)
    message = str(exc.value)
    assert "not loss" in message.lower() or "NOT loss" in message
    assert "0.37" in message
    with pytest.raises(EL.EnergyLedgerError):
        EL.refuse_transferred_energy_as_loss()


def test_refuse_hidden_basis_energy_raises_on_a_short_sum():
    """Attack 8: hide mode energy in a discarded basis."""
    with pytest.raises(EL.EnergyLedgerError) as exc:
        EL.refuse_hidden_basis_energy([0.5, 0.2])
    assert "0.7" in str(exc.value)
    with pytest.raises(EL.EnergyLedgerError):
        EL.refuse_hidden_basis_energy([0.6, 0.6])
    with pytest.raises(EL.EnergyLedgerError):
        EL.refuse_hidden_basis_energy([1.2, -0.2])
    with pytest.raises(EL.EnergyLedgerError):
        EL.refuse_hidden_basis_energy([])


def test_refuse_hidden_basis_energy_passes_a_complete_projection():
    assert EL.refuse_hidden_basis_energy([0.5, 0.3, 0.2]) == pytest.approx(1.0)


def test_dropping_a_mode_from_the_report_is_caught():
    """Truncating a real projection is exactly the attack, and it trips."""
    before, after = chain(1.0), chain(4.0)
    fractions = EL.switch_basis(
        turning_point_state(before), before, after).fractions
    assert EL.refuse_hidden_basis_energy(fractions) == pytest.approx(1.0)
    with pytest.raises(EL.EnergyLedgerError):
        EL.refuse_hidden_basis_energy(fractions[:-1])


# --- (5) the electrical input integral -------------------------------------

def test_constant_power_integrates_to_v_times_i_times_t():
    v = np.full(5, 2.0)
    i = np.full(5, 3.0)
    assert EL.electrical_input_energy(v, i, dt=0.25) == pytest.approx(6.0)


def test_explicit_times_give_the_same_integral():
    t = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
    v = np.full(5, 2.0)
    i = np.full(5, 3.0)
    assert EL.electrical_input_energy(v, i, times=t) == pytest.approx(6.0)


def test_electrical_input_energy_guards():
    v = np.ones(4)
    with pytest.raises(EL.EnergyLedgerError):
        EL.electrical_input_energy(v, np.ones(3), dt=0.1)
    with pytest.raises(EL.EnergyLedgerError):
        EL.electrical_input_energy([1.0], [1.0], dt=0.1)
    with pytest.raises(EL.EnergyLedgerError):
        EL.electrical_input_energy(v, v)
    with pytest.raises(EL.EnergyLedgerError):
        EL.electrical_input_energy(v, v, times=np.array([0.0, 1.0, 1.0, 2.0]))


# --- (6) the ledger: the power control ------------------------------------

def test_a_synthetic_ledger_closes_exactly():
    lg = EL.synthetic_ledger(include_switching_work=True)
    assert lg["e_input_j"] == 10.0
    assert lg["e_unclosed_j"] == 0.0
    assert lg["sigma_unclosed_j"] == 0.0
    assert lg["e_unclosed_interval_j"] == (0.0, 0.0)
    assert lg["interval_includes_zero"] is True
    assert lg["closes"] is True
    assert lg["closure_is_vacuous"] is False
    assert lg["switching_work_included"] is True


def test_omitting_switching_work_leaves_exactly_that_residual():
    """The detector has teeth: the deficit is the missing term, exactly."""
    lg = EL.synthetic_ledger(include_switching_work=False)
    assert lg["e_unclosed_j"] == EL.SYNTHETIC_TERMS["switching_work"]
    assert lg["e_unclosed_j"] == 1.0
    assert lg["closes"] is False
    assert lg["interval_includes_zero"] is False
    assert lg["switching_work_included"] is False


def test_power_check_reports_both_arms():
    power = EL.power_check()
    assert power["closed_residual_j"] == 0.0
    assert power["closed_closes"] is True
    assert power["closed_is_vacuous"] is False
    assert power["omitted_residual_equals_switching_work"] is True
    assert power["omitted_closes"] is False
    assert power["synthetic_input_j"] == 10.0


def test_every_ledger_term_is_reported():
    lg = EL.synthetic_ledger()
    names = [t["name"] for t in lg["terms"]]
    assert names == list(EL.LEDGER_TERMS)
    assert len(names) == 8
    assert "switching_work" in names
    for term in lg["terms"]:
        assert term["meaning"]
        assert term["status"] in EL.CLAIM_CLASSES


# --- (7) the ledger: uncertainty and the unmeasured residual --------------

def test_sigmas_propagate_in_quadrature():
    lg = EL.ledger(10.0, sigmas={n: 0.1 for n in EL.LEDGER_TERMS},
                   **EL.SYNTHETIC_TERMS)
    assert lg["sigma_unclosed_j"] == pytest.approx(math.sqrt(8 * 0.01))
    lo, hi = lg["e_unclosed_interval_j"]
    assert hi - lo == pytest.approx(2 * 2.0 * lg["sigma_unclosed_j"])
    assert lg["interval_includes_zero"] is True


def test_dropping_a_term_drops_its_sigma_from_the_quadrature():
    lg = EL.ledger(10.0, sigmas={n: 0.1 for n in EL.LEDGER_TERMS},
                   include_switching_work=False, **EL.SYNTHETIC_TERMS)
    assert lg["sigma_unclosed_j"] == pytest.approx(math.sqrt(7 * 0.01))


def test_the_ledger_as_it_stands_has_an_interval_that_includes_zero():
    """No bench data: every term blocked, the residual unmeasured."""
    lg = EL.blocked_ledger()
    assert lg["all_terms_blocked"] is True
    assert lg["sigma_unclosed_j"] is None
    assert lg["e_unclosed_interval_j"] == (-math.inf, math.inf)
    assert lg["interval_includes_zero"] is True
    assert lg["closure_is_vacuous"] is True
    assert lg["residual_status"] == "BLOCKED_MISSING_DATA"
    assert lg["claim_class"] == "BLOCKED_MISSING_DATA"
    assert lg["residual_is_evidence_of_unknown_channel"] is False
    assert set(lg["uncalibrated_terms"]) == set(EL.LEDGER_TERMS)
    for term in lg["terms"]:
        assert term["status"] == "BLOCKED_MISSING_DATA"
        assert term["sigma_j"] is None
        assert term["calibrated"] is False


def test_one_uncalibrated_term_makes_the_whole_interval_unbounded():
    sigmas = {n: 0.1 for n in EL.LEDGER_TERMS}
    del sigmas["e_acoustic"]
    lg = EL.ledger(10.0, sigmas=sigmas, **EL.SYNTHETIC_TERMS)
    assert lg["uncalibrated_terms"] == ["e_acoustic"]
    assert lg["sigma_unclosed_j"] is None
    assert lg["closure_is_vacuous"] is True
    assert lg["interval_includes_zero"] is True


def test_ledger_guards():
    with pytest.raises(EL.EnergyLedgerError):
        EL.ledger(1.0, k_sigma=0.0)
    with pytest.raises(EL.EnergyLedgerError):
        EL.ledger(1.0, sigmas={"e_mystery": 0.1})
    with pytest.raises(EL.EnergyLedgerError):
        EL.ledger(1.0, calibrated_status="VIBES")
    with pytest.raises(EL.EnergyLedgerError):
        EL.LedgerTerm("not_a_term", 1.0)
    with pytest.raises(EL.EnergyLedgerError):
        EL.LedgerTerm("e_joule", 1.0, sigma=-1.0)
    with pytest.raises(EL.EnergyLedgerError):
        EL.LedgerTerm("e_joule", float("inf"))


# --- (8) the two ledger refusals ------------------------------------------

def test_refuse_unknown_channel_claim_always_raises():
    lg = EL.blocked_ledger()
    with pytest.raises(EL.EnergyLedgerError) as exc:
        EL.refuse_unknown_channel_claim(
            lg["e_unclosed_j"], lg["e_unclosed_interval_j"],
            "a new energy channel")
    message = str(exc.value)
    assert "includes zero" in message
    assert "BLOCKED_MISSING_DATA" in message
    with pytest.raises(EL.EnergyLedgerError):
        EL.refuse_unknown_channel_claim(1.0, (0.5, 1.5))


def test_refuse_ignored_switching_work_always_raises():
    """Attack 10: boundary and switching work must appear in the ledger."""
    with pytest.raises(EL.EnergyLedgerError):
        EL.refuse_ignored_switching_work()
    omitted = EL.synthetic_ledger(include_switching_work=False)
    with pytest.raises(EL.EnergyLedgerError) as exc:
        EL.refuse_ignored_switching_work(omitted)
    assert "switching_work" in str(exc.value)


# --- (9) the report --------------------------------------------------------

def test_report_carries_the_verdict_and_the_disclaimers():
    report = EL.energyledger_report()
    assert report["verdict"] == "ENERGY_LEDGER_CLOSES_RESIDUAL_UNMEASURED"
    assert EL.VERDICT == "ENERGY_LEDGER_CLOSES_RESIDUAL_UNMEASURED"
    assert report["measured_here"] == "nothing"
    assert report["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert report["claim_class"] in EL.CLAIM_CLASSES
    assert report["claim_class"] == "REPOSITORY_COMPUTATIONAL_RESULT"
    assert report["what_this_does_not_say"]
    assert report["damping_convention"]["rate_ratio_is_two"] is True
    assert report["ledger_as_it_stands"]["interval_includes_zero"] is True
    assert report["ledger_as_it_stands"]["closure_is_vacuous"] is True
    assert report["ledger_as_it_stands"]["all_terms_blocked"] is True
    assert report["power_control"]["closed_residual_j"] == 0.0
    assert set(report["ledger_terms"]) == set(EL.LEDGER_TERMS)


def test_the_declared_claim_classes_are_the_shared_nine():
    assert EL.CLAIM_CLASSES == (
        "EXACT_IDENTITY", "SOURCE_ESTABLISHED_PHYSICS",
        "REPOSITORY_COMPUTATIONAL_RESULT", "ENGINEERING_CANDIDATE",
        "RETROSPECTIVE_NUMERIC_MATCH", "PROSPECTIVE_PREDICTION",
        "BENCH_MEASUREMENT", "UNSUPPORTED", "BLOCKED_MISSING_DATA")
