"""R11 — decoder identifiability: freezes, alias sets, description lengths.

Every test here can fail. The commitment is asserted to change when any
one of the sixteen frozen fields changes; the refusals are asserted to
raise; the POWER control asserts that a decoder handed its own planted
output wins outright, so a null result elsewhere cannot be blindness;
and the NULL controls assert that on random digit strings, shuffled
labels, random coordinates and held-out landmarks no decoder clears
chance at all."""

from __future__ import annotations

import pytest

from r11 import identifiability as I


FAMILIES = tuple(I.DecoderFamily)


def _altered(spec: I.DecoderSpec, field: str) -> I.DecoderSpec:
    """The same spec with exactly one frozen field given a new value."""
    import dataclasses
    if field == "codec":
        new = (I.DecoderFamily.MIXED_RADIX
               if spec.codec is not I.DecoderFamily.MIXED_RADIX
               else I.DecoderFamily.HEDRON_LOCAL)
    elif field == "header":
        new = (spec.header or 0) + 1
    elif field == "tolerance":
        new = float(spec.tolerance or 0.02) + 0.005
    else:
        new = "ALTERED_VALUE"
    return dataclasses.replace(spec, **{field: new})


# =======================================================================
# Freeze-before-reveal
# =======================================================================

def test_all_sixteen_fields_are_frozen_fields():
    assert len(I.FROZEN_FIELDS) == 16
    assert len(set(I.FROZEN_FIELDS)) == 16
    for name in I.FROZEN_FIELDS:
        assert hasattr(I.BASE_SPEC, name)
        assert name in I.FIELD_DOMAIN_BITS


def test_base_spec_is_fully_frozen():
    assert I.BASE_SPEC.is_fully_frozen()
    assert I.BASE_SPEC.free_fields() == ()


def test_commitment_is_stable_across_calls_and_equal_specs():
    a = I.spec_for(I.DecoderFamily.HEDRON_LOCAL)
    b = I.spec_for(I.DecoderFamily.HEDRON_LOCAL)
    assert I.commitment(a) == I.commitment(a)
    assert I.commitment(a) == I.commitment(b)
    assert len(I.commitment(a)) == 64
    assert I.freeze(a) == I.commitment(a)


def test_spec_id_is_not_part_of_the_commitment():
    """The commitment binds content, so a rename cannot change it."""
    a = I.spec_for(I.DecoderFamily.SOUTH_POLAR, spec_id="NAME_ONE")
    b = I.spec_for(I.DecoderFamily.SOUTH_POLAR, spec_id="NAME_TWO")
    assert a.spec_id != b.spec_id
    assert I.commitment(a) == I.commitment(b)


@pytest.mark.parametrize("field", I.FROZEN_FIELDS)
def test_changing_any_frozen_field_changes_the_commitment(field):
    base = I.spec_for(I.DecoderFamily.DIRECT_GEOGRAPHIC)
    changed = _altered(base, field)
    assert getattr(changed, field) != getattr(base, field)
    assert I.commitment(changed) != I.commitment(base)


@pytest.mark.parametrize("field", I.FROZEN_FIELDS)
def test_freeing_any_frozen_field_changes_the_commitment(field):
    import dataclasses
    base = I.spec_for(I.DecoderFamily.DIRECT_GEOGRAPHIC)
    freed = dataclasses.replace(base, **{field: None})
    assert I.commitment(freed) != I.commitment(base)
    assert field in freed.free_fields()


def test_freeze_registers_the_spec_and_is_frozen_reports_it():
    spec = I.spec_for(I.DecoderFamily.MIXED_RADIX,
                      magnetic_epoch="2031.5")
    assert not I.is_frozen(spec)
    digest = I.freeze(spec)
    assert I.is_frozen(spec)
    assert digest in I.frozen_specs()


def test_all_default_decoders_are_frozen():
    assert len(I.DEFAULT_DECODERS) == len(FAMILIES)
    for d in I.DEFAULT_DECODERS:
        assert I.is_frozen(d.spec)
        assert I.refuse_unfrozen_evaluation(d) == I.commitment(d.spec)


