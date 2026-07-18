"""v4.7 PMWR core tests: doctrine, phase authority, signal stages,
worldline/causality, closure ambiguity, recovery + identifiability
(acceptance rows R04-R19).
"""
from __future__ import annotations

import math

import pytest


# --- doctrine (R02/R26) ---------------------------------------------------

def test_evidence_classes_match_core_08():
    import pmwr
    assert len(pmwr.EVIDENCE_CLASSES) == 17
    for c in ("METAPHOR", "GEOMETRY_IDENTITY", "ANTHROPOGENIC_STRUCTURE",
              "CIRCULAR_DERIVATION", "UNEXPLAINED_INSTRUMENT_RESIDUAL",
              "PROSPECTIVE_PREDICTION"):
        assert c in pmwr.EVIDENCE_CLASSES


def test_detected_phryll_does_not_exist_anywhere():
    """R26: the prohibited states appear nowhere in the package source
    except the prohibition list itself."""
    import pathlib

    import pmwr
    pkg = pathlib.Path(pmwr.__file__).parent
    for p in pkg.glob("*.py"):
        text = p.read_text(encoding="utf-8")
        for bad in ("DETECTED_PHRYLL", "PHRYLL_DETECTED"):
            hits = text.count(bad)
            if p.name == "__init__.py":
                # allowed only inside PROHIBITED_STATES and its docstring
                assert hits <= 3, f"{p.name} normalises {bad}"
            else:
                assert hits == 0, f"{p.name} contains {bad}"


def test_all_ten_firewalls_present():
    import pmwr
    assert len(pmwr.FIREWALLS) == 10
    for key in ("PERFECT_ABSOLUTE_PHASE", "CLOSURE_REMOVES_AMBIGUITY",
                "REORDER_IS_REVERSAL", "SENSOR_CHANGE_IS_PHRYLL",
                "DEVICE_MIRACLES"):
        assert key in pmwr.FIREWALLS


# --- phase authority (R04/R06) ---------------------------------------------

def test_cycle_count_requires_phase_locked():
    import pmwr
    from pmwr.phase_authority import PhaseAuthority
    with pytest.raises(pmwr.ClaimBoundaryError):
        PhaseAuthority("A", 4096.0, "2026-07-18T00:00:00Z", "UTC",
                       sync_state="FREE_RINGDOWN", cycle_count=5)
    ok = PhaseAuthority("A", 4096.0, "2026-07-18T00:00:00Z", "UTC",
                        sync_state="PHASE_LOCKED", cycle_count=5)
    assert ok.cycle_count == 5


def test_losing_lock_surrenders_cycle_count():
    from pmwr.phase_authority import PhaseAuthority
    a = PhaseAuthority("A", 4096.0, "e", "UTC",
                       sync_state="PHASE_LOCKED", cycle_count=99)
    h = a.transition("HOLDOVER")
    assert h.cycle_count is None


def test_illegal_transition_refused_and_no_force_flag():
    import inspect

    from pmwr import phase_authority
    from pmwr.phase_authority import PhaseAuthority, SyncTransitionError
    a = PhaseAuthority("A", 4096.0, "e", "UTC")
    with pytest.raises(SyncTransitionError):
        a.transition("PHASE_LOCKED")     # must go through FREQ_LOCKED
    src = inspect.getsource(phase_authority)
    assert "force=" not in src and "override=" not in src


def test_two_authorities_without_sync_method_are_incomparable():
    from pmwr.phase_authority import PhaseAuthority, epoch_comparison
    a = PhaseAuthority("TX", 4096.0, "e1", "LOCAL_XO")
    b = PhaseAuthority("RX", 4096.0, "e2", "LOCAL_XO")
    rep = epoch_comparison(a, b, None)
    assert rep["comparable"] is False
    assert "regardless of Q" in rep["reason"]


# --- finite-Q memory (R07) ---------------------------------------------------

def test_ringdown_matches_analytic_form():
    from pmwr.phase_authority import RingdownModel
    m = RingdownModel(32768.0, 50000.0)
    t = m.tau_s
    assert abs(m.amplitude(t) - math.exp(-1)) < 1e-12
    assert abs(m.cycles_to_1e() - 50000.0 / math.pi) < 1e-9


