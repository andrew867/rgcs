"""Recursive interleaved XYZ parser — ordered triplet levels (R10.8.4 §1).

No decimal flattening, no base-100 fallback, no shell-from-last-digit rule.
A vector may end after X or Y inside its last level: that partial level is
represented explicitly, never padded and never rejected.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Rejected interpretations. Regression tests assert this registry names
#: them and that no production path in this package implements them.
REJECTED_MODELS = (
    "FIVE_BASE100_TOKENS_FOLD_MOD20",
    "CONTIGUOUS_XYZ_BLOCKS",
    "COMPLETED_DECIMAL_FRACTIONS",
    "DIRECT_XYZ_TO_LATLON",
    "SHELL_FROM_FINAL_DIGIT",
    "FIXED_NINE_DIGIT_MAX_LENGTH",
)


@dataclass(frozen=True)
class CWRawVector:
    """A raw decimal source-vector string (validated, arbitrary length)."""

    digits: str

    def __post_init__(self):
        if not self.digits or not self.digits.isdigit():
            raise ValueError(
                f"source vector must be decimal digits: {self.digits!r}")


@dataclass(frozen=True)
class CWLevelInstruction:
    """One complete refinement level: (X, Y, Z) digits, each 0..9."""

    x_digit: int
    y_digit: int
    z_digit: int

    def __post_init__(self):
        for d in (self.x_digit, self.y_digit, self.z_digit):
            if not 0 <= d <= 9:
                raise ValueError(f"digit out of range: {d}")

    def as_tuple(self) -> tuple[int, int, int]:
        return (self.x_digit, self.y_digit, self.z_digit)


@dataclass(frozen=True)
class CWPartialLevel:
    """An incomplete final level: X alone, or X and Y (never Y/Z alone —
    digits append in X, Y, Z order)."""

    x_digit: int | None = None
    y_digit: int | None = None

    def __post_init__(self):
        if self.y_digit is not None and self.x_digit is None:
            raise ValueError("Y digit cannot precede X in the stream")
        for d in (self.x_digit, self.y_digit):
            if d is not None and not 0 <= d <= 9:
                raise ValueError(f"digit out of range: {d}")

    @property
    def axes_present(self) -> tuple[str, ...]:
        out = []
        if self.x_digit is not None:
            out.append("X")
        if self.y_digit is not None:
            out.append("Y")
        return tuple(out)


def parse_levels(raw: str | CWRawVector
                 ) -> tuple[tuple[CWLevelInstruction, ...],
                            CWPartialLevel | None]:
    """Parse digits into ordered complete levels plus an optional partial.

    ``165876523`` -> ``((1,6,5), (8,7,6), (5,2,3))``, no partial.
    ``16782953437`` -> ``((1,6,7), (8,2,9), (5,3,4))``, partial ``(3, 7)``.
    """
    vec = raw if isinstance(raw, CWRawVector) else CWRawVector(raw)
    d = [int(c) for c in vec.digits]
    levels = tuple(CWLevelInstruction(*d[i:i + 3])
                   for i in range(0, len(d) - len(d) % 3, 3))
    rem = d[len(d) - len(d) % 3:]
    partial = None
    if len(rem) == 1:
        partial = CWPartialLevel(x_digit=rem[0])
    elif len(rem) == 2:
        partial = CWPartialLevel(x_digit=rem[0], y_digit=rem[1])
    return levels, partial


def reconstruct(levels, partial=None) -> str:
    """Exact inverse of :func:`parse_levels` (used by the encoder and the
    remove-final-digits containment tests)."""
    out = []
    for lv in levels:
        out += [str(lv.x_digit), str(lv.y_digit), str(lv.z_digit)]
    if partial is not None:
        if partial.x_digit is not None:
            out.append(str(partial.x_digit))
        if partial.y_digit is not None:
            out.append(str(partial.y_digit))
    return "".join(out)