def test_refuse_unfrozen_evaluation_raises_for_an_uncommitted_spec():
    spec = I.spec_for(I.DecoderFamily.DIRECT_GEOGRAPHIC,
                      magnetic_epoch="1899.1")
    assert not I.is_frozen(spec)
    decoder = I.Decoder("DECODER_NEVER_FROZEN", spec)
    with pytest.raises(I.IdentifiabilityError, match="not been frozen"):
        I.refuse_unfrozen_evaluation(decoder)
    with pytest.raises(I.IdentifiabilityError):
        I.hit_rate(decoder, I.random_coordinate_dataset(8))
    with pytest.raises(I.IdentifiabilityError):
        I.alias_set(decoder, I.OutputPoint(0.5, 0.5), 0.05)


def test_refuse_unfrozen_evaluation_rejects_a_mismatched_commitment():
    d = I.decoder_for(I.DecoderFamily.HEDRON_LOCAL)
    with pytest.raises(I.IdentifiabilityError, match="does not match"):
        I.refuse_unfrozen_evaluation(d, commitment_hash="0" * 64)


def test_refuse_unfrozen_evaluation_rejects_a_non_spec():
    with pytest.raises(I.IdentifiabilityError):
        I.refuse_unfrozen_evaluation("DECODER_DIRECT_GEOGRAPHIC")


def test_refuse_spec_change_after_reveal_raises():
    frozen = I.spec_for(I.DecoderFamily.SOUTH_POLAR)
    I.freeze(frozen)
    edited = _altered(frozen, "magnetic_epoch")
    with pytest.raises(I.IdentifiabilityError, match="after the holdout"):
        I.refuse_spec_change_after_reveal(frozen, edited,
                                          labels_revealed=True)


@pytest.mark.parametrize("field", ["gradient_sign", "codec", "header",
                                   "tolerance", "score_function"])
def test_refuse_spec_change_after_reveal_catches_each_field(field):
    frozen = I.spec_for(I.DecoderFamily.ENVELOPE_42BIT)
    edited = _altered(frozen, field)
    with pytest.raises(I.IdentifiabilityError, match=field):
        I.refuse_spec_change_after_reveal(frozen, edited,
                                          labels_revealed=True)


def test_spec_change_before_the_reveal_is_allowed():
    frozen = I.spec_for(I.DecoderFamily.SOUTH_POLAR)
    edited = _altered(frozen, "gradient_scalar")
    out = I.refuse_spec_change_after_reveal(frozen, edited,
                                            labels_revealed=False)
    assert out["allowed"] is True
    assert [c["field"] for c in out["changed_fields"]] == ["gradient_scalar"]


def test_an_unchanged_spec_survives_the_reveal():
    frozen = I.spec_for(I.DecoderFamily.SOUTH_POLAR)
    out = I.refuse_spec_change_after_reveal(frozen, frozen,
                                            labels_revealed=True)
    assert out["changed_fields"] == ()
    assert out["frozen_commitment"] == out["proposed_commitment"]


def test_reveal_holdout_flips_the_refusal():
    holdout = "HOLDOUT_FOR_REVEAL_TEST"
    frozen = I.spec_for(I.DecoderFamily.HEDRON_LOCAL)
    edited = _altered(frozen, "face_orientation")
    assert not I.is_revealed(holdout)
    # before the reveal the same edit is permitted
    assert I.refuse_spec_change_after_reveal(
        frozen, edited, holdout_id=holdout)["allowed"] is True
    I.reveal_holdout(holdout)
    assert I.is_revealed(holdout)
    with pytest.raises(I.IdentifiabilityError):
        I.refuse_spec_change_after_reveal(frozen, edited,
                                          holdout_id=holdout)


# =======================================================================
# POWER: a planted decoder must be recovered
# =======================================================================

@pytest.mark.parametrize("family", FAMILIES, ids=[f.value for f in FAMILIES])
def test_power_planted_data_recovers_its_own_decoder(family):
    """On labels generated by decoder X's own rule, X beats every null."""
    result = I.benchmark(I.planted_dataset(family, 160))
    row = result["decoders"][f"DECODER_{family.value}"]
    assert row["hit_rate_planted"] == 1.0
    assert row["worst_null_hit_rate"] < 0.10
    assert row["excess_over_best_null"] > 0.5
    assert row["better_than_chance"] is True


@pytest.mark.parametrize("family", FAMILIES, ids=[f.value for f in FAMILIES])
def test_power_planted_decoder_is_the_only_winner(family):
    result = I.benchmark(I.planted_dataset(family, 160))
    assert result["better_than_chance"] == [f"DECODER_{family.value}"]
    assert result["verdict"] == "DECODER_SEPARATED_ON_PLANTED_CONTROL"


