"""P04 — handedness, optical rotation, magnetochiral parity.

The parity tests exercise all five outcomes of the four-cell design,
including the two that are refusals of a finding. The amorphous refusal
is asserted to raise, not to return a default.
"""

from __future__ import annotations

import math
import pathlib

import pytest

import r6
from r6 import chirality as ch


# --- specimen ------------------------------------------------------------

def test_space_groups_are_the_enantiomorphic_pair():
    assert ch.SPACE_GROUP_BY_HANDEDNESS["LEFT"] == "P3121"
    assert ch.SPACE_GROUP_BY_HANDEDNESS["RIGHT"] == "P3221"


def test_space_group_assignment_is_declared_conventional():
    """The literature genuinely conflicts; the module must say so."""
    note = ch.SPACE_GROUP_CONVENTION_NOTE
    assert "CONVENTIONAL, NOT MEASURED" in note
    assert "disagree" in note
    assert "diffraction" in note
    assert ch.QuartzSpecimen("LEFT").space_group_note() == note


def test_specimen_defaults_follow_the_declared_convention():
    left = ch.QuartzSpecimen("LEFT", length_m=0.01)
    right = ch.QuartzSpecimen("RIGHT", length_m=0.01)
    assert left.space_group == "P3121"
    assert right.space_group == "P3221"
    assert left.chi == -1 and right.chi == +1
    assert left.specific_rotation_deg_per_mm == pytest.approx(
        -right.specific_rotation_deg_per_mm)


def test_specimen_refuses_an_unknown_handedness():
    with pytest.raises(ch.ChiralityModelError):
        ch.QuartzSpecimen("AMBIDEXTROUS")


def test_opposite_flips():
    assert ch.opposite("LEFT") == "RIGHT"
    assert ch.opposite("RIGHT") == "LEFT"
    with pytest.raises(ch.ChiralityModelError):
        ch.opposite("NEITHER")


# --- optical rotation ----------------------------------------------------

def test_sodium_d_rotatory_power_is_the_literature_21_7_per_mm():
    assert ch.rotatory_power_deg_per_mm(589.3) == pytest.approx(21.72)
    assert ch.ROTATORY_POWER_589_DEG_PER_MM == 21.72


def test_one_millimetre_of_right_quartz_rotates_about_21_7_degrees():
    a = ch.optical_rotation_deg(1e-3, 589.3, "RIGHT")
    assert a == pytest.approx(21.72, rel=1e-12)


def test_optical_rotation_sign_flips_with_handedness():
    """The exact, load-bearing symmetry of this module."""
    for wl in (404.7, 508.6, 589.3, 656.3, 500.0, 620.0):
        r = ch.optical_rotation_deg(2.5e-3, wl, "RIGHT")
        l = ch.optical_rotation_deg(2.5e-3, wl, "LEFT")
        assert r > 0.0 > l
        assert r == pytest.approx(-l, rel=1e-15)


def test_optical_rotation_is_linear_in_thickness():
    a1 = ch.optical_rotation_deg(1e-3, 589.3, "RIGHT")
    a3 = ch.optical_rotation_deg(3e-3, 589.3, "RIGHT")
    assert a3 == pytest.approx(3 * a1, rel=1e-12)
    assert ch.optical_rotation_deg(0.0, 589.3, "RIGHT") == 0.0


def test_dispersion_reproduces_every_tabulated_point():
    for wl, rho in ch.ROTATORY_DISPERSION_DEG_PER_MM.items():
        assert ch.rotatory_power_deg_per_mm(wl) == pytest.approx(rho,
                                                                rel=1e-12)


def test_dispersion_is_monotonic_blue_rotates_more_than_red():
    vals = [ch.rotatory_power_deg_per_mm(w)
            for w in (404.7, 450.0, 508.6, 589.3, 656.3)]
    assert vals == sorted(vals, reverse=True)
    assert vals[0] > 2 * vals[-1]


def test_dispersion_refuses_to_extrapolate_outside_the_table():
    for wl in (300.0, 404.0, 700.0, 1064.0):
        with pytest.raises(ch.ChiralityModelError, match="refuses to extrapolate"):
            ch.rotatory_power_deg_per_mm(wl)


def test_negative_thickness_refused():
    with pytest.raises(ch.ChiralityModelError):
        ch.optical_rotation_deg(-1e-3, 589.3, "RIGHT")


# --- handedness inference ------------------------------------------------

def test_handedness_from_rotation_sign():
    assert ch.handedness_from_rotation(+21.7) == "RIGHT"
    assert ch.handedness_from_rotation(-21.7) == "LEFT"
    assert ch.handedness_from_rotation(1e-9) == "RIGHT"


def test_handedness_round_trips_through_the_rotation_model():
    for hand in ("LEFT", "RIGHT"):
        rot = ch.optical_rotation_deg(1e-3, 589.3, hand)
        assert ch.handedness_from_rotation(rot) == hand


def test_zero_rotation_is_a_failed_measurement_not_a_third_handedness():
    with pytest.raises(ch.ChiralityModelError, match="failed or ambiguous"):
        ch.handedness_from_rotation(0.0)


