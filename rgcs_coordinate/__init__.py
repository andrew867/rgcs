"""rgcs_coordinate — the RGCS Coordinate Workbench public package.

A typed, deterministic structural decoder/encoder for the
Federation/Terra candidate 30-bit F5 | Q22 | S3 packet family, with an
honest candidate-projection layer.

Claim boundary (embedded in every trace):

* ``SOURCE_ORIGIN_VALIDATED: no``
* ``STONEHENGE_INDEPENDENTLY_DECODED: no`` — ``165876523`` is a
  supplied training equality and regression fixture
* ``OCTAL_PACKET_STRUCTURE_RECOVERED: yes``
* ``PHYSICAL_PROJECTION: underdetermined`` unless a later receipt
  proves otherwise

Structural decode is pure stdlib and works everywhere; the candidate
projection profile uses the repository scientific stack when
installed and reports ``PROFILE_BACKEND_UNAVAILABLE`` otherwise.
Morton/octree indices are hierarchical path registers — never
latitude, longitude, Cartesian coordinates, kilometres or altitude.
"""

from __future__ import annotations

from rgcs_coordinate.codecs import get_codec, list_codecs
from rgcs_coordinate.codecs.federation_terra_30 import (
    PacketError,
    PacketTrace,
    refuse_indices_as_coordinates,
)
from rgcs_coordinate.codecs import federation_terra_30 as _ft30
from rgcs_coordinate.projection import (
    inverse_project,
    list_body_profiles,
    project_coordinate,
)

__version__ = "0.1.0.dev0"

DEFAULT_CODEC = "federation-terra-30"


def decode_coordinate(raw: int, codec: str = DEFAULT_CODEC,
                      fixture_label: str | None = None) -> PacketTrace:
    """Exact structural decode of one packet word."""
    return get_codec(codec).decode(raw, fixture_label=fixture_label)


def encode_coordinate(face: int, path, shell: int,
                      codec: str = DEFAULT_CODEC) -> int:
    """Exact structural encode (fields -> word)."""
    return get_codec(codec).encode(face, path, shell)


def roundtrip_coordinate(raw: int, codec: str = DEFAULT_CODEC) -> dict:
    """Decode then re-encode; reports exactness."""
    return get_codec(codec).roundtrip(raw)


def export_trace(trace: PacketTrace) -> str:
    """Canonical JSON for a trace."""
    return _ft30.export_trace(trace)


def load_trace(text: str) -> PacketTrace:
    """Load an exported trace, verifying it against the arithmetic."""
    return _ft30.load_trace(text)


__all__ = [
    "__version__", "DEFAULT_CODEC",
    "PacketError", "PacketTrace",
    "decode_coordinate", "encode_coordinate", "roundtrip_coordinate",
    "list_codecs", "list_body_profiles",
    "project_coordinate", "inverse_project",
    "export_trace", "load_trace",
    "refuse_indices_as_coordinates",
]
