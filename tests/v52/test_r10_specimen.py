"""P04 — specimen ontology and chain of custody for natural-vs-synthetic
quartz.

Every test is written to be capable of failing: for each rule there is an
input that flips the assertion. The load-bearing tests are the two
refusals -- that a seller's "natural" label is not provenance, and that a
material class cannot be confirmed from a label without measurement --
because those are what stop a purchase from being mistaken for evidence.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from r10 import specimen as SP


# --- helpers -----------------------------------------------------------

def _event(from_party="seller", to_party="lab", date="2026-01-02",
           evidence="intake form #7"):
    return SP.CustodyEvent(from_party, to_party, date, evidence)


def _chain(*events):
    return SP.ChainOfCustody(tuple(events))


def _specimen(specimen_id="SPX-1", material_class=SP.MaterialClass.UNKNOWN,
              chain=None, locality="a private locality",
              seller="a private seller"):
    return SP.Specimen(
        specimen_id=specimen_id,
        material_class=material_class,
        locality=locality,
        seller=seller,
        chain_of_custody=chain if chain is not None else SP.ChainOfCustody(),
    )


# --- origin status: custody, not label --------------------------------

def test_origin_verified_only_with_documented_custody():
    s = _specimen(chain=_chain(_event()))
    assert SP.origin_status(s) is SP.OriginStatus.VERIFIED


def test_origin_unverified_without_custody():
    s = _specimen()                      # empty chain
    assert SP.origin_status(s) is SP.OriginStatus.ORIGIN_UNVERIFIED


def test_natural_label_without_custody_is_still_unverified():
    """The load-bearing rule: a NATURAL_QUARTZ label with an empty custody
    chain does not make the origin verified. If the label alone drove the
    status this would wrongly return VERIFIED."""
    s = _specimen(material_class=SP.MaterialClass.NATURAL_QUARTZ)
    assert SP.origin_status(s) is SP.OriginStatus.ORIGIN_UNVERIFIED


def test_adding_custody_flips_origin_to_verified():
    s = _specimen(material_class=SP.MaterialClass.NATURAL_QUARTZ)
    assert SP.origin_status(s) is SP.OriginStatus.ORIGIN_UNVERIFIED
    s.chain_of_custody.append(_event())
    assert SP.origin_status(s) is SP.OriginStatus.VERIFIED


# --- refusals ----------------------------------------------------------

def test_refuse_natural_claim_without_custody_raises():
    s = _specimen(material_class=SP.MaterialClass.NATURAL_QUARTZ)
    with pytest.raises(SP.SpecimenError) as e:
        SP.refuse_natural_claim_without_custody(s)
    assert "not provenance" in str(e.value)


def test_refuse_natural_claim_does_not_raise_with_custody():
    """The refusal must be able to *not* fire -- otherwise the test above
    proves nothing. With documented custody there is no refusal."""
    s = _specimen(material_class=SP.MaterialClass.NATURAL_QUARTZ,
                  chain=_chain(_event()))
    assert SP.refuse_natural_claim_without_custody(s) is None


def test_refuse_material_class_without_measurement_raises():
    with pytest.raises(SP.SpecimenError) as e:
        SP.refuse_material_class_without_measurement(
            SP.MaterialClass.NATURAL_QUARTZ)
    assert "requires measurement" in str(e.value)


def test_material_class_refusal_clears_once_measured():
    """With measurement performed the refusal does not fire. If it fired
    unconditionally this would fail."""
    assert SP.refuse_material_class_without_measurement(
        SP.MaterialClass.HYDROTHERMAL_SYNTHETIC_QUARTZ, measured=True) is None


# --- integrity: content hash ------------------------------------------

def test_content_hash_is_stable_for_equal_specimens():
    assert SP.content_hash(_specimen()) == SP.content_hash(_specimen())


def test_content_hash_is_sensitive_to_a_field_change():
    base = _specimen()
    changed = replace(base, material_class=SP.MaterialClass.NATURAL_QUARTZ)
    assert SP.content_hash(base) != SP.content_hash(changed)


def test_content_hash_is_sensitive_to_the_custody_chain():
    """A hash that ignored custody would let history be altered silently."""
    a = _specimen()
    b = _specimen(chain=_chain(_event()))
    assert SP.content_hash(a) != SP.content_hash(b)


# --- public view redacts private locality and seller ------------------

def test_public_view_redacts_locality_and_seller():
    s = _specimen(locality="a private locality",
                  seller="a private seller")
    pv = SP.public_view(s)
    assert "a private locality" not in str(pv)
    assert "a private seller" not in str(pv)
    assert pv["locality"] == SP.REDACTED
    assert pv["seller"] == SP.REDACTED
    assert pv["endorsed"] is False


def test_public_view_reports_origin_status_and_custody_count():
    s = _specimen(chain=_chain(_event(), _event(date="2026-02-01")))
    pv = SP.public_view(s)
    assert pv["origin_status"] == "VERIFIED"
    assert pv["custody_event_count"] == 2
    assert pv["custody_documented"] is True


# --- the vocabularies and the append-only chain -----------------------

def test_every_material_class_is_representable_in_a_specimen():
    for mc in SP.MaterialClass:
        s = _specimen(material_class=mc)
        assert s.material_class is mc
        assert SP.public_view(s)["material_class"] == mc.value


def test_every_handedness_value_exists():
    values = {h.value for h in SP.Handedness}
    assert values == {"LEFT", "RIGHT", "UNTWINNED_UNKNOWN"}


def test_chain_of_custody_is_append_only():
    chain = SP.ChainOfCustody()
    chain.append(_event())
    chain.append(_event(date="2026-03-01"))
    assert len(chain) == 2
    assert chain.events[0].date == "2026-01-02"
    with pytest.raises(SP.SpecimenError):
        chain.refuse_overwrite(0)


def test_custody_event_requires_documentary_evidence():
    with pytest.raises(SP.SpecimenError):
        SP.CustodyEvent("seller", "lab", "2026-01-02", "")   # no evidence


def test_specimen_requires_an_id():
    with pytest.raises(SP.SpecimenError):
        SP.Specimen(specimen_id="")


# --- the report --------------------------------------------------------

def test_report_measures_nothing_and_disclaims_validation():
    r = SP.specimen_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["evidence_class"] == "DERIVED_MATHEMATICS"
    assert r["verdict"] == "SPECIMEN_ONTOLOGY_SOFTWARE_ONLY"
    assert r["load_bearing_fields"] == ["verified_origin", "chain_of_custody"]
    assert "measurement" in r["what_this_does_not_say"]
