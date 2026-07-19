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

def test_model_does_not_refuse_a_working_experiment():
    """Super-Kamiokande detects solar neutrinos and has since 1996, so
    the model must not refuse it (R9-D-001: it did, by applying
    sea-level muon flux to a detector under 2700 mwe of rock).

    R9-D-016: this used to assert raw signal-to-background > 1, and
    passed at 1.17 -- a margin produced by two large errors partly
    cancelling. Correcting the electron count broke it, which was
    useful, because the assertion was wrong in principle. Super-K's
    true raw S/B is of order 1e-4; it detects neutrinos through event
    reconstruction and directionality, not by out-numbering muons.
    The model does not simulate that chain, so it must not pretend to
    certify it.
    """
    r = C.assess("SUPER_K_SCALE", has_readout_channel=True)
    assert r.verdict != "REFUSED_BY_ARITHMETIC"
    assert r.verdict in C.FEASIBILITY_VERDICTS


def test_raw_signal_to_background_is_disclaimed_as_a_criterion():
    n = C.RAW_SB_IS_NOT_THE_DISCRIMINATOR
    assert "does not determine whether a detector" in n
    assert "cannot certify" in n


def test_bench_and_super_k_are_separated_by_many_orders():
    """What the model CAN say: the bench is refused, Super-K is not,
    and the gap between them is enormous."""
    bench = C.assess("BENCH_QUARTZ_100G", has_readout_channel=True)
    sk = C.assess("SUPER_K_SCALE", has_readout_channel=True)
    assert bench.verdict == "REFUSED_BY_ARITHMETIC"
    assert sk.signal_to_background > 1e6 * bench.signal_to_background


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


# --- cross-section denominators (R9-D-015) ----------------------------

def test_each_cross_section_declares_its_denominator():
    for key, spec in C.CROSS_SECTIONS.items():
        assert spec["per"] in C.TARGET_COUNT_KINDS, key


def test_quartz_has_no_free_protons():
    """SiO2 contains no hydrogen, so inverse beta decay cannot occur
    in it at all -- the module used to report 12.34 events/yr."""
    q = C.TARGETS["BENCH_QUARTZ_100G"]
    assert q.n_free_protons == 0
    r = C.assess("BENCH_QUARTZ_100G",
                 cross_section_key="INVERSE_BETA_DECAY_MEV",
                 has_readout_channel=True)
    assert r.verdict == "NO_TARGET_CENTRES"
    assert r.interactions_per_year == 0.0
    assert "chemistry, not sensitivity" in r.note


def test_water_does_have_free_protons():
    """Control: the same code path must not zero out a target that
    genuinely has hydrogen."""
    w = C.TARGETS["SUPER_K_SCALE"]
    assert w.free_protons_per_molecule == 2
    assert w.n_free_protons > 0


def test_electron_count_is_used_for_elastic_scattering():
    """Quartz: 30 electrons per 60 nucleons, so using nucleons
    overcounted the elastic rate by exactly 2x."""
    q = C.TARGETS["BENCH_QUARTZ_100G"]
    assert q.n_electrons == pytest.approx(q.n_nucleons / 2)
    per_e = C.interaction_rate_per_year(q, 6.5e10, 1e-44, per="ELECTRON")
    per_n = C.interaction_rate_per_year(q, 6.5e10, 1e-44, per="NUCLEON")
    assert per_n == pytest.approx(2 * per_e)


def test_nucleus_count_is_used_for_cevns():
    """Using nucleons for a per-nucleus cross-section overcounts by
    the nucleons-per-molecule factor, here 60x."""
    q = C.TARGETS["BENCH_QUARTZ_100G"]
    assert q.n_molecules == pytest.approx(q.n_nucleons / 60)


def test_unknown_target_count_kind_refused():
    q = C.TARGETS["BENCH_QUARTZ_100G"]
    with pytest.raises(ValueError):
        q.target_count("PHLOGISTON")


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


def test_the_barrier_is_readout_not_mass():
    """R9-D-006. This used to compare against Super-K and conclude
    the barrier was mass. NUCLEUS runs a 10 g target -- a tenth of the
    bench crystal -- so mass is demonstrably not what is missing.
    """
    g = C.scale_gap()
    assert g["barrier"] == "READOUT_NOT_MASS"
    assert g["bench_is_heavier_than_smallest_detector"]
    assert g["mass_ratio_to_smallest"] < 1.0


def test_gram_scale_detection_is_a_real_programme():
    b = C.DETECTOR_BENCHMARKS
    assert b["NUCLEUS"]["mass_g"] == 10.0
    assert b["NUCLEUS"]["threshold_eV"] <= 20.0
    # what NUCLEUS has that the bench does not
    assert "cryogenic" in b["NUCLEUS"]["material"]
    assert "veto" in b["NUCLEUS"]["conditions"]


def test_smallest_detection_is_kilogram_scale_not_gram_scale():
    """NUCLEUS has not published a detection; CONUS+ is the record."""
    b = C.DETECTOR_BENCHMARKS
    assert "no detection published" in b["NUCLEUS"]["status"]
    detected = [v for v in b.values()
                if "no detection" not in v["status"]]
    assert min(v["mass_g"] for v in detected) == 3_000.0


def test_every_benchmark_carries_a_source():
    for name, spec in C.DETECTOR_BENCHMARKS.items():
        assert spec["source"], name
        assert spec["threshold_eV"] > 0


def test_miniaturisation_argument_is_credited_to_prior_art():
    assert "Drukier" in C.COHERENT_SCATTERING_PRIOR_ART
    assert "1974" in C.COHERENT_SCATTERING_PRIOR_ART
    assert "theirs" in C.scale_gap()["prior_art"]


def test_rate_is_labelled_a_zero_threshold_ceiling():
    """Quoting ~1.2/yr without this caveat would overstate it."""
    assert "ZERO-THRESHOLD ceiling" in C.THRESHOLD_CAVEAT
    assert "the real one is lower" in C.THRESHOLD_CAVEAT


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
