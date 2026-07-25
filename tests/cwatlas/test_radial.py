"""P29 — Radial <-> (shell, altitude) round-trip; effective-potential nonliteral."""

from __future__ import annotations

import pytest

from cwatlas import radial as R
from cwatlas import shells as S
from cwatlas.claims import ClaimClass, ClaimError


# --- Profiles are declared, not defaulted -------------------------------------

def test_four_radial_conventions_are_declared():
    keys = set(R.RADIAL_PROFILES)
    assert {"DIMENSIONLESS@1.0.0", "SURFACE@1.0.0",
            "ATMOSPHERE@1.0.0", "ORBIT@1.0.0"} <= keys


def test_unknown_profile_is_refused():
    with pytest.raises(R.RadialError):
        R.get_radial_profile("NOPE@9.9.9")


def test_a_radial_profile_with_a_physical_claim_class_is_refused():
    with pytest.raises(R.RadialError):
        R.RadialProfile(
            "X", "1.0.0", unit="m", datum_offset=0.0, band_width=1.0,
            claim_class=ClaimClass.CANONICAL_ROUND_TRIP)


def test_a_radial_profile_needs_a_positive_band_width():
    with pytest.raises(R.RadialError):
        R.RadialProfile("X", "1.0.0", unit="m", datum_offset=0.0, band_width=0.0)


# --- Mapping to a shell band --------------------------------------------------

def test_radial_zero_maps_to_surface_datum_shell_0():
    p = R.get_radial_profile("DIMENSIONLESS@1.0.0")
    m = R.radial_to_shell(p, 0.0, body_id="EARTH")
    assert m.shell_index == 0
    assert m.altitude_in_band == 0.0
    assert m.body_id == "EARTH"


def test_radial_maps_into_the_expected_band():
    p = R.get_radial_profile("DIMENSIONLESS@1.0.0")
    # u = 2.5 -> ceil -> shell 3, altitude 0.5 within band [2,3]
    m = R.radial_to_shell(p, 2.5, body_id="MARS")
    assert m.shell_index == 3
    assert m.altitude_in_band == pytest.approx(0.5)


def test_surface_convention_scales_by_band_width():
    p = R.get_radial_profile("SURFACE@1.0.0")  # band_width 1000 m
    m = R.radial_to_shell(p, 3500.0, body_id="EARTH")
    assert m.shell_index == 4  # u = 3.5 -> ceil 4
    assert m.altitude_in_band == pytest.approx(0.5)


def test_radial_outside_range_is_refused():
    p = R.get_radial_profile("DIMENSIONLESS@1.0.0")
    with pytest.raises(R.RadialError):
        R.radial_to_shell(p, 8.5, body_id="EARTH")  # beyond shell 8
    with pytest.raises(R.RadialError):
        R.radial_to_shell(p, -0.1, body_id="EARTH")


def test_mapping_needs_a_body():
    p = R.get_radial_profile("DIMENSIONLESS@1.0.0")
    with pytest.raises(R.RadialError):
        R.radial_to_shell(p, 1.0, body_id="")


# --- POWER: radial <-> (shell, altitude) round-trip ---------------------------

def test_round_trip_dimensionless():
    p = R.get_radial_profile("DIMENSIONLESS@1.0.0")
    for r in (0.0, 0.5, 1.0, 3.25, 6.75, 8.0):
        m = R.radial_to_shell(p, r, body_id="EARTH")
        back = R.shell_to_radial(p, m.shell_index, m.altitude_in_band)
        assert back == pytest.approx(r, abs=R.RADIAL_ROUND_TRIP_TOL)


def test_round_trip_all_metric_conventions():
    for key in ("SURFACE@1.0.0", "ATMOSPHERE@1.0.0", "ORBIT@1.0.0"):
        p = R.get_radial_profile(key)
        for frac in (0.0, 0.1, 0.5, 0.9):
            for shell in range(1, 9):
                r = p.datum_offset + (shell - 1 + frac) * p.band_width
                m = R.radial_to_shell(p, r, body_id="MARS")
                back = R.shell_to_radial(p, m.shell_index, m.altitude_in_band)
                assert back == pytest.approx(r, rel=1e-12, abs=1e-6)


def test_shell_to_radial_refuses_bad_altitude():
    p = R.get_radial_profile("DIMENSIONLESS@1.0.0")
    with pytest.raises(R.RadialError):
        R.shell_to_radial(p, 3, 1.5)  # altitude > 1
    with pytest.raises(R.RadialError):
        R.shell_to_radial(p, 0, 0.5)  # shell 0 must have altitude 0


# --- Effective potential is nonliteral SOURCE ontology ------------------------

def test_effective_potential_label_is_nonliteral_source_ontology():
    m = R.radial_to_shell(
        R.get_radial_profile("DIMENSIONLESS@1.0.0"), 3.0, body_id="EARTH")
    assert m.effective_potential_label == "EFFECTIVE_POTENTIAL_ORDINAL_3"
    assert m.claim_class is ClaimClass.SOURCE_CLAIM


def test_effective_potential_as_physical_is_refused():
    with pytest.raises(ClaimError):
        R.refuse_effective_potential_as_physical()


# --- 8 <-> 0 closure stays opt-in ---------------------------------------------

def test_shell_8_closure_is_refused_by_default():
    p = R.get_radial_profile("DIMENSIONLESS@1.0.0")
    m = R.radial_to_shell(p, 8.0, body_id="EARTH")
    assert m.shell_index == 8
    with pytest.raises(ClaimError):
        R.resolve_shell_closure(m)  # opt-in off by default


def test_shell_8_closure_resolves_only_with_opt_in():
    p = R.get_radial_profile("DIMENSIONLESS@1.0.0")
    m = R.radial_to_shell(p, 8.0, body_id="EARTH")
    assert R.resolve_shell_closure(m, apply_closure=True) == 0


# --- Determinism + import -----------------------------------------------------

def test_report_is_deterministic_and_claims_nothing_physical():
    a = R.radial_report()
    b = R.radial_report()
    assert a == b
    assert a["phase_id"] == "P29"
    assert a["measured_here"] == "nothing"
    assert a["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert a["source_vector_geographic_semantics"] == "NOT_CLAIMED"
    assert a["effective_potential_is_nonliteral"] is True


def test_import_surface():
    from cwatlas import radial  # noqa: F401
