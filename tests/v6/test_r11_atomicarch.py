"""P09 — atomic-clock architecture: Rabi, Ramsey, maser, quartz flywheel."""

from __future__ import annotations

import math

import numpy as np
import pytest

from r11 import atomicarch as A


# --- the functional graph -----------------------------------------------

def test_build_graph_returns_the_stages_in_order():
    g = A.build_graph()
    assert tuple(g) == (
        A.Stage.SOURCE,
        A.Stage.STATE_SELECTOR_MAGNET,
        A.Stage.FIRST_INTERACTION_REGION,
        A.Stage.FREE_EVOLUTION,
        A.Stage.SECOND_INTERACTION_REGION,
        A.Stage.ANALYZER_MAGNET,
        A.Stage.DETECTOR,
        A.Stage.ERROR_SIGNAL,
        A.Stage.SERVO,
        A.Stage.FLYWHEEL,
    )
    assert len(g) == 10
    assert g[0] is A.Stage.SOURCE
    assert g[-1] is A.Stage.FLYWHEEL


def test_graph_edges_are_ordered_and_connected():
    g = A.build_graph()
    assert g.is_connected()
    assert len(g.edges) == len(g.nodes) - 1
    for (a, b), (na, nb) in zip(g.edges, zip(g.nodes, g.nodes[1:])):
        assert a is na and b is nb
    # state selection strictly precedes the first interaction region
    order = list(g.nodes)
    assert order.index(A.Stage.STATE_SELECTOR_MAGNET) < \
        order.index(A.Stage.FIRST_INTERACTION_REGION)
    assert order.index(A.Stage.ERROR_SIGNAL) < order.index(A.Stage.SERVO)


def test_the_flywheel_is_a_quartz_oscillator_or_a_maser_cavity():
    q = A.build_graph(A.FlywheelKind.QUARTZ_OSCILLATOR)
    m = A.build_graph(A.FlywheelKind.SELF_OSCILLATING_MASER_CAVITY)
    assert q.flywheel_kind is A.FlywheelKind.QUARTZ_OSCILLATOR
    assert m.flywheel_kind is A.FlywheelKind.SELF_OSCILLATING_MASER_CAVITY
    assert tuple(q) == tuple(m)          # same functional chain either way


def test_every_stage_has_a_declared_role():
    g = A.build_graph()
    for s in g:
        assert g.role(s)
    assert "GRADIENT" in g.role(A.Stage.STATE_SELECTOR_MAGNET)


def test_a_missing_stage_is_refused():
    chain = [s for s in A.CANONICAL_CHAIN
             if s is not A.Stage.STATE_SELECTOR_MAGNET]
    with pytest.raises(A.AtomicArchError):
        A.refuse_invalid_chain(chain)


def test_an_out_of_order_chain_is_refused():
    chain = list(A.CANONICAL_CHAIN)
    i = chain.index(A.Stage.SERVO)
    j = chain.index(A.Stage.ERROR_SIGNAL)
    chain[i], chain[j] = chain[j], chain[i]      # servo before error signal
    with pytest.raises(A.AtomicArchError):
        A.refuse_invalid_chain(chain)


def test_a_repeated_or_untyped_node_is_refused():
    with pytest.raises(A.AtomicArchError):
        A.refuse_invalid_chain(list(A.CANONICAL_CHAIN) + [A.Stage.SOURCE])
    with pytest.raises(A.AtomicArchError):
        A.refuse_invalid_chain(list(A.CANONICAL_CHAIN) + ["servo"])


def test_the_canonical_chain_passes_validation():
    assert A.refuse_invalid_chain(A.build_graph()) is None
    assert A.refuse_invalid_chain(A.CANONICAL_CHAIN) is None


# --- Rabi ---------------------------------------------------------------

def test_a_pi_pulse_on_resonance_inverts_the_population():
    omega = 2.0 * math.pi * 100.0
    t_pi = A.pi_pulse_duration(omega)
    assert omega * t_pi == pytest.approx(math.pi, rel=1e-12)
    assert A.rabi_probability(omega, t_pi, 0.0) == pytest.approx(1.0, abs=1e-12)


def test_a_half_pi_pulse_on_resonance_gives_an_equal_superposition():
    omega = 3.7
    assert A.rabi_probability(
        omega, A.half_pi_pulse_duration(omega), 0.0) == pytest.approx(0.5,
                                                                     abs=1e-12)


