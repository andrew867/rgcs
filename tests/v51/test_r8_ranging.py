"""P12 — phase ranging and recursive addressing.

Two things are checked harder than the rest: that the module never
lets a range out while the integer ambiguity is open, and that its
wide-lane function admits in its own docstring that the technique is
textbook prior art. The second is not a style check. A repository that
reimplements a 1985 GNSS result without saying so has claimed it, and
the only durable place to prevent that is a test.
"""

from __future__ import annotations

import pytest

from r6.mailbox import KEY_RADIX, KeyPath
from r8 import ranging


#: The real GPS carriers, used because their wide-lane is a number a
#: reader can check against any GNSS textbook (~0.862 m).
L1_HZ = 1_575.42e6
L2_HZ = 1_227.60e6


@pytest.fixture
def l1():
    return ranging.wavelength_from_frequency(L1_HZ)


@pytest.fixture
def l2():
    return ranging.wavelength_from_frequency(L2_HZ)


# --- wavelength --------------------------------------------------------

def test_wavelength_is_c_over_f(l1):
    assert l1 == pytest.approx(ranging.C / L1_HZ, rel=1e-15)
    assert l1 == pytest.approx(0.1903, abs=1e-4)


def test_medium_velocity_factor_changes_the_wavelength():
    """A thirty percent error if c is used inside coax."""
    vac = ranging.wavelength_from_frequency(100e6)
    coax = ranging.wavelength_from_frequency(
        100e6, propagation_speed_m_s=0.66 * ranging.C)
    assert coax == pytest.approx(0.66 * vac)


def test_wavelength_rejects_nonpositive_inputs():
    with pytest.raises(ValueError):
        ranging.wavelength_from_frequency(0.0)
    with pytest.raises(ValueError):
        ranging.wavelength_from_frequency(1e6,
                                          propagation_speed_m_s=0.0)


# --- range from phase --------------------------------------------------

def test_range_is_n_plus_phi_times_lambda(l1):
    rec = ranging.range_from_phase(0.25, l1, 100)
    assert rec["range_m"] == pytest.approx((100 + 0.25) * l1)
    assert rec["integer_part_m"] == pytest.approx(100 * l1)
    assert rec["fractional_part_m"] == pytest.approx(0.25 * l1)


def test_wrong_n_shifts_the_range_by_whole_wavelengths(l1):
    a = ranging.range_from_phase(0.4, l1, 100)["range_m"]
    b = ranging.range_from_phase(0.4, l1, 103)["range_m"]
    assert b - a == pytest.approx(3 * l1)


def test_round_trip_path_halves_the_range(l1):
    one = ranging.range_from_phase(0.4, l1, 100)["range_m"]
    two = ranging.range_from_phase(0.4, l1, 100,
                                   path_factor=2.0)["range_m"]
    assert two == pytest.approx(one / 2.0)


def test_range_states_that_n_is_unresolved(l1):
    rec = ranging.range_from_phase(0.0, l1, 0)
    assert "N is NOT determined by this measurement" in rec["statement"]
    assert "modulo one wavelength" in rec["statement"]
    assert rec["ambiguity_source"] == "SUPPLIED_BY_CALLER"
    assert rec["what_would_resolve_it"].strip()


def test_unwrapped_phase_is_refused_rather_than_folded(l1):
    """1.5 cycles means the caller already folded in an integer."""
    with pytest.raises(ValueError):
        ranging.range_from_phase(1.5, l1, 0)
    with pytest.raises(ValueError):
        ranging.range_from_phase(-0.1, l1, 0)
    # the boundary: 1.0 belongs to the next integer, not this fraction
    with pytest.raises(ValueError):
        ranging.range_from_phase(1.0, l1, 0)


def test_non_integer_ambiguity_is_a_type_error(l1):
    with pytest.raises(TypeError):
        ranging.range_from_phase(0.5, l1, 100.0)
    with pytest.raises(TypeError):
        ranging.range_from_phase(0.5, l1, True)


def test_negative_ambiguity_and_bad_geometry_refused(l1):
    with pytest.raises(ValueError):
        ranging.range_from_phase(0.5, l1, -1)
    with pytest.raises(ValueError):
        ranging.range_from_phase(0.5, 0.0, 1)
    with pytest.raises(ValueError):
        ranging.range_from_phase(0.5, l1, 1, path_factor=0.0)


