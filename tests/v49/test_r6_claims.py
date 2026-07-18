"""P00/P01 — claim registry, refusal and claim-language guards."""

from __future__ import annotations

import pathlib

import pytest

import r6
from r6 import claims


ROOT = pathlib.Path(__file__).resolve().parents[2]


def test_registry_ids_unique():
    assert len(claims.registry()) == len(claims.ALL_CLAIMS)


def test_every_claim_has_a_ceiling():
    for c in claims.ALL_CLAIMS:
        assert c.ceiling.strip(), f"{c.id} has no claim ceiling"


def test_every_claim_preserves_verbatim_source():
    for c in claims.ALL_CLAIMS:
        assert c.verbatim.strip(), f"{c.id} lost its source wording"
        assert c.verbatim != c.translation, (
            f"{c.id}: translation must not silently replace the source")


def test_factually_corrected_claims_carry_a_correction():
    for c in claims.ALL_CLAIMS:
        if c.standing == "FACTUALLY_CORRECTED":
            assert c.correction, f"{c.id} corrected without saying why"


def test_caesium_claim_is_corrected_not_implemented():
    """The SI second is a hyperfine transition, not a decay."""
    c = claims.registry()["R6-C-101"]
    assert c.standing == "FACTUALLY_CORRECTED"
    assert "transition" in c.correction.lower()
    assert "not by radioactive decay" in c.correction.lower() or \
           "not" in c.correction.lower() and "decay" in c.correction.lower()


def test_photon_charge_claim_is_corrected():
    c = claims.registry()["R6-C-008"]
    assert "neutral" in c.correction.lower()


def test_biological_claims_are_registered_as_refused():
    ref = {c.verbatim.replace(" ", "_") for c in claims.refused()}
    for topic in r6.BIOLOGICAL_REFUSALS:
        assert topic in ref, f"{topic} not registered as refused"


def test_refused_claims_have_no_translation():
    for c in claims.refused():
        assert "does not test" in c.translation


def test_sovereign_navigation_ceiling_is_unsupported():
    c = claims.registry()["R6-C-107"]
    assert c.standing == "UNSUPPORTED_AS_ABSOLUTE"
    assert "SOVEREIGN_NAVIGATION_UNSUPPORTED" in c.ceiling


def test_bad_standing_rejected():
    with pytest.raises(ValueError):
        claims.Claim(
            id="X", verbatim="v", source_class="LORE",
            translation="t", required_evidence=(), standing="TRUE",
            ceiling="c")


def test_bad_evidence_class_rejected():
    with pytest.raises(ValueError):
        claims.Claim(
            id="X", verbatim="v", source_class="LORE",
            translation="t", required_evidence=(),
            standing="HYPOTHESIS", ceiling="c",
            evidence_class="PHRYLL_DETECTED")


def test_records_are_json_shaped():
    for rec in claims.claim_records():
        assert isinstance(rec["required_evidence"], list)
        assert isinstance(rec["ordinary_first"], list)


# --- claim-language guard over the whole r6 package -------------------

def _r6_sources():
    return sorted((ROOT / "r6").rglob("*.py"))


def test_forbidden_states_absent_from_package():
    """No module may define a state R6 has ruled out.

    The names appear in r6/__init__.py's FORBIDDEN_STATES tuple, which
    is the declaration of what is banned; anywhere else is a defect.
    """
    for path in _r6_sources():
        if path.name == "__init__.py":
            continue
        text = path.read_text(encoding="utf-8")
        for state in r6.FORBIDDEN_STATES:
            assert state not in text, (
                f"{path.name} references forbidden state {state}")


def test_no_phryll_detection_language():
    """`__init__` names the banned string once, to ban it; nowhere else."""
    banned = ("phryll_detected", "detected phryll", "phryll was detected")
    for path in _r6_sources():
        if path.name == "__init__.py":
            continue
        text = path.read_text(encoding="utf-8").lower()
        for phrase in banned:
            assert phrase not in text, f"{path.name}: {phrase!r}"


def test_forbidden_collapses_all_explained():
    for name, reason in r6.FORBIDDEN_COLLAPSES.items():
        assert len(reason) > 40, f"{name} refused without explanation"


def test_witness_ladder_has_no_direct_read_state():
    assert "SPACETIME_FABRIC_DIRECTLY_READ" not in r6.WITNESS_CLASSES
    assert r6.WITNESS_CLASSES[-1] == "INDEPENDENTLY_REPLICATED_METROLOGY"


def test_navigation_ladder_terminates_in_unsupported():
    assert r6.NAVIGATION_STATUSES[-1] == "SOVEREIGN_NAVIGATION_UNSUPPORTED"


def test_phryll_ladder_unchanged_from_v47():
    assert r6.PHRYLL_CLASSES[0] == "SOURCE_CLAIM"
    assert r6.PHRYLL_CLASSES[-1] == "CANDIDATE_NEW_MECHANISM"
    assert not any("DETECT" in c for c in r6.PHRYLL_CLASSES)


def test_all_eighteen_ordinary_channels_present():
    assert len(r6.ORDINARY_CHANNELS) == 18
    assert "sham_drive" in r6.ORDINARY_CHANNELS


def test_protocol_maturity_does_not_start_at_standard():
    assert r6.PROTOCOL_MATURITY[0] == "EXPERIMENTAL_SCHEMA"
    assert r6.PROTOCOL_MATURITY.index("ADOPTED_STANDARD") == \
        len(r6.PROTOCOL_MATURITY) - 1
