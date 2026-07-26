"""R10.8.5A §7 — the orange-slice triplet: operator-corrected 7,7,7.

Raw packet extraction of the three orange-slice vectors gives shells
``7, 3, 7`` (the middle word ``165892763`` decodes to shell 3 — that is
what the frozen parser says and it is retained verbatim). The operator
lock resolves this as a **likely transcription or packet error in the
middle vector's transmitted value**, and the ACTIVE SOLVE uses shells
``7, 7, 7``.

Discipline:

* the raw extraction stays in provenance, uncorrected, forever;
* the correction is a typed OPERATOR_CORRECTION on the shell field of
  one named vector — the parser itself is NOT modified and no search
  for a "nicer" decimal value is performed;
* explaining a physical 7,3,7 shell pattern is refused — the 3 is a
  recorded error candidate, not a phenomenon.
"""

from __future__ import annotations

from dataclasses import dataclass

from r12 import icosapacket as pk

from cwatlas.claims import ClaimError

ORANGE_SLICE_VECTORS = ("165892743", "165892763", "165892783")

#: The operator-declared intended shells for the active solve.
ACTIVE_SHELLS = (7, 7, 7)

CORRECTED_VECTOR = "165892763"
CORRECTED_FIELD = "shell"
CORRECTION_CLAIM = "OPERATOR_CORRECTION_TRANSCRIPTION_OR_PACKET_ERROR"


@dataclass(frozen=True)
class OrangeSliceRow:
    """One triplet member: raw parse plus the active-solve shell."""

    vector: str
    face: int
    path_levels: tuple[int, ...]
    raw_shell: int
    active_shell: int
    corrected: bool
    correction_claim: str | None


def rows() -> tuple[OrangeSliceRow, ...]:
    """Raw extraction (frozen parser, verbatim) + active-solve shells."""
    out = []
    for vector, active in zip(ORANGE_SLICE_VECTORS, ACTIVE_SHELLS):
        face, path, shell = pk.decode(int(vector))
        corrected = vector == CORRECTED_VECTOR
        if corrected and shell == active:
            raise ClaimError(
                "provenance drift: the raw middle-vector shell no longer "
                "differs from the correction — the raw parse must have "
                "changed, which the R10.8.5A lock forbids.")
        out.append(OrangeSliceRow(
            vector=vector, face=face,
            path_levels=tuple(pk.path_levels(path)),
            raw_shell=shell,
            active_shell=active,
            corrected=corrected,
            correction_claim=CORRECTION_CLAIM if corrected else None))
    return tuple(out)


def provenance() -> dict:
    """The permanent raw record beside the active-solve values."""
    rs = rows()
    return {
        "raw_shells": [r.raw_shell for r in rs],
        "active_shells": list(ACTIVE_SHELLS),
        "corrected_vector": CORRECTED_VECTOR,
        "corrected_field": CORRECTED_FIELD,
        "correction_claim": CORRECTION_CLAIM,
        "note": (
            "raw middle shell 3 is retained in provenance as a likely "
            "transcription or packet error; the active solve uses "
            "7,7,7. The parser is unmodified; no alternative decimal "
            "value was searched for."),
    }


def refuse_physical_737_pattern(*_a, **_k) -> None:
    """A 7,3,7 physical shell pattern may not be constructed."""
    raise ClaimError(
        "refused: the raw 7,3,7 shell reading is resolved by operator "
        "lock as a likely transcription or packet error in the middle "
        "vector (retained in provenance). Turning the 3 into a physical "
        "shell pattern would promote a suspected error to a phenomenon.")