# --- ambiguity set -----------------------------------------------------

def test_candidate_count_is_window_over_wavelength_plus_one():
    rec = ranging.ambiguity_set(0.5, 10.0)
    assert rec["candidates"] == 21
    assert rec["spacing_m"] == 0.5


def test_candidates_scale_linearly_with_the_window():
    a = ranging.ambiguity_set(0.2, 100.0)["candidates"]
    b = ranging.ambiguity_set(0.2, 1_000.0)["candidates"]
    assert b == pytest.approx(10 * a, rel=0.01)
    assert b > a


def test_candidates_scale_inversely_with_wavelength():
    short = ranging.ambiguity_set(0.1, 100.0)["candidates"]
    long_ = ranging.ambiguity_set(1.0, 100.0)["candidates"]
    assert short == pytest.approx(10 * long_, rel=0.02)
    assert short > long_


def test_a_window_shorter_than_a_wavelength_leaves_one_candidate():
    rec = ranging.ambiguity_set(1.0, 0.5)
    assert rec["candidates"] == 1
    assert rec["resolved"]
    assert rec["status"] == "AMBIGUITY_BOUNDED_BY_WINDOW"
    # and it must not pretend that is a measurement result
    assert "assumption about the geometry" in rec["statement"]


def test_realistic_gps_window_is_hopelessly_ambiguous(l1):
    rec = ranging.ambiguity_set(l1, 1_000.0)
    assert rec["candidates"] > 5_000
    assert rec["status"] == "AMBIGUITY_UNRESOLVED"


def test_ambiguity_set_rejects_bad_geometry():
    with pytest.raises(ValueError):
        ranging.ambiguity_set(0.0, 10.0)
    with pytest.raises(ValueError):
        ranging.ambiguity_set(0.1, -1.0)


def test_ambiguity_set_mirrors_the_r3_alias_audit():
    """Same shape as r3.root_space.zero_residual_aliases, on purpose."""
    from r3 import root_space
    aliases = root_space.zero_residual_aliases(10.0, 1.0)
    ours = ranging.ambiguity_set(0.1, 1.0)
    assert aliases["zero_residual_candidates"] == ours["candidates"]
    for key in ("statement", "status", "evidence_class"):
        assert key in ours and key in aliases


# --- dual-wavelength thinning ------------------------------------------

def test_beat_wavelength_matches_the_gnss_wide_lane(l1, l2):
    rec = ranging.dual_wavelength_thinning(l1, l2, 1_000.0)
    assert rec["beat_wavelength_m"] == pytest.approx(0.8619, abs=1e-3)
    assert rec["beat_wavelength_m"] > max(l1, l2)


def test_thinning_reduces_the_candidate_count(l1, l2):
    rec = ranging.dual_wavelength_thinning(l1, l2, 1_000.0)
    assert rec["surviving_candidates"] < rec["candidates_l1"]
    assert rec["surviving_candidates"] < rec["candidates_l2"]
    assert rec["thinning_factor"] > 1.0


def test_thinning_agrees_with_an_independent_ambiguity_set(l1, l2):
    rec = ranging.dual_wavelength_thinning(l1, l2, 1_000.0)
    direct = ranging.ambiguity_set(rec["beat_wavelength_m"], 1_000.0)
    assert rec["surviving_candidates"] == direct["candidates"]


def test_thinning_still_leaves_the_range_ambiguous_over_a_km(l1, l2):
    """Wide-laning helps and does not finish the job."""
    rec = ranging.dual_wavelength_thinning(l1, l2, 1_000.0)
    assert not rec["resolved_within_window"]
    assert rec["surviving_candidates"] > 1


def test_thinning_resolves_a_small_enough_window(l1, l2):
    rec = ranging.dual_wavelength_thinning(l1, l2, 0.5)
    assert rec["resolved_within_window"]
    assert rec["surviving_candidates"] == 1


def test_docstring_admits_the_technique_is_textbook_prior_art():
    # normalised, because the claim must survive line wrapping
    doc = " ".join(ranging.dual_wavelength_thinning.__doc__.split())
    assert "NOT NOVEL" in doc
    assert "RGCS did not invent it" in doc
    assert "wide-lane" in doc
    # and it must cite something a reader can look up
    assert "Melbourne" in doc and "1985" in doc
    assert "Teunissen" in doc or "LAMBDA" in doc


