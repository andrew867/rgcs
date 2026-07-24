"""R13 P41 — deterministic serialization and a tamper-evident hash chain:
canonical bytes, a stable-and-tamper-sensitive content hash, a chain that
verifies and breaks under tampering, and the two refusals."""

from __future__ import annotations

import dataclasses
from fractions import Fraction

import pytest

from r13 import serialize as S


# --- POWER: serialization is deterministic and key-order-independent ----

def test_serialization_is_byte_identical_for_equal_objects():
    a = {"result": [1, 2, 3], "claim": "DERIVED_ARITHMETIC", "n": 7}
    b = {"result": [1, 2, 3], "claim": "DERIVED_ARITHMETIC", "n": 7}
    assert S.serialize(a) == S.serialize(b)
    assert isinstance(S.serialize(a), bytes)


def test_serialization_ignores_dict_key_order():
    a = {"x": 1, "y": 2, "z": {"b": 4, "a": 5}}
    b = {"z": {"a": 5, "b": 4}, "y": 2, "x": 1}
    assert a == b                          # same logical object
    assert S.serialize(a) == S.serialize(b)


def test_serialization_distinguishes_different_content():
    # If canonicalisation collapsed distinct objects, tamper evidence
    # would be impossible. It must not.
    assert S.serialize({"n": 1}) != S.serialize({"n": 2})
    assert S.serialize([1, 2]) != S.serialize([2, 1])
    assert S.serialize(1) != S.serialize(1.0)     # int vs float


def test_fraction_and_float_have_canonical_forms():
    assert S.serialize(Fraction(1, 3)) == S.serialize(Fraction(1, 3))
    assert S.serialize(0.1) == S.serialize(0.1)
    # a fixed float format: repr is deterministic and round-trips
    assert S.serialize(0.1) != S.serialize(0.2)


def test_non_finite_float_is_refused():
    with pytest.raises(S.SerializeError):
        S.serialize(float("inf"))
    with pytest.raises(S.SerializeError):
        S.serialize(float("nan"))


def test_non_string_dict_key_is_refused():
    with pytest.raises(S.SerializeError):
        S.serialize({1: "one"})


# --- POWER: content hash is stable and changes on mutation --------------

def test_content_hash_is_stable_across_calls_and_key_order():
    a = {"x": 1, "y": {"b": 2, "a": 3}}
    b = {"y": {"a": 3, "b": 2}, "x": 1}
    assert S.content_hash(a) == S.content_hash(b)
    assert S.content_hash(a) == S.content_hash(a)


def test_content_hash_changes_when_any_field_changes():
    base = {"payload": {"result": "alpha"}, "epoch": 1000, "n": 1}
    h0 = S.content_hash(base)
    for mutated in (
        {"payload": {"result": "beta"}, "epoch": 1000, "n": 1},
        {"payload": {"result": "alpha"}, "epoch": 1001, "n": 1},
        {"payload": {"result": "alpha"}, "epoch": 1000, "n": 2},
    ):
        assert S.content_hash(mutated) != h0


def test_content_hash_is_sha256_hex():
    h = S.content_hash({"a": 1})
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)


# --- POWER: the chain verifies and breaks on tampering ------------------

def _sample_chain():
    chain = S.new_chain({"result": "alpha"}, epoch=1000)
    chain = S.append_record(chain, {"result": "beta"}, epoch=1001)
    chain = S.append_record(chain, {"result": "gamma"}, epoch=1002)
    return chain


def test_fresh_chain_verifies():
    chain = _sample_chain()
    assert len(chain) == 3
    assert S.verify_chain(chain) is True
    assert chain[0].prev_hash == S.GENESIS_PREV_HASH
    assert chain[1].prev_hash == chain[0].record_hash
    assert chain[2].prev_hash == chain[1].record_hash


def test_tampering_with_a_past_record_breaks_verification():
    # The load-bearing integrity test. Mutate the payload of record 0 but
    # keep its stored (now stale) record_hash: verification must fail.
    chain = _sample_chain()
    tampered = dataclasses.replace(chain[0], payload={"result": "FORGED"})
    broken = (tampered,) + chain[1:]
    assert S.verify_chain(broken) is False
    # the tampered record itself is no longer intact
    assert tampered.is_intact() is False


def test_tampering_breaks_the_downstream_backlink():
    # Recompute the tampered record's own hash so it is "intact", but its
    # new hash no longer matches the back-link stored downstream: the
    # break propagates to every later record.
    chain = _sample_chain()
    forged = S.make_record({"result": "FORGED"}, chain[1].claim_class,
                           chain[1].epoch, chain[1].prev_hash)
    broken = (chain[0], forged, chain[2])
    assert forged.is_intact() is True
    assert S.verify_chain(broken) is False        # chain[2] back-link fails
    report = S.verify_chain_report(broken)
    assert report["verified"] is False
    assert report["records"][2]["back_link_ok"] is False


def test_append_record_links_to_the_tip():
    chain = S.new_chain({"n": 1}, epoch=1000)
    grown = S.append_record(chain, {"n": 2}, epoch=1001)
    assert len(grown) == 2
    assert grown[-1].prev_hash == grown[0].record_hash
    assert S.verify_chain(grown) is True


def test_verify_empty_chain_is_refused():
    with pytest.raises(S.SerializeError):
        S.verify_chain(())


# --- the two refusals ---------------------------------------------------

def test_refuse_wallclock_timestamp_raises_on_clock_read():
    with pytest.raises(S.SerializeError, match="live clock read"):
        S.refuse_wallclock_timestamp(reads_clock=True)


def test_refuse_wallclock_timestamp_returns_explicit_epoch():
    # A genuinely passed-in epoch with reads_clock=False is allowed.
    assert S.refuse_wallclock_timestamp(epoch=1234, reads_clock=False) == 1234


def test_refuse_wallclock_timestamp_needs_an_explicit_epoch():
    with pytest.raises(S.SerializeError):
        S.refuse_wallclock_timestamp(epoch=None, reads_clock=False)


def test_refuse_hash_match_as_authentication_always_raises():
    with pytest.raises(S.SerializeError, match="not"):
        S.refuse_hash_match_as_authentication("deadbeef", "deadbeef",
                                              claimed_source="SOME_SOURCE")


def test_refuse_hash_match_as_authentication_raises_with_no_args():
    with pytest.raises(S.SerializeError):
        S.refuse_hash_match_as_authentication()


# --- report -------------------------------------------------------------

def test_report_carries_verdict_and_claim_discipline():
    r = S.serialize_report()
    assert r["verdict"] == "DETERMINISTIC_SERIALIZATION_HASHED"
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["claim_class"] == "DERIVED_ARITHMETIC"
    assert r["canonical_is_key_order_independent"] is True
    assert r["content_hash_stable"] is True
    assert r["chain_verifies"] is True
    assert "what_this_does_not_say" in r
