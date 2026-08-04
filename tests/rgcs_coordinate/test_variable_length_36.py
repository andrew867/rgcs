"""Acceptance tests for the public variable-length vector codec."""

from __future__ import annotations

import pytest

from rgcs_coordinate.codecs import variable_length_36 as codec


@pytest.mark.parametrize("epoch_groups", [(), (1,), (1, 2), (1, 2, 3)])
def test_every_supported_width_roundtrips(epoch_groups) -> None:
    word = codec.encode(2, 0xA5, 0xABC, epoch_groups, check_group=7)
    assert word.width_bits == 27 + 3 * len(epoch_groups)
    assert len(word.octal) == word.width_bits // 3
    assert codec.roundtrip(word)
    assert codec.decode(word.value, width_bits=word.width_bits) == word


def test_explicit_width_preserves_leading_zero_root() -> None:
    word = codec.encode(0, 1, 2, (3, 4, 5), check_group=6)
    assert word.width_bits == 36
    assert word.bits.startswith("0000")
    assert codec.decode(word.value, width_bits=36) == word


def test_structural_output_refuses_physical_projection() -> None:
    row = codec.encode(2, 1, 3, check_group=4).to_dict()
    assert row["structural_status"] == "EXACT_REVERSIBLE"
    assert row["physical_projection_status"] == "NOT_PERFORMED"


@pytest.mark.parametrize(
    "call",
    [
        lambda: codec.decode(-1),
        lambda: codec.decode(1 << 36),
        lambda: codec.decode(1, width_bits=29),
        lambda: codec.encode(16, 0, 0),
        lambda: codec.encode(0, 256, 0),
        lambda: codec.encode(0, 0, 4096),
        lambda: codec.encode(0, 0, 0, (1, 2, 3, 4)),
        lambda: codec.encode(0, 0, 0, check_group=8),
    ],
)
def test_invalid_values_are_refused(call) -> None:
    with pytest.raises(codec.VariableCodecError):
        call()
