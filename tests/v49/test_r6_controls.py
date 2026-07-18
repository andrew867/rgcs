"""P08 - material, environmental and orientation controls."""

from __future__ import annotations

import random

import pytest

from r6 import ORDINARY_CHANNELS
from r6 import controls as C


def _complete_design(**kw) -> dict:
    base = dict(
        materials=[m.material_id for m in C.MATERIAL_CONTROLS],
        sham_drive=True,
        randomized_order=True,
        blinding=list(C.REQUIRED_BLINDING),
    )
    base.update(kw)
    return base


# --- material registry ------------------------------------------------

def test_registry_has_no_duplicate_ids():
    assert len(C.material_registry()) == len(C.MATERIAL_CONTROLS)


def test_both_quartz_handednesses_are_present():
    hands = {m.crystal_handedness for m in C.specimens()}
    assert hands == {"left", "right"}


def test_the_enantiomer_is_the_parity_control():
    right = C.material_registry()["right_alpha_quartz"]
    assert right.role == "PARITY_CONTROL"
    assert any("handedness" in r for r in right.rules_out)


def test_empty_mount_control_is_present():
    """The control the whole design turns on."""
    m = C.empty_mount()
    assert m.material_id == "empty_mount"
    assert m.is_empty_mount
    assert not m.is_specimen
    assert m.role == "APPARATUS_CONTROL"


def test_empty_mount_rules_out_the_instrument_itself():
    assert any("apparatus" in r or "instrument" in r
               for r in C.empty_mount().rules_out)


def test_fused_silica_is_flagged_amorphous():
    fs = C.material_registry()["fused_silica"]
    assert fs.amorphous
    assert not fs.long_range_order
    assert not fs.piezoelectric
    assert fs.crystal_handedness == "none"


def test_a_nonpiezoelectric_crystal_control_exists():
    npc = [m for m in C.MATERIAL_CONTROLS
           if m.role == "PIEZOELECTRIC_CONTROL"]
    assert npc, "an ordered but non-piezoelectric crystal is required"
    for m in npc:
        assert m.long_range_order
        assert not m.piezoelectric


def test_metal_blank_is_a_fixture_control():
    mb = C.material_registry()["metal_blank"]
    assert mb.role == "FIXTURE_CONTROL"
    assert not mb.is_specimen


def test_specimens_and_controls_partition_the_registry():
    assert len(C.specimens()) + len(C.controls()) == len(C.MATERIAL_CONTROLS)


def test_a_control_must_rule_something_out():
    with pytest.raises(ValueError):
        C.MaterialControl(
            material_id="x", common_name="x", role="FIXTURE_CONTROL",
            long_range_order=False, local_tetrahedral_order="none",
            piezoelectric=False, crystal_handedness="none",
            control_property="nothing in particular", rules_out=())


def test_unknown_role_rejected():
    with pytest.raises(ValueError):
        C.MaterialControl(
            material_id="x", common_name="x", role="VIBES",
            long_range_order=False, local_tetrahedral_order="none",
            piezoelectric=False, crystal_handedness="none",
            control_property="p", rules_out=("q",))


def test_empty_mount_cannot_also_be_a_specimen():
    with pytest.raises(ValueError):
        C.MaterialControl(
            material_id="x", common_name="x", role="APPARATUS_CONTROL",
            long_range_order=False, local_tetrahedral_order="none",
            piezoelectric=False, crystal_handedness="none",
            control_property="p", rules_out=("q",),
            is_specimen=True, is_empty_mount=True)


def test_control_records_are_serializable():
    recs = C.control_records()
    assert len(recs) == len(C.MATERIAL_CONTROLS)
    assert all(isinstance(r["rules_out"], list) for r in recs)


# --- orientation: claim R6-C-003 --------------------------------------

def test_orientation_control_names_its_claim():
    assert C.OrientationControl().claim_id == "R6-C-003"


def test_sweep_covers_aligned_anti_orthogonal_and_random():
    sweep = C.OrientationControl().geomagnetic_sweep()
    roles = [o.role for o in sweep]
    assert "aligned" in roles
    assert "anti-aligned" in roles
    assert roles.count("orthogonal") >= 2, "two orthogonal axes required"
    assert "randomized" in roles


def test_orthogonal_conditions_are_two_distinct_axes():
    orth = [o for o in C.OrientationControl().geomagnetic_sweep()
            if o.orthogonal]
    assert len(orth) == 2
    assert orth[0].condition != orth[1].condition


def test_full_matrix_keeps_gravity_and_geomagnetic_separate():
    """core/05: the source blends the axes; R6 does not."""
    axes = {o.reference_axis for o in C.OrientationControl()
            .orientation_matrix()}
    assert "GEOMAGNETIC_FIELD_VECTOR" in axes
    assert "LOCAL_GRAVITY_PLUMB_VERTICAL" in axes
    assert "GEOGRAPHIC_NORTH" in axes


def test_every_condition_is_declared():
    for o in C.OrientationControl().orientation_matrix():
        assert o.condition in C.ORIENTATION_CONDITIONS


