"""P05 -- numeric source registry and normalization tests (synthetic only)."""

from __future__ import annotations

import dataclasses

import pytest

from cwatlas import claims
from cwatlas import privacy
from cwatlas import source_registry as R


def test_register_preserves_exact_original_string():
    reg = R.SourceRegistry()
    v = reg.register("v1", "12 07 33", R.ValueKind.GROUPED_NUMBER)
    assert v.raw == "12 07 33"
    assert v.as_original() == "12 07 33"
    assert v.integer_tuple() == (12, 7, 33)


def test_leading_zeros_are_preserved():
    reg = R.SourceRegistry()
    v = reg.register("z1", "007", R.ValueKind.DIAL_VALUE, separator="")
    assert v.raw == "007"                       # exact original kept
    assert v.has_leading_zeros()
    comp = v.components[0]
    assert comp.original == "007"               # not shortened
    assert comp.integer == 7                    # value available beside it
    assert comp.leading_zeros == 2


def test_grouped_leading_zeros_preserved_per_component():
    reg = R.SourceRegistry()
    v = reg.register("g1", "00 07 019", R.ValueKind.GROUPED_NUMBER)
    assert [c.original for c in v.components] == ["00", "07", "019"]
    assert [c.integer for c in v.components] == [0, 7, 19]
    assert [c.leading_zeros for c in v.components] == [1, 1, 1]
    assert v.as_original() == "00 07 019"


def test_raw_string_is_immutable():
    reg = R.SourceRegistry()
    v = reg.register("i1", "042", R.ValueKind.DIAL_VALUE, separator="")
    with pytest.raises(dataclasses.FrozenInstanceError):
        v.raw = "42"  # type: ignore[misc]
    assert v.raw_hash == R._sha256("042")


def test_unitless_value_stays_unitless():
    reg = R.SourceRegistry()
    v = reg.register("u1", "137", R.ValueKind.NO_UNIT, separator="")
    assert v.is_unitless()
    assert v.unit is None


def test_forced_unit_on_unitless_is_refused():
    reg = R.SourceRegistry()
    with pytest.raises(claims.ClaimError):
        reg.register("u2", "137", R.ValueKind.NO_UNIT, unit="metres",
                     separator="")


def test_refuse_forced_interpretation_direct():
    with pytest.raises(claims.ClaimError):
        R.refuse_forced_interpretation("137", forced_unit="deg")
    with pytest.raises(claims.ClaimError):
        R.refuse_forced_interpretation("51 07", forced_meaning="Stonehenge")


def test_geographic_claim_class_is_refused():
    reg = R.SourceRegistry()
    with pytest.raises(claims.ClaimError):
        reg.register("cg", "51 30", R.ValueKind.NUMERIC_VECTOR,
                     claim_class=claims.ClaimClass.CALIBRATED_MAPPING)


def test_allowed_classes_are_never_geographic():
    assert claims.ClaimClass.SOURCE_CLAIM in R.ALLOWED_CLASSES
    assert claims.ClaimClass.MATHEMATICAL_TRANSLATION in R.ALLOWED_CLASSES
    assert claims.ClaimClass.CALIBRATED_MAPPING not in R.ALLOWED_CLASSES


def test_timestamp_registered_without_forced_interpretation():
    reg = R.SourceRegistry()
    v = reg.register("ts", "00:07:33", R.ValueKind.TIMESTAMP, separator=":")
    assert [c.original for c in v.components] == ["00", "07", "33"]
    assert v.components[0].has_leading_zeros()
    assert v.unit is None


def test_duplicate_registration_is_refused():
    reg = R.SourceRegistry()
    reg.register("d1", "1", R.ValueKind.NO_UNIT, separator="")
    with pytest.raises(R.RegistryError):
        reg.register("d1", "2", R.ValueKind.NO_UNIT, separator="")


def test_empty_value_fails_safely():
    reg = R.SourceRegistry()
    with pytest.raises(R.RegistryError):
        reg.register("e1", "", R.ValueKind.NO_UNIT, separator="")


def test_normalization_is_deterministic():
    a = R.normalize("00 07 019")
    b = R.normalize("00 07 019")
    assert a == b


def test_report_claims_nothing_geographic():
    r = R.source_registry_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"


def test_fixtures_carry_no_private_tokens():
    for raw in ("12 07 33", "007", "00:07:33", "137"):
        assert privacy.scan_for_private(raw) == []
