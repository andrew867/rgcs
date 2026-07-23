"""P12 — multiscale mode mixing: one algebra, five typed domains.

The shared core is exercised with numbers: swept through zero detuning,
two coupled modes repel with a minimum splitting of exactly 2*|k| and a
mixing angle of 45 degrees, and the participation fractions exhaust the
bare basis. Each of the five adapters is then checked on its own physics
in its own units — the acoustic branch vanishing at the zone centre, the
mass gap at the zone boundary, modal energy fractions summing to one,
the BVD fs/fp/Q algebra on planted elements, transverse mode spacing and
astigmatic splitting, and the Bogoliubov identity. Finally the firewall:
every ordered pair of different domains is refused transfer, shared
algebra is refused as shared mechanism, modal truncation is refused as a
physical cut, and cross-unit comparison is refused.
"""

from __future__ import annotations

import itertools
import json
import math

import numpy as np
import pytest

from r11 import modemix as MM


DOMAIN_PAIRS = [(a, b) for a, b in itertools.permutations(MM.Domain, 2)]


# --- (1) the shared core --------------------------------------------------

def test_eigen_split_matches_a_direct_eigendecomposition():
    """The closed form and numpy must agree, or one of them is wrong."""
    for w1, w2, k in ((1.0, 1.4, 0.13), (5.0, 5.0, 0.02),
                      (2.0, -1.0, 0.9), (0.0, 3.0, -0.4)):
        split = MM.eigen_split(w1, w2, k)
        system = MM.CoupledModeSystem.two_mode(w1, w2, k)
        values = system.eigenvalues()
        assert split.lower == pytest.approx(float(values[0]), abs=1e-12)
        assert split.upper == pytest.approx(float(values[1]), abs=1e-12)
        assert split.participation == pytest.approx(system.participation(),
                                                    abs=1e-12)


@pytest.mark.parametrize("coupling", [0.001, 0.05, 0.5, 2.0, -0.3])
def test_the_minimum_splitting_over_a_sweep_equals_twice_the_coupling(
        coupling):
    """POWER: sweep the detuning through zero and measure the closest
    approach. It must equal 2*|k| exactly, at zero detuning."""
    sweep = MM.avoided_crossing(reference=7.0, coupling=coupling,
                                n_points=401)
    assert sweep["grid_contains_zero_detuning"] is True
    assert sweep["minimum_splitting"] == pytest.approx(
        2.0 * abs(coupling), rel=1e-12)
    assert sweep["expected_minimum_splitting"] == 2.0 * abs(coupling)
    assert sweep["minimum_matches_twice_the_coupling"] is True
    assert sweep["detuning_at_minimum"] == pytest.approx(0.0, abs=1e-12)


def test_the_splitting_never_falls_below_twice_the_coupling():
    """Repulsion: nowhere on the sweep do the branches approach closer."""
    sweep = MM.avoided_crossing(reference=1.0, coupling=0.2, n_points=301)
    splitting = np.asarray(sweep["splitting"])
    assert np.all(splitting >= 2.0 * 0.2 - 1e-12)
    assert sweep["splitting_never_below_twice_the_coupling"] is True
    assert sweep["branches_never_cross"] is True


def test_a_swept_detuning_would_expose_a_wrong_minimum():
    """The sweep is not tautological: an inflated coupling fails it."""
    sweep = MM.avoided_crossing(reference=1.0, coupling=0.2, n_points=201)
    assert sweep["minimum_splitting"] != pytest.approx(2.0 * 0.25, rel=1e-6)


def test_the_mixing_angle_is_45_degrees_at_zero_detuning():
    split = MM.eigen_split(3.0, 3.0, 0.07)
    assert split.mixing_angle_deg == pytest.approx(45.0, abs=1e-12)
    assert split.is_maximally_mixed is True
    sweep = MM.avoided_crossing(reference=3.0, coupling=0.07, n_points=101)
    assert sweep["mixing_angle_at_zero_detuning_deg"] == pytest.approx(
        45.0, abs=1e-12)