def test_infinite_q_is_refused():
    import pmwr
    from pmwr.phase_authority import RingdownModel
    with pytest.raises(pmwr.ClaimBoundaryError):
        RingdownModel(32768.0, math.inf)


def test_perfect_memory_claim_is_refused():
    import pmwr
    from pmwr.phase_authority import (RingdownModel,
                                      assert_not_perfect_memory,
                                      phase_memory_horizon)
    m = RingdownModel(32768.0, 50000.0)
    h = phase_memory_horizon(m, 1e-8)
    assert h["after_horizon_state"] == "CYCLE_COUNT_UNKNOWN"
    with pytest.raises(pmwr.ClaimBoundaryError):
        assert_not_perfect_memory(1e9, m, 1e-8)
    with pytest.raises(pmwr.ClaimBoundaryError):
        phase_memory_horizon(m, 0.0)     # zero-error model = disguise


# --- signal stages (R05/R17) --------------------------------------------------

def test_stages_do_not_convert_implicitly():
    import pmwr
    from pmwr.signal_state import SignalState, observe, wrap
    ideal = SignalState("IDEAL", "ELECTRICAL", 4096.0, 1.0, wrap(0.0))
    with pytest.raises(pmwr.ClaimBoundaryError):
        observe(ideal, 0.01, 0.001)      # IDEAL is not PROPAGATED


def test_propagation_loses_cycle_count():
    from pmwr.signal_state import SignalState, command, propagate, realize, wrap
    s = command(SignalState("IDEAL", "ELECTRICAL", 4096.0, 1.0,
                            wrap(0.0, cycles_known=True)), 0.01)
    r = realize(s, 1.0 + 1e-9)
    p = propagate(r, 1.234e-3, 0.5)
    assert p.phase.cycle_known is False


def test_unwrap_without_cycle_count_is_refused():
    import pmwr
    from pmwr.signal_state import wrap
    w = wrap(7.5)                        # cycles unknown
    with pytest.raises(pmwr.ClaimBoundaryError):
        w.unwrapped()
    known = wrap(7.5, cycles_known=True)
    assert abs(known.unwrapped() - 7.5) < 1e-12


def test_reconstructed_requires_refusal_reason_when_unidentifiable():
    import pmwr
    from pmwr.signal_state import Reconstructed
    with pytest.raises(pmwr.ClaimBoundaryError):
        Reconstructed({}, {}, (), identifiable=False)


# --- worldline / causality (R08/R14/R15) ---------------------------------------

def test_negative_delay_is_refused():
    import pmwr
    from pmwr.worldline import PathState
    with pytest.raises(pmwr.ClaimBoundaryError):
        PathState("bad", -1e-6)


def test_arrival_reordering_detected_but_never_called_reversal():
    from pmwr.worldline import Emission, PathState, causal_order_audit
    aud = causal_order_audit(
        [Emission("A", 0.0), Emission("B", 0.001)],
        {"A": [PathState("long", 0.010)],
         "B": [PathState("short", 0.0001)]})
    assert aud["arrival_reordering_present"] is True
    assert aud["first_arrival_order"] == ["B", "A"]
    assert aud["emission_order"] == ["A", "B"]
    assert "UNCHANGED" in aud["causal_order"]
    assert "reversal" not in aud["explanation"].lower()


def test_reversal_language_lint():
    import pmwr
    from pmwr.worldline import assert_no_reversal_claim
    assert_no_reversal_claim("later emissions arrived first over "
                             "shorter paths")
    with pytest.raises(pmwr.ClaimBoundaryError):
        assert_no_reversal_claim("this demonstrates causal reversal")


def test_two_geodesic_case_signs_match_known_physics():
    """LEO must be net-negative (velocity wins at 400 km); GPS altitude
    must be net-positive — same fixture family as the validated v4.6
    model."""
    from pmwr.worldline import Worldline, two_geodesic_case
    t = two_geodesic_case()
    assert t["differential_rate"] < 0            # LEO clock runs slow
    gps = Worldline("GPS", 26_560_000.0,
                    math.sqrt(3.986004418e14 / 26_560_000.0))
    off = gps.proper_rate_offset(6_378_137.0)
    assert abs(off * 86400e6 - 38.5) < 0.5       # +38.5 us/day
    assert "metrology" in t["not_an_interpretation"]


