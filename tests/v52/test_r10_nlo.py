"""P10 — SHG in quartz: a real but weak nonlinearity that bulk optics
cannot phase-match.

The real facts are exercised (class 32 is non-centrosymmetric, so SHG is
allowed; d11 ~ 0.3 pm/V) and the honest negative is pinned down with
power: quartz's birefringence is too small to phase-match its dispersion,
so bulk quartz is NOT_PHASE_MATCHABLE_IN_BULK_QUARTZ. Every over-claim is
refused.
"""

from __future__ import annotations

import math

import pytest

from r10 import nlo as N


# --- phase mismatch and coherence length -------------------------------

def test_phase_mismatch_sign_and_value():
    """Delta_k = (4*pi/lambda)*(n2w - nw); positive under normal
    dispersion, and matches the closed form on planted indices."""
    lam = 1.064e-6
    dk = N.phase_mismatch(1.50, 1.52, lam)
    assert dk > 0.0
    assert dk == pytest.approx(4.0 * math.pi / lam * 0.02, rel=1e-12)


def test_phase_mismatch_zero_at_perfect_matching():
    assert N.phase_mismatch(1.5, 1.5, 1.0e-6) == 0.0


def test_coherence_length_closed_form():
    lam = 1.0e-6
    lc = N.coherence_length_m(1.50, 1.52, lam)
    assert lc == pytest.approx(lam / (4.0 * 0.02), rel=1e-12)


def test_larger_dispersion_gives_shorter_coherence_length():
    """POWER: a doubled |n2w - nw| halves L_c."""
    lam = 1.0e-6
    small = N.coherence_length_m(1.50, 1.51, lam)   # dn = 0.01
    large = N.coherence_length_m(1.50, 1.52, lam)   # dn = 0.02
    assert large < small
    assert small / large == pytest.approx(2.0, rel=1e-12)


def test_quartz_coherence_length_is_short():
    """Tens of microns for quartz's visible dispersion -> tiny
    conversion without quasi-phase-matching."""
    lc = N.coherence_length_m(1.54, 1.54 + N.QUARTZ_DISPERSION_VISIBLE,
                              550e-9)
    assert 1e-6 < lc < 5e-5


def test_perfect_matching_gives_infinite_coherence_length():
    assert math.isinf(N.coherence_length_m(1.5, 1.5, 1e-6))


def test_nonpositive_wavelength_is_refused():
    with pytest.raises(ValueError):
        N.phase_mismatch(1.5, 1.52, 0.0)
    with pytest.raises(ValueError):
        N.coherence_length_m(1.5, 1.52, -1.0)


# --- the honest negative: birefringent phase matching ------------------

def test_quartz_is_not_birefringently_phase_matchable():
    """Birefringence (~0.009) < dispersion (~0.013): False."""
    assert not N.birefringent_phase_matchable(
        N.QUARTZ_BIREFRINGENCE_589NM, N.QUARTZ_DISPERSION_VISIBLE)


def test_a_large_enough_birefringence_would_phase_match():
    """A hypothetical crystal whose birefringence exceeds its dispersion
    IS phase-matchable -- the test can distinguish the cases."""
    assert N.birefringent_phase_matchable(0.05, 0.013)


def test_phase_matchable_exactly_at_the_boundary():
    assert N.birefringent_phase_matchable(0.013, 0.013)


def test_quartz_status_reports_the_negative():
    st = N.quartz_phase_match_status()
    assert st["birefringent_phase_matchable"] is False
    assert st["shortfall"] > 0.0
    assert st["verdict"] == "NOT_PHASE_MATCHABLE_IN_BULK_QUARTZ"


# --- the class-32 second-order tensor ----------------------------------

def test_class_32_tensor_symmetry_relations():
    """d12 = -d11 and d26 = -d11 for point group 32."""
    d = N.class_32_d_tensor(d11=0.3, d14=0.01)
    assert d["d12"] == pytest.approx(-d["d11"])
    assert d["d26"] == pytest.approx(-d["d11"])
    assert d["d25"] == pytest.approx(-d["d14"])
    assert d["d11"] == pytest.approx(0.3)


def test_d11_literature_value_is_small():
    assert N.D11_PM_PER_V == pytest.approx(0.3, abs=0.05)


def test_centrosymmetric_medium_forbids_shg():
    """All d = 0 under inversion symmetry: SHG forbidden."""
    d = N.centrosymmetric_d_tensor()
    assert all(v == 0.0 for v in d.values())
    assert not N.second_harmonic_allowed(N.CrystalClass.CENTROSYMMETRIC)


def test_class_32_allows_shg():
    assert N.second_harmonic_allowed(N.CrystalClass.CLASS_32)


# --- the refusal -------------------------------------------------------

def test_efficient_shg_claim_is_refused():
    with pytest.raises(N.NloError):
        N.refuse_efficient_shg_claim()
    with pytest.raises(N.NloError):
        N.refuse_efficient_shg_claim("as a doubler")


# --- report ------------------------------------------------------------

def test_report_measures_nothing_and_names_the_verdicts():
    r = N.nlo_report()
    assert r["measured_here"] == "nothing"
    assert r["verdict"] == "NLO_MODEL_ONLY"
    assert r["phase_matching_verdict"] == "NOT_PHASE_MATCHABLE_IN_BULK_QUARTZ"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert "DERIVED_MATHEMATICS" in r["evidence_class"]
    assert "CONVENTIONAL_LITERATURE" in r["evidence_class"]


def test_report_cites_franken_1961():
    r = N.nlo_report()
    joined = " ".join(r["primary_sources"])
    assert "Franken" in joined and "1961" in joined


def test_report_states_the_honest_negative():
    r = N.nlo_report()
    assert "not say" in r["what_this_does_not_say"].lower()
    assert "phase-match" in r["the_honest_negative"]