def test_the_mixing_angle_collapses_when_the_detuning_dominates():
    far = MM.eigen_split(10.0, 0.0, 1e-6)
    assert far.mixing_angle_deg == pytest.approx(0.0, abs=1e-4)
    assert far.is_maximally_mixed is False


def test_participation_rows_and_columns_each_sum_to_one():
    part = MM.participation(1.0, 1.3, 0.11)
    assert part.shape == (2, 2)
    assert part.sum(axis=0) == pytest.approx(np.ones(2), abs=1e-12)
    assert part.sum(axis=1) == pytest.approx(np.ones(2), abs=1e-12)
    assert np.all(part >= 0.0)


def test_participation_is_half_and_half_at_zero_detuning():
    part = MM.participation(4.0, 4.0, 0.3)
    assert part == pytest.approx(0.5 * np.ones((2, 2)), abs=1e-12)


def test_zero_coupling_leaves_the_bare_modes_alone():
    split = MM.eigen_split(2.0, 1.0, 0.0)
    assert split.splitting == pytest.approx(1.0, abs=1e-12)
    assert split.participation == pytest.approx(np.array([[0.0, 1.0],
                                                          [1.0, 0.0]]),
                                                abs=1e-12)


def test_the_eigenvectors_diagonalise_the_coupling_matrix():
    split = MM.eigen_split(1.0, 1.6, 0.25)
    vectors = split.eigenvectors()
    matrix = np.real(MM.CoupledModeSystem.two_mode(1.0, 1.6, 0.25).matrix)
    diagonal = vectors.T @ matrix @ vectors
    assert diagonal == pytest.approx(np.diag([split.lower, split.upper]),
                                     abs=1e-12)


def test_the_core_handles_more_than_two_modes():
    matrix = np.array([[1.0, 0.2, 0.05],
                       [0.2, 1.1, 0.3],
                       [0.05, 0.3, 1.4]])
    system = MM.CoupledModeSystem(matrix)
    assert system.n == 3
    part = system.participation()
    assert part.sum(axis=0) == pytest.approx(np.ones(3), abs=1e-12)
    assert part.sum(axis=1) == pytest.approx(np.ones(3), abs=1e-12)
    assert system.splitting() > 0.0


def test_a_non_hermitian_or_malformed_matrix_is_refused():
    with pytest.raises(MM.ModeMixError):
        MM.CoupledModeSystem(np.array([[1.0, 0.5], [-0.5, 2.0]]))
    with pytest.raises(MM.ModeMixError):
        MM.CoupledModeSystem(np.array([[1.0, 0.5, 0.0], [0.5, 2.0, 0.0]]))
    with pytest.raises(MM.ModeMixError):
        MM.CoupledModeSystem(np.array([[1.0]]))
    with pytest.raises(MM.ModeMixError):
        MM.eigen_split(float("inf"), 1.0, 0.1)


def test_a_sweep_needs_a_usable_grid():
    with pytest.raises(MM.ModeMixError):
        MM.avoided_crossing(n_points=200)
    with pytest.raises(MM.ModeMixError):
        MM.avoided_crossing(detunings=[0.0, 1.0])


# --- (2) the five typed domains ------------------------------------------

def test_all_five_domains_exist():
    assert len(list(MM.Domain)) == 5
    for name in ("ATOMIC_LATTICE_PHONON", "MACROSCOPIC_QUARTZ_ELASTIC",
                 "BVD_ELECTRICAL", "OPTICAL_CAVITY_TRANSVERSE",
                 "DYNAMIC_BOUNDARY"):
        assert MM.Domain[name].value == name


def test_every_domain_has_units_no_other_domain_shares():
    units = [MM.domain_units(d) for d in MM.Domain]
    assert all(u.strip() for u in units)
    assert len(set(units)) == len(units)


def test_every_domain_has_a_source_no_other_domain_shares():
    sources = [MM.domain_source(d) for d in MM.Domain]
    assert all(s.strip() for s in sources)
    assert len(set(sources)) == len(sources)
    for d in MM.Domain:
        assert MM.domain_source_class(d) in MM.CLAIM_CLASSES


