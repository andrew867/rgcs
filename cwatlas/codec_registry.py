"""P24 — Codec plugin registry and alias-set API.

A small, decoupled plugin surface for the CW Atlas codecs. A **codec** is any
object exposing four things — ``codec_id`` (str), ``version`` (str), and
callable ``encode`` / ``decode`` — so codecs stay independent and can be built
in parallel. The registry never hard-imports specific codec modules to do its
job: :func:`build_default_registry` *discovers* the available codec modules
(``codec_pack40``, ``codec_pack38``, ``codec_base100``, ``codec_triplet9``)
with a ``try/except`` per module, so a module that does not yet exist is simply
skipped.

The **alias-set API** enforces System Contract invariant 4: *a legacy candidate
decoder may return zero, one, or many aliases — it may not force one pin.*
:meth:`CodecRegistry.decode_all` runs every registered *legacy* codec over a
raw string and returns an :class:`AliasSet` holding ``0..N``
``LEGACY_ALIAS_CANDIDATE`` decodes, each carrying a score, an uncertainty, and
a search-space count. The set may be empty. Asking the API to collapse a
multi-candidate set to a single pin is refused — it delegates to
:func:`cwatlas.claims.refuse_alias_as_unique`.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass

from cwatlas import claims
from cwatlas.claims import ClaimClass, ClaimError

#: The candidate codec modules to discover, in deterministic order. Modules
#: that are absent (e.g. a sibling still building) are skipped, not required.
CANDIDATE_MODULES = (
    "codec_pack40",
    "codec_pack38",
    "codec_base100",
    "codec_triplet9",
)


def _is_codec(obj: object) -> bool:
    return (
        isinstance(getattr(obj, "codec_id", None), str)
        and isinstance(getattr(obj, "version", None), str)
        and callable(getattr(obj, "encode", None))
        and callable(getattr(obj, "decode", None))
    )


@dataclass(frozen=True)
class AliasCandidate:
    """One admissible legacy decode within an :class:`AliasSet`.

    Always a ``LEGACY_ALIAS_CANDIDATE`` — one reading among a set, never a
    forced pin. It quantifies its own weakness: ``score`` (relative
    admissibility, not a probability), ``uncertainty``, and
    ``search_space_count`` (how many inputs the codec could represent).
    """

    codec_id: str
    version: str
    claim_class: str
    value: dict
    score: float
    uncertainty: float
    search_space_count: int

    def to_dict(self) -> dict:
        return {
            "codec_id": self.codec_id,
            "version": self.version,
            "claim_class": self.claim_class,
            "value": dict(self.value),
            "score": self.score,
            "uncertainty": self.uncertainty,
            "search_space_count": self.search_space_count,
        }


@dataclass(frozen=True)
class AliasSet:
    """A container of ``0..N`` legacy alias candidates for one raw string.

    The set may be empty (no legacy codec admitted the input). It never forces
    one pin: :meth:`require_unique_pin` refuses a multi-candidate (or empty)
    set by delegating to :func:`cwatlas.claims.refuse_alias_as_unique`.
    """

    raw: str
    candidates: tuple[AliasCandidate, ...] = ()

    def __len__(self) -> int:
        return len(self.candidates)

    def is_empty(self) -> bool:
        return not self.candidates

    def require_unique_pin(self) -> AliasCandidate:
        """Return the sole candidate, or refuse (invariant 4).

        A genuinely unique decode (exactly one candidate) is returned. Zero or
        many candidates is refused — forcing one pin from a multi-candidate (or
        empty) set would invent precision the data do not support.
        """
        if len(self.candidates) == 1:
            return self.candidates[0]
        claims.refuse_alias_as_unique(self.candidates)  # always raises
        raise AssertionError("unreachable")  # pragma: no cover

    def to_dict(self) -> dict:
        return {
            "raw": self.raw,
            "count": len(self.candidates),
            "candidates": [c.to_dict() for c in self.candidates],
        }


class CodecRegistry:
    """A registry of codec plugins keyed by ``codec_id``."""

    def __init__(self) -> None:
        self._codecs: dict[str, object] = {}

    def register(self, codec: object) -> object:
        """Register a codec exposing ``codec_id``, ``version``, ``encode``,
        ``decode``. Refuses a non-conforming object or a duplicate id."""
        if not _is_codec(codec):
            raise ClaimError(
                "refused: a codec must expose codec_id (str), version (str), "
                "and callable encode/decode.")
        cid = codec.codec_id  # type: ignore[attr-defined]
        if cid in self._codecs:
            raise ClaimError(f"refused: codec {cid!r} is already registered.")
        self._codecs[cid] = codec
        return codec

    def get(self, codec_id: str) -> object:
        try:
            return self._codecs[codec_id]
        except KeyError:
            raise ClaimError(f"unknown codec {codec_id!r}.") from None

    def codec_ids(self) -> list[str]:
        return sorted(self._codecs)

    def all_codecs(self) -> list[object]:
        return [self._codecs[c] for c in sorted(self._codecs)]

    def legacy_codecs(self) -> list[object]:
        """Registered codecs flagged as legacy alias candidates, sorted."""
        return [
            c for c in self.all_codecs()
            if getattr(c, "is_legacy_candidate", False)
        ]

    def decode_all(self, raw: str) -> AliasSet:
        """Run every registered legacy codec over ``raw`` and collect an
        :class:`AliasSet` (possibly empty). Deterministic order by codec id."""
        candidates: list[AliasCandidate] = []
        for codec in self.legacy_codecs():
            result = codec.decode(raw)  # type: ignore[attr-defined]
            if not str(getattr(result, "status", "")).startswith("OK"):
                continue
            for raw_candidate in getattr(result, "candidates", ()):
                candidates.append(
                    AliasCandidate(
                        codec_id=getattr(codec, "codec_id"),
                        version=getattr(codec, "version"),
                        claim_class=ClaimClass.LEGACY_ALIAS_CANDIDATE.value,
                        value=dict(raw_candidate),
                        score=float(raw_candidate.get("score", 0.0)),
                        uncertainty=float(raw_candidate.get("uncertainty", 1.0)),
                        search_space_count=int(
                            raw_candidate.get("search_space_count", -1)),
                    )
                )
        return AliasSet(raw=raw, candidates=tuple(candidates))

    def refuse_alias_as_unique(self, alias_set: AliasSet) -> None:
        """Delegate the invariant-4 refusal to the governance core."""
        claims.refuse_alias_as_unique(alias_set.candidates)


def build_default_registry() -> CodecRegistry:
    """Discover and register the available codec modules with per-module
    ``try/except``. Absent modules are skipped; duplicate ids are ignored."""
    registry = CodecRegistry()
    for module_name in CANDIDATE_MODULES:
        try:
            module = importlib.import_module(f"cwatlas.{module_name}")
        except Exception:
            continue
        for codec in getattr(module, "CODECS", ()):
            if not _is_codec(codec):
                continue
            try:
                registry.register(codec)
            except ClaimError:
                continue
    return registry


def codec_registry_report() -> dict:
    """P24 declaration receipt. The API surfaces alias sets; it never pins."""
    registry = build_default_registry()
    return {
        "phase_id": "P24",
        "what_this_is": (
            "a codec plugin registry and alias-set API; legacy codecs return "
            "typed LEGACY_ALIAS_CANDIDATE decodes with score, uncertainty, and "
            "search-space count; the API never forces one pin (invariant 4)."),
        "claim_class": ClaimClass.LEGACY_ALIAS_CANDIDATE.value,
        "candidate_modules": list(CANDIDATE_MODULES),
        "registered_codec_ids": registry.codec_ids(),
        "legacy_codec_ids": sorted(
            getattr(c, "codec_id") for c in registry.legacy_codecs()),
        "invariant_4": (
            "a legacy candidate decoder may return zero, one, or many aliases; "
            "it may not force one pin. require_unique_pin refuses a "
            "multi-candidate or empty set via claims.refuse_alias_as_unique."),
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "GREEN_R10_8_1_P24_CODEC_PLUGIN_AND_ALIAS_SET_API",
    }
