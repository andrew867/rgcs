"""P03 — the source corpus registered by hash: typed records, provenance
digests, and the two governance refusals."""

from __future__ import annotations

import hashlib

import pytest

from r13 import srcregistry as S


def _hex(seed: str) -> str:
    return hashlib.sha256(seed.encode()).hexdigest()


# --- construction refuses re-derivation and bench validation -------------

def test_rederived_equation_is_refused_at_construction():
    with pytest.raises(S.SrcRegistryError):
        S.SourceEquation(
            "EQ_X", r"x = y", "a meaning", "SRC_X", _hex("EQ_X"),
            claim_class="CONVENTIONAL_LITERATURE", rederived_here=True)


def test_bench_validated_equation_is_refused_at_construction():
    with pytest.raises(S.SrcRegistryError):
        S.SourceEquation(
            "EQ_X", r"x = y", "a meaning", "SRC_X", _hex("EQ_X"),
            claim_class="CONVENTIONAL_LITERATURE", bench_validated=True)


def test_an_over_strong_claim_class_is_refused():
    with pytest.raises(S.SrcRegistryError):
        S.SourceEquation(
            "EQ_X", r"x = y", "a meaning", "SRC_X", _hex("EQ_X"),
            claim_class="BENCH_MEASUREMENT")


def test_a_malformed_digest_is_refused():
    with pytest.raises(S.SrcRegistryError):
        S.SourceEquation("EQ_X", r"x = y", "a meaning", "SRC_X", "not-a-hash")


def test_a_clean_equation_constructs_and_is_not_rederived_or_validated():
    e = S.SourceEquation(
        "EQ_OK", r"E = mc^2", "mass-energy equivalence", "SRC_OK",
        _hex("EQ_OK"), claim_class="SOURCE_ESTABLISHED_PHYSICS")
    assert e.rederived_here is False
    assert e.bench_validated is False
    assert len(e.digest) == 64


# --- provenance by digest round-trips ------------------------------------

def test_register_and_verify_hash_round_trips_and_wrong_hash_fails():
    digest = _hex("some-source-document")
    S.register_hash("SRC_ROUNDTRIP", digest)
    assert S.verify_hash("SRC_ROUNDTRIP", digest) is True
    assert S.verify_hash("SRC_ROUNDTRIP", _hex("a-different-document")) is False


def test_verifying_an_unregistered_source_is_refused():
    with pytest.raises(S.SrcRegistryError):
        S.verify_hash("SRC_NEVER_REGISTERED", _hex("x"))


# --- the seeded registry -------------------------------------------------

def test_registry_has_at_least_six_entries_all_conventional_or_established():
    assert len(S.REGISTRY) >= 6
    for e in S.REGISTRY:
        assert e.claim_class in S.REGISTRABLE_CLASSES
        assert e.rederived_here is False
        assert e.bench_validated is False
        assert len(e.sha256) == 64


def test_representative_equations_are_present():
    ids = {e.eq_id for e in S.REGISTRY}
    for required in ("EQ_DAMPED_OSC_GREEN", "EQ_BOGOLIUBOV", "EQ_BVD",
                     "EQ_BRAGG", "EQ_KRAMERS_KRONIG", "EQ_IGRF_SECULAR"):
        assert required in ids


def test_every_registry_source_has_a_seeded_digest():
    for e in S.REGISTRY:
        assert S.verify_hash(e.source_id, e.sha256) is True


def test_the_other_record_kinds_construct():
    assert S.MECHANISMS and S.OBSERVABLES and S.ASSUMPTIONS and S.NON_CLAIMS
    with pytest.raises(S.SrcRegistryError):
        S.MechanismRecord("", "text", "SRC_X")


# --- the two governance refusals -----------------------------------------

def test_paper_is_not_carrier_evidence():
    with pytest.raises(S.SrcRegistryError):
        S.refuse_paper_as_carrier_evidence("SRC_QUANTUM_OPTICS")


def test_unregistered_equation_is_refused():
    with pytest.raises(S.SrcRegistryError):
        S.refuse_unregistered_equation("EQ_NOT_IN_THE_REGISTRY")
    # a registered one is not refused
    S.refuse_unregistered_equation("EQ_BRAGG")
    with pytest.raises(S.SrcRegistryError):
        S.get_equation("EQ_NOT_IN_THE_REGISTRY")


# --- the report ----------------------------------------------------------

def test_report_verdict_and_claims_no_measurement():
    rep = S.srcregistry_report()
    assert rep["verdict"] == "SOURCE_CORPUS_REGISTERED_BY_HASH"
    assert rep["measured_here"] == "nothing"
    assert rep["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert rep["registered_equations"] >= 6
    assert rep["all_conventional_or_established"] is True
    assert rep["none_rederived"] is True
    assert rep["none_bench_validated"] is True
    assert "what_this_does_not_say" in rep


def test_srcregistry_module_imports_from_r13():
    from r13 import srcregistry          # noqa: F401
    assert srcregistry.DEFAULT_VERDICT == "SOURCE_CORPUS_REGISTERED_BY_HASH"
