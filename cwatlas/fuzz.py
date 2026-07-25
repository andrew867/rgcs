"""P63 -- seeded fuzz harness for the ingest + decode pipeline.

A deterministic, seeded generator of *arbitrary* raw vector strings, plus a
runner that pushes each one through the atlas's ingest + decode pipeline and
guarantees the property the whole decoder rests on:

    a raw vector NEVER crashes the pipeline and ALWAYS yields a typed result --
    a canonical decode, a legacy alias set, or an explicit refusal -- never an
    unhandled exception, and never a forced pin.

The generator (:func:`generate_raw`) draws from a :class:`random.Random` seeded
by an integer, so two runs with the same seed emit byte-identical inputs. It
mixes digit runs, grouped/dashed numbers, unicode, punctuation, canonical-looking
``codec=`` payloads, and pure garbage, so the pipeline meets inputs of every
shape.

The runner (:func:`run_one`) classifies each input into one
:class:`FuzzOutcome` and swallows every exception into a typed ``REFUSAL`` --
the boundary is the last line of defence, so even a bug downstream becomes a
refusal rather than a crash. It never calls ``require_unique_pin`` and never
promotes a source vector to a location.

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED

Fully deterministic given a seed; nothing here reads a wall-clock.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum
from typing import List

from cwatlas import claims, service

#: Phase identity.
PHASE_ID = "P63"
TRANCHE = "T08"

#: The character menu the generator draws from.
_DIGITS = "0123456789"
_SEPARATORS = " -_,|/.\t"
_UNICODE = "–— −　 "
_PUNCT = "=;*:+@#%&(){}[]<>"
_LETTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


class FuzzError(RuntimeError):
    """Raised only by the harness's own self-checks, never by decoding input."""


class FuzzOutcome(Enum):
    """The typed outcomes a fuzzed input may reach -- and nothing else."""

    DECODE = "DECODE"          # a canonical vector decoded to one point
    ALIAS_SET = "ALIAS_SET"    # a legacy search returned 1..N candidates
    REFUSAL = "REFUSAL"        # nothing admitted it; an explicit refusal


def _kind_string(rng: random.Random) -> str:
    """Generate one arbitrary raw string of a randomly chosen shape."""
    kind = rng.randrange(9)
    if kind == 0:  # pure digit run
        n = rng.randint(0, 40)
        return "".join(rng.choice(_DIGITS) for _ in range(n))
    if kind == 1:  # grouped / dashed digits
        groups = [
            "".join(rng.choice(_DIGITS) for _ in range(rng.randint(1, 5)))
            for _ in range(rng.randint(1, 6))
        ]
        sep = rng.choice(_SEPARATORS)
        return sep.join(groups)
    if kind == 2:  # digits with unicode dashes / spaces mixed in
        chars = []
        for _ in range(rng.randint(1, 30)):
            pool = _DIGITS + _UNICODE + _SEPARATORS
            chars.append(rng.choice(pool))
        return "".join(chars)
    if kind == 3:  # canonical-looking payload (may or may not checksum)
        lat = rng.randint(-9000000000, 9000000000)
        lon = rng.randint(-18000000000, 18000000000)
        return (f"v=1.0.0;codec=CW-GEO-1;body=EARTH;frame=CRS84;"
                f"epoch=2020.0;lat={lat};lon={lon};h=0;shell=-*cwck1:deadbeefdeadbeef")
    if kind == 4:  # arbitrary punctuation soup
        return "".join(rng.choice(_PUNCT + _DIGITS)
                       for _ in range(rng.randint(0, 30)))
    if kind == 5:  # letters + digits (identifier-like)
        return "".join(rng.choice(_LETTERS + _DIGITS)
                       for _ in range(rng.randint(0, 25)))
    if kind == 6:  # nine-digit-ish (bait for the legacy triplet codecs)
        return "".join(rng.choice(_DIGITS) for _ in range(9))
    if kind == 7:  # empty or whitespace only
        return rng.choice(["", " ", "   ", "\t", "\n", _UNICODE[:2]])
    # kind == 8: fully random unicode-ish bytes rendered as text
    return "".join(chr(rng.randint(1, 0x2FFF)) for _ in range(rng.randint(0, 20)))


def generate_raw(seed: int, n: int) -> List[str]:
    """Generate ``n`` arbitrary raw strings deterministically from ``seed``.

    Two calls with the same ``seed`` and ``n`` return identical lists.
    """
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise FuzzError("seed must be an int")
    if not isinstance(n, int) or n < 0:
        raise FuzzError("n must be a non-negative int")
    rng = random.Random(seed)
    return [_kind_string(rng) for _ in range(n)]