# --- amorphous refusal ---------------------------------------------------

@pytest.mark.parametrize("material", [
    "fused silica",
    "Fused Quartz",
    "amorphous SiO2",
    "silica glass",
    "vitreous silica",
    "quartz glass",
    "  FUSED   SILICA  ",
    "fused-silica window",
])
def test_refuses_handedness_for_amorphous_silica(material):
    with pytest.raises(ch.ChiralityRefusal, match="amorphous"):
        ch.refuse_chirality_of_amorphous(material)


def test_refusal_explains_that_the_question_has_no_referent():
    with pytest.raises(ch.ChiralityRefusal) as exc:
        ch.refuse_chirality_of_amorphous("fused silica")
    msg = str(exc.value)
    assert "no referent" in msg
    assert "not racemic" in msg


@pytest.mark.parametrize("material", [
    "alpha-quartz", "crystalline SiO2", "natural quartz crystal",
])
def test_crystalline_materials_pass_the_refusal_gate(material):
    assert ch.refuse_chirality_of_amorphous(material)


def test_refusal_gate_rejects_an_empty_material():
    with pytest.raises(ch.ChiralityModelError):
        ch.refuse_chirality_of_amorphous("   ")


# --- magnetochiral model -------------------------------------------------

def _cfg(hand="RIGHT", sign=+1, gamma=1e-6, b=1.0, **kw):
    return ch.MagnetochiralConfig(hand, b, sign, gamma, **kw)


def test_absorbance_follows_the_stated_model():
    c = _cfg(gamma=1e-3, b=2.0)
    # A = A0 (1 + gamma B (k.B sign) chi), chi=+1
    assert c.absorbance() == pytest.approx(1.0 * (1 + 1e-3 * 2.0))


def test_anisotropy_is_two_gamma_b_chi():
    right = ch.magnetochiral_anisotropy(_cfg("RIGHT", gamma=1e-6, b=3.0))
    left = ch.magnetochiral_anisotropy(_cfg("LEFT", gamma=1e-6, b=3.0))
    assert right["fractional_anisotropy"] == pytest.approx(2 * 1e-6 * 3.0)
    assert left["fractional_anisotropy"] == pytest.approx(
        -right["fractional_anisotropy"])


def test_double_reversal_restores_the_modeled_absorbance():
    c = _cfg("RIGHT", +1, gamma=1e-4)
    both = c.reversed_field().reversed_handedness()
    assert both.absorbance() == pytest.approx(c.absorbance(), rel=1e-15)
    assert both.handedness == "LEFT" and both.k_dot_b_sign == -1
    # a single reversal must NOT restore it
    assert c.reversed_field().absorbance() != pytest.approx(c.absorbance())


def test_anisotropy_flags_a_prediction_larger_than_anything_measured():
    rec = ch.magnetochiral_anisotropy(_cfg(gamma=1e-1, b=1.0))
    assert rec["regime"] == "IMPLAUSIBLY_LARGE_CHECK_GAMMA"
    assert "assumed rather than sourced" in rec["note"]


def test_anisotropy_flags_a_prediction_below_anything_resolved():
    rec = ch.magnetochiral_anisotropy(_cfg(gamma=1e-12, b=1.0))
    assert rec["regime"] == "BELOW_ANYTHING_EVER_RESOLVED"
    assert "can claim to detect this" in rec["note"]


def test_anisotropy_reports_the_literature_range_honestly():
    rec = ch.magnetochiral_anisotropy(_cfg(gamma=1e-6, b=1.0))
    assert rec["regime"] == "WITHIN_MEASURED_LITERATURE_RANGE"
    assert rec["literature_measured_range"] == (1e-9, 1e-4)
    assert rec["gamma_is_an_assumption"] is True
    assert rec["not_bench_data"] is True


def test_required_sensitivity_states_resolution_and_averaging():
    c = _cfg(gamma=1e-6, b=1.0, instrument_fractional_noise=1e-5)
    req = ch.required_sensitivity(c, target_snr=5.0)
    g = 2e-6
    assert req["required_fractional_resolution"] == pytest.approx(g / 5.0)
    assert req["required_averages"] == pytest.approx((1e-5 * 5.0 / g) ** 2)
    assert req["single_shot_sufficient"] is False


def test_required_sensitivity_reports_an_absurd_averaging_count_honestly():
    c = _cfg(gamma=1e-12, b=1.0, instrument_fractional_noise=1e-5)
    req = ch.required_sensitivity(c)
    assert req["required_averages"] > 1e9
    assert req["feasible_within_1e9_averages"] is False
    assert "NECESSARY" in req["note"]


def test_required_sensitivity_refuses_nonpositive_snr():
    with pytest.raises(ch.ChiralityModelError):
        ch.required_sensitivity(_cfg(), target_snr=0.0)


def test_config_rejects_bad_inputs():
    with pytest.raises(ch.ChiralityModelError):
        ch.MagnetochiralConfig("RIGHT", 1.0, 0, 1e-6)
    with pytest.raises(ch.ChiralityModelError):
        ch.MagnetochiralConfig("RIGHT", -1.0, 1, 1e-6)
    with pytest.raises(ch.ChiralityModelError):
        ch.MagnetochiralConfig("SIDEWAYS", 1.0, 1, 1e-6)