def test_record_declares_no_novelty_and_names_the_prior_art(l1, l2):
    rec = ranging.dual_wavelength_thinning(l1, l2, 100.0)
    assert rec["novelty"] == "NONE_TEXTBOOK_PRIOR_ART"
    assert "Wuebbena" in rec["prior_art"]
    assert "Melbourne" in rec["prior_art"]


def test_the_noise_tradeoff_is_reported_not_hidden(l1, l2):
    rec = ranging.dual_wavelength_thinning(l1, l2, 100.0)
    assert rec["noise_amplification"] > 1.0
    assert rec["noise_amplification"] == pytest.approx(
        rec["beat_wavelength_m"] / min(l1, l2))
    assert "noisier" in rec["tradeoff"]


def test_identical_wavelengths_are_refused(l1):
    with pytest.raises(ranging.RangeRefused):
        ranging.dual_wavelength_thinning(l1, l1, 100.0)


def test_thinning_rejects_bad_geometry(l1, l2):
    with pytest.raises(ValueError):
        ranging.dual_wavelength_thinning(0.0, l2, 100.0)
    with pytest.raises(ValueError):
        ranging.dual_wavelength_thinning(l1, l2, -1.0)


# --- recursive addressing ----------------------------------------------

def test_address_interval_narrows_by_the_radix_each_level():
    root = 1.0e6
    widths = [
        ranging.recursive_address_to_range(
            KeyPath(tuple([1] * d)), root)["width_m"]
        for d in (1, 2, 3)]
    assert widths[1] == pytest.approx(widths[0] / KEY_RADIX)
    assert widths[2] == pytest.approx(widths[1] / KEY_RADIX)


def test_interval_start_is_the_accumulated_key_offset():
    root = 4096.0 ** 2
    rec = ranging.recursive_address_to_range(KeyPath((2, 3)), root)
    assert rec["start_m"] == pytest.approx(
        2 * root / 4096 + 3 * root / 4096 ** 2)
    assert rec["interval"]["end_m"] == pytest.approx(
        rec["start_m"] + rec["width_m"])
    assert rec["centre_m"] == pytest.approx(
        rec["start_m"] + rec["width_m"] / 2)


def test_interval_stays_inside_the_root_cell():
    root = 1.0e6
    rec = ranging.recursive_address_to_range(
        KeyPath((KEY_RADIX - 1, KEY_RADIX - 1)), root)
    assert 0.0 <= rec["start_m"]
    assert rec["interval"]["end_m"] <= root


def test_uncertainty_accumulates_and_never_shrinks_with_depth():
    root = 1.0e6
    sigmas = [
        ranging.recursive_address_to_range(
            KeyPath(tuple([1] * d)), root)["uncertainty_m"]
        for d in range(1, 6)]
    assert all(a <= b for a, b in zip(sigmas, sigmas[1:]))
    assert sigmas[-1] > sigmas[0]


def test_uncertainty_is_dominated_by_the_coarsest_level():
    rec = ranging.recursive_address_to_range(KeyPath((1, 2, 3, 4)), 1.0e6)
    levels = rec["levels"]
    assert rec["dominant_level"] == 1
    assert levels[0]["level_uncertainty_m"] == max(
        lv["level_uncertainty_m"] for lv in levels)
    # quadrature: the total barely exceeds the first term
    assert rec["uncertainty_m"] < 1.001 * levels[0]["level_uncertainty_m"]


def test_cumulative_uncertainty_is_a_quadrature_sum():
    rec = ranging.recursive_address_to_range(KeyPath((1, 2, 3)), 1.0e6)
    running = 0.0
    for lv in rec["levels"]:
        running += lv["level_uncertainty_m"] ** 2
        assert lv["cumulative_uncertainty_m"] == pytest.approx(
            running ** 0.5)
    assert rec["uncertainty_m"] == pytest.approx(
        rec["levels"][-1]["cumulative_uncertainty_m"])


def test_deep_addresses_are_finer_than_the_physics_supports():
    """The honest result: extra levels buy naming, not position."""
    rec = ranging.recursive_address_to_range(KeyPath((1, 2, 3)), 1.0e6)
    assert rec["address_finer_than_physics"]
    assert rec["width_m"] < rec["uncertainty_m"]
    assert rec["depth_beyond_useful"] > 0
    assert "no physical precision" in rec["statement"]


