"""Public structural codec for the 27/30/33/36-bit vector family.

The word layout is ``R4 | S8 | P12 | tail``. The tail contains zero to
three optional 3-bit epoch/state groups followed by one mandatory 3-bit
check group. This module performs reversible bit parsing only; it does not
map a word to a physical location or infer a physical interpretation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


CODEC_ID = "terra-variable-r4-s8-p12"
ROOT_BITS = 4
SURFACE_BITS = 8
PATH_BITS = 12
FIXED_BITS = ROOT_BITS + SURFACE_BITS + PATH_BITS
GROUP_BITS = 3
TAIL_WIDTHS = (3, 6, 9, 12)
VALID_WIDTHS = tuple(FIXED_BITS + width for width in TAIL_WIDTHS)


class VariableCodecError(ValueError):
    """Raised when a value or field set is outside the structural family."""


@dataclass(frozen=True)
class VariableWord:
    value: int
    width_bits: int
    bits: str
    octal: str
    root: int
    surface: int
    path: int
    epoch_groups: tuple[int, ...]
    check_group: int

    def to_dict(self) -> dict[str, object]:
        return {
            "codec_id": CODEC_ID,
            "value": self.value,
            "width_bits": self.width_bits,
            "bits": self.bits,
            "octal": self.octal,
            "root": self.root,
            "surface": self.surface,
            "path": self.path,
            "epoch_groups": list(self.epoch_groups),
            "check_group": self.check_group,
            "structural_status": "EXACT_REVERSIBLE",
            "physical_projection_status": "NOT_PERFORMED",
        }


def _plain_int(value: object, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise VariableCodecError(f"{name} must be a plain int")
    return value


def infer_width(value: int) -> int:
    """Return the smallest supported width containing ``value``."""
    value = _plain_int(value, "value")
    if value < 0:
        raise VariableCodecError("value must be non-negative")
    bit_length = max(1, value.bit_length())
    for width in VALID_WIDTHS:
        if bit_length <= width:
            return width
    raise VariableCodecError(
        f"value needs {bit_length} bits; maximum is {VALID_WIDTHS[-1]}"
    )


def decode(value: int, *, width_bits: int | None = None) -> VariableWord:
    """Decode one word, optionally preserving an explicitly framed width."""
    value = _plain_int(value, "value")
    if value < 0:
        raise VariableCodecError("value must be non-negative")
    width = infer_width(value) if width_bits is None else _plain_int(
        width_bits, "width_bits"
    )
    if width not in VALID_WIDTHS:
        raise VariableCodecError(f"width_bits must be one of {VALID_WIDTHS}")
    if value >= 1 << width:
        raise VariableCodecError(f"value does not fit in {width} bits")

    tail_width = width - FIXED_BITS
    position = width
    position -= ROOT_BITS
    root = (value >> position) & 0xF
    position -= SURFACE_BITS
    surface = (value >> position) & 0xFF
    position -= PATH_BITS
    path = (value >> position) & 0xFFF
    tail = value & ((1 << tail_width) - 1)
    groups = tuple(
        (tail >> (tail_width - GROUP_BITS * (index + 1))) & 0x7
        for index in range(tail_width // GROUP_BITS)
    )
    return VariableWord(
        value=value,
        width_bits=width,
        bits=format(value, f"0{width}b"),
        octal=format(value, f"0{width // 3}o"),
        root=root,
        surface=surface,
        path=path,
        epoch_groups=groups[:-1],
        check_group=groups[-1],
    )


def encode(root: int, surface: int, path: int,
           epoch_groups: Sequence[int] = (), check_group: int = 0) -> VariableWord:
    """Encode fields and return the value together with its framed width."""
    root = _plain_int(root, "root")
    surface = _plain_int(surface, "surface")
    path = _plain_int(path, "path")
    check_group = _plain_int(check_group, "check_group")
    groups = tuple(_plain_int(value, "epoch group") for value in epoch_groups)
    if not 0 <= root < 16:
        raise VariableCodecError("root must fit R4")
    if not 0 <= surface < 256:
        raise VariableCodecError("surface must fit S8")
    if not 0 <= path < 4096:
        raise VariableCodecError("path must fit P12")
    if len(groups) > 3:
        raise VariableCodecError("at most three optional groups are supported")
    if any(not 0 <= value < 8 for value in (*groups, check_group)):
        raise VariableCodecError("tail groups must be in 0..7")

    tail_groups = (*groups, check_group)
    width = FIXED_BITS + GROUP_BITS * len(tail_groups)
    header = (root << (SURFACE_BITS + PATH_BITS)) | (surface << PATH_BITS) | path
    tail = 0
    for group in tail_groups:
        tail = (tail << GROUP_BITS) | group
    value = (header << (width - FIXED_BITS)) | tail
    return decode(value, width_bits=width)


def roundtrip(word: VariableWord) -> bool:
    """Return true only when field re-encoding preserves value and width."""
    rebuilt = encode(
        word.root,
        word.surface,
        word.path,
        word.epoch_groups,
        word.check_group,
    )
    return rebuilt.value == word.value and rebuilt.width_bits == word.width_bits


__all__ = [
    "CODEC_ID",
    "FIXED_BITS",
    "TAIL_WIDTHS",
    "VALID_WIDTHS",
    "VariableCodecError",
    "VariableWord",
    "decode",
    "encode",
    "infer_width",
    "roundtrip",
]