def test_on_resonance_rabi_is_sin_squared_of_half_the_pulse_area():
    omega = 2.5
    for t in (0.0, 0.3, 1.1, 2.7, 5.0):
        assert A.rabi_probability(omega, t, 0.0) == pytest.approx(
            math.sin(0.5 * omega * t) ** 2, rel=1e-12, abs=1e-15)


def test_POWER_detuning_caps_the_peak_below_the_on_resonance_peak():
    """A detuned drive cannot reach full inversion, at ANY pulse length."""
    omega = 2.0 * math.pi * 50.0
    times = np.linspace(0.0, 4.0 * A.pi_pulse_duration(omega), 4001)

    on_res_peak = A.rabi_sweep(omega, times, 0.0).max()
    assert on_res_peak == pytest.approx(1.0, abs=1e-6)

    for delta in (0.25 * omega, 0.5 * omega, 1.0 * omega, 3.0 * omega):
        detuned_peak = A.rabi_sweep(omega, times, delta).max()
        assert detuned_peak < on_res_peak
        # and it matches the analytic ceiling Omega^2/(Omega^2 + delta^2)
        assert detuned_peak == pytest.approx(
            A.rabi_peak_probability(omega, delta), abs=1e-5)


def test_the_rabi_ceiling_falls_monotonically_with_detuning():
    omega = 1.0
    peaks = [A.rabi_peak_probability(omega, d)
             for d in (0.0, 0.5, 1.0, 2.0, 4.0, 8.0)]
    assert peaks[0] == pytest.approx(1.0)
    assert all(a > b for a, b in zip(peaks, peaks[1:]))


def test_rabi_rejects_negative_rates_and_times():
    with pytest.raises(A.AtomicArchError):
        A.rabi_probability(-1.0, 1.0)
    with pytest.raises(A.AtomicArchError):
        A.rabi_probability(1.0, -1.0)
    with pytest.raises(A.AtomicArchError):
        A.pi_pulse_duration(0.0)


# --- Ramsey -------------------------------------------------------------

def test_ramsey_fringe_is_maximal_at_zero_detuning_and_periodic():
    T = 0.5
    assert A.ramsey_fringe(0.0, T) == pytest.approx(1.0, abs=1e-12)
    period = A.ramsey_fringe_period(T)
    assert period == pytest.approx(2.0 * math.pi / T, rel=1e-12)
    for d in (0.3, 1.7, -2.2):
        assert A.ramsey_fringe(d + period, T) == pytest.approx(
            A.ramsey_fringe(d, T), abs=1e-12)


def test_POWER_the_measured_fringe_width_shrinks_as_T_grows():
    """Longer free evolution -> narrower fringe. Measured from a sweep."""
    Ts = [0.01, 0.02, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0]
    widths = [A.ramsey_central_fringe_width(T) for T in Ts]
    # strictly monotone decreasing in T
    assert all(w1 > w2 for w1, w2 in zip(widths, widths[1:]))
    # and the swept width tracks the ideal pi/T
    for T, w in zip(Ts, widths):
        assert w == pytest.approx(math.pi / T, rel=1e-3)
    # halving the width takes doubling T: width * T is invariant
    products = [w * T for w, T in zip(widths, Ts)]
    assert max(products) - min(products) < 1e-3 * max(products)


def test_a_longer_ramsey_T_beats_a_single_rabi_pulse_of_the_same_length():
    """The Ramsey fringe is narrower than the Rabi resonance of equal duration.

    A single Rabi pi-pulse of duration t_pi has an on-resonance ceiling
    that falls off over a detuning scale of order Omega = pi/t_pi. A
    Ramsey sequence with free evolution T = t_pi has a fringe FWHM of
    pi/T, which is narrower than the Rabi half-width for the same total
    time spent.
    """
    omega = 2.0 * math.pi * 10.0
    t_pi = A.pi_pulse_duration(omega)
    ramsey_fwhm = A.ramsey_central_fringe_width(t_pi)
    # Rabi half-power detuning: peak probability drops to 1/2 at delta = Omega
    rabi_fwhm = 2.0 * omega
    assert ramsey_fwhm < rabi_fwhm