def test_every_domain_says_what_it_does_not_license():
    strings = [MM.domain_does_not_license(d) for d in MM.Domain]
    assert all(s.strip() for s in strings)
    assert len(set(strings)) == len(strings)
    assert "quartz" in MM.domain_does_not_license(
        MM.Domain.ATOMIC_LATTICE_PHONON).lower()


@pytest.mark.parametrize("domain", list(MM.Domain))
def test_every_adapter_hybridises_through_the_shared_core(domain):
    out = MM.domain_hybridisation(domain)
    assert out["domain"] == domain.value
    assert out["units"] == MM.domain_units(domain)
    assert out["source"] == MM.domain_source(domain)
    assert out["comparable_with_other_domains"] is False
    assert out["measured_here"] == "nothing"
    part = np.asarray(out["split"]["participation"])
    assert part.sum(axis=0) == pytest.approx(np.ones(2), abs=1e-12)
    assert out["split"]["splitting"] >= 2.0 * abs(
        out["split"]["coupling"]) - 1e-9


def test_an_adapter_must_declare_a_registered_claim_class():
    with pytest.raises(MM.ModeMixError):
        MM.DomainAdapter(
            domain=MM.Domain.BVD_ELECTRICAL, units="u", source="s",
            source_class="NOT_A_CLAIM_CLASS", length_scale="l",
            what_mixes="w", coupling_origin="c", does_not_license="d")
    with pytest.raises(MM.ModeMixError):
        MM.DomainAdapter(
            domain=MM.Domain.BVD_ELECTRICAL, units="u", source="s",
            source_class="SOURCE_ESTABLISHED_PHYSICS", length_scale="l",
            what_mixes="w", coupling_origin="c", does_not_license="  ")


def test_an_unknown_domain_object_is_refused():
    with pytest.raises(MM.ModeMixError):
        MM.domain_units("BVD_ELECTRICAL")


# --- (3) adapter A: atomic lattice phonons -------------------------------

def test_the_acoustic_branch_vanishes_at_the_zone_centre():
    chain = MM.DEFAULT_CHAIN
    acoustic, optical = chain.branches(0.0)
    assert acoustic == pytest.approx(0.0, abs=1e-3)
    assert optical > 1e12


def test_the_optical_branch_at_the_zone_centre_matches_the_closed_form():
    chain = MM.DiatomicChain(mass_a_amu=20.0, mass_b_amu=80.0,
                             force_constant_n_per_m=30.0)
    _, optical = chain.branches(0.0)
    assert optical == pytest.approx(chain.zone_centre_optical_rad_s(),
                                    rel=1e-9)


def test_unequal_masses_open_a_gap_at_the_zone_boundary():
    chain = MM.DiatomicChain(mass_a_amu=20.0, mass_b_amu=80.0)
    assert (chain.coupling_magnitude(chain.zone_boundary_q)
            < 1e-12 * chain.coupling_magnitude(0.0))
    low, high = chain.branches(chain.zone_boundary_q)
    c = chain.force_constant_n_per_m
    assert low == pytest.approx(math.sqrt(2.0 * c / chain.mass_b_kg),
                                rel=1e-9)
    assert high == pytest.approx(math.sqrt(2.0 * c / chain.mass_a_kg),
                                 rel=1e-9)
    assert chain.zone_boundary_gap_rad_s() > 0.0


def test_equal_masses_close_the_zone_boundary_gap():
    chain = MM.DiatomicChain(mass_a_amu=50.0, mass_b_amu=50.0)
    gap = chain.zone_boundary_gap_rad_s()
    assert gap == pytest.approx(0.0, abs=1e-3)
    assert MM.DiatomicChain(mass_a_amu=20.0,
                            mass_b_amu=80.0).zone_boundary_gap_rad_s() > gap


def test_the_interbranch_coupling_is_wavevector_dependent():
    chain = MM.DEFAULT_CHAIN
    qs = [0.0, 0.25, 0.5, 0.75, 1.0]
    values = [chain.coupling_magnitude(f * chain.zone_boundary_q)
              for f in qs]
    assert all(b < a for a, b in zip(values, values[1:]))
    assert values[-1] < 1e-12 * values[0]