def test_power_check_reports_detection():
    power = I.power_check(I.DecoderFamily.MIXED_RADIX)
    assert power["detected"] is True
    assert power["better_than_chance"] is True
    assert power["other_families_better_than_chance"] == []


def test_planted_labels_really_come_from_the_generator():
    family = I.DecoderFamily.ENVELOPE_36BIT
    d = I.decoder_for(family)
    for obs in I.planted_dataset(family, 12):
        assert d.best_distance(obs.value, obs.target) == 0.0


# =======================================================================
# NULL: nothing beats chance on any control
# =======================================================================

def test_null_random_digit_strings_no_decoder_beats_chance():
    result = I.benchmark(I.random_digit_string_dataset(200))
    assert result["better_than_chance"] == []
    assert result["any_better_than_chance"] is False
    assert result["verdict"] == "NO_DECODER_IDENTIFIED"
    for row in result["decoders"].values():
        assert row["better_than_chance"] is False


def test_null_shuffled_labels_no_decoder_beats_chance():
    base = I.random_coordinate_dataset(200)
    result = I.benchmark(I.shuffled_label_dataset(base))
    assert result["better_than_chance"] == []
    for row in result["decoders"].values():
        assert row["better_than_chance"] is False


def test_shuffled_labels_really_are_deranged():
    base = I.random_coordinate_dataset(64)
    shuffled = I.shuffled_label_dataset(base)
    assert len(shuffled) == len(base)
    assert [o.value for o in shuffled] == [o.value for o in base]
    assert sorted(o.target.as_tuple() for o in shuffled) == \
        sorted(o.target.as_tuple() for o in base)
    assert all(a.target != b.target for a, b in zip(shuffled, base))


def test_null_random_coordinates_no_decoder_beats_chance():
    result = I.benchmark(I.random_coordinate_dataset(200))
    assert result["any_better_than_chance"] is False


def test_null_heldout_landmarks_no_decoder_beats_chance():
    result = I.benchmark(I.heldout_landmark_dataset(200))
    assert result["any_better_than_chance"] is False


def test_null_check_summary_is_clean():
    nulls = I.null_check()
    assert nulls["any_decoder_beat_chance"] is False
    assert nulls["random_digit_strings"]["better_than_chance"] == []
    assert nulls["shuffled_labels"]["better_than_chance"] == []


def test_benchmark_reports_every_null():
    result = I.benchmark(I.random_digit_string_dataset(40))
    assert result["nulls_used"] == ["heldout_landmarks",
                                    "random_coordinates",
                                    "random_digit_strings",
                                    "shuffled_labels"]
    for row in result["decoders"].values():
        assert set(row["hit_rate_nulls"]) == set(result["nulls_used"])


# =======================================================================
# Alias sets: never a unique answer
# =======================================================================

@pytest.mark.parametrize("family", FAMILIES, ids=[f.value for f in FAMILIES])
def test_alias_set_is_never_a_unique_answer(family):
    d = I.decoder_for(family)
    target = d.decode(I.DEFAULT_ALIAS_POOL[3])
    aliases = I.alias_set(d, target, 0.05)
    assert len(aliases) > 1, (family.value, len(aliases))
    assert len({(a.value, a.branch) for a in aliases}) == len(aliases)


@pytest.mark.parametrize("family", FAMILIES, ids=[f.value for f in FAMILIES])
def test_alias_set_members_are_within_tolerance_and_sorted(family):
    d = I.decoder_for(family)
    target = d.decode(I.DEFAULT_ALIAS_POOL[7])
    tol = 0.05
    aliases = I.alias_set(d, target, tol)
    for a in aliases:
        assert a.distance <= tol
        assert I.point_distance(d.decode(a.value, a.branch), target) \
            == pytest.approx(a.distance)
    assert list(aliases) == sorted(aliases,
                                   key=lambda a: (a.distance, a.value,
                                                  a.branch))


def test_alias_set_contains_the_generating_input():
    d = I.decoder_for(I.DecoderFamily.DIRECT_GEOGRAPHIC)
    value = I.DEFAULT_ALIAS_POOL[11]
    aliases = I.alias_set(d, d.decode(value), 0.0)
    assert value in {a.value for a in aliases}