# --- closure ambiguity + probes (R09/R10/R11/R12) --------------------------------

def test_closure_window_is_the_alias_spacing():
    from pmwr.recovery import closure_delay_ambiguity
    c = closure_delay_ambiguity(["4096", "20480", "40960"], 1.0)
    assert abs(c["closure_window_s"] - 1.0 / 4096.0) < 1e-15
    assert c["aliases_within_max_delay"] == 4097
    assert "alias" in c["statement"]


def test_dual_lattice_extends_unambiguous_range():
    from pmwr.recovery import dual_lattice_probe
    d = dual_lattice_probe(["4096", "20480"], ["4375"])
    assert d["improvement_over_a"] > 1000
    assert d["combined_unambiguous_range_s"] > d["window_a_s"]


def test_synthetic_wavelength_leverage():
    import pmwr
    from pmwr.recovery import synthetic_wavelength
    s = synthetic_wavelength(20480.0, 20480.0 + 16.0)
    assert abs(s["coarse_unambiguous_delay_s"] - 1 / 16.0) < 1e-12
    with pytest.raises(pmwr.ClaimBoundaryError):
        synthetic_wavelength(4096.0, 4096.0)


# --- recovery + identifiability (R13/R16/R18/R19) ---------------------------------

def _paths():
    from pmwr.worldline import PathState
    return [PathState("p1", 1e-4, complex_gain=0.8 + 0.1j),
            PathState("p2", 2.5e-4, complex_gain=0.3 - 0.2j)]


def test_recovery_of_identifiable_synthetic_case():
    from pmwr.recovery import reconstruct, simulate_observations
    freqs = [4096.0, 4133.0, 4211.0, 4297.0, 4409.0]
    obs = simulate_observations(freqs, _paths(), 0.001, seed=41)
    v = reconstruct(freqs, obs, [1e-4, 2.5e-4], 0.001)
    assert v["verdict"] == "RECOVERED"
    assert abs(v["path_gains"][0] - (0.8 + 0.1j)) < 0.05
    assert "alias_caveat" in v
    assert v["evidence_class"] == "NUMERICAL_SIMULATION"


def test_underdetermined_case_is_refused_not_guessed():
    from pmwr.recovery import reconstruct, simulate_observations
    obs = simulate_observations([4096.0], _paths(), 0.001)
    v = reconstruct([4096.0], obs, [1e-4, 2.5e-4], 0.001)
    assert v["verdict"] == "REFUSED"
    assert "path_gains" not in v
    assert any("rank" in r for r in v["refusal_reasons"])


def test_ill_conditioned_case_is_refused():
    from pmwr.recovery import reconstruct, simulate_observations
    freqs = [4096.0, 4096.000001]         # nearly identical rows
    obs = simulate_observations(freqs, _paths(), 0.001)
    v = reconstruct(freqs, obs, [1e-4, 2.5e-4], 0.001)
    assert v["verdict"] == "REFUSED"
    assert any("condition" in r for r in v["refusal_reasons"])


def test_simulator_is_deterministic_by_seed():
    from pmwr.recovery import simulate_observations
    a = simulate_observations([4096.0, 5000.0], _paths(), 0.01, seed=7)
    b = simulate_observations([4096.0, 5000.0], _paths(), 0.01, seed=7)
    assert all(x.value == y.value for x, y in zip(a, b))


def test_unwrapping_returns_a_list_not_a_value():
    from pmwr.recovery import integer_cycle_candidates
    cands = integer_cycle_candidates(1.0, 4096.0, (0.0, 0.01))
    assert len(cands) > 1                 # honesty: many delays fit


def test_spoof_condition_detected():
    """Two path sets aliased by the closure window are
    indistinguishable — detected, not papered over."""
    from pmwr.recovery import simulate_observations, spoof_check
    from pmwr.worldline import PathState
    w = 1.0 / 4096.0
    freqs = [4096.0, 20480.0, 40960.0]
    a = simulate_observations(freqs, [PathState("t", 1e-4)], 0.0)
    b = simulate_observations(freqs, [PathState("t2", 1e-4 + w)], 0.0)
    rep = spoof_check(a, b)
    assert rep["indistinguishable"] is True