def test_undeclared_orientation_condition_rejected():
    with pytest.raises(ValueError):
        C.Orientation(condition="AXIS_TOWARD_THE_MOON",
                      reference_axis="GEOMAGNETIC_FIELD_VECTOR",
                      angle_to_reference_deg=0.0, role="aligned",
                      rationale="")


def test_randomized_condition_has_no_fixed_angle():
    r = [o for o in C.OrientationControl().geomagnetic_sweep()
         if o.randomized]
    assert len(r) == 1
    assert r[0].angle_to_reference_deg is None


def test_local_field_reference_states_the_microtesla_range():
    ref = C.OrientationControl().local_field_reference()
    lo, hi = ref["surface_range_microtesla"]
    assert (lo, hi) == (25.0, 65.0)
    assert ref["temporal_character"] == "QUASI_STATIC"


def test_local_field_reference_demands_exceeding_the_null():
    ref = C.OrientationControl().local_field_reference()
    assert "exceed the orientation null" in ref["requirement"]
    assert ref["status"] == "NO_FIELD_MEASURED"


# --- presentation order ------------------------------------------------

def test_presentation_order_is_deterministic_for_a_seed():
    conds = tuple(C.ORIENTATION_CONDITIONS[:4])
    a = C.randomized_presentation_order(conds, n_repeats=3, seed=11)
    b = C.randomized_presentation_order(conds, n_repeats=3, seed=11)
    assert a == b


def test_presentation_order_differs_between_seeds():
    conds = tuple(C.ORIENTATION_CONDITIONS[:5])
    a = C.randomized_presentation_order(conds, n_repeats=5, seed=1)
    b = C.randomized_presentation_order(conds, n_repeats=5, seed=2)
    assert a != b


def test_presentation_order_is_balanced():
    conds = ("A", "B", "C")
    order = C.randomized_presentation_order(conds, n_repeats=4, seed=3)
    assert len(order) == 12
    assert all(order.count(c) == 4 for c in conds)


def test_presentation_order_is_not_the_fixed_order():
    """A fixed order aliases thermal drift into orientation."""
    conds = tuple(C.ORIENTATION_CONDITIONS)
    order = C.randomized_presentation_order(conds, n_repeats=4, seed=17)
    assert order[:len(conds)] != conds


def test_presentation_order_rejects_empty_input():
    with pytest.raises(ValueError):
        C.randomized_presentation_order((), n_repeats=1, seed=0)


# --- orientation null --------------------------------------------------

def _noise(conditions, n, seed, shift=None):
    rng = random.Random(seed)
    shift = shift or {}
    return {c: [rng.gauss(shift.get(c, 0.0), 1.0) for _ in range(n)]
            for c in conditions}


def test_orientation_null_p_is_in_the_unit_interval():
    rep = C.orientation_null(_noise("abcd", 8, 5), seed=1,
                             n_permutations=400)
    assert 0.0 < rep["p"] <= 1.0


def test_orientation_null_never_returns_exactly_zero():
    """A finite permutation test cannot license p = 0."""
    resp = {"a": [0.0] * 6, "b": [100.0] * 6}
    rep = C.orientation_null(resp, seed=2, n_permutations=200)
    assert rep["p"] >= 1.0 / 201.0
    assert rep["p"] < 0.05


def test_orientation_null_is_approximately_uniform_under_no_effect():
    ps = [C.orientation_null(_noise("abc", 6, 100 + i), seed=i,
                             n_permutations=200)["p"]
          for i in range(60)]
    mean = sum(ps) / len(ps)
    assert 0.35 < mean < 0.65, mean
    assert sum(1 for p in ps if p < 0.05) <= 8


def test_orientation_null_detects_a_large_real_effect():
    resp = _noise("abc", 12, 7, shift={"a": 6.0})
    rep = C.orientation_null(resp, seed=3, n_permutations=500)
    assert rep["p"] < 0.05


def test_orientation_null_is_deterministic_for_a_seed():
    resp = _noise("abc", 8, 9)
    a = C.orientation_null(resp, seed=4, n_permutations=300)
    b = C.orientation_null(resp, seed=4, n_permutations=300)
    assert a["p"] == b["p"]
    assert a["statistic"] == b["statistic"]


def test_orientation_null_reports_group_means():
    resp = {"a": [1.0, 1.0], "b": [3.0, 3.0]}
    rep = C.orientation_null(resp, seed=5, n_permutations=50)
    assert rep["group_means"] == {"a": 1.0, "b": 3.0}


def test_orientation_null_refuses_a_single_condition():
    with pytest.raises(ValueError):
        C.orientation_null({"a": [1.0, 2.0]}, seed=0, n_permutations=10)


def test_orientation_null_refuses_an_empty_condition():
    with pytest.raises(ValueError):
        C.orientation_null({"a": [1.0], "b": []}, seed=0,
                           n_permutations=10)


def test_orientation_null_note_points_at_presentation_order():
    rep = C.orientation_null(_noise("ab", 4, 1), seed=1,
                             n_permutations=50)
    assert "randomized_presentation_order" in rep["note"]


# --- environment -------------------------------------------------------