def test_alias_set_grows_with_tolerance():
    d = I.decoder_for(I.DecoderFamily.MIXED_RADIX)
    target = d.decode(I.DEFAULT_ALIAS_POOL[5])
    sizes = [I.alias_set_size(d, target, t) for t in (0.0, 0.02, 0.05, 0.1)]
    assert sizes == sorted(sizes)
    assert sizes[-1] > sizes[0]


def test_envelope36_aliasing_is_irreducible():
    """Freezing cannot restore three truncated bits: eight readings stay."""
    d = I.decoder_for(I.DecoderFamily.ENVELOPE_36BIT)
    assert d.spec.is_fully_frozen()
    assert len(d.branches) == 8
    assert I.FAMILY_BRANCH_FIELD[I.DecoderFamily.ENVELOPE_36BIT] is None
    points = d.candidates(I.DEFAULT_ALIAS_POOL[0])
    assert len(points) == 8
    assert len(set(p.as_tuple() for p in points)) == 8


@pytest.mark.parametrize("family", [f for f in FAMILIES
                                    if f is not I.DecoderFamily.ENVELOPE_36BIT])
def test_freezing_collapses_branches_where_a_field_governs_them(family):
    import dataclasses
    frozen = I.spec_for(family)
    field = I.FAMILY_BRANCH_FIELD[family]
    freed = dataclasses.replace(frozen, **{field: None})
    assert len(I.admissible_branches(frozen)) == 1
    assert len(I.admissible_branches(freed)) == \
        I.FAMILY_BRANCH_COUNT[family]


def test_refuse_unique_decoding_raises():
    d = I.decoder_for(I.DecoderFamily.ENVELOPE_36BIT)
    target = d.decode(I.DEFAULT_ALIAS_POOL[1])
    with pytest.raises(I.IdentifiabilityError, match="first row of a set"):
        I.refuse_unique_decoding(d, target)


# =======================================================================
# Description length
# =======================================================================

def test_description_length_ranks_free_choices_above_a_tight_freeze():
    tight = I.spec_for(I.DecoderFamily.MIXED_RADIX, spec_id="TIGHT")
    loose = I.DecoderSpec(spec_id="LOOSE", codec=I.DecoderFamily.MIXED_RADIX)
    assert len(loose.free_fields()) == 15
    assert I.description_length(loose) > I.description_length(tight)
    assert I.description_length(tight) == 16      # one bit per commitment


def test_description_length_increases_as_fields_are_freed():
    import dataclasses
    spec = I.spec_for(I.DecoderFamily.MIXED_RADIX)
    previous = I.description_length(spec)
    for name in I.FROZEN_FIELDS:
        spec = dataclasses.replace(spec, **{name: None})
        current = I.description_length(spec)
        assert current > previous, name
        previous = current


def test_description_length_table_totals_agree():
    spec = I.spec_for(I.DecoderFamily.HEDRON_LOCAL)
    table = I.description_length_table(spec)
    total = sum(r["bits"] for r in table["rows"]) + table["branch_bits"]
    assert total == table["total_bits"] == I.description_length(spec)
    assert table["free_field_count"] == 0


def test_a_fully_free_spec_costs_its_whole_search_width():
    free = I.DecoderSpec(spec_id="ALL_FREE")
    expected = (sum(I.FIELD_DOMAIN_BITS.values())
                + I.FREE_CHOICE_SURCHARGE * len(I.FROZEN_FIELDS)
                + I._branch_bits(free))
    assert I.description_length(free) == expected
    assert I.description_length(free) > I.description_length(I.BASE_SPEC)


# =======================================================================
# The headline refusal
# =======================================================================

@pytest.mark.parametrize("args,kwargs", [
    ((), {}),
    (("DECODER_DIRECT_GEOGRAPHIC",), {}),
    ((), {"alias_set_size": 1, "p_value": 0.0, "frozen": True}),
    ((I.OutputPoint(0.25, 0.75),), {"confidence": 1.0}),
])
def test_refuse_decoded_location_verdict_always_raises(args, kwargs):
    with pytest.raises(I.IdentifiabilityError,
                       match="no decoded-location verdict"):
        I.refuse_decoded_location_verdict(*args, **kwargs)


def test_refuse_decoded_location_verdict_survives_a_perfect_power_result():
    """Even a decoder that cleared every null gets no location verdict."""
    power = I.power_check(I.DecoderFamily.DIRECT_GEOGRAPHIC)
    assert power["detected"] is True
    with pytest.raises(I.IdentifiabilityError):
        I.refuse_decoded_location_verdict(power)


