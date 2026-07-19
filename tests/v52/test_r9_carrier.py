"""P06/P10 — hidden neutral carrier feasibility.

The load-bearing test is
``test_model_reproduces_a_working_experiment``. A feasibility model
that refuses everything proves nothing; it has to say yes where the
answer is known to be yes.
"""

from __future__ import annotations

import pytest

from r9 import carrier as C


# --- model validation against a known-working experiment --------------

def test_model_reproduces_a_working_experiment():
    """Super-Kamiokande detects solar neutrinos and has since 1996.

    The first version of this module reported it REFUSED_BY_ARITHMETIC
    because it applied sea-level muon flux to a detector under 2700 mwe
    of rock. A model that refutes a working experiment is wrong, and
    this test exists so it cannot silently happen again.
    """
    r = C.assess("SUPER_K_SCALE", has_readout_channel=True)
    assert r.verdict == "CONVENTIONALLY_MEASURABLE"
    assert r.signal_to_background > 1.0


def test_overburden_suppresses_background():
    assert C.muon_suppression(0) == 1.0
    assert C.muon_suppression(2700) == pytest.approx(1e-5)
    assert C.muon_suppression(0) > C.muon_suppression(1000) \
        > C.muon_suppression(6000)


def test_suppression_is_monotonic_and_interpolates():
    prev = 1.0
    for d in (0, 50, 100, 500, 1000, 2000, 2700, 4000, 6000):
        s = C.muon_suppression(d)
        assert s <= prev + 1e-15
        prev = s


def test_negative_overburden_refused():
    with pytest.raises(ValueError):
        C.muon_suppression(-1.0)


# --- the bench verdict -------------------------------------------------

def test_bench_quartz_has_no_readout_channel():
    """The binding obstacle, and it is prior to the rate question."""
    r = C.assess("BENCH_QUARTZ_100G")
    assert r.verdict == "NO_READOUT_CHANNEL"
    assert "never transduced is not a measurement" in r.note


def test_bench_quartz_refused_even_granting_readout():
    r = C.assess("BENCH_QUARTZ_100G", has_readout_channel=True)
    assert r.verdict == "REFUSED_BY_ARITHMETIC"
    assert r.signal_to_background < 1e-6


def test_interactions_do_occur_the_rate_is_not_zero():
    """The honest framing: neutrinos interact, roughly annually. The
    problem is knowing which event it was."""
    r = C.assess("BENCH_QUARTZ_100G", has_readout_channel=True)
    assert r.interactions_per_year > 0.1
    assert r.interactions_per_year < 100


def test_more_mass_does_not_rescue_the_bench_case():
    """100x the mass does not close an 8-order gap."""
    small = C.assess("BENCH_QUARTZ_100G", has_readout_channel=True)
    big = C.assess("GENEROUS_QUARTZ_10KG", has_readout_channel=True)
    assert big.interactions_per_year > small.interactions_per_year
    assert big.verdict == "REFUSED_BY_ARITHMETIC"


def test_scale_gap_is_eight_orders():
    g = C.scale_gap()
    assert g["mass_ratio"] > 1e7
    assert "not a refinement problem" in g["note"]


# --- rate arithmetic ---------------------------------------------------

def test_nucleon_count_is_physical():
    t = C.TARGETS["BENCH_QUARTZ_100G"]
    assert 1e25 < t.n_nucleons < 1e26


def test_rate_scales_linearly_with_flux_and_cross_section():
    t = C.TARGETS["BENCH_QUARTZ_100G"]
    a = C.interaction_rate_per_year(t, 1e10, 1e-44)
    b = C.interaction_rate_per_year(t, 2e10, 1e-44)
    c = C.interaction_rate_per_year(t, 1e10, 2e-44)
    assert b == pytest.approx(2 * a)
    assert c == pytest.approx(2 * a)


def test_invalid_rate_inputs_refused():
    t = C.TARGETS["BENCH_QUARTZ_100G"]
    with pytest.raises(ValueError):
        C.interaction_rate_per_year(t, -1.0, 1e-44)
    with pytest.raises(ValueError):
        C.interaction_rate_per_year(t, 1e10, 0.0)


def test_target_rejects_nonpositive_mass():
    with pytest.raises(ValueError):
        C.Target("bad", 0.0, 60.0, 60, 1.0)


def test_unknown_keys_refused():
    with pytest.raises(ValueError):
        C.assess("WARP_CORE")
    with pytest.raises(ValueError):
        C.assess("BENCH_QUARTZ_100G", hypothesis="PHRYLL")
    with pytest.raises(ValueError):
        C.assess("BENCH_QUARTZ_100G", cross_section_key="MAGIC")


# --- hypothesis ladder and discriminators -----------------------------

def test_mundane_hypotheses_come_first():
    """Exclusion order matters: an exotic carrier is not a candidate
    until the ordinary explanations are measured and bounded."""
    h = C.CARRIER_HYPOTHESES
    assert h[0] == "ORDINARY_APPARATUS_MODE"
    assert h.index("ORDINARY_APPARATUS_MODE") < h.index("ACTIVE_ANTINEUTRINO")
    assert h.index("INSTRUMENTATION_ARTEFACT") < h.index("STERILE_NEUTRINO")
    assert "NO_NEW_CARRIER" in h


def test_every_hypothesis_has_a_discriminator():
    for hyp in C.CARRIER_HYPOTHESES:
        assert C.DISCRIMINATORS[hyp], f"{hyp} has no discriminator"


def test_the_central_question_is_answered_honestly():
    d = C.distinguishing_programme()
    assert "none of them" in d["answer"]
    assert "cannot register a single interaction" in d["answer"]
    assert "ordinary hypotheses are fully testable" in \
        d["what_is_reachable"]


def test_ordering_rule_is_stated():
    d = C.distinguishing_programme()
    assert "mundane first" in d["ordering_rule"]


def test_detection_claim_is_refused():
    with pytest.raises(C.CarrierRefused) as e:
        C.refuse_carrier_detection_claim()
    assert "owns no particle detector" in str(e.value)
    assert "not the same as interactions being measured" in str(e.value)


def test_cross_sections_carry_provenance():
    for key, spec in C.CROSS_SECTIONS.items():
        assert spec["sigma_cm2"] > 0
        assert spec["process"]
        assert spec["source"]


def test_every_verdict_is_declared():
    for tk in C.TARGETS:
        for readout in (True, False):
            r = C.assess(tk, has_readout_channel=readout)
            assert r.verdict in C.FEASIBILITY_VERDICTS
