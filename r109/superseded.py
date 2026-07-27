"""R10.9 superseded-model ledger (Phase 5.3, R109-MTL-02/03).

Superseded interpretations are PRESERVED here — retrievable for
historical audit, unusable in production. Every accessor demands an
explicit historical profile id so nothing reaches these models by
default code paths.
"""

from __future__ import annotations

from r109.types import CodecTypeError

HISTORICAL_PROFILE = "HISTORICAL_R10_8_AFFINE_CANONICALIZATION"

LEDGER = {
    "HISTORICAL_R10_8_AFFINE_CANONICALIZATION": {
        "model": "y = (923*x + 550585316) mod 2^30",
        "purpose": "general long->compact canonicalization bridge",
        "status": "SUPERSEDED (R109-MTL-02-SUPERSEDED)",
        "superseded_by": "typed T10/T11 depth families (r109.codec)",
        "known_products": {"165879243": 168500683},
        "why_stale": "the source confirmed 165879243 is itself a DIRECT "
                     "compact packet; the bridge is unjustified unless an "
                     "independently recovered source transform revives it",
    },
    "HISTORICAL_MONTREAL_TRANSCRIPTION": {
        "value": 168729543,
        "status": "SUPERSEDED (R109-MTL-03-SUPERSEDED)",
        "superseded_by": "direct compact Montréal 165879243 (R109-MTL-01)",
        "why_stale": "older transcription; preserved as provenance only",
    },
}


def historical_affine(x: int, *, profile: str | None = None) -> int:
    """The superseded affine bridge — HISTORICAL ACCESS ONLY.

    Refuses to run unless the caller explicitly selects the historical
    profile by exact id; production code must never pass it.
    """
    if profile != HISTORICAL_PROFILE:
        raise CodecTypeError(
            "refused: the general affine bridge is superseded "
            "(R109-MTL-02-SUPERSEDED); historical replay requires the "
            f"explicit profile id {HISTORICAL_PROFILE!r}")
    return (923 * x + 550585316) % (1 << 30)


def ledger_dict() -> dict:
    return {"schema": "rgcs.r109.superseded-models.v1", "models": LEDGER}