def test_ramsey_rejects_a_zero_or_negative_free_evolution_time():
    with pytest.raises(A.AtomicArchError):
        A.ramsey_fringe(0.0, 0.0)
    with pytest.raises(A.AtomicArchError):
        A.ramsey_fringe_period(-1.0)
    with pytest.raises(A.AtomicArchError):
        A.ramsey_central_fringe_width(0.0)


# --- cavity pulling -----------------------------------------------------

def test_cavity_pulling_is_zero_when_the_cavity_is_tuned_to_the_line():
    f0 = A.H_HYPERFINE_HZ
    for q_ratio in (0.0, 1e-6, 1e-3, 1.0):
        out = A.cavity_pulling(f0, f0, Q_cavity=q_ratio * 1e9, Q_line=1e9)
        assert out == pytest.approx(f0, rel=1e-15)
        assert out - f0 == pytest.approx(0.0, abs=1e-9)


def test_cavity_pulling_grows_with_the_Q_ratio():
    f0 = 1.0e9
    f_cav = f0 + 1.0e6                       # cavity detuned high
    Q_line = 1.0e6
    pulls = [A.cavity_pulling(f0, f_cav, Qc, Q_line) - f0
             for Qc in (1e2, 1e3, 1e4, 1e5)]
    assert all(p > 0 for p in pulls)
    assert all(a < b for a, b in zip(pulls, pulls[1:]))
    # exactly linear in the ratio
    assert pulls[1] == pytest.approx(10.0 * pulls[0], rel=1e-9)


def test_cavity_pulling_drags_toward_the_cavity_in_both_directions():
    f0, Q_line, Q_c = 1.0e9, 1.0e9, 1.0e5
    assert A.cavity_pulling(f0, f0 + 1e3, Q_c, Q_line) > f0
    assert A.cavity_pulling(f0, f0 - 1e3, Q_c, Q_line) < f0


def test_cavity_pulling_refuses_a_nonpositive_line_Q():
    with pytest.raises(A.AtomicArchError):
        A.cavity_pulling(1.0e9, 1.0e9, Q_cavity=1e5, Q_line=0.0)
    with pytest.raises(A.AtomicArchError):
        A.cavity_pulling(1.0e9, 1.0e9, Q_cavity=-1.0, Q_line=1e9)


# --- the hydrogen maser error budget ------------------------------------

def test_the_error_budget_lists_every_named_term():
    b = A.MaserErrorBudget()
    assert set(b.names) == set(A.MASER_ERROR_TERM_NAMES)
    for name in ("wall_shift", "magnetic_inhomogeneity", "cavity_pulling",
                 "doppler_first_order", "doppler_second_order",
                 "transient_response"):
        assert name in b.names
    assert b.all_declared()
    assert b.undeclared() == ()
    assert b.measured_here == "nothing"


def test_undeclared_terms_are_flagged():
    terms = tuple(
        A.MaserErrorTerm(t.name, t.description,
                         declared=(t.name != "wall_shift"))
        for t in A.default_maser_error_terms())
    b = A.MaserErrorBudget(terms=terms)
    assert b.undeclared() == ("wall_shift",)
    assert not b.all_declared()
    assert b.flags()["wall_shift"]["declared"] is False
    assert b.flags()["cavity_pulling"]["declared"] is True


def test_a_budget_that_omits_a_named_term_is_refused():
    short = tuple(t for t in A.default_maser_error_terms()
                  if t.name != "cavity_pulling")
    with pytest.raises(A.AtomicArchError):
        A.MaserErrorBudget(terms=short)


def test_no_error_term_is_measured_here():
    b = A.MaserErrorBudget()
    for t in b.terms:
        assert t.status == "NOT_MEASURED_HERE"
        assert t.evidence_class == "CONVENTIONAL_LITERATURE"


def test_the_maser_model_names_its_distinguishing_parts():
    m = A.HYDROGEN_MASER
    assert "six-pole" in m.state_focuser
    assert "Teflon" in m.storage_bulb and "quartz" in m.storage_bulb
    assert m.storage_bulb_is_a_quartz_oscillator is False
    assert "cavity" in m.cavity
    assert "LONG" in m.interaction_time_regime
    assert m.evidence_class == "CONVENTIONAL_LITERATURE"
    assert m.measured_here == "nothing"
    assert m.status == "NOT_MEASURED_HERE"