def test_the_dispersion_keeps_the_optical_branch_on_top():
    out = MM.DEFAULT_CHAIN.dispersion(n_points=25)
    assert out["acoustic_starts_at_zero"] is True
    assert out["optical_never_below_acoustic"] is True
    assert out["units"] == MM.domain_units(MM.Domain.ATOMIC_LATTICE_PHONON)


def test_a_degenerate_chain_is_refused():
    with pytest.raises(MM.ModeMixError):
        MM.DiatomicChain(mass_a_amu=0.0)
    with pytest.raises(MM.ModeMixError):
        MM.DiatomicChain(force_constant_n_per_m=-1.0)


# --- (4) adapter B: macroscopic quartz elastic modes ---------------------

def test_modal_energy_fractions_sum_to_one():
    out = MM.modal_energy_fractions(2.0 * math.pi * 13.0e6, 1.0e-9, 0.04)
    assert out["strain_fraction"] + out["kinetic_fraction"] == pytest.approx(
        1.0, abs=1e-12)
    assert 0.0 < out["strain_fraction"] < 1.0


def test_a_turning_point_is_all_strain_and_a_zero_crossing_all_kinetic():
    omega = 2.0 * math.pi * 13.0e6
    turning = MM.modal_energy_fractions(omega, 1.0e-9, 0.0)
    crossing = MM.modal_energy_fractions(omega, 0.0, 1.0)
    assert turning["strain_fraction"] == pytest.approx(1.0, abs=1e-12)
    assert crossing["kinetic_fraction"] == pytest.approx(1.0, abs=1e-12)
    with pytest.raises(MM.ModeMixError):
        MM.modal_energy_fractions(omega, 0.0, 0.0)


def test_bevelling_shifts_the_trapped_frequency_monotonically():
    base = 13.0e6
    values = [MM.bevel_frequency_hz(base, b)
              for b in (0.0, 0.1, 0.2, 0.4, 0.8)]
    assert values[0] == pytest.approx(base, rel=1e-12)
    assert all(b < a for a, b in zip(values, values[1:]))
    with pytest.raises(MM.ModeMixError):
        MM.bevel_frequency_hz(base, 1.5)


def test_energy_trapping_rises_with_plateback_and_stays_bounded():
    values = [MM.energy_trapping_fraction(p)
              for p in (0.0, 0.001, 0.004, 0.01, 0.05)]
    assert values[0] == pytest.approx(0.0, abs=1e-15)
    assert all(b > a for a, b in zip(values, values[1:]))
    assert all(0.0 <= v < 1.0 for v in values)
    assert MM.energy_trapping_fraction(0.004, 1.0) > \
        MM.energy_trapping_fraction(0.004, 0.25)
    with pytest.raises(MM.ModeMixError):
        MM.energy_trapping_fraction(-0.1)


def test_two_nearby_plate_modes_repel():
    split = MM.elastic_hybridisation(MM.ElasticMode.THICKNESS_SHEAR,
                                     MM.ElasticMode.SPURIOUS_ANHARMONIC,
                                     coupling_hz=4.0e3)
    bare = abs(MM.plate_mode_frequency_hz(MM.ElasticMode.THICKNESS_SHEAR)
               - MM.plate_mode_frequency_hz(
                   MM.ElasticMode.SPURIOUS_ANHARMONIC))
    assert split.splitting > bare
    assert split.splitting >= 2.0 * 4.0e3
    with pytest.raises(MM.ModeMixError):
        MM.elastic_hybridisation(MM.ElasticMode.TWIST,
                                 MM.ElasticMode.TWIST)


def test_every_elastic_mode_has_a_declared_frequency_and_role():
    for mode in MM.ElasticMode:
        assert MM.plate_mode_frequency_hz(mode) > 0.0
        assert MM.ELASTIC_MODE_ROLES[mode].strip()


# --- (5) adapter C: the BVD electrical branch ----------------------------

