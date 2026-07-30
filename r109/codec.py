"""R10.9 depth dispatch: T10 compact family / T11 refined family.

T10 delegates to the FROZEN public parser
(:mod:`rgcs_coordinate.codecs.federation_terra_30`) — no
reimplementation, no reinterpretation. T11 values are NEVER truncated
into the compact parser; they route to the finite candidate registry
(:mod:`r109.t11_candidates`) which reports aliases rather than
inventing the unknown interleave.

Refused here, permanently:

- decimal-triplet XYZ readings;
- truncation of long values to 30 bits;
- the old general affine bridge (y=(923*x+550585316) mod 2^30);
- modulo-20 promotion of reserved faces;
- a literal physical F5=23.
"""

from __future__ import annotations

from dataclasses import dataclass

from rgcs_coordinate.codecs import federation_terra_30 as t10

from r109.types import (
    CodecTypeError,
    CompactAddress,
    WireAddress,
)

T10_OCTAL_DEPTH = 10
T11_OCTAL_DEPTH = 11

#: The superseded general affine bridge, kept ONLY so tests can prove it
#: is refused in production (R109-MTL-02-SUPERSEDED).
_SUPERSEDED_AFFINE = ("y = (923*x + 550585316) mod 2^30",
                      923, 550585316)


class DepthError(CodecTypeError):
    """Wire value does not belong to a supported octal-depth family."""


def classify(wire: WireAddress) -> str:
    """T10 / T11 family selection by octal depth. Depth<=10 with a
    30-bit-range value is compact; depth 11 is the refined family."""
    if wire.raw_decimal < (1 << 30) and wire.octal_depth <= T10_OCTAL_DEPTH:
        return "T10"
    if wire.octal_depth == T11_OCTAL_DEPTH:
        return "T11"
    raise DepthError(
        f"octal depth {wire.octal_depth} is outside the supported "
        f"families (10 = compact T10, 11 = refined T11); deeper "
        f"recursion is not yet source-confirmed and is refused, never "
        f"truncated")


def decode_compact(wire: WireAddress) -> tuple[CompactAddress, dict]:
    """Exact T10 decode via the frozen parser; returns typed fields and
    the full frozen trace dict."""
    if classify(wire) != "T10":
        raise DepthError(
            f"{wire.raw_decimal} is not a compact T10 value; long "
            f"values are never truncated to 30 bits")
    trace = t10.decode(wire.raw_decimal)
    compact = CompactAddress(f5=trace.face_id,
                             q22_path=trace.q22_path,
                             s3=trace.extracted_shell)
    return compact, trace.to_dict()


def encode_compact(compact: CompactAddress) -> int:
    """Exact inverse via the frozen encoder (reserved faces refused)."""
    return t10.encode(compact.f5, compact.q22_path, compact.s3)


def refuse_affine_bridge(*_a, **_k) -> None:
    """The old general affine long->compact bridge is SUPERSEDED
    (R109-MTL-02-SUPERSEDED) and never runs in production."""
    raise CodecTypeError(
        "refused: the general affine bridge "
        f"{_SUPERSEDED_AFFINE[0]!r} is a superseded historical model "
        "(see r109.superseded); long vectors are decoded by the typed "
        "T11 candidate registry, never by affine canonicalization")


def refuse_truncation(raw: int) -> None:
    """Explicit refusal helper: T11 values never enter the T10 parser."""
    raise CodecTypeError(
        f"refused: {raw} is an 11-octal-digit family value; it is "
        f"never truncated or padded into the 30-bit compact parser")


def refuse_decimal_triplet_xyz(*_a, **_k) -> None:
    raise CodecTypeError(
        "refused: decimal-triplet XYZ readings of wire values are a "
        "stale model; wire values convert to binary/octal before any "
        "spatial decoding (R109-PKT-01)")


def refuse_reserved_face_promotion(face: int) -> None:
    raise CodecTypeError(
        f"refused: face {face} is in the reserved range 20..31; "
        f"modulo-20 promotion of reserved faces is a stale model and "
        f"a literal physical F5=23 does not name a source face "
        f"(R109-FACE-03)")