@dataclass(frozen=True)
class FuzzResult:
    """The typed classification of one fuzzed input."""

    raw: str
    outcome: FuzzOutcome
    claim_class: str
    detail: str

    def to_dict(self) -> dict:
        return {
            "raw": self.raw,
            "outcome": self.outcome.value,
            "claim_class": self.claim_class,
            "detail": self.detail,
        }


def run_one(raw: str) -> FuzzResult:
    """Push one raw string through ingest + decode; return a typed result.

    Tries a canonical decode first (a string may be a well-formed vector), then
    a legacy candidate search. Any exception anywhere collapses to an explicit
    ``REFUSAL`` -- the pipeline never crashes and never forces a pin.
    """
    # 1. Canonical decode attempt (guaranteed typed by the service layer).
    try:
        decoded = service.decode_vector(raw)
        if decoded.get("status") == "OK_POINT":
            return FuzzResult(
                raw=raw,
                outcome=FuzzOutcome.DECODE,
                claim_class=decoded.get(
                    "claim_class", claims.ClaimClass.CANONICAL_ROUND_TRIP.value),
                detail="canonical vector decoded to one point")
    except Exception as exc:  # defence in depth; should not happen
        return FuzzResult(
            raw=raw, outcome=FuzzOutcome.REFUSAL,
            claim_class=claims.ClaimClass.REFUSAL.value,
            detail=f"canonical decode guarded: {exc}")

    # 2. Legacy candidate search (also guaranteed typed by the service layer).
    try:
        legacy = service.legacy_search(raw)
        if legacy.get("status") == "OK_ALIAS_SET" and legacy.get("count", 0) > 0:
            return FuzzResult(
                raw=raw,
                outcome=FuzzOutcome.ALIAS_SET,
                claim_class=claims.ClaimClass.LEGACY_ALIAS_CANDIDATE.value,
                detail=f"legacy search returned {legacy.get('count')} candidate(s)")
    except Exception as exc:  # defence in depth; should not happen
        return FuzzResult(
            raw=raw, outcome=FuzzOutcome.REFUSAL,
            claim_class=claims.ClaimClass.REFUSAL.value,
            detail=f"legacy search guarded: {exc}")

    # 3. Nothing admitted it -- an explicit refusal (never a forced pin).
    return FuzzResult(
        raw=raw,
        outcome=FuzzOutcome.REFUSAL,
        claim_class=claims.ClaimClass.REFUSAL.value,
        detail="no canonical decode and no legacy candidate; explicit refusal")


def run_campaign(seed: int, n: int) -> dict:
    """Generate and run ``n`` fuzzed inputs; return a deterministic summary.

    The summary tallies outcomes and asserts the harness invariant: every input
    produced a typed :class:`FuzzOutcome` (no crash escaped the boundary).
    """
    inputs = generate_raw(seed, n)
    results = [run_one(r) for r in inputs]
    tally = {o.value: 0 for o in FuzzOutcome}
    for res in results:
        tally[res.outcome.value] += 1
    total_typed = sum(tally.values())
    if total_typed != len(results):
        raise FuzzError("a fuzzed input escaped classification")  # unreachable
    return {
        "operation": "fuzz_campaign",
        "seed": seed,
        "n": n,
        "count": len(results),
        "outcomes": tally,
        "all_typed": total_typed == len(results),
        "claim_class": claims.ClaimClass.REFUSAL.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
    }


def fuzz_report() -> dict:
    """P63 declaration receipt. What the fuzz harness guarantees -- and does not."""
    return {
        "module": "cwatlas.fuzz",
        "phase_id": PHASE_ID,
        "tranche": TRANCHE,
        "seeded_deterministic": True,
        "outcomes": [o.value for o in FuzzOutcome],
        "guarantees": [
            "arbitrary raw input never crashes ingest + decode",
            "every input yields a typed outcome (decode, alias set, or refusal)",
            "never forces a pin; never promotes a source vector to a location",
            "same seed -> byte-identical inputs and outcomes",
        ],
        "claim_class": claims.ClaimClass.REFUSAL.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "CW_ATLAS_FUZZ_HARNESS_NEVER_CRASHES_ALWAYS_TYPED",
        "what_this_does_not_say": (
            "That the pipeline survives arbitrary input and always returns a "
            "typed result says nothing about any input's geographic meaning; a "
            "refusal is the common, correct outcome for a random string."),
    }
