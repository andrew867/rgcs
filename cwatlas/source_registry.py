"""P05 -- numeric source registry and non-coercive normalization.

Source records carry raw numbers in many shapes: bare vectors, dial readings,
grouped digit blocks, values with *leading zeros*, timestamps, and quantities
with *no unit at all*. The temptation is to "clean" them -- drop the leading
zero, assume metres or degrees, fold a group into one integer. That is
exactly the forced interpretation this module refuses.

A :class:`RawVector` keeps the **exact original string** and, beside it, a
**normalized parse** that:

* never discards a leading zero (``"007"`` stays three characters, and the
  count of leading zeros is recorded);
* never coerces a unitless value into a unit (``unit=None`` stays ``None``);
* never assigns a geographic meaning.

Every registered value is, at most, a ``SOURCE_CLAIM`` or a
``MATHEMATICAL_TRANSLATION`` -- never a geographic pin.

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED

All parsing is deterministic and derives only from the raw string passed in.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Tuple

from cwatlas import claims

#: Claim classes a registered source value may legally carry. A raw source
#: value is reported (``SOURCE_CLAIM``) or arithmetically re-expressed
#: (``MATHEMATICAL_TRANSLATION``); it is never promoted to a geographic pin.
ALLOWED_CLASSES = frozenset({
    claims.ClaimClass.SOURCE_CLAIM,
    claims.ClaimClass.MATHEMATICAL_TRANSLATION,
})


class RegistryError(ValueError):
    """Raised on a malformed value or a duplicate registration id."""


class ValueKind(Enum):
    """The shapes of raw numeric source values, registered without coercion."""

    NUMERIC_VECTOR = "NUMERIC_VECTOR"
    DIAL_VALUE = "DIAL_VALUE"
    GROUPED_NUMBER = "GROUPED_NUMBER"
    TIMESTAMP = "TIMESTAMP"
    NO_UNIT = "NO_UNIT"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class NormalizedComponent:
    """One parsed token that never loses information from the original.

    ``original`` is the exact substring (leading zeros intact). ``integer``
    is its integer value when the token is a pure digit string, else
    ``None`` -- an ambiguous or non-integral token is *not* forced into a
    number. ``leading_zeros`` is the count of significant-position zeros the
    normalization would otherwise have silently dropped.
    """

    original: str
    integer: Optional[int]
    leading_zeros: int

    def has_leading_zeros(self) -> bool:
        return self.leading_zeros > 0


def _normalize_component(token: str) -> NormalizedComponent:
    """Parse one token, preserving its exact original and leading zeros."""
    if token == "":
        raise RegistryError("empty component; refusing to invent a value")
    if token.isdigit():
        integer = int(token)
        # Leading zeros = characters the canonical integer form would drop.
        leading_zeros = len(token) - len(str(integer))
        return NormalizedComponent(token, integer, leading_zeros)
    # Non-digit token (sign, decimal point, letters): keep verbatim, no int.
    return NormalizedComponent(token, None, 0)


@dataclass(frozen=True)
class RawVector:
    """A registered raw numeric source value: original preserved, parse beside.

    ``raw`` is the exact original string and is authoritative. ``components``
    is the non-coercive parse. ``unit`` is ``None`` for a unitless value and
    is *never* filled in by normalization. ``raw_hash`` binds the original
    string (immutable, per System Contract invariant 1).
    """

    vector_id: str
    raw: str
    kind: ValueKind
    components: Tuple[NormalizedComponent, ...]
    unit: Optional[str]
    separator: str
    raw_hash: str
    claim_class: claims.ClaimClass

    def __post_init__(self) -> None:
        if not self.vector_id:
            raise RegistryError("vector_id must be a non-empty string")
        if self.raw_hash != _sha256(self.raw):
            raise RegistryError(
                "raw_hash does not match raw string: the original string is "
                "immutable and must not be altered")
        if self.claim_class not in ALLOWED_CLASSES:
            raise RegistryError(
                f"a registered source value may only be {sorted(c.value for c in ALLOWED_CLASSES)}; "
                f"{self.claim_class.value} is not permitted (never geographic)")

    def has_leading_zeros(self) -> bool:
        """True iff any component carries a leading zero the parse kept."""
        return any(c.has_leading_zeros() for c in self.components)

    def is_unitless(self) -> bool:
        return self.unit is None

    def as_original(self) -> str:
        """Reconstruct the original string from the preserved components."""
        return self.separator.join(c.original for c in self.components)

    def integer_tuple(self) -> Tuple[Optional[int], ...]:
        """The integer values, with ``None`` where a token is non-integral."""
        return tuple(c.integer for c in self.components)


def normalize(raw: str, separator: str = " ") -> Tuple[NormalizedComponent, ...]:
    """Split ``raw`` on ``separator`` and normalize each token, losslessly.

    Passing ``separator=""`` treats the whole string as one component (a bare
    value like ``"007"``). No token is coerced into a unit or a coordinate.
    """
    if raw == "":
        raise RegistryError("empty raw value; refusing to invent a parse")
    tokens = [raw] if separator == "" else raw.split(separator)
    return tuple(_normalize_component(t) for t in tokens)


def refuse_forced_interpretation(
    value: str,
    *,
    forced_unit: Optional[str] = None,
    forced_meaning: Optional[str] = None,
) -> None:
    """Refuse to coerce a raw value into a unit or a (geographic) meaning.

    Registering a value declares only what the source wrote. Attaching a unit
    the source did not state, or a geographic/destination meaning, invents
    information the data do not support.
    """
    if forced_meaning is not None:
        # Route geographic coercion through the governance refusal.
        claims.refuse_source_as_geographic()
    raise claims.ClaimError(
        f"refused: value {value!r} carries no declared unit; forcing "
        f"{forced_unit!r} onto it would invent an interpretation the source "
        f"did not state. A unitless value stays unitless.")


class SourceRegistry:
    """A registry of raw numeric source values, held without coercion."""

    def __init__(self) -> None:
        self._items: Dict[str, RawVector] = {}

    def __len__(self) -> int:
        return len(self._items)

    def register(
        self,
        vector_id: str,
        raw: str,
        kind: ValueKind,
        *,
        unit: Optional[str] = None,
        separator: str = " ",
        claim_class: claims.ClaimClass = claims.ClaimClass.SOURCE_CLAIM,
    ) -> RawVector:
        """Register one raw value, preserving its exact string and leading zeros.

        ``unit`` defaults to ``None`` and is never inferred. A ``NO_UNIT``
        value with a non-``None`` ``unit`` is refused: normalization does not
        coerce a unitless value into a unit. ``claim_class`` must be in
        :data:`ALLOWED_CLASSES` -- a source value is never geographic.
        """
        if vector_id in self._items:
            raise RegistryError(f"duplicate vector_id {vector_id!r}")
        if claim_class not in ALLOWED_CLASSES:
            raise claims.ClaimError(
                f"refused: {claim_class.value} is not an allowed source claim "
                f"class; a registered value is SOURCE_CLAIM or "
                f"MATHEMATICAL_TRANSLATION, never geographic")
        if kind is ValueKind.NO_UNIT and unit is not None:
            refuse_forced_interpretation(raw, forced_unit=unit)
        sep = "" if separator == "" else separator
        components = normalize(raw, separator=sep)
        vector = RawVector(
            vector_id=vector_id,
            raw=raw,
            kind=kind,
            components=components,
            unit=unit,
            separator=sep,
            raw_hash=_sha256(raw),
            claim_class=claim_class,
        )
        self._items[vector_id] = vector
        return vector

    def get(self, vector_id: str) -> RawVector:
        if vector_id not in self._items:
            raise RegistryError(f"no such vector_id {vector_id!r}")
        return self._items[vector_id]

    @property
    def vectors(self) -> Tuple[RawVector, ...]:
        return tuple(self._items[k] for k in self._items)


def source_registry_report() -> dict:
    """What this module claims -- and, deliberately, what it does not."""
    return {
        "module": "cwatlas.source_registry",
        "phase_id": "P05",
        "value_kinds": [k.value for k in ValueKind],
        "allowed_claim_classes": sorted(c.value for c in ALLOWED_CLASSES),
        "guarantees": [
            "exact original string preserved beside the normalized parse",
            "leading zeros never discarded",
            "unitless values never coerced into a unit",
            "no geographic interpretation assigned",
        ],
        "claim_class": claims.ClaimClass.SOURCE_CLAIM.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "NUMERIC_SOURCE_REGISTRY_NON_COERCIVE_NORMALIZATION",
        "what_this_does_not_say": (
            "A registered value records only what a source wrote. Its "
            "normalized parse asserts no unit the source did not state and no "
            "geographic location. It stays a SOURCE_CLAIM or a "
            "MATHEMATICAL_TRANSLATION, never a pin."),
    }