def test_a_clean_chain_keeps_every_level_meaningful():
    """With small enough per-level error the levels do carry meaning."""
    rec = ranging.recursive_address_to_range(
        KeyPath((1, 2)), 1.0e6, per_level_uncertainty_frac=1e-12)
    assert not rec["address_finer_than_physics"]
    assert rec["useful_depth"] == rec["depth"]
    assert rec["depth_beyond_useful"] == 0


def test_zero_per_level_uncertainty_is_allowed_and_gives_zero():
    rec = ranging.recursive_address_to_range(
        KeyPath((1,)), 1.0, per_level_uncertainty_frac=0.0)
    assert rec["uncertainty_m"] == 0.0


def test_address_range_rejects_bad_inputs():
    with pytest.raises(TypeError):
        ranging.recursive_address_to_range((1, 2), 1.0e6)
    with pytest.raises(ValueError):
        ranging.recursive_address_to_range(KeyPath((1,)), 0.0)
    with pytest.raises(ValueError):
        ranging.recursive_address_to_range(KeyPath((1,)), 1.0, radix=1)
    with pytest.raises(ValueError):
        ranging.recursive_address_to_range(
            KeyPath((1,)), 1.0, per_level_uncertainty_frac=-1e-3)


# --- refusal -----------------------------------------------------------

def test_refusal_raises_with_no_evidence_at_all():
    with pytest.raises(ranging.RangeRefused):
        ranging.refuse_range_without_ambiguity_resolution()


def test_refusal_raises_when_candidates_survive(l1):
    with pytest.raises(ranging.RangeRefused):
        ranging.refuse_range_without_ambiguity_resolution(
            wavelength_m=l1, window_m=1_000.0)
    with pytest.raises(ranging.RangeRefused):
        ranging.refuse_range_without_ambiguity_resolution(
            surviving_candidates=7)


def test_refusal_message_names_the_surviving_count():
    with pytest.raises(ranging.RangeRefused) as exc:
        ranging.refuse_range_without_ambiguity_resolution(
            surviving_candidates=42)
    assert "42" in str(exc.value)


def test_refusal_passes_only_when_exactly_one_candidate_survives(l1):
    rec = ranging.refuse_range_without_ambiguity_resolution(
        wavelength_m=l1, window_m=0.05)
    assert rec["status"] == "AMBIGUITY_RESOLVED_WITHIN_WINDOW"
    assert rec["surviving_candidates"] == 1
    assert "assumption about the geometry" in rec["caveat"]


def test_a_wide_lane_resolved_window_passes_the_refusal(l1, l2):
    """End to end: thin, then check, then you may report a range."""
    thin = ranging.dual_wavelength_thinning(l1, l2, 0.5)
    ok = ranging.refuse_range_without_ambiguity_resolution(
        surviving_candidates=thin["surviving_candidates"])
    assert ok["surviving_candidates"] == 1
    rec = ranging.range_from_phase(0.5, thin["beat_wavelength_m"], 0)
    assert rec["range_m"] > 0


# --- evidence discipline -----------------------------------------------

def _every_record(l1, l2):
    yield ranging.range_from_phase(0.5, l1, 3)
    yield ranging.ambiguity_set(l1, 10.0)
    yield ranging.dual_wavelength_thinning(l1, l2, 10.0)
    yield ranging.recursive_address_to_range(KeyPath((1, 2)), 1.0e6)
    yield ranging.recursive_address_to_range(
        KeyPath((1, 2)), 1.0e6)["interval"]
    yield ranging.refuse_range_without_ambiguity_resolution(
        surviving_candidates=1)


def test_every_returned_record_carries_an_evidence_class(l1, l2):
    for rec in _every_record(l1, l2):
        assert rec["evidence_class"] in ("SYNTHETIC_MODEL",
                                         "DERIVED_ARITHMETIC")


def test_every_returned_record_states_no_measurement_was_taken(l1, l2):
    for rec in _every_record(l1, l2):
        assert rec["no_measurement_statement"] == ranging.NO_MEASUREMENT
        assert "No measurement has been taken" in \
            rec["no_measurement_statement"]