# --- THE FOUR-CELL PARITY TEST: all five outcomes ------------------------

def test_parity_matrix_is_the_four_cell_design():
    m = ch.parity_test_matrix()
    assert m["cells"] == (("a", "LEFT", "UP"), ("b", "LEFT", "DOWN"),
                          ("c", "RIGHT", "UP"), ("d", "RIGHT", "DOWN"))
    assert "double reversal" in m["the_actual_test"].lower()
    assert set(m["outcomes"]) == set(ch.PARITY_OUTCOMES)


def test_parity_consistent_magnetochiral():
    """s0=1, g=0.1: a=d=1.1, b=c=0.9. Only the product contrast survives."""
    r = ch.classify_parity_result(1.1, 0.9, 0.9, 1.1)
    assert r["outcome"] == "PARITY_CONSISTENT_MAGNETOCHIRAL"
    assert r["product_contrast"] == pytest.approx(0.1)
    assert r["field_contrast"] == pytest.approx(0.0, abs=1e-12)
    assert r["enantiomer_contrast"] == pytest.approx(0.0, abs=1e-12)
    assert r["double_reversal_restores"] is True
    assert "not the same as demonstrating" in r["reason"]


def test_instrumental_offset_when_nothing_reverses():
    r = ch.classify_parity_result(1.0, 1.0, 1.0, 1.0)
    assert r["outcome"] == "INSTRUMENTAL_OFFSET"
    assert r["mean"] == pytest.approx(1.0)


def test_instrumental_offset_when_contrasts_are_below_stated_noise():
    r = ch.classify_parity_result(1.001, 0.999, 0.999, 1.001, noise=0.01)
    assert r["outcome"] == "INSTRUMENTAL_OFFSET"


def test_enantiomer_only_is_a_difference_between_two_rocks():
    # LEFT reads 1.2 in both fields, RIGHT reads 0.8 in both.
    r = ch.classify_parity_result(1.2, 1.2, 0.8, 0.8)
    assert r["outcome"] == "ENANTIOMER_ONLY"
    assert r["enantiomer_contrast"] == pytest.approx(0.2)
    assert "two pieces of rock" in r["reason"]


def test_field_only_is_the_magnet_acting_on_the_instrument():
    # B up reads 1.2 for both specimens, B down reads 0.8 for both.
    r = ch.classify_parity_result(1.2, 0.8, 1.2, 0.8)
    assert r["outcome"] == "FIELD_ONLY"
    assert r["field_contrast"] == pytest.approx(0.2)
    assert "instrument" in r["reason"]


def test_inconsistent_when_contrasts_are_mixed():
    r = ch.classify_parity_result(1.4, 1.0, 0.8, 1.0)
    assert r["outcome"] == "INCONSISTENT"
    assert sum(r["contrast_present"].values()) > 1
    assert "Fix the experiment" in r["reason"]


def test_all_five_outcomes_are_reachable():
    seen = {
        ch.classify_parity_result(1.1, 0.9, 0.9, 1.1)["outcome"],
        ch.classify_parity_result(1.0, 1.0, 1.0, 1.0)["outcome"],
        ch.classify_parity_result(1.2, 1.2, 0.8, 0.8)["outcome"],
        ch.classify_parity_result(1.2, 0.8, 1.2, 0.8)["outcome"],
        ch.classify_parity_result(1.4, 1.0, 0.8, 1.0)["outcome"],
    }
    assert seen == set(ch.PARITY_OUTCOMES)


def test_parity_classification_is_scale_free_in_the_baseline():
    """A tiny real effect on a large baseline must not be swallowed."""
    g = 1e-6
    r = ch.classify_parity_result(100 + g, 100 - g, 100 - g, 100 + g)
    assert r["outcome"] == "PARITY_CONSISTENT_MAGNETOCHIRAL"


def test_parity_classification_refuses_bad_arguments():
    with pytest.raises(ch.ChiralityModelError):
        ch.classify_parity_result(1.0, 1.0, 1.0, math.nan)
    with pytest.raises(ch.ChiralityModelError):
        ch.classify_parity_result(1.1, 0.9, 0.9, 1.1, tol=0.0)
    with pytest.raises(ch.ChiralityModelError):
        ch.classify_parity_result(1.1, 0.9, 0.9, 1.1, noise=-1.0)


def test_parity_result_carries_a_ceiling():
    r = ch.classify_parity_result(1.1, 0.9, 0.9, 1.1)
    assert "not detection" in r["ceiling"]
    assert r["evidence_class"] in r6.PHRYLL_CLASSES


# --- claim-language guards ----------------------------------------------

def test_module_names_no_forbidden_state():
    text = pathlib.Path(ch.__file__).read_text(encoding="utf-8")
    for state in r6.FORBIDDEN_STATES:
        assert state not in text, f"{state} must never appear in R6"


def test_module_declares_it_holds_no_bench_data():
    assert "NOTHING IN THIS MODULE IS BENCH DATA" in ch.__doc__