# =======================================================================
# The report and the neutrality of the fixtures
# =======================================================================

def test_report_measures_nothing_and_identifies_no_decoder():
    report = I.identifiability_report()
    assert report["measured_here"] == "nothing"
    assert report["verdict"] == "NO_DECODER_IDENTIFIED"
    assert report["verdict"] == I.DEFAULT_VERDICT
    assert report["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert report["evidence_class"] == "DERIVED_MATHEMATICS"
    assert "NO_DECODER_POSSIBLE" in report["what_this_does_not_say"]


def test_report_carries_both_deliverables_and_its_controls():
    report = I.identifiability_report()
    assert report["all_defaults_frozen"] is True
    assert report["power_control"]["detected"] is True
    assert report["null_controls"]["any_decoder_beat_chance"] is False
    assert report["alias_example"]["alias_set_size"] > 1
    assert report["description_length"]["free_costs_more"] is True
    assert sorted(report["decoder_families"]) == \
        sorted(f.value for f in FAMILIES)
    for name in ("refuse_unfrozen_evaluation",
                 "refuse_spec_change_after_reveal",
                 "refuse_decoded_location_verdict"):
        assert name in report["refusals"]


def test_heldout_landmarks_are_synthetic_and_neutral():
    assert len(I.HELDOUT_LANDMARKS) == 8
    for name, point in I.HELDOUT_LANDMARKS:
        assert name.startswith("HOLDOUT_REFERENCE_")
        assert 0.0 <= point.u < 1.0 and 0.0 <= point.v < 1.0
    assert len({n for n, _ in I.HELDOUT_LANDMARKS}) == 8


def test_all_six_decoder_families_are_present_and_distinct():
    assert len(FAMILIES) == 6
    names = {f.value for f in FAMILIES}
    assert names == {"DIRECT_GEOGRAPHIC", "SOUTH_POLAR", "HEDRON_LOCAL",
                     "ENVELOPE_42BIT", "ENVELOPE_36BIT", "MIXED_RADIX"}
    value = I.DEFAULT_ALIAS_POOL[2]
    points = {d.decode(value).as_tuple() for d in I.DEFAULT_DECODERS}
    assert len(points) == 6


# =======================================================================
# Input hygiene
# =======================================================================

@pytest.mark.parametrize("u,v", [(1.0, 0.5), (-0.1, 0.5), (0.5, 1.0)])
def test_output_point_rejects_coordinates_outside_the_unit_square(u, v):
    with pytest.raises(I.IdentifiabilityError):
        I.OutputPoint(u, v)


@pytest.mark.parametrize("value", [-1, 10 ** 12, 10 ** 13, True])
def test_decode_rejects_values_outside_the_twelve_digit_range(value):
    d = I.decoder_for(I.DecoderFamily.DIRECT_GEOGRAPHIC)
    with pytest.raises(I.IdentifiabilityError):
        d.decode(value)


def test_decode_rejects_a_branch_the_spec_does_not_admit():
    d = I.decoder_for(I.DecoderFamily.MIXED_RADIX)
    forbidden = [b for b in range(3) if b not in d.branches]
    assert forbidden
    with pytest.raises(I.IdentifiabilityError, match="not admissible"):
        d.decode(I.DEFAULT_ALIAS_POOL[0], forbidden[0])


def test_a_free_codec_has_no_family_and_no_branches():
    spec = I.DecoderSpec(spec_id="NO_CODEC")
    with pytest.raises(I.IdentifiabilityError, match="codec"):
        I.admissible_branches(spec)
    with pytest.raises(I.IdentifiabilityError):
        I.Decoder("DECODER_NO_CODEC", spec).family


@pytest.mark.parametrize("kwargs", [
    {"tolerance": 0.0}, {"tolerance": 1.0}, {"tolerance": -0.1},
    {"header": -1}, {"spec_id": ""},
])
def test_decoder_spec_rejects_malformed_fields(kwargs):
    with pytest.raises(I.IdentifiabilityError):
        I.DecoderSpec(**kwargs)


def test_benchmark_needs_rows_and_decoders():
    with pytest.raises(I.IdentifiabilityError):
        I.benchmark(())
    with pytest.raises(I.IdentifiabilityError):
        I.benchmark(I.random_coordinate_dataset(8), decoders=())
