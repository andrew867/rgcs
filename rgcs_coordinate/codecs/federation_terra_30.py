"""RCW P02 — the Federation/Terra 30-bit structural codec (public).

Structural F5 | Q22 | S3 parsing ONLY. This module never performs a
physical Earth projection, and its Morton/octree indices are
hierarchical path registers, never coordinates.

The arithmetic mirrors the frozen repository parser
(``r12.icosapacket``) and is locked to it bit-for-bit by
``tests/rgcs_coordinate/test_rcw_codec_parity.py`` — the frozen parser
stays the authority; this is a dependency-free public adapter of it,
not a reinterpretation. Pure stdlib, deterministic, no network, no
global state.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Sequence

from rgcs_coordinate.domain.claims import ClaimClass, trace_claims

CODEC_ID = "federation-terra-30"
PACKET_FAMILY = "federation-terra-f5-q22-s3-candidate"
TRACE_SCHEMA = "rgcs.structural-trace.v1"

WIDTH_BITS = 30
FACE_BITS = 5
Q22_BITS = 22
SHELL_BITS = 3
Q22_LEVELS = 11
FACE_VALID_MAX = 19          # 20..31 reserved
OCTAL_DIGITS = 10
SPATIAL_OCTAL_DIGITS = 9


class PacketError(ValueError):
    """Invalid input for the 30-bit packet family (never silently fixed)."""


@dataclass(frozen=True)
class MortonAudit:
    """Deinterleaved hierarchical bit paths. Path registers, NOT x/y/z
    positions: any attempt to read them as coordinates is refused by
    :func:`refuse_indices_as_coordinates`."""

    x_bits: str
    y_bits: str
    z_bits: str
    x_index: int
    y_index: int
    z_index: int


@dataclass(frozen=True)
class PacketTrace:
    """One complete reversible structural decode."""

    raw_decimal: str
    width_bits: int
    binary30: str
    octal10: str
    packet_family: str
    face_bits: str
    face_id: int
    face_status: str
    q22_bits: str
    q22_path: tuple[int, ...]
    shell_bits: str
    extracted_shell: int
    spatial_octal_path: str
    morton_audit: MortonAudit
    fixture_label: str | None
    structural_status: str
    physical_projection_status: str
    claim_class: str

    def to_dict(self) -> dict:
        return {
            "schema": TRACE_SCHEMA,
            "raw_decimal": self.raw_decimal,
            "width_bits": self.width_bits,
            "binary30": self.binary30,
            "octal10": self.octal10,
            "packet_family": self.packet_family,
            "face_bits": self.face_bits,
            "face_id": self.face_id,
            "face_status": self.face_status,
            "q22_bits": self.q22_bits,
            "q22_path": list(self.q22_path),
            "shell_bits": self.shell_bits,
            "extracted_shell": self.extracted_shell,
            "spatial_octal_path": self.spatial_octal_path,
            "morton_audit": {
                "x_bits": self.morton_audit.x_bits,
                "y_bits": self.morton_audit.y_bits,
                "z_bits": self.morton_audit.z_bits,
                "x_index": self.morton_audit.x_index,
                "y_index": self.morton_audit.y_index,
                "z_index": self.morton_audit.z_index,
            },
            "fixture_label": self.fixture_label,
            "structural_status": self.structural_status,
            "physical_projection_status": self.physical_projection_status,
            "claim_class": self.claim_class,
            "claims": trace_claims(),
        }


def refuse_indices_as_coordinates(what: str = "coordinates") -> None:
    raise PacketError(
        f"refused: Morton/octree X, Y and Z values are deinterleaved "
        f"hierarchical path indices, not {what}. They are never "
        f"latitude, longitude, Cartesian coordinates, kilometres or "
        f"altitude; conventional coordinates exist only after a named "
        f"downstream projection profile, which is a separate, honest "
        f"step (currently UNDERDETERMINED).")


def _validate_raw(raw: int) -> None:
    if not isinstance(raw, int) or isinstance(raw, bool):
        raise PacketError("packet value must be a plain int")
    if raw < 0:
        raise PacketError("packet value must be non-negative")
    if raw >= (1 << WIDTH_BITS):
        raise PacketError(
            f"value does not fit the {WIDTH_BITS}-bit packet family; "
            f"longer vectors are a SEPARATE family (31–34-bit words, "
            f"no proven version bridge) and are never truncated or "
            f"padded silently.")


def morton_audit(spatial_octal: str) -> MortonAudit:
    if (len(spatial_octal) != SPATIAL_OCTAL_DIGITS
            or any(c not in "01234567" for c in spatial_octal)):
        raise PacketError(
            f"spatial octal path must be exactly "
            f"{SPATIAL_OCTAL_DIGITS} octal digits")
    x = "".join(str((int(c) >> 2) & 1) for c in spatial_octal)
    y = "".join(str((int(c) >> 1) & 1) for c in spatial_octal)
    z = "".join(str(int(c) & 1) for c in spatial_octal)
    return MortonAudit(x_bits=x, y_bits=y, z_bits=z,
                       x_index=int(x, 2), y_index=int(y, 2),
                       z_index=int(z, 2))


def decode(raw: int, fixture_label: str | None = None) -> PacketTrace:
    """Exact structural decode of one 30-bit word."""
    _validate_raw(raw)
    binary = format(raw, f"0{WIDTH_BITS}b")
    octal = format(raw, f"0{OCTAL_DIGITS}o")
    face_bits = binary[:FACE_BITS]
    q22_bits = binary[FACE_BITS:FACE_BITS + Q22_BITS]
    shell_bits = binary[FACE_BITS + Q22_BITS:]
    face = int(face_bits, 2)
    path = tuple(int(q22_bits[i:i + 2], 2) for i in range(0, Q22_BITS, 2))
    spatial = octal[:SPATIAL_OCTAL_DIGITS]
    return PacketTrace(
        raw_decimal=str(raw),
        width_bits=WIDTH_BITS,
        binary30=binary,
        octal10=octal,
        packet_family=PACKET_FAMILY,
        face_bits=face_bits,
        face_id=face,
        face_status=("valid-source-face-range" if face <= FACE_VALID_MAX
                     else "reserved"),
        q22_bits=q22_bits,
        q22_path=path,
        shell_bits=shell_bits,
        extracted_shell=int(shell_bits, 2),
        spatial_octal_path=spatial,
        morton_audit=morton_audit(spatial),
        fixture_label=fixture_label,
        structural_status="EXACT_STRUCTURAL_DECODE",
        physical_projection_status="UNDERDETERMINED",
        claim_class=ClaimClass.EXACT_STRUCTURAL.value,
    )


def encode(face: int, path: Sequence[int], shell: int) -> int:
    """Exact inverse: fields -> 30-bit word. Reserved faces refused."""
    if not isinstance(face, int) or not 0 <= face <= FACE_VALID_MAX:
        raise PacketError(
            f"face must be 0..{FACE_VALID_MAX} (20..31 are reserved and "
            f"name no source face)")
    path = tuple(int(p) for p in path)
    if len(path) != Q22_LEVELS or any(p not in (0, 1, 2, 3) for p in path):
        raise PacketError(
            f"path must be exactly {Q22_LEVELS} quaternary symbols")
    if not isinstance(shell, int) or not 0 <= shell <= 7:
        raise PacketError("shell must fit the 3-bit S3 register (0..7)")
    bits = (format(face, "05b")
            + "".join(format(p, "02b") for p in path)
            + format(shell, "03b"))
    return int(bits, 2)


def roundtrip(raw: int) -> dict:
    """Decode then re-encode; the two must be identical."""
    trace = decode(raw)
    back = encode(trace.face_id, trace.q22_path, trace.extracted_shell)
    return {"raw": raw, "reencoded": back, "exact": back == raw,
            "trace": trace.to_dict()}


def export_trace(trace: PacketTrace) -> str:
    """Canonical JSON serialization of a trace."""
    return json.dumps(trace.to_dict(), indent=2, sort_keys=False) + "\n"


def load_trace(text: str) -> PacketTrace:
    """Load an exported trace, re-deriving and verifying every field.

    The raw decimal is authoritative; every other field is recomputed
    and compared, so a hand-edited trace cannot smuggle in a different
    face, path or shell.
    """
    payload = json.loads(text)
    if payload.get("schema") != TRACE_SCHEMA:
        raise PacketError(
            f"unsupported trace schema {payload.get('schema')!r}; "
            f"expected {TRACE_SCHEMA}")
    trace = decode(int(payload["raw_decimal"]),
                   fixture_label=payload.get("fixture_label"))
    fresh = trace.to_dict()
    for key in ("binary30", "octal10", "face_id", "q22_path",
                "extracted_shell", "spatial_octal_path"):
        if payload.get(key) != fresh[key]:
            raise PacketError(
                f"trace field {key!r} does not match the packet "
                f"arithmetic for raw_decimal={payload['raw_decimal']}: "
                f"stored {payload.get(key)!r}, derived {fresh[key]!r}")
    return trace
