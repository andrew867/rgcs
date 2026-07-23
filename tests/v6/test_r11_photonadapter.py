"""P08b — the truncated-photon source equations, registered and priced.

The six source equations must be registered with their paper equation
numbers and the verified document hash. The two closed forms that are
pure arithmetic (Eq. 29 and Eq. 30) are exercised with numbers, including
the source's own optical example. The classical reduced-order analogue of
Eq. 28 is exercised with a POWER check that pins 1.0, 0.0 and 0.5. Every
over-claim it invites — the classical fraction as a quantum fidelity, a
bench validation, a QFT computation, a fractional photon — is refused.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from r11 import photonadapter as PA
from r11.sources import SourceKind


VERIFIED_SHA256 = (
    "b9e54ac8b1f7a4f7a1d00f98d540d1941684f3483bc4b96648337a6693f6472e")

EXPECTED_EQUATION_IDS = {
    "EQ21_FIDELITY_DEFINITION": 21,
    "EQ22_EXPECTED_PHOTON_NUMBER": 22,
    "EQ28_FIDELITY_SMALL_N": 28,
    "EQ29_PHOTON_NUMBER_BOUND": 29,
    "EQ30_TRANSMISSIVITY": 30,
    "EQ31_VALIDITY_CONDITION": 31,
}


# --- (1) the registered source ------------------------------------------

def test_all_six_source_equations_are_registered_with_paper_numbers():
    got = {e.equation_id: e.paper_eq_number for e in PA.SOURCE_EQUATIONS}
    assert got == EXPECTED_EQUATION_IDS
    assert len(PA.SOURCE_EQUATIONS) == 6


def test_every_equation_carries_the_verified_document_hash():
    assert PA.SOURCE_PAPER_SHA256 == VERIFIED_SHA256
    assert PA.SOURCE_PAPER.sha256 == VERIFIED_SHA256
    assert len(VERIFIED_SHA256) == 64
    for e in PA.SOURCE_EQUATIONS:
        assert e.source_sha256 == VERIFIED_SHA256


def test_the_registered_equations_are_established_source_not_our_results():
    for e in PA.SOURCE_EQUATIONS:
        assert e.kind is SourceKind.ESTABLISHED_SOURCE
        assert e.rederived_here is False
        assert e.bench_validated is False
        assert e.text and e.meaning


def test_an_equation_registered_against_the_wrong_hash_is_refused():
    with pytest.raises(PA.PhotonAdapterError):
        PA.SourceEquation("EQ_FAKE", 99, "x = y", "nothing",
                          source_sha256="0" * 64)


def test_an_equation_cannot_be_marked_rederived_or_bench_validated():
    with pytest.raises(PA.PhotonAdapterError):
        PA.SourceEquation("EQ_FAKE", 99, "x = y", "nothing",
                          rederived_here=True)
    with pytest.raises(PA.PhotonAdapterError):
        PA.SourceEquation("EQ_FAKE", 99, "x = y", "nothing",
                          bench_validated=True)


def test_the_equation_texts_are_the_source_forms():
    assert PA.get_equation_by_number(29).text == (
        "<n> <= kappa_0/(4*T) + kappa_0**2/(16*T**2)")
    assert PA.get_equation_by_number(30).text == (
        "|T(omega)|**2 = 1 / (1 + (omega*kappa_0)**2 / 4)")
    assert PA.get_equation_by_number(31).text == "1/omega_0 << kappa_0 <~ T"
    assert PA.get_equation_by_number(21).text == (
        "F_xi**2 = <0| a_xi rho_xi a_xi^dagger |0>")
    assert PA.get_equation_by_number(22).text == (
        "<n> = sum_xi ( ||xi_-||**2 + ||xi_+||**2 )")
    assert PA.get_equation_by_number(28).text == (
        "F_xi = | integral dx theta(-x) conj(xi_bar(x)) xi(x) |")


def test_eq28_means_the_fraction_of_the_photon_to_the_left():
    meaning = PA.get_equation("EQ28_FIDELITY_SMALL_N").meaning
    assert "fraction of the photon located at x < 0" in meaning


def test_an_unregistered_equation_is_refused():
    with pytest.raises(PA.PhotonAdapterError):
        PA.get_equation("EQ_NOT_REGISTERED")
    with pytest.raises(PA.PhotonAdapterError):
        PA.get_equation_by_number(1)


# --- (2) the qualitative claims -----------------------------------------

EXPECTED_CLAIM_IDS = {
    "CLAIM_NOT_A_PHOTON_NOR_A_MIX_WITH_VACUUM",
    "CLAIM_LOCAL_EQUIVALENCE",
    "CLAIM_INSTANTANEOUS_DIVERGES_GRADUAL_BOUNDED",
    "CLAIM_SWITCHING_BOUNDARY_SUPPLIES_THE_ENERGY",
    "CLAIM_OPTICAL_SCALE_EXAMPLE",
}


def test_the_qualitative_claims_are_registered_and_unverified_here():
    assert {c.claim_id for c in PA.SOURCE_CLAIMS} == EXPECTED_CLAIM_IDS
    for c in PA.SOURCE_CLAIMS:
        assert c.kind is SourceKind.SOURCE_CLAIM
        assert c.verified_here is False


def test_a_claim_cannot_be_marked_verified_here():
    with pytest.raises(PA.PhotonAdapterError):
        PA.SourceClaim("CLAIM_FAKE", "anything", "nowhere",
                       verified_here=True)


def test_the_claims_say_what_the_source_says():
    not_a_photon = PA.get_claim("CLAIM_NOT_A_PHOTON_NOR_A_MIX_WITH_VACUUM")
    assert "neither another photon" in not_a_photon.statement
    assert "up to infinity" in not_a_photon.statement
    local = PA.get_claim("CLAIM_LOCAL_EQUIVALENCE")
    assert "locally equivalent" in local.statement
    assert "vacuum to the right" in local.statement
    div = PA.get_claim("CLAIM_INSTANTANEOUS_DIVERGES_GRADUAL_BOUNDED")
    assert "divergent" in div.statement and "gradual" in div.statement.lower()
    energy = PA.get_claim("CLAIM_SWITCHING_BOUNDARY_SUPPLIES_THE_ENERGY")
    assert "time-translation invariance is broken" in energy.statement
    assert "boundary supplies the energy" in energy.statement


def test_an_unregistered_claim_is_refused():
    with pytest.raises(PA.PhotonAdapterError):
        PA.get_claim("CLAIM_NOT_REGISTERED")


# --- (3) Eq. 29: the photon-number bound --------------------------------

def test_eq29_matches_a_hand_computed_value():
    """kappa_0 = 2, T = 1: 2/4 + 4/16 = 0.5 + 0.25 = 0.75."""
    assert PA.photon_number_bound(2.0, 1.0) == pytest.approx(0.75, rel=1e-15)
    # kappa_0 = 4, T = 2: 4/8 + 16/64 = 0.5 + 0.25 = 0.75 (depends on ratio)
    assert PA.photon_number_bound(4.0, 2.0) == pytest.approx(0.75, rel=1e-15)
    # kappa_0 = 1, T = 0.5: 1/2 + 1/4 = 0.75
    assert PA.photon_number_bound(1.0, 0.5) == pytest.approx(0.75, rel=1e-15)
    # kappa_0 = 1e-14, T = 1e-14: 1/4 + 1/16 = 0.3125
    assert PA.photon_number_bound(1e-14, 1e-14) == pytest.approx(
        0.3125, rel=1e-12)


@pytest.mark.parametrize("kappa_0,T", [(1.0, 1.0), (3.0, 0.25), (1e-14, 2e-14)])
def test_eq29_equals_the_closed_form_written_out(kappa_0, T):
    expected = kappa_0 / (4.0 * T) + kappa_0 ** 2 / (16.0 * T ** 2)
    assert PA.photon_number_bound(kappa_0, T) == pytest.approx(
        expected, rel=1e-15)


def test_eq29_diverges_as_removal_time_goes_to_zero():
    """Instantaneous removal has no finite bound: T == 0 raises."""
    with pytest.raises(PA.PhotonAdapterError):
        PA.photon_number_bound(1.0, 0.0)
    ladder = [1e-2, 1e-4, 1e-6, 1e-8]
    values = [PA.photon_number_bound(1.0, t) for t in ladder]
    assert all(math.isfinite(v) for v in values)
    # each decade faster gives at least a hundredfold larger bound
    assert all(b > 100.0 * a for a, b in zip(values, values[1:]))
    assert values[-1] > 1e14


def test_eq29_refuses_negative_times_and_permittivities():
    with pytest.raises(PA.PhotonAdapterError):
        PA.photon_number_bound(1.0, -1.0)
    with pytest.raises(PA.PhotonAdapterError):
        PA.photon_number_bound(-1.0, 1.0)


def test_eq29_decreases_strictly_as_the_removal_time_grows():
    times = np.logspace(-15, -9, 40)
    values = [PA.photon_number_bound(3e-14, float(t)) for t in times]
    assert all(math.isfinite(v) for v in values)
    assert all(b < a for a, b in zip(values, values[1:]))
    sweep = PA.bound_sweep(3e-14, times)
    assert sweep["all_finite"] is True
    assert sweep["monotone_decreasing_in_T"] is True
    assert sweep["paper_eq_number"] == 29


def test_a_sweep_needs_more_than_one_removal_time():
    with pytest.raises(PA.PhotonAdapterError):
        PA.bound_sweep(1e-14, [1e-14])


def test_inverting_eq29_round_trips():
    kappa_0 = 3.1829397029157425e-14
    for target in (0.01, 0.5, 1.0, 10.0):
        t = PA.removal_time_for_bound(kappa_0, target)
        assert PA.photon_number_bound(kappa_0, t) == pytest.approx(
            target, rel=1e-12)


def test_inverting_eq29_refuses_nonsense():
    with pytest.raises(PA.PhotonAdapterError):
        PA.removal_time_for_bound(0.0, 1.0)
    with pytest.raises(PA.PhotonAdapterError):
        PA.removal_time_for_bound(1e-14, 0.0)


# --- (4) Eq. 30: the transmissivity -------------------------------------

def test_eq30_is_unity_at_zero_frequency():
    for kappa_0 in (0.0, 1e-14, 1.0, 1e3):
        assert PA.transmissivity(0.0, kappa_0) == pytest.approx(1.0,
                                                                rel=1e-15)


def test_eq30_matches_the_closed_form_written_out():
    omega, kappa_0 = 5.0, 0.4
    expected = 1.0 / (1.0 + (omega * kappa_0) ** 2 / 4.0)
    assert PA.transmissivity(omega, kappa_0) == pytest.approx(expected,
                                                              rel=1e-15)
    # omega*kappa_0 == 2 gives exactly 1/2
    assert PA.transmissivity(2.0, 1.0) == pytest.approx(0.5, rel=1e-15)


def test_eq30_decreases_in_frequency_and_stays_in_the_unit_interval():
    omegas = np.linspace(0.0, 1e16, 200)
    t2 = PA.transmissivity(omegas, 3.1829397029157425e-14)
    assert t2.shape == omegas.shape
    assert np.all(t2 > 0.0)
    assert np.all(t2 <= 1.0)
    assert np.all(np.diff(t2) < 0.0)


def test_eq30_refuses_a_negative_permittivity():
    with pytest.raises(PA.PhotonAdapterError):
        PA.transmissivity(1.0, -1.0)


def test_inverting_eq30_round_trips_and_refuses_impossible_values():
    for t_sq in (1e-6, 1e-4, 0.5, 1.0):
        kappa_0 = PA.kappa_0_from_transmissivity(1e15, t_sq)
        assert PA.transmissivity(1e15, kappa_0) == pytest.approx(t_sq,
                                                                 rel=1e-12)
    with pytest.raises(PA.PhotonAdapterError):
        PA.kappa_0_from_transmissivity(1e15, 1.5)      # |T|**2 > 1
    with pytest.raises(PA.PhotonAdapterError):
        PA.kappa_0_from_transmissivity(1e15, 0.0)
    with pytest.raises(PA.PhotonAdapterError):
        PA.kappa_0_from_transmissivity(0.0, 0.5)


# --- (5) the source's optical example -----------------------------------

def test_the_optical_example_reproduces_the_sources_order_of_magnitude():
    """omega_0/2pi = 1e15 Hz, |T|**2 = 1e-4, T ~ 1e-14 s -> <n> ~ 1."""
    ex = PA.optical_example()
    assert ex["omega_0_over_2pi_hz"] == pytest.approx(1e15, rel=1e-12)
    # Eq. 30 at |T|**2 = 1e-4 fixes kappa_0 = (2/omega_0)*sqrt(1e4 - 1)
    assert ex["kappa_0_s"] == pytest.approx(3.1829397e-14, rel=1e-6)
    assert ex["transmissivity_check"] == pytest.approx(1e-4, rel=1e-12)
    # the Eq. 29 bound at the stated removal time is of order unity
    assert ex["photon_number_bound"] == pytest.approx(1.42892900, rel=1e-6)
    assert 0.1 <= ex["photon_number_bound"] <= 10.0
    assert ex["bound_is_order_unity"] is True
    assert ex["agreement_with_source_example"] == "CONSISTENT"
    # the removal time at which the bound reaches exactly 1 is ~1.29e-14 s
    assert ex["removal_time_for_unit_bound_s"] == pytest.approx(
        1.28752616e-14, rel=1e-6)
    assert 1e-14 <= ex["removal_time_for_unit_bound_s"] < 1e-13


def test_the_example_reports_the_marginal_validity_condition_honestly():
    """Eq. 31 wants 1/omega_0 << kappa_0 <~ T; here kappa_0 ~ 3.2 T."""
    v = PA.optical_example()["validity"]
    assert v["kappa_0_over_optical_period"] == pytest.approx(199.99, rel=1e-3)
    assert v["lower_inequality_satisfied"] is True
    assert v["kappa_0_over_T"] == pytest.approx(3.18294, rel=1e-4)
    # kappa_0 exceeds T, so the upper inequality is only marginally met and
    # the module must say so rather than report a clean pass
    assert v["upper_inequality_satisfied"] is False
    assert v["upper_inequality_marginal"] is True
    assert v["in_declared_regime"] is True


def test_the_validity_condition_refuses_nonpositive_inputs():
    with pytest.raises(PA.PhotonAdapterError):
        PA.validity_condition(0.0, 1e-14, 1e-14)
    with pytest.raises(PA.PhotonAdapterError):
        PA.validity_condition(1e15, 0.0, 1e-14)
    with pytest.raises(PA.PhotonAdapterError):
        PA.validity_condition(1e15, 1e-14, 0.0)


def test_a_slower_removal_satisfies_eq31_and_lowers_the_bound():
    kappa_0 = PA.kappa_0_from_transmissivity(PA.EXAMPLE_OMEGA_0_RAD_S, 1e-4)
    slow = PA.validity_condition(PA.EXAMPLE_OMEGA_0_RAD_S, kappa_0, 1e-12)
    assert slow["upper_inequality_satisfied"] is True
    assert slow["in_declared_regime"] is True
    assert (PA.photon_number_bound(kappa_0, 1e-12)
            < PA.photon_number_bound(kappa_0, 1e-14))


# --- (6) the CLASSICAL analogue of Eq. 28: a POWER check ----------------

X_GRID = np.linspace(-10.0, 10.0, 4001)


def _gaussian(centre: float, width: float = 0.5) -> np.ndarray:
    return np.exp(-((X_GRID - centre) ** 2) / (2.0 * width ** 2))


def test_an_envelope_entirely_to_the_left_gives_one():
    assert PA.fidelity_fraction_left(_gaussian(-5.0), X_GRID) == \
        pytest.approx(1.0, abs=1e-12)


def test_an_envelope_entirely_to_the_right_gives_zero():
    assert PA.fidelity_fraction_left(_gaussian(5.0), X_GRID) == \
        pytest.approx(0.0, abs=1e-12)


def test_a_symmetric_envelope_gives_one_half():
    assert PA.fidelity_fraction_left(_gaussian(0.0), X_GRID) == \
        pytest.approx(0.5, abs=1e-12)


def test_the_fraction_is_exact_for_a_flat_envelope_on_an_offset_grid():
    """Flat power on [-1, 3]: the left quarter of the interval -> 0.25."""
    x = np.linspace(-1.0, 3.0, 401)
    xi = np.ones_like(x)
    assert PA.fidelity_fraction_left(xi, x) == pytest.approx(0.25, abs=1e-12)


def test_the_split_does_not_depend_on_the_grid_containing_the_origin():
    with_origin = np.linspace(-4.0, 4.0, 801)          # contains 0.0
    without_origin = np.linspace(-4.0, 4.0, 800)       # straddles 0.0
    assert 0.0 in with_origin
    assert 0.0 not in without_origin
    a = PA.fidelity_fraction_left(np.exp(-with_origin ** 2), with_origin)
    b = PA.fidelity_fraction_left(np.exp(-without_origin ** 2),
                                  without_origin)
    assert a == pytest.approx(0.5, abs=1e-9)
    assert b == pytest.approx(0.5, abs=1e-6)


def test_shifting_the_envelope_leftwards_raises_the_fraction():
    fractions = [PA.fidelity_fraction_left(_gaussian(c, 1.0), X_GRID)
                 for c in (2.0, 1.0, 0.0, -1.0, -2.0)]
    assert all(b > a for a, b in zip(fractions, fractions[1:]))
    assert all(0.0 <= f <= 1.0 for f in fractions)


def test_the_fraction_ignores_overall_normalization():
    xi = _gaussian(-1.0, 2.0)
    assert PA.fidelity_fraction_left(1e6 * xi, X_GRID) == pytest.approx(
        PA.fidelity_fraction_left(xi, X_GRID), rel=1e-12)


def test_a_complex_envelope_is_taken_by_its_power():
    xi = _gaussian(-1.0, 2.0).astype(complex) * np.exp(1j * 3.0 * X_GRID)
    assert PA.fidelity_fraction_left(xi, X_GRID) == pytest.approx(
        PA.fidelity_fraction_left(_gaussian(-1.0, 2.0), X_GRID), rel=1e-12)


def test_a_malformed_envelope_or_grid_is_refused():
    with pytest.raises(PA.PhotonAdapterError):
        PA.fidelity_fraction_left([1.0, 2.0], [0.0, 1.0, 2.0])   # size
    with pytest.raises(PA.PhotonAdapterError):
        PA.fidelity_fraction_left([1.0], [0.0])                  # too short
    with pytest.raises(PA.PhotonAdapterError):
        PA.fidelity_fraction_left([1.0, 1.0, 1.0],
                                  [0.0, 2.0, 1.0])               # unsorted
    with pytest.raises(PA.PhotonAdapterError):
        PA.fidelity_fraction_left([0.0, 0.0, 0.0],
                                  [-1.0, 0.0, 1.0])              # zero power
    with pytest.raises(PA.PhotonAdapterError):
        PA.fidelity_fraction_left([1.0, float("nan"), 1.0],
                                  [-1.0, 0.0, 1.0])              # non-finite


def test_the_analogue_report_labels_itself_as_not_the_quantum_result():
    r = PA.classical_analogue_report(_gaussian(-5.0), X_GRID)
    assert r["classical_power_fraction_left"] == pytest.approx(1.0, abs=1e-12)
    assert r["evidence_class"] == SourceKind.ANALYTIC_MODEL.value
    assert r["is_the_quantum_fidelity"] is False
    assert r["paper_eq_number"] == 28
    assert r["regime_of_the_source_result"] == "<n> << 1"
    assert r["measured_here"] == "nothing"
    assert r["what_this_does_not_say"]


# --- (7) the refusals ----------------------------------------------------

def test_a_quantum_claim_from_the_classical_analogue_is_refused():
    with pytest.raises(PA.PhotonAdapterError):
        PA.refuse_quantum_claim_from_classical_analogue()
    with pytest.raises(PA.PhotonAdapterError):
        PA.refuse_quantum_claim_from_classical_analogue(
            "F_xi from Eq. 28", 0.73)


def test_bench_validation_is_refused():
    with pytest.raises(PA.PhotonAdapterError):
        PA.refuse_bench_validation()
    with pytest.raises(PA.PhotonAdapterError):
        PA.refuse_bench_validation("the Eq. 30 transmissivity",
                                   "a spectrometer")


def test_a_qft_solver_claim_is_refused():
    with pytest.raises(PA.PhotonAdapterError):
        PA.refuse_qft_solver_claim()
    with pytest.raises(PA.PhotonAdapterError):
        PA.refuse_qft_solver_claim("a numerical reproduction of Eq. 22")


def test_the_fractional_photon_reading_is_refused():
    with pytest.raises(PA.PhotonAdapterError):
        PA.refuse_fractional_photon()
    with pytest.raises(PA.PhotonAdapterError):
        PA.refuse_fractional_photon(0.6)


def test_the_refusals_are_the_modules_own_typed_error():
    assert issubclass(PA.PhotonAdapterError, RuntimeError)
    for fn in (PA.refuse_quantum_claim_from_classical_analogue,
               PA.refuse_bench_validation,
               PA.refuse_qft_solver_claim,
               PA.refuse_fractional_photon):
        with pytest.raises(PA.PhotonAdapterError):
            fn()


# --- (8) the report ------------------------------------------------------

def test_report_measures_nothing_and_claims_no_bench_validation():
    r = PA.photonadapter_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["verdict"] == "QUANTUM_TRUNCATION_NOT_BENCH_VALIDATED"
    assert r["verdict"] == PA.DEFAULT_VERDICT
    assert r["what_this_does_not_say"]
    assert "bench-validated" in r["what_this_does_not_say"]


def test_report_carries_both_evidence_classes():
    r = PA.photonadapter_report()
    assert "ESTABLISHED_SOURCE" in r["evidence_class"]
    assert "ANALYTIC_MODEL" in r["evidence_class"]
    breakdown = r["evidence_class_breakdown"]
    assert breakdown["registered_source_equations"] == "ESTABLISHED_SOURCE"
    assert breakdown["classical_fidelity_analogue"] == "ANALYTIC_MODEL"


def test_report_carries_the_verified_paper_hash_and_all_six_equations():
    r = PA.photonadapter_report()
    assert r["source_paper"]["sha256"] == VERIFIED_SHA256
    assert r["registered_equation_count"] == 6
    numbers = {e["paper_eq_number"] for e in r["registered_equations"]}
    assert numbers == {21, 22, 28, 29, 30, 31}
    assert all(e["evidence_class"] == "ESTABLISHED_SOURCE"
               for e in r["registered_equations"])
    assert all(e["bench_validated"] is False
               for e in r["registered_equations"])


def test_report_carries_the_five_registered_claims_unverified():
    r = PA.photonadapter_report()
    assert r["registered_claim_count"] == 5
    assert {c["claim_id"] for c in r["registered_claims"]} == \
        EXPECTED_CLAIM_IDS
    assert all(c["verified_here"] is False for c in r["registered_claims"])


def test_report_carries_the_optical_example_numbers():
    r = PA.photonadapter_report()
    ex = r["optical_example"]
    assert ex["bench_validated"] is False
    assert ex["measured_here"] == "nothing"
    assert ex["photon_number_bound"] == pytest.approx(1.42892900, rel=1e-6)


def test_the_public_alias_is_neutral():
    assert PA.TRUNCATED_PHOTON_REFERENCE_A == "TRUNCATED_PHOTON_REFERENCE_A"
    assert PA.photonadapter_report()["reference"] == \
        PA.TRUNCATED_PHOTON_REFERENCE_A


def test_every_verdict_is_registered_and_the_default_leads():
    assert PA.VERDICTS[0] == PA.DEFAULT_VERDICT
    r = PA.photonadapter_report()
    assert r["verdict"] in r["verdicts"]
    assert set(r["verdicts"]) == set(PA.VERDICTS)


def test_the_firewalls_are_stated():
    r = PA.photonadapter_report()
    joined = " ".join(r["firewalls"]).lower()
    assert "not re-derived" in joined
    assert "not the quantum fidelity" in joined
    assert "no qft solver" in joined
    assert "bench-validated" in joined
    assert "not a fraction of a photon" in joined