def test_the_series_resonance_returns_the_planted_target():
    branch = MM.BVDBranch.planted(fs_hz=13.0e6, c1_f=5.0e-15,
                                  r1_ohm=8.0, c0_f=3.0e-12)
    assert branch.series_resonance_hz() == pytest.approx(13.0e6, rel=1e-12)
    assert branch.series_resonance_hz() == pytest.approx(
        1.0 / (2.0 * math.pi * math.sqrt(branch.l1_h * branch.c1_f)),
        rel=1e-15)


@pytest.mark.parametrize("c1,c0", [(5.0e-15, 3.0e-12), (1.0e-14, 1.0e-12),
                                   (2.0e-15, 8.0e-12), (1.0e-13, 1.0e-13)])
def test_the_parallel_resonance_is_always_above_the_series_one(c1, c0):
    branch = MM.BVDBranch.planted(fs_hz=13.0e6, c1_f=c1, c0_f=c0)
    fs = branch.series_resonance_hz()
    fp = branch.parallel_resonance_hz()
    assert fp > fs
    assert fp == pytest.approx(fs * math.sqrt(1.0 + c1 / c0), rel=1e-15)
    assert branch.pole_zero_spacing_hz() > 0.0


def test_the_two_quality_factor_forms_agree_on_a_consistent_branch():
    branch = MM.BVDBranch.planted()
    fs = branch.series_resonance_hz()
    assert branch.quality_factor() == pytest.approx(
        1.0 / (2.0 * math.pi * fs * branch.c1_f * branch.r1_ohm), rel=1e-12)
    assert branch.quality_factor() == pytest.approx(
        branch.quality_factor_from_inductance(), rel=1e-9)


def test_the_quality_factor_rises_as_the_motional_resistance_falls():
    values = [MM.BVDBranch.planted(r1_ohm=r).quality_factor()
              for r in (64.0, 32.0, 16.0, 8.0, 4.0)]
    assert all(b > a for a, b in zip(values, values[1:]))
    assert values[-1] == pytest.approx(16.0 * values[0], rel=1e-12)


def test_a_non_passive_bvd_branch_is_refused():
    with pytest.raises(MM.ModeMixError):
        MM.BVDBranch(r1_ohm=0.0, l1_h=1.0, c1_f=1e-15, c0_f=1e-12)
    with pytest.raises(MM.ModeMixError):
        MM.BVDBranch(r1_ohm=8.0, l1_h=-1.0, c1_f=1e-15, c0_f=1e-12)
    with pytest.raises(MM.ModeMixError):
        MM.bvd_series_resonance_hz(0.0, 1e-15)
    with pytest.raises(MM.ModeMixError):
        MM.bvd_quality_factor(13.0e6, 1e-15, 0.0)


def test_a_spurious_branch_hybridises_with_the_main_response():
    branch = MM.BVDBranch.planted()
    split = MM.bvd_hybridisation(branch, 13.01e6, coupling_hz=3.0e3)
    assert split.splitting >= 2.0 * 3.0e3
    assert split.participation.sum(axis=1) == pytest.approx(np.ones(2),
                                                            abs=1e-12)


# --- (6) adapter D: optical cavity transverse modes ----------------------

def test_transverse_mode_frequencies_rise_with_transverse_order():
    cavity = MM.OpticalCavity()
    modes = [MM.CavityMode(100000, n, 0) for n in range(4)]
    freqs = [cavity.mode_frequency_hz(m) for m in modes]
    assert all(b > a for a, b in zip(freqs, freqs[1:]))
    steps = np.diff(freqs)
    assert steps == pytest.approx(
        cavity.transverse_spacing_hz * np.ones(3), rel=1e-9)


def test_degenerate_transverse_modes_are_degenerate_until_astigmatism():
    cavity = MM.OpticalCavity()
    a, b = MM.CavityMode(100000, 1, 0), MM.CavityMode(100000, 0, 1)
    assert cavity.mode_frequency_hz(a) == pytest.approx(
        cavity.mode_frequency_hz(b), rel=1e-15)
    assert cavity.astigmatic_split_hz(a, 1.0e-3) != 0.0
    assert cavity.astigmatic_split_hz(MM.CavityMode(100000, 1, 1),
                                      1.0e-3) == 0.0


