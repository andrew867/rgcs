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
