"""P41 — deterministic serialization and a tamper-evident hash chain: the
provenance layer. A matching hash proves the bytes, NOT the source.

A result is only reproducible evidence if it serialises the same way
every time. :func:`serialize` produces a CANONICAL byte string --- keys
sorted, floats in a fixed format, one explicit encoding --- so the same
logical object always yields identical bytes regardless of the order its
keys happened to be built in. :func:`content_hash` is the SHA-256 of
those bytes, so it is stable across runs and changes if any field
changes: that is the tamper-evidence.

Results are then chained. A :class:`Record` bundles a payload, its claim
class, an epoch, and the hash of the record before it; each record's own
hash is taken over all four fields, so the chain is a mini Merkle / hash
chain of results. :func:`append_record` links a new record to the tip,
and :func:`verify_chain` recomputes every hash and every back-link.
Mutating any past record breaks verification for that record and every
record downstream of it --- the load-bearing integrity property.

Two things this layer is careful NOT to claim. First, it never reads a
clock: every epoch is PASSED IN, because a timestamp baked from a live
clock read would make the output non-deterministic and unverifiable, and
:func:`refuse_wallclock_timestamp` guards that anti-pattern. Second, a
hash match is integrity, not authentication:
:func:`refuse_hash_match_as_authentication` refuses to read "the hashes
agree" as "this came from who it claims to". Identical bytes hash
identically no matter who produced them; provenance needs a signature
over the content and a key, which a bare digest does not supply.

The standing verdict is ``DETERMINISTIC_SERIALIZATION_HASHED``.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction

#: The standing verdict.
VERDICT = "DETERMINISTIC_SERIALIZATION_HASHED"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: The genesis back-link: the prev_hash of the first record in a chain.
GENESIS_PREV_HASH = "0" * 64

#: Encoding used for every serialization. Declared, not assumed.
ENCODING = "utf-8"


class SerializeError(RuntimeError):
    """Raised on a non-canonicalisable object, a malformed record or
    chain, an attempt to stamp with a live clock, or an attempt to read a
    hash match as authentication."""


class ClaimClass(Enum):
    """How a statement in this module is entitled to be believed."""

    DERIVED_ARITHMETIC = "DERIVED_ARITHMETIC"
    ANALYTIC_MODEL = "ANALYTIC_MODEL"
    RETROSPECTIVE_NUMERIC_MATCH = "RETROSPECTIVE_NUMERIC_MATCH"
    BLOCKED_MISSING_INPUT = "BLOCKED_MISSING_INPUT"
    UNSUPPORTED = "UNSUPPORTED"


# --- canonical serialization -------------------------------------------

def _canonical_float(x: float) -> str:
    """A fixed, round-trippable text form for a float.

    ``repr`` gives the shortest string that round-trips to the same IEEE
    double, and it is deterministic in CPython, so it is a fixed format:
    the same float always renders identically, and two different floats
    render differently. Non-finite floats are refused -- they have no
    canonical, portable text form and no place in a tamper-evident
    record.
    """
    if x != x or x in (float("inf"), float("-inf")):
        raise SerializeError(
            "non-finite floats (nan, inf) have no canonical form and may "
            "not enter a serialized record")
    return repr(float(x))


def _canonical(obj) -> str:
    """Canonical text for one object. Deterministic and total over the
    supported types; the byte string is this text encoded once."""
    if obj is None:
        return "null"
    if isinstance(obj, bool):                     # before int: bool is int
        return "true" if obj else "false"
    if isinstance(obj, int):
        return str(obj)
    if isinstance(obj, float):
        return _canonical_float(obj)
    if isinstance(obj, Fraction):
        # Exact, unambiguous, and independent of any float rounding.
        return f'"Fraction:{obj.numerator}/{obj.denominator}"'
    if isinstance(obj, str):
        # json.dumps supplies canonical string escaping with a stable
        # encoding of every code point.
        return json.dumps(obj, ensure_ascii=True)
    if isinstance(obj, (list, tuple)):
        return "[" + ",".join(_canonical(v) for v in obj) + "]"
    if isinstance(obj, dict):
        items = []
        for key in obj:
            if not isinstance(key, str):
                raise SerializeError(
                    f"canonical dict keys must be strings (got "
                    f"{type(key).__name__}); a non-string key has no "
                    f"stable ordering")
        for key in sorted(obj):                   # SORTED: order-independent
            items.append(f"{json.dumps(key, ensure_ascii=True)}:"
                         f"{_canonical(obj[key])}")
        return "{" + ",".join(items) + "}"
    raise SerializeError(
        f"cannot canonically serialize {type(obj).__name__}; supported "
        f"types are None, bool, int, float, Fraction, str, list, tuple, "
        f"dict")


def serialize(obj) -> bytes:
    """Canonical byte string for ``obj``.

    Two equal objects serialise to byte-identical output, and the order
    in which a dict's keys were inserted does not change the result --
    keys are sorted. That canonicalisation is what makes the downstream
    hash a stable fingerprint of the logical content rather than of an
    incidental in-memory layout.
    """
    return _canonical(obj).encode(ENCODING)


def content_hash(obj) -> str:
    """SHA-256 of the canonical bytes, as hex.

    Stable across runs for equal objects (canonicalisation guarantees
    it) and different whenever any field differs (SHA-256 collision
    resistance) -- so a changed digest is evidence the content changed.
    """
    return hashlib.sha256(serialize(obj)).hexdigest()


# --- the provenance record and its chain --------------------------------

@dataclass(frozen=True)
class Record:
    """One link in a hash chain of results.

    ``payload`` is the result being recorded; ``claim_class`` is how it
    is entitled to be believed; ``epoch`` is a PASSED-IN timestamp (never
    a clock read); ``prev_hash`` is the hash of the previous record.
    ``record_hash`` is taken over all four, so any change to any field --
    here or in an earlier record it links back to -- is detectable.
    """

    payload: object
    claim_class: str
    epoch: object
    prev_hash: str
    record_hash: str

    def body(self) -> dict:
        """The hashed content of this record, excluding its own hash."""
        return {
            "payload": self.payload,
            "claim_class": self.claim_class,
            "epoch": self.epoch,
            "prev_hash": self.prev_hash,
        }

    def recompute_hash(self) -> str:
        return content_hash(self.body())

    def is_intact(self) -> bool:
        """True iff the stored hash still matches the content."""
        return self.record_hash == self.recompute_hash()


def make_record(payload, claim_class: str, epoch,
                prev_hash: str = GENESIS_PREV_HASH) -> Record:
    """Build a record, computing its hash over its four content fields."""
    if not isinstance(claim_class, str) or not claim_class:
        raise SerializeError("claim_class must be a non-empty string")
    if not isinstance(prev_hash, str) or not prev_hash:
        raise SerializeError("prev_hash must be a non-empty string")
    body = {
        "payload": payload,
        "claim_class": claim_class,
        "epoch": epoch,
        "prev_hash": prev_hash,
    }
    return Record(
        payload=payload,
        claim_class=claim_class,
        epoch=epoch,
        prev_hash=prev_hash,
        record_hash=content_hash(body),
    )


def new_chain(payload, epoch,
              claim_class: str = ClaimClass.DERIVED_ARITHMETIC.value
              ) -> tuple[Record, ...]:
    """Start a chain with a genesis record linked to GENESIS_PREV_HASH."""
    return (make_record(payload, claim_class, epoch, GENESIS_PREV_HASH),)


def append_record(chain: tuple[Record, ...] | list, payload, epoch,
                  claim_class: str = ClaimClass.DERIVED_ARITHMETIC.value
                  ) -> tuple[Record, ...]:
    """Append a record linked to the tip of ``chain`` by its hash.

    The new record's ``prev_hash`` is the current tip's ``record_hash``,
    so the tip is now referenced by content: editing it after the fact
    changes its hash and breaks this back-link. ``epoch`` is passed in;
    nothing here reads a clock.
    """
    records = tuple(chain)
    if not records:
        return new_chain(payload, epoch, claim_class)
    tip = records[-1]
    if not isinstance(tip, Record):
        raise SerializeError("chain tip is not a Record")
    return records + (make_record(payload, claim_class, epoch,
                                  tip.record_hash),)


def verify_chain(chain: tuple[Record, ...] | list) -> bool:
    """Verify every record's own hash and every back-link.

    Two checks per record: the stored ``record_hash`` still equals the
    hash of its content, and its ``prev_hash`` equals the previous
    record's ``record_hash`` (the genesis link for the first). Mutating
    any past record's content makes its recomputed hash differ from its
    stored hash, and also breaks the back-link of every record after it,
    so a single tamper fails verification from that point onward.
    """
    records = tuple(chain)
    if not records:
        raise SerializeError("cannot verify an empty chain")
    expected_prev = GENESIS_PREV_HASH
    for rec in records:
        if not isinstance(rec, Record):
            raise SerializeError("chain contains a non-Record element")
        if not rec.is_intact():
            return False
        if rec.prev_hash != expected_prev:
            return False
        expected_prev = rec.record_hash
    return True


def verify_chain_report(chain: tuple[Record, ...] | list) -> dict:
    """Per-record breakdown of :func:`verify_chain`."""
    records = tuple(chain)
    if not records:
        raise SerializeError("cannot verify an empty chain")
    rows = []
    expected_prev = GENESIS_PREV_HASH
    ok = True
    for i, rec in enumerate(records):
        intact = rec.is_intact()
        linked = rec.prev_hash == expected_prev
        if not (intact and linked):
            ok = False
        rows.append({
            "index": i,
            "hash_intact": intact,
            "back_link_ok": linked,
            "record_hash": rec.record_hash,
        })
        expected_prev = rec.record_hash
    return {"verified": ok, "length": len(records), "records": rows}


# --- the two refusals ---------------------------------------------------

def refuse_wallclock_timestamp(epoch: object = None,
                               reads_clock: bool = True) -> object:
    """Refuse to stamp a record with a live clock read.

    A timestamp taken from ``time.time()`` / ``datetime.now()`` at the
    moment of writing makes the output non-deterministic: the same
    logical result serialises differently on every run, its content hash
    is unstable, and the chain can never be reproduced or independently
    verified. Epochs must be PASSED IN explicitly. If ``reads_clock`` is
    True (the anti-pattern) this raises; if a caller has genuinely passed
    an explicit epoch and set ``reads_clock=False``, the epoch is
    returned unchanged.
    """
    if reads_clock:
        raise SerializeError(
            "refused: a record may not be stamped with a live clock read "
            "(time.time() / datetime.now()). A wall-clock stamp makes the "
            "serialization non-deterministic, so the content hash is "
            "unstable and the chain cannot be reproduced or verified. "
            "Pass the epoch in explicitly and call with reads_clock=False. "
            + VERDICT + ".")
    if epoch is None:
        raise SerializeError(
            "reads_clock=False requires an explicit epoch to have been "
            "passed in; none was")
    return epoch


def refuse_hash_match_as_authentication(hash_a: object = None,
                                        hash_b: object = None,
                                        claimed_source: object = None
                                        ) -> None:
    """Refuse to read a matching content hash as authentication.

    A hash match proves that two byte strings are identical -- integrity,
    that the content was not altered. It says nothing about WHO produced
    the content or whether a claimed source is genuine: identical bytes
    hash identically regardless of origin, and anyone can compute the
    same digest over the same bytes. Authentication of a source needs a
    signature over the content under a key held by that source, which a
    bare digest does not provide. Always raises.
    """
    raise SerializeError(
        f"refused: a matching content hash is integrity, not "
        f"authentication"
        + (f" (claimed source {claimed_source!r})"
           if claimed_source is not None else "")
        + ". Equal hashes prove the bytes are identical and unaltered; "
        "they do not prove who produced them, because identical bytes "
        "hash identically whoever writes them and the digest is public. "
        "Authenticating a source requires a cryptographic signature over "
        "the content under that source's key -- a hash alone cannot bind "
        "content to an identity. " + VERDICT + ".")


# --- report -------------------------------------------------------------

def serialize_report() -> dict:
    """The standing result: canonical serialization and a hash chain."""
    # A deterministic worked chain over passed-in epochs.
    chain = new_chain({"result": "alpha", "n": 1}, epoch=1000,
                      claim_class=ClaimClass.DERIVED_ARITHMETIC.value)
    chain = append_record(chain, {"result": "beta", "n": 2}, epoch=1001)
    chain = append_record(chain, {"result": "gamma", "n": 3}, epoch=1002)
    # Determinism / key-order independence demonstration.
    a = {"x": 1, "y": [2, 3], "z": {"b": 4, "a": 5}}
    b = {"z": {"a": 5, "b": 4}, "y": [2, 3], "x": 1}
    return {
        "what_this_is": (
            "a canonical serializer and a tamper-evident hash chain of "
            "results. The same logical object always serializes to the "
            "same bytes, its SHA-256 is a stable fingerprint, and records "
            "are linked so that editing any past record breaks "
            "verification downstream"),
        "claim_class": ClaimClass.DERIVED_ARITHMETIC.value,
        "measured_here": "nothing",
        "physical_validation": PHYSICAL_VALIDATION,
        "encoding": ENCODING,
        "canonical_is_key_order_independent": serialize(a) == serialize(b),
        "content_hash_stable": content_hash(a) == content_hash(b),
        "example_content_hash": content_hash(a),
        "chain_length": len(chain),
        "chain_verifies": verify_chain(chain),
        "genesis_prev_hash": GENESIS_PREV_HASH,
        "refusals_available": [
            "refuse_wallclock_timestamp (raises on a live clock read)",
            "refuse_hash_match_as_authentication (always raises)",
        ],
        "verdict": VERDICT,
        "what_this_does_not_say": (
            "It does not authenticate a source: a matching hash proves "
            "the bytes are identical and unaltered (integrity), never who "
            "produced them, because identical bytes hash identically "
            "whoever writes them. It does not read a clock -- every epoch "
            "is passed in, so the serialization is deterministic and the "
            "chain is reproducible; a wall-clock stamp is refused because "
            "it would make the hash unstable. It does not verify the "
            "truth of any payload, only that the payload has not changed "
            "since it was recorded. Nothing here is measured."),
    }