def test_the_misalignment_overlap_is_zero_when_aligned_and_grows():
    cavity = MM.OpticalCavity()
    assert cavity.misalignment_overlap(0.0, 0.0) == 0.0
    tilts = [cavity.misalignment_overlap(0.0, t)
             for t in (0.0, 1e-4, 2e-4, 4e-4)]
    assert all(b > a for a, b in zip(tilts, tilts[1:]))
    shifts = [cavity.misalignment_overlap(d, 0.0)
              for d in (0.0, 1e-5, 5e-5, 1e-4)]
    assert all(b > a for a, b in zip(shifts, shifts[1:]))
    with pytest.raises(MM.ModeMixError):
        cavity.misalignment_overlap(displacement_m=1.0)


def test_misalignment_coupling_hybridises_two_transverse_modes():
    cavity = MM.OpticalCavity()
    aligned = MM.optical_hybridisation(cavity, MM.CavityMode(100000, 1, 0),
                                       MM.CavityMode(100000, 0, 0))
    mixed = MM.optical_hybridisation(cavity, MM.CavityMode(100000, 1, 0),
                                     MM.CavityMode(100000, 0, 0),
                                     displacement_m=1.0e-4)
    assert aligned.coupling == 0.0
    assert mixed.coupling > 0.0
    assert mixed.splitting > aligned.splitting


def test_a_malformed_cavity_or_mode_is_refused():
    with pytest.raises(MM.ModeMixError):
        MM.OpticalCavity(gouy_phase_rad=0.0)
    with pytest.raises(MM.ModeMixError):
        MM.OpticalCavity(fsr_hz=-1.0)
    with pytest.raises(MM.ModeMixError):
        MM.CavityMode(100000, -1, 0)


# --- (7) adapter E: the dynamic-boundary Bogoliubov lane -----------------

def test_the_bogoliubov_identity_holds():
    for r in (0.0, 0.2, 0.9, 2.0):
        alpha, beta = MM.bogoliubov_pair(r)
        assert alpha ** 2 - beta ** 2 == pytest.approx(1.0, abs=1e-12)


def test_the_created_photon_number_is_sinh_squared():
    out = MM.dynamic_boundary_hybridisation(r=0.6)
    assert out["mean_photon_number"] == pytest.approx(math.sinh(0.6) ** 2,
                                                      rel=1e-12)
    assert out["bogoliubov_defect"] == pytest.approx(0.0, abs=1e-12)
    assert out["hermitian_part_conserves_photon_number"] is True
    assert out["squeeze_part_conserves_photon_number"] is False


def test_a_squeeze_is_not_a_rotation():
    """Same 2x2 shape, same unit determinant, different invariant."""
    out = MM.rotation_versus_squeeze(0.4)
    assert out["rotation_determinant"] == pytest.approx(1.0, abs=1e-12)
    assert out["squeeze_determinant"] == pytest.approx(1.0, abs=1e-12)
    assert out["rotation_preserves_sum_of_squares"] is True
    assert out["squeeze_preserves_sum_of_squares"] is False
    assert out["squeeze_preserves_indefinite_form"] is True
    assert out["squeeze_sum_of_squares"] > 1.0


# --- (8) the load-bearing refusals ---------------------------------------

@pytest.mark.parametrize("src,dst", DOMAIN_PAIRS)
def test_cross_domain_transfer_is_refused_for_every_ordered_pair(src, dst):
    assert src is not dst
    with pytest.raises(MM.ModeMixError) as excinfo:
        MM.refuse_cross_domain_transfer(src, dst)
    message = str(excinfo.value)
    assert src.value in message and dst.value in message
    assert "CROSS_DOMAIN_TRANSFER_REFUSED" in message


@pytest.mark.parametrize("domain", list(MM.Domain))
def test_a_domain_may_speak_about_itself(domain):
    assert MM.refuse_cross_domain_transfer(domain, domain) is None


def test_the_canonical_attack_names_the_quartz_lattice():
    src, dst = MM.CANONICAL_CROSS_DOMAIN_ATTACK
    with pytest.raises(MM.ModeMixError) as excinfo:
        MM.refuse_cross_domain_transfer(src, dst)
    message = str(excinfo.value).lower()
    assert "trigonal" in message
    assert "sio2" in message
    assert "27" in message


