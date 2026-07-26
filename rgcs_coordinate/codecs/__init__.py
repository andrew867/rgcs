"""RCW codec registry — civilization-specific wire grammars.

Codecs are civilization-specific (wire radix + packet layout). They
are registered here and kept strictly separate from body profiles: a
codec never knows about shells, gravity or maps, and a plugin cannot
mutate the canonical model or another codec (the registry hands out
copies of its metadata, never the live table).
"""

from __future__ import annotations

from rgcs_coordinate.codecs import federation_terra_30 as ft30

_CODECS = {
    ft30.CODEC_ID: {
        "codec_id": ft30.CODEC_ID,
        "civilization": "Federation/Terra (candidate attribution)",
        "wire_radix": 10,
        "word_bits": ft30.WIDTH_BITS,
        "layout": "F5 | Q22 | S3",
        "status": "STRUCTURAL_GREEN",
        "physical_projection": "UNDERDETERMINED",
        "module": "rgcs_coordinate.codecs.federation_terra_30",
        "notes": ("nine-digit decimal family; longer vectors (31-34 "
                  "bit) are a separate family with no proven bridge "
                  "and are refused, never truncated"),
    },
}


def list_codecs() -> list[dict]:
    """Registered codecs (metadata copies; the registry is immutable)."""
    return [dict(meta) for meta in _CODECS.values()]


def get_codec(codec_id: str):
    """The codec module for an id, or a typed error listing known ids."""
    if codec_id not in _CODECS:
        raise KeyError(
            f"unsupported codec {codec_id!r}; known: {sorted(_CODECS)}")
    return ft30


def codec_info(codec_id: str) -> dict:
    if codec_id not in _CODECS:
        raise KeyError(
            f"unsupported codec {codec_id!r}; known: {sorted(_CODECS)}")
    return dict(_CODECS[codec_id])
