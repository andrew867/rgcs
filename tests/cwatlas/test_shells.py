"""P16 — Shell registry: nonliteral labels, no auto 8<->0 closure, refusals."""

from __future__ import annotations

import pytest

from cwatlas import shells as S
from cwatlas.claims import ClaimClass, ClaimError


# --- Registry shape -----------------------------------------------------------

def test_registry_covers_shells_0_through_8():
    assert set(S.SHELL_REGISTRY) == set(range(0, 9))
    assert S.SHELL_MIN == 0 and S.SHELL_MAX == 8


def test_shell_0_is_the_surface_datum():
    s0 = S.get_shell(0)
    assert "surface" in s0.surface_semantics.lower()
    assert s0.altitude_band_lower == 0.0 and s0.altitude_band_upper == 0.0


def test_altitude_bands_are_ordered_and_ascending():
    for i in range(1, 9):
        s = S.get_shell(i)
        assert s.altitude_band_upper >= s.altitude_band_lower
        prev = S.get_shell(i - 1)
        assert s.altitude_band_lower >= prev.altitude_band_lower


# --- Labels are nonliteral SOURCE ontology -----------------------------------

def test_every_shell_label_is_nonliteral_source_ontology():
    for s in S.SHELL_REGISTRY.values():
        assert s.literal is False
        assert s.claim_class is ClaimClass.SOURCE_CLAIM


def test_a_literal_shell_is_refused():
    with pytest.raises(ClaimError):
        S.ShellDefinition(
            index=0, ontology_label="L", surface_semantics="s",
            altitude_band_lower=0.0, altitude_band_upper=0.0,
            claim_class=ClaimClass.SOURCE_CLAIM, literal=True)


def test_a_shell_labelled_as_a_physical_claim_is_refused():
    with pytest.raises(ClaimError):
        S.ShellDefinition(
            index=0, ontology_label="L", surface_semantics="s",
            altitude_band_lower=0.0, altitude_band_upper=0.0,
            claim_class=ClaimClass.CANONICAL_ROUND_TRIP)


# --- ShellState ---------------------------------------------------------------

def test_make_shell_state_binds_index_to_body():
    st = S.make_shell_state(3, "MARS")
    assert st.shell_index == 3 and st.body_id == "MARS"
    assert st.claim_class is ClaimClass.SOURCE_CLAIM
    assert st.ontology_label == S.get_shell(3).ontology_label


def test_shell_state_out_of_range_is_refused():
    with pytest.raises(ClaimError):
        S.ShellState(shell_index=9, body_id="MARS",
                     ontology_label="x", claim_class=ClaimClass.SOURCE_CLAIM)


def test_shell_state_needs_a_body():
    with pytest.raises(ClaimError):
        S.make_shell_state(2, "")


# --- Unknown shell is refused -------------------------------------------------

def test_unknown_shell_is_refused():
    with pytest.raises(ClaimError):
        S.get_shell(9)
    with pytest.raises(ClaimError):
        S.get_shell(-1)
    with pytest.raises(ClaimError):
        S.get_shell("surface")  # wrong type


# --- The 8 <-> 0 closure is stored, never auto-applied (invariant 8) ---------

def test_closure_is_stored_as_source_ontology_and_off_by_default():
    assert S.SHELL_CLOSURE["from_shell"] == 8
    assert S.SHELL_CLOSURE["to_shell"] == 0
    assert S.SHELL_CLOSURE["auto_apply"] is False
    assert S.SHELL_CLOSURE["claim_class"] == ClaimClass.SOURCE_CLAIM.value


def test_closure_is_not_auto_applied():
    # default off: shell 8 does not silently become shell 0.
    with pytest.raises(ClaimError):
        S.apply_shell_closure(8)  # apply_closure defaults to False


def test_auto_closure_helper_always_refuses():
    with pytest.raises(ClaimError):
        S.refuse_auto_closure()


def test_closure_applies_only_with_explicit_opt_in():
    assert S.apply_shell_closure(8, apply_closure=True) == 0
    # non-8 indices pass through unchanged, opt-in or not
    assert S.apply_shell_closure(5, apply_closure=True) == 5
    assert S.apply_shell_closure(5, apply_closure=False) == 5


def test_apply_closure_refuses_unknown_index():
    with pytest.raises(ClaimError):
        S.apply_shell_closure(42, apply_closure=True)


# --- Determinism --------------------------------------------------------------

def test_registry_is_deterministic():
    a = S.shells_report()
    b = S.shells_report()
    assert a == b


# --- Report -------------------------------------------------------------------

def test_report_claims_nothing_physical_and_labels_are_nonliteral():
    r = S.shells_report()
    assert r["phase_id"] == "P16"
    assert r["claim_class"] == ClaimClass.SOURCE_CLAIM.value
    assert r["labels_are_nonliteral"] is True
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["source_vector_geographic_semantics"] == (
        "SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED")
    assert r["shell_closure"]["auto_apply"] is False
    assert set(r["shells"]) == set(range(0, 9))


def test_import_surface():
    from cwatlas import shells  # noqa: F401