def test_a_non_domain_argument_is_refused_rather_than_waved_through():
    with pytest.raises(MM.ModeMixError):
        MM.refuse_cross_domain_transfer("ATOMIC_LATTICE_PHONON",
                                        MM.Domain.BVD_ELECTRICAL)


def test_shared_math_is_refused_as_shared_mechanism():
    with pytest.raises(MM.ModeMixError):
        MM.refuse_shared_math_as_shared_mechanism()
    with pytest.raises(MM.ModeMixError) as excinfo:
        MM.refuse_shared_math_as_shared_mechanism(
            MM.Domain.ATOMIC_LATTICE_PHONON, MM.Domain.BVD_ELECTRICAL,
            "both are 2x2 so both are the same effect")
    assert "SHARED_ALGEBRA_IS_NOT_SHARED_MECHANISM" in str(excinfo.value)


def test_modal_truncation_is_refused_as_a_physical_cut():
    with pytest.raises(MM.ModeMixError):
        MM.refuse_modal_truncation_as_physical_cut()
    with pytest.raises(MM.ModeMixError) as excinfo:
        MM.refuse_modal_truncation_as_physical_cut(
            3, 27, "the discarded phonons were cut out of the crystal")
    message = str(excinfo.value)
    assert "MODAL_TRUNCATION_IS_NUMERICAL_NOT_PHYSICAL" in message
    assert "NUMERICAL" in message


@pytest.mark.parametrize("src,dst", DOMAIN_PAIRS)
def test_cross_unit_comparison_is_refused(src, dst):
    with pytest.raises(MM.ModeMixError) as excinfo:
        MM.refuse_unit_comparison(src, dst, 4000.0, 4000.0)
    assert "UNIT_COMPARISON_REFUSED" in str(excinfo.value)


@pytest.mark.parametrize("domain", list(MM.Domain))
def test_comparison_within_one_unit_system_is_arithmetic(domain):
    assert MM.refuse_unit_comparison(domain, domain, 1.0, 2.0) is None


# --- (9) the report -------------------------------------------------------

def test_the_report_measures_nothing_and_carries_the_verdict():
    r = MM.modemix_report()
    assert r["measured_here"] == "nothing"
    assert r["verdict"] == "MODE_MIXING_DOMAINS_TYPED_NOT_INTERCHANGEABLE"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["what_this_does_not_say"]
    assert r["evidence_class"] == "DERIVED_MATHEMATICS"


def test_the_report_declares_a_registered_claim_class():
    r = MM.modemix_report()
    assert r["claim_class"] == "REPOSITORY_COMPUTATIONAL_RESULT"
    assert r["claim_class"] in MM.CLAIM_CLASSES
    assert r["verdict"] in r["verdicts"]


def test_the_report_carries_every_domain_with_its_own_typing():
    r = MM.modemix_report()
    assert set(r["domains"]) == {d.value for d in MM.Domain}
    for domain in MM.Domain:
        entry = r["domains"][domain.value]
        assert entry["units"] and entry["source"]
        assert entry["does_not_license"]
        assert entry["source_class"] in MM.CLAIM_CLASSES
        assert r["hybridisations"][domain.value]["measured_here"] == "nothing"
    assert r["units_are_distinct"] is True
    assert r["sources_are_distinct"] is True


def test_the_report_states_the_avoided_crossing_result():
    r = MM.modemix_report()
    crossing = r["the_avoided_crossing"]
    assert crossing["minimum_matches_twice_the_coupling"] is True
    assert crossing["minimum_splitting"] == pytest.approx(
        2.0 * abs(crossing["coupling"]), rel=1e-12)
    assert crossing["mixing_angle_at_zero_detuning_deg"] == pytest.approx(
        45.0, abs=1e-12)
    assert crossing["branches_never_cross"] is True


def test_the_report_is_public_safe():
    blob = json.dumps(MM.modemix_report()).lower()
    for token in ("c:\\", "c:/", "onedrive", "users\\", "users/"):
        assert token not in blob
