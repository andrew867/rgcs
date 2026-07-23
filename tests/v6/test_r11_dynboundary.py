"""P08 — a time-dependent boundary is a Bogoliubov transformation.

The real physics (pair creation from a switched boundary, finite for
finite switching time) is exercised with numbers; every over-claim it
invites — a fractional photon, a broken photon at a dark port, a new
particle, infinite free energy, energy from nothing — is refused.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from r11 import dynboundary as DB


# --- (1) the Bogoliubov transformation ----------------------------------

@pytest.mark.parametrize("r", [0.0, 0.1, 0.5, 1.0, 2.0, 3.5])
def test_bogoliubov_identity_holds_for_cosh_sinh(r):
    """|alpha|**2 - |beta|**2 == 1 for (cosh r, sinh r)."""
    alpha, beta = DB.squeezing_alpha_beta(r)
    assert abs(alpha) ** 2 - abs(beta) ** 2 == pytest.approx(1.0, abs=1e-9)
    DB.check_bogoliubov(alpha, beta)           # does not raise
    assert DB.bogoliubov_defect(alpha, beta) == pytest.approx(0.0, abs=1e-9)


def test_a_pair_that_breaks_the_identity_is_refused():
    with pytest.raises(DB.DynBoundaryError):
        DB.check_bogoliubov(1.0, 1.0)          # 1 - 1 == 0, not 1
    with pytest.raises(DB.DynBoundaryError):
        DB.BogoliubovMode(2.0, 0.0)            # 4 - 0 == 4, not 1


@pytest.mark.parametrize("r", [0.0, 0.3, 1.0, 2.5])
def test_created_photons_equals_sinh_squared(r):
    """<n> = |beta|**2 = sinh(r)**2."""
    _, beta = DB.squeezing_alpha_beta(r)
    assert DB.created_photons(beta) == pytest.approx(math.sinh(r) ** 2,
                                                     rel=1e-12, abs=1e-15)
    assert DB.created_photons(beta) == pytest.approx(
        DB.squeezing_photon_number(r), rel=1e-12, abs=1e-15)


def test_a_static_boundary_creates_nothing():
    """beta == 0 (no frequency mixing) means no photons."""
    mode = DB.BogoliubovMode.from_squeezing(0.0)
    assert mode.beta == 0.0
    assert mode.mean_photon_number == 0.0


def test_the_transformation_mixes_in_the_conjugate_term():
    """a_out = alpha*a_in + beta*conj(a_in_dagger): the beta term is real
    work, not decoration."""
    mode = DB.BogoliubovMode.from_squeezing(1.0)
    with_mix = mode.out_amplitude(1.0, 1.0)
    without_mix = DB.BogoliubovMode.from_squeezing(0.0).out_amplitude(1.0, 1.0)
    assert with_mix != pytest.approx(without_mix)
    assert with_mix == pytest.approx(mode.alpha + mode.beta)


def test_photon_number_sectors_are_integers_from_zero_upward():
    """The output has sectors 0, 2, 4, ... and no fractional sector."""
    d = DB.photon_number_distribution(0.8)
    assert d["total_probability"] == pytest.approx(1.0, abs=1e-9)
    assert d["fractional_sectors"] == {}
    assert all(isinstance(k, int) for k in d["sectors"])
    assert min(d["sectors"]) == 0
    mean = sum(k * p for k, p in d["sectors"].items())
    assert mean == pytest.approx(math.sinh(0.8) ** 2, rel=1e-6)


# --- (2) the divergence vs finite switching -----------------------------

def test_instantaneous_switching_diverges():
    """tau == 0 has no finite answer: arbitrarily high frequencies."""
    with pytest.raises(DB.DynBoundaryError):
        DB.expected_photon_number(0.0)
    with pytest.raises(DB.DynBoundaryError):
        DB.expected_photon_number(0.0, omega_max=1e12)


@pytest.mark.parametrize("tau", [1e-9, 1e-6, 1e-3, 1.0, 10.0])
def test_finite_switching_time_gives_a_finite_number(tau):
    n = DB.expected_photon_number(tau)
    assert math.isfinite(n)
    assert n > 0.0


def test_photon_number_decreases_monotonically_with_switching_time():
    """Slower switching, fewer photons — across a real sweep."""
    taus = np.logspace(-9, 1, 25)
    values = [DB.expected_photon_number(float(t)) for t in taus]
    assert all(math.isfinite(v) for v in values)
    assert all(b < a for a, b in zip(values, values[1:]))
    sweep = DB.switching_time_sweep(taus)
    assert sweep["all_finite"]
    assert sweep["monotone_decreasing_in_tau"]


def test_the_divergence_grows_without_bound_as_tau_shrinks():
    ladder = [1e-3, 1e-6, 1e-9, 1e-12]
    values = [DB.expected_photon_number(t) for t in ladder]
    assert all(b > 1e3 * a for a, b in zip(values, values[1:]))
    d = DB.divergence_report()
    assert d["instantaneous_limit"] == "DIVERGENT"
    assert d["finite_switching_limit"] == "FINITE"


def test_a_band_limited_count_never_exceeds_the_full_band():
    tau = 1e-3
    full = DB.expected_photon_number(tau)
    part = DB.expected_photon_number(tau, omega_max=100.0)
    assert 0.0 < part < full
    # the truncated integral converges up to the full-band value
    assert DB.expected_photon_number(tau, omega_max=1e9) == pytest.approx(
        full, rel=1e-9)


def test_negative_switching_time_is_refused():
    with pytest.raises(DB.DynBoundaryError):
        DB.expected_photon_number(-1.0)


def test_infinite_free_energy_is_refused():
    with pytest.raises(DB.DynBoundaryError):
        DB.refuse_infinite_free_energy()


# --- (3) energy accounting ----------------------------------------------

def test_the_switching_agent_pays_for_the_photons():
    e = DB.switching_energy_input(1e-3)
    assert math.isfinite(e["field_energy_j"])
    assert e["field_energy_j"] > 0.0
    assert e["net_gain_available"] is False
    assert "boundary" in e["energy_source"]
    assert e["verdict"] == "SWITCHING_ENERGY_REQUIRED"


def test_faster_switching_costs_more_energy():
    fast = DB.switching_energy_input(1e-6)["field_energy_j"]
    slow = DB.switching_energy_input(1e-3)["field_energy_j"]
    assert fast > slow


def test_energy_accounting_refuses_the_instantaneous_limit():
    with pytest.raises(DB.DynBoundaryError):
        DB.switching_energy_input(0.0)


def test_energy_from_nothing_is_refused():
    with pytest.raises(DB.DynBoundaryError):
        DB.refuse_energy_from_nothing()


# --- (4) competing mechanisms -------------------------------------------

EXPECTED_MECHANISMS = {
    "STATIC_MIRROR_OR_BEAMSPLITTER",
    "ORDINARY_DESTRUCTIVE_INTERFERENCE",
    "PULSE_GATING",
    "TIME_DEPENDENT_DIELECTRIC",
    "DYNAMICAL_CASIMIR",
    "WAVEPACKET_TRUNCATION",
    "CLASSICAL_SPECTRAL_BROADENING",
    "DETECTOR_ARTIFACT",
}


def test_every_competing_mechanism_exists():
    assert {m.name for m in DB.Mechanism} == EXPECTED_MECHANISMS


def test_the_mechanisms_are_distinct():
    values = [m.value for m in DB.Mechanism]
    assert len(set(values)) == len(values) == len(EXPECTED_MECHANISMS)


def test_each_mechanism_is_modelled_separately():
    for m in DB.Mechanism:
        model = DB.mechanism_model(m)
        assert model.mechanism is m
        assert model.description
        assert model.does_not_license


def test_only_the_time_dependent_mechanisms_create_photons():
    for m in DB.Mechanism:
        model = DB.mechanism_model(m)
        if model.creates_photons:
            assert model.needs_time_dependence


def test_fractional_photon_is_refused():
    with pytest.raises(DB.DynBoundaryError):
        DB.refuse_fractional_photon(0.6)


def test_interference_as_a_broken_photon_is_refused():
    with pytest.raises(DB.DynBoundaryError):
        DB.refuse_interference_as_broken_photon()


def test_the_new_particle_claim_is_refused():
    with pytest.raises(DB.DynBoundaryError):
        DB.refuse_new_particle_claim()
    with pytest.raises(DB.DynBoundaryError):
        DB.refuse_new_particle_claim(
            DB.DYNAMIC_BOUNDARY_MULTIMODE_STATE_CANDIDATE)


# --- (5) the observables -------------------------------------------------

def test_every_required_observable_is_present_and_unmeasured():
    names = {o.name for o in DB.REQUIRED_OBSERVABLES}
    assert names == {
        "photon_number_distribution",
        "squeezing_correlations",
        "sideband_spectrum",
        "forward_backward_correlations",
        "switching_energy_input",
        "transition_region_energy_density",
        "dependence_on_switching_time",
        "nulls_with_static_boundaries_and_classical_pulses",
    }
    assert all(o.status == "UNMEASURED" for o in DB.REQUIRED_OBSERVABLES)
    r = DB.observables_report()
    assert r["count"] == 8
    assert r["any_measured"] is False


# --- (6) accessibility ---------------------------------------------------

def test_accessibility_returns_both_the_claim_and_the_caveat():
    a = DB.accessibility_vs_neutrino()
    assert "neutrino" in a["accessibility_statement"]
    assert "accessib" in a["accessibility_statement"]
    assert "does not establish" in a["does_not_establish_statement"]
    assert a["both_statements_are_required"] is True
    assert a["accessibility_statement"] != a["does_not_establish_statement"]


# --- the report ----------------------------------------------------------

def test_report_claims_no_measurement_and_no_new_particle():
    r = DB.dynboundary_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["evidence_class"] == "DERIVED_MATHEMATICS"
    assert r["what_this_does_not_say"]
    assert r["verdict"] == (
        "TRUNCATED_PHOTON_IS_MULTIMODE_EM_STATE_NOT_NEW_PARTICLE")
    assert r["verdict"] == DB.DEFAULT_VERDICT


def test_the_public_aliases_are_neutral():
    assert DB.TRUNCATED_PHOTON_REFERENCE_A == "TRUNCATED_PHOTON_REFERENCE_A"
    assert DB.DYNAMIC_BOUNDARY_MULTIMODE_STATE_CANDIDATE == (
        "DYNAMIC_BOUNDARY_MULTIMODE_STATE_CANDIDATE")
    r = DB.dynboundary_report()
    assert r["reference"] == DB.TRUNCATED_PHOTON_REFERENCE_A
    assert r["candidate_label"] == DB.DYNAMIC_BOUNDARY_MULTIMODE_STATE_CANDIDATE
