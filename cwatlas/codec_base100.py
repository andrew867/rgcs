"""P21 — CW-BASE100-1 variable-depth two-decimal-token codec.

A ``CW-BASE100-1`` vector is a string of *two-decimal-digit tokens* — each
token is exactly two ASCII digits and names a value in ``00..99`` (integer
``0..99``). A raw string of ``N`` concatenated tokens decodes to a **depth-N
path**: ``"001299"`` -> tokens ``["00", "12", "99"]`` -> path ``(0, 12, 99)``.

The grammar is reversible by construction. :func:`encode` maps a path of
integers to the token string; :func:`decode_to_path` maps a token string back
to the exact same path. The round-trip is exact for every well-formed path,
including the empty (depth-0) path.

This is a *canonical, reversible* arithmetic codec. Its round-trip is a
verified property of the codec (``CANONICAL_ROUND_TRIP``) — a math fact about
the grammar, not a claim that any decoded path identifies a real location.
Source-vector geographic semantics remain ``NOT_CLAIMED``.

Validation lives at the boundary. :func:`decode` never guesses: a malformed
token string (odd length, or any non-ASCII-digit character) yields an explicit
``INVALID`` result rather than a silent repair. The strict
:func:`decode_to_path` refuses malformed input with a :class:`ClaimError`.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Sequence

from cwatlas.claims import ClaimClass, ClaimError

#: Codec identity. The version is part of every receipt (invariant 2).
CODEC_ID = "CW-BASE100-1"
CODEC_VERSION = "1.0.0"

#: This codec is a canonical reversible codec, not a legacy alias candidate.
IS_LEGACY_CANDIDATE = False

#: Grammar constants: each token is exactly two decimal digits, value 0..99.
TOKEN_DIGITS = 2
TOKEN_MIN = 0
TOKEN_MAX = 99

_ASCII_DIGITS = frozenset("0123456789")

#: CodecResult status strings (subset of codec_result.schema.json enum).
STATUS_OK_POINT = "OK_POINT"
STATUS_INVALID = "INVALID"


@dataclass(frozen=True)
class CodecResult:
    """A typed codec result conforming to ``codec_result.schema.json``.

    ``candidates`` is a tuple of plain dicts so the result serialises directly
    to the schema (each candidate is a JSON object). ``receipt_id`` is a
    deterministic content hash — no wall-clock, so a clean checkout reproduces
    it exactly.
    """

    status: str
    codec_id: str
    candidates: tuple[dict, ...] = ()
    receipt_id: str = ""
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        d: dict = {
            "status": self.status,
            "codec_id": self.codec_id,
            "candidates": [dict(c) for c in self.candidates],
            "receipt_id": self.receipt_id,
        }
        if self.warnings:
            d["warnings"] = list(self.warnings)
        return d


def _receipt_id(codec_id: str, raw: str) -> str:
    """A deterministic receipt id from the codec identity and the raw string."""
    digest = hashlib.sha256(
        f"{codec_id}|{CODEC_VERSION}|{raw}".encode("utf-8")).hexdigest()[:16]
    return f"rcpt:{codec_id}:{digest}"


def _is_wellformed(raw: str) -> bool:
    return (
        isinstance(raw, str)
        and len(raw) % TOKEN_DIGITS == 0
        and all(ch in _ASCII_DIGITS for ch in raw)
    )


def encode(path: Sequence[int]) -> str:
    """Encode a depth-N path of integers ``0..99`` to a token string.

    Refuses a non-iterable, a string/bytes passed as a path, a non-integer or
    boolean element, or any value outside ``0..99`` — these are malformed
    canonical inputs, not boundary data, so they raise rather than returning a
    result state.
    """
    if isinstance(path, (str, bytes, bytearray)):
        raise ClaimError(
            f"{CODEC_ID} encode expects a sequence of ints, not a "
            f"{type(path).__name__}.")
    tokens: list[str] = []
    for index, value in enumerate(path):
        if isinstance(value, bool) or not isinstance(value, int):
            raise ClaimError(
                f"{CODEC_ID} path element {index} must be an int in "
                f"[{TOKEN_MIN}, {TOKEN_MAX}], got {value!r}.")
        if not TOKEN_MIN <= value <= TOKEN_MAX:
            raise ClaimError(
                f"{CODEC_ID} path element {index}={value} out of range "
                f"[{TOKEN_MIN}, {TOKEN_MAX}].")
        tokens.append(f"{value:0{TOKEN_DIGITS}d}")
    return "".join(tokens)


def decode_to_path(raw: str) -> tuple[int, ...]:
    """Strict decode: return the exact depth-N path, or refuse malformed input.

    A malformed token string (not a str, odd length, or any non-ASCII-digit
    character) is refused with a :class:`ClaimError`. The empty string decodes
    to the empty (depth-0) path.
    """
    if not isinstance(raw, str):
        raise ClaimError(
            f"{CODEC_ID} malformed: raw must be a str, got "
            f"{type(raw).__name__}.")
    if len(raw) % TOKEN_DIGITS != 0:
        raise ClaimError(
            f"{CODEC_ID} malformed: token string length {len(raw)} is not a "
            f"multiple of {TOKEN_DIGITS} (odd-length token).")
    if any(ch not in _ASCII_DIGITS for ch in raw):
        raise ClaimError(
            f"{CODEC_ID} malformed: tokens must be ASCII decimal digits 0-9.")
    return tuple(
        int(raw[i:i + TOKEN_DIGITS]) for i in range(0, len(raw), TOKEN_DIGITS))


def _candidate(path: tuple[int, ...]) -> dict:
    return {
        "codec_id": CODEC_ID,
        "version": CODEC_VERSION,
        "claim_class": ClaimClass.CANONICAL_ROUND_TRIP.value,
        "path": list(path),
        "depth": len(path),
        "tokens": [f"{v:0{TOKEN_DIGITS}d}" for v in path],
        "reversible": True,
    }


def decode(raw: str) -> CodecResult:
    """Boundary decode: return a typed :class:`CodecResult`, never a guess.

    A well-formed token string yields a single ``OK_POINT`` result whose one
    candidate is the exact depth-N path. Malformed input yields an explicit
    ``INVALID`` result carrying the refusal reason as a warning.
    """
    if not _is_wellformed(raw):
        raw_repr = raw if isinstance(raw, str) else repr(raw)
        return CodecResult(
            status=STATUS_INVALID,
            codec_id=CODEC_ID,
            candidates=(),
            receipt_id=_receipt_id(CODEC_ID, raw_repr),
            warnings=(
                f"{CODEC_ID} malformed: input is not a whole number of "
                f"two-ASCII-digit tokens; refused (no silent repair).",),
        )
    path = decode_to_path(raw)
    return CodecResult(
        status=STATUS_OK_POINT,
        codec_id=CODEC_ID,
        candidates=(_candidate(path),),
        receipt_id=_receipt_id(CODEC_ID, raw),
    )


class Base100Codec:
    """Codec-protocol wrapper: ``codec_id``, ``version``, ``encode``, ``decode``."""

    codec_id = CODEC_ID
    version = CODEC_VERSION
    is_legacy_candidate = IS_LEGACY_CANDIDATE
    round_trips = True

    def encode(self, path: Sequence[int]) -> str:
        return encode(path)

    def decode(self, raw: str) -> CodecResult:
        return decode(raw)


#: The codec object(s) this module contributes to the registry (P24).
CODEC = Base100Codec()
CODECS = (CODEC,)


def codec_base100_report() -> dict:
    """P21 declaration receipt. Reversible arithmetic; nothing is measured."""
    return {
        "phase_id": "P21",
        "codec_id": CODEC_ID,
        "version": CODEC_VERSION,
        "what_this_is": (
            "a variable-depth grammar of two-decimal-digit tokens (00..99); "
            "reversible token<->value; a string of N tokens decodes to a "
            "depth-N path; encode/decode round-trip exactly."),
        "claim_class": ClaimClass.CANONICAL_ROUND_TRIP.value,
        "token_digits": TOKEN_DIGITS,
        "token_range": [TOKEN_MIN, TOKEN_MAX],
        "reversible": True,
        "is_legacy_candidate": IS_LEGACY_CANDIDATE,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "GREEN_R10_8_1_P21_CW_BASE100_VARIABLE_DEPTH_TOKEN_CODEC",
    }
