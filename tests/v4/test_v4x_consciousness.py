"""Consciousness-lane tests (gates G31-G40)."""

import pathlib

import numpy as np
import pytest

import consciousness_lane as cl
from consciousness_lane import reduced_models as rm
from consciousness_lane import theory_registry as tr


def test_registry_complete_and_layered():
    """G31: C001-C052 complete; G38: layer separation."""
    reg = tr.build_theory_registry()
    assert set(reg) == {f"C{i:03d}" for i in range(1, 53)}
    for rec in reg.values():
        assert rec["layer"] in \
            __import__("rscs2_core.research_records",
                       fromlist=["x"]).CONSCIOUSNESS_LAYERS
        assert rec["status"] in cl.ALLOWED_STATUSES
        assert rec["failure_conditions"]
        assert rec["quarantine"]
    # private layers are not public
    for rid in ("C037", "C038", "C039"):
        assert reg[rid]["public"] is False


def test_no_quartz_import_in_lane():
    """Quarantine contract: the lane must not import quartz solvers."""
    root = pathlib.Path(cl.__file__).parent
    for f in root.glob("*.py"):
        text = f.read_text(encoding="utf-8")
        for bad in cl.FORBIDDEN_IMPORTS:
            assert f"import {bad}" not in text
            assert f"from {bad}" not in text


def test_thz_and_hydrogenuine_do_not_claim_consciousness():
    """G34 + G39."""
    reg = tr.build_theory_registry()
    for rid in ("C020", "C022"):
        assert "ANALOGY ONLY" in reg[rid]["failure_conditions"][0]
        assert reg[rid]["status"] == "ENGINEERING_PROTOTYPE"
    for rid in ("C049", "C050", "C051", "C052"):
        assert reg[rid]["status"] == "ENGINEERING_PROTOTYPE"
        assert reg[rid]["evidence_tags"] == ["ENG"]


def test_quantum_cognition_boundary():
    """G37: quantum-probability models are not a quantum brain."""
    reg = tr.build_theory_registry()
    assert "BOUNDARY" in reg["C032"]["failure_conditions"][0]
    assert reg["C033"]["status"] == "SOURCE_HYPOTHESIS"


def test_kuramoto_matches_analytic_critical_coupling():
    """C025: sub-critical stays incoherent, super-critical locks."""
    gamma = 0.2
    kc = rm.kuramoto_critical_k(gamma)
    rng = np.random.default_rng(0)
    omega = rng.standard_cauchy(200) * gamma
    lo = rm.kuramoto(omega, k=0.3 * kc, t_end=40)
    hi = rm.kuramoto(omega, k=6.0 * kc, t_end=40)
    assert lo["r_final"] < hi["r_final"]
    assert hi["r_final"] > 0.7


def test_coherence_is_not_truth_control():
    """C048/G35."""
    out = rm.coherence_is_not_truth()
    assert out["both_coherent"] and out["states_contradictory"]


def test_state_change_decay_and_dream_wake():
    t = np.linspace(0, 5, 20000)
    out = rm.state_change_response(t, 2.0, 0.1,
                                   drive=np.exp(-t / 0.01))
    assert out["tau_s"] == pytest.approx(1 / (0.1 * 2 * np.pi * 2),
                                         rel=1e-6)
    assert np.abs(out["x"][-1]) < np.abs(out["x"]).max()
    wake = rm.dream_wake_constraint(0.0, 5.0)
    dream = rm.dream_wake_constraint(0.0, 0.1)
    assert wake["regime"] == "wake" and dream["regime"] == "dream"
    assert wake["k_ext_quarantined"]


def test_microtubule_threshold_honest():
    """G33: reference decoherence time fails the causal threshold."""
    out = rm.microtubule_threshold(1e-13, 1.0, 1.0)
    assert not out["clears_threshold"]
    assert out["status"] == "SOURCE_HYPOTHESIS"
    hi = rm.microtubule_threshold(1e-3, 1e4, 1.0)
    assert hi["clears_threshold"]
    assert hi["status"] == "SOURCE_HYPOTHESIS"  # never upgrades


def test_synchrony_surrogate_control():
    rng = np.random.default_rng(5)
    t = np.linspace(0, 20, 2000)
    a = np.sin(2 * np.pi * 1.0 * t)
    b = np.sin(2 * np.pi * 1.0 * t + 0.4)
    indep = rng.standard_normal(2000)
    assert rm.synchrony_with_surrogates(a, b)["plv"] > \
        rm.synchrony_with_surrogates(a, indep)["plv"]


# --- v4.2.1 completeness audit: depth must back the status ------------