# --- the load-bearing refusals ------------------------------------------

def test_a_storage_bulb_is_refused_as_an_oscillator():
    with pytest.raises(A.AtomicArchError) as exc:
        A.refuse_bulb_as_oscillator()
    msg = str(exc.value)
    assert "STORAGE BULB" in msg and "OSCILLATOR" in msg
    assert "piezoelectric" in msg


def test_two_coils_are_refused_as_a_state_selection_magnet():
    with pytest.raises(A.AtomicArchError) as exc:
        A.refuse_coils_as_state_selector(2)
    msg = str(exc.value)
    assert "MULTIPOLE FIELD GRADIENT" in msg
    assert "UNIFORMITY" in msg


def test_a_measured_claim_is_refused():
    with pytest.raises(A.AtomicArchError) as exc:
        A.refuse_measured_claim("the maser wall shift")
    assert "not measured here" in str(exc.value)
    assert "PHYSICAL_VALIDATION_NOT_CLAIMED" in str(exc.value)


# --- the neutral crystal analogue ---------------------------------------

def test_the_crystal_analogue_states_its_failure_boundaries():
    c = A.crystal_analogue()
    assert len(c["failure_boundaries"]) >= 4
    joined = " ".join(c["failure_boundaries"])
    assert "state selection" in joined
    assert "coherence time" in joined
    assert "clock performance" in joined


def test_the_crystal_analogue_claims_no_clock_performance():
    c = A.crystal_analogue()
    assert c["claims_atomic_state_selection"] is False
    assert c["claims_coherence_time"] is False
    assert c["claims_clock_performance"] is False
    assert c["evidence_class"] == "ANALOGY_ONLY"
    assert c["measured_here"] == "nothing"
    assert c["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"


def test_the_two_channel_combining_rules_are_the_stated_arithmetic():
    orth = A.crystal_analogue("orthogonal")
    assert orth["combined_amplitude_unit_inputs"] == pytest.approx(
        math.sqrt(2.0), rel=1e-12)
    in_phase = A.crystal_analogue("phase_coherent", 0.0)
    assert in_phase["combined_amplitude_unit_inputs"] == pytest.approx(
        2.0, rel=1e-12)
    anti = A.crystal_analogue("phase_coherent", math.pi)
    assert anti["combined_amplitude_unit_inputs"] == pytest.approx(
        0.0, abs=1e-9)


def test_an_unspecified_channel_relation_is_refused():
    with pytest.raises(A.AtomicArchError):
        A.crystal_analogue("whatever")


# --- the report is honest -----------------------------------------------

def test_report_is_model_only_and_measures_nothing():
    r = A.atomicarch_report()
    assert r["measured_here"] == "nothing"
    assert r["verdict"] == "ATOMIC_ARCHITECTURE_MODEL_ONLY"
    assert r["verdict"] == A.DEFAULT_VERDICT
    assert r["evidence_class"] == "CONVENTIONAL_LITERATURE"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"


def test_report_carries_the_chain_and_its_edges():
    r = A.atomicarch_report()
    assert r["chain"][0] == "source"
    assert r["chain"][-1] == "flywheel"
    assert len(r["chain"]) == 10
    assert len(r["edges"]) == 9
    assert r["chain_connected"] is True


def test_report_carries_the_named_error_terms_and_their_flags():
    r = A.atomicarch_report()
    b = r["maser_error_budget"]
    assert set(b["named_terms"]) == set(A.MASER_ERROR_TERM_NAMES)
    assert set(b["listed"]) == set(A.MASER_ERROR_TERM_NAMES)
    assert b["undeclared"] == []
    assert b["all_declared"] is True


def test_report_says_what_it_does_not_say():
    r = A.atomicarch_report()
    w = r["what_this_does_not_say"]
    assert "quartz storage bulb is a quartz oscillator" in w
    assert "two coils" in w
    assert "PHYSICAL_VALIDATION_NOT_CLAIMED" in w
    joined = " ".join(r["distinctions_enforced"])
    assert "refuse_bulb_as_oscillator" in joined
    assert "refuse_coils_as_state_selector" in joined
    assert "refuse_measured_claim" in joined
    assert "refuse_invalid_chain" in joined