def test_all_six_environmental_variables_are_registered():
    reg = C.environmental_registry()
    for v in ("temperature", "humidity", "line_voltage", "vibration",
              "electromagnetic_interference", "operator_presence"):
        assert v in reg


def test_every_environmental_variable_is_logged_and_controlled():
    for e in C.ENVIRONMENTAL_CONTROLS:
        assert e.control_method
        assert e.logging_method


def test_environmental_channels_are_ordinary_channels():
    for e in C.ENVIRONMENTAL_CONTROLS:
        for c in e.ordinary_channels:
            assert c in ORDINARY_CHANNELS


def test_undeclared_ordinary_channel_rejected():
    with pytest.raises(ValueError):
        C.EnvironmentalControl(
            variable="mood", unit="none", control_method="c",
            logging_method="l", mimics=("everything",),
            ordinary_channels=("aether_pressure",))


def test_environmental_variable_must_mimic_something():
    with pytest.raises(ValueError):
        C.EnvironmentalControl(
            variable="x", unit="u", control_method="c",
            logging_method="l", mimics=())


def test_confound_matrix_maps_variables_to_mimicked_effects():
    m = C.confound_matrix()
    assert set(m["by_variable"]) == {
        e.variable for e in C.ENVIRONMENTAL_CONTROLS}
    assert m["by_effect"]


def test_temperature_can_mimic_an_orientation_dependence():
    """The confound the randomized order exists to break."""
    mimics = C.environmental_registry()["temperature"].mimics
    assert any("orientation" in x for x in mimics)


def test_operator_presence_is_treated_as_a_confound():
    ops = C.environmental_registry()["operator_presence"]
    assert any("expectancy" in x for x in ops.mimics)


# --- blinding ----------------------------------------------------------

def test_blinding_protocol_lists_every_required_element():
    bp = C.blinding_protocol()
    assert set(bp["elements"]) == set(C.REQUIRED_BLINDING)


def test_blinding_protocol_includes_analysis_blinding():
    bp = C.blinding_protocol()
    assert "analysis_preregistered" in bp["elements"]
    req = bp["elements"]["analysis_preregistered"]["requirement"]
    assert "before the first trial" in req


def test_blinding_requires_independent_decoding():
    bp = C.blinding_protocol()
    req = bp["elements"]["independent_decoding"]["requirement"]
    assert "did not run the apparatus" in req


def test_blinding_requires_specimen_orientation_and_drive():
    for k in ("specimen_identity", "orientation", "drive_state"):
        assert k in C.blinding_protocol()["elements"]


def test_blinding_protocol_is_declared_design_only():
    assert C.blinding_protocol()["status"] == "DESIGN_ONLY"


# --- completeness ------------------------------------------------------

def test_a_complete_design_is_certified():
    rep = C.control_completeness(_complete_design())
    assert rep["certified"], rep["missing"]
    assert rep["status"] == "DESIGN_CONTROLLED"


def test_design_missing_the_empty_mount_is_refused_by_name():
    mats = [m.material_id for m in C.MATERIAL_CONTROLS
            if not m.is_empty_mount]
    rep = C.control_completeness(_complete_design(materials=mats))
    assert not rep["certified"]
    assert "empty_mount_control" in rep["missing"]
    assert "empty_mount" in rep["missing_detail"]["empty_mount_control"]
    assert "empty_mount" in rep["missing_controls"]


def test_design_missing_the_sham_drive_is_refused():
    rep = C.control_completeness(_complete_design(sham_drive=False))
    assert "sham_drive" in rep["missing"]


def test_design_with_fixed_order_is_refused():
    rep = C.control_completeness(_complete_design(randomized_order=False))
    assert "randomized_order" in rep["missing"]
    assert "drift" in rep["missing_detail"]["randomized_order"]


def test_design_with_partial_blinding_is_refused():
    rep = C.control_completeness(
        _complete_design(blinding=["specimen_identity"]))
    assert "blinding" in rep["missing"]
    assert "analysis_preregistered" in rep["missing_blinding"]


def test_empty_design_reports_all_four_gaps_not_just_the_first():
    rep = C.control_completeness({})
    assert set(rep["missing"]) == set(C.REQUIRED_DESIGN_ELEMENTS)


def test_unknown_materials_are_reported():
    rep = C.control_completeness(
        _complete_design(materials=["orgone_accumulator"]))
    assert "orgone_accumulator" in rep["unknown_materials"]


def test_completeness_is_not_a_claim_about_a_result():
    rep = C.control_completeness(_complete_design())
    assert "no run has been performed" in rep["note"]


def test_completeness_rejects_a_non_mapping():
    with pytest.raises(TypeError):
        C.control_completeness(["empty_mount"])


def test_refusal_is_first_class_for_an_incomplete_design():
    with pytest.raises(C.ControlRefused) as e:
        C.refuse_uncontrolled_report({}, "an orientation dependence")
    assert "empty_mount_control" in str(e.value)


def test_refusal_passes_a_complete_design_through():
    rep = C.refuse_uncontrolled_report(_complete_design(), "anything")
    assert rep["certified"]