def test_reduced_order_claims_have_models():
    """G42F: an entry may claim REDUCED_ORDER_VALIDATED only if a real
    model function exists and is callable. The v4.2.0 registry marked
    18 entries validated while only 6 had models."""
    reg = tr.build_theory_registry()
    for rid, rec in reg.items():
        if rec["status"] == "REDUCED_ORDER_VALIDATED":
            sym = rec["model_symbol"]
            assert sym, f"{rid} claims validated with no model_symbol"
            assert callable(getattr(rm, sym, None)), \
                f"{rid} names model {sym} which does not exist"


def test_every_entry_has_owner_and_doc():
    reg = tr.build_theory_registry()
    for rid, rec in reg.items():
        assert rec["owner_agent"] in tr.LANE_DOCS
        assert rec["documentation_path"].endswith(".md")
        assert rec["failure_conditions"][0]


def test_downgraded_entries_say_so():
    """Statuses that the audit lowered must record why, so the change
    is auditable rather than silent."""
    reg = tr.build_theory_registry()
    for rid in ("C006", "C034", "C036", "C040", "C046", "C047"):
        assert reg[rid]["status"] == "SOURCE_HYPOTHESIS"
        assert "DOWNGRADED" in reg[rid]["failure_conditions"][0]


def test_ring_attractor_forms_and_persists_bump():
    """C010: a bump forms under input, persists after the input is
    removed, tracks the input direction, and stays bounded."""
    out = rm.ring_attractor(input_dir=np.pi / 2)
    assert out["bump_formed"] and out["persisted_without_input"]
    assert abs(out["bump_direction_rad"] - np.pi / 2) < 0.2
    assert out["peak_rate"] <= 1.5          # saturation bounds it
    for d in (0.0, np.pi, 3 * np.pi / 2):
        got = rm.ring_attractor(input_dir=d)["bump_direction_rad"]
        assert abs((got - d + np.pi) % (2 * np.pi) - np.pi) < 0.2


def test_ring_attractor_needs_recurrent_excitation():
    """Null: without recurrent excitation nothing persists, so the
    bump is a property of the network, not of the input."""
    flat = rm.ring_attractor(k_exc=0.0, k_inh=1.0,
                             input_dir=np.pi / 2)
    assert not flat["bump_formed"]
    assert flat["peak_rate"] < 0.1


def test_ring_attractor_survives_noise():
    out = rm.ring_attractor(input_dir=np.pi / 2, noise=0.02)
    assert out["bump_formed"]
    assert abs(out["bump_direction_rad"] - np.pi / 2) < 0.3


def test_pac_detects_coupling_and_rejects_noise():
    """C013/C023: PAC must exceed surrogates for a coupled signal and
    fail to for noise."""
    fs = 500.0
    t = np.arange(0, 20, 1 / fs)
    phase = 2 * np.pi * 6 * t
    coupled = np.sin(phase) + (1 + np.cos(phase)) * \
        0.5 * np.sin(2 * np.pi * 80 * t)
    out = rm.phase_amplitude_coupling(coupled, fs, (4, 8), (60, 100),
                                      n_surrogate=60)
    assert out["exceeds_surrogates"]
    rng = np.random.default_rng(1)
    noise = rng.standard_normal(len(t))
    n_out = rm.phase_amplitude_coupling(noise, fs, (4, 8), (60, 100),
                                        n_surrogate=60)
    assert n_out["modulation_index"] < out["modulation_index"]


def test_quantum_cognition_boundary_and_qq_equality():
    """C032/G37: order effects need a non-commuting model; the QQ
    equality is parameter-free and can fail."""
    sym = rm.order_effect_model(0.5, 0.5)
    assert sym["classical_joint_model_adequate"]
    asym = rm.order_effect_model(0.62, 0.41)
    assert asym["requires_noncommuting_model"]
    assert "NOT evidence of a quantum brain" in asym["boundary"]
    assert rm.qq_equality(0.4, 0.3, 0.2, 0.3)["satisfied"]
    assert not rm.qq_equality(0.9, 0.1, 0.9, 0.1)["satisfied"]
    assert rm.classical_comparator(0.5, 0.4)["p_joint"] == 0.2


def test_subjective_time_dilates_with_novelty():
    """C003: more novelty/arousal -> longer perceived duration."""
    flat = np.zeros(100)
    busy = np.ones(100)
    calm = rm.subjective_time(flat, flat, dt_s=1.0)
    rich = rm.subjective_time(busy, busy, dt_s=1.0)
    assert rich["perceived_duration_s"] > calm["perceived_duration_s"]
    assert rich["dilated"] and not calm["dilated"]
    with pytest.raises(ValueError):
        rm.subjective_time(np.zeros(3), np.zeros(4))
