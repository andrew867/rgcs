"""R10.8.3 — typed source-vector decoder candidates (reconciliation lane).

The R10.8.2 release locked ``spatialization`` (five base-100 tokens folded to
an integer; face from ``n % 20``) as the production decode path. Operator
review then identified an exact semantic defect in that face rule (for a
base-100 fold, ``n % 20`` depends only on the final token: 23, 43, 63 and 83
all select face 3) and instructed successive alternative decoders, ending with
the **interleaved radix-10 XYZ stream** (``CW_INTERLEAVED_XYZ_DECIMAL_V1``).

This module does what the reconciliation instruction requires: instead of
silently selecting one decoder (or silently leaving a rejected one reachable),
it registers every candidate as a **typed profile** with an explicit status
and the recorded defect, and implements the interleaved codec with its
prefix-containment law and inverse encoder.

Statuses are about *decoding pre-existing source vectors to claimed places*.
No profile here asserts a validated source origin:
``SOURCE_ORIGIN_VALIDATED: no`` (see :mod:`cwatlas.r1082.claims`).
Everything here is ``DERIVED_MATHEMATICS`` at the ``SOFTWARE`` level.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction

__all__ = [
    "DecoderCandidate",
    "InterleavedXYZDecimalV1",
    "AXES",
    "CANDIDATES",
    "candidate",
]

AXES = ("X", "Y", "Z")


@dataclass(frozen=True)
class DecoderCandidate:
    """One typed decoder-candidate profile.

    ``status`` values used by the R10.8.3 reconciliation:

    ``LOCKED_PRODUCTION_KNOWN_DEFECT``
        Shipped and frozen at v8.2.0; kept for release integrity, with the
        operator-identified defect recorded rather than hidden.
    ``REJECTED_FOR_SOURCE_DECODE``
        Tested against the training anchor under a preregistered ablation and
        found inadmissible by the declared standard (residual far above
        quantization); retained only as a typed record.
    ``CANDIDATE_STRUCTURAL_ONLY``
        The parse itself is exact and reproducible, but no face selector /
        Earth placement derived from it has met the admissibility standard.
    """

    candidate_id: str
    status: str
    parse: str
    face_rule: str
    known_defect: str
    best_training_residual_km: float | None
    residual_over_quantization: float | None
    notes: str = ""


class InterleavedXYZDecimalV1:
    """``CW_INTERLEAVED_XYZ_DECIMAL_V1`` — radix-10 Morton-style XYZ stream.

    For decimal digits ``d0 d1 d2 d3 ...`` the axes are read cyclically::

        X = d0 d3 d6 d9 ...
        Y = d1 d4 d7 d10 ...
        Z = d2 d5 d8 d11 ...

    Each axis prefix denotes the half-open decimal interval
    ``[p / 10**k, (p + 1) / 10**k)``. Incomplete final triplets are valid and
    yield anisotropic axis depths (X depth >= Y depth >= Z depth, never
    differing by more than one). The final decimal digit is **not** a shell
    field under this candidate.
    """

    CODEC_ID = "CW_INTERLEAVED_XYZ_DECIMAL_V1"

    @staticmethod
    def deinterleave(vector: str) -> dict:
        """Split a decimal source-vector string into per-axis digit prefixes."""
        if not vector or not vector.isdigit():
            raise ValueError(f"source vector must be decimal digits: {vector!r}")
        return {"X": vector[0::3], "Y": vector[1::3], "Z": vector[2::3]}

    @staticmethod
    def interleave(x: str, y: str, z: str) -> str:
        """Inverse encoder: merge axis prefixes back into one digit stream.

        Depths must satisfy the stream constraint
        ``len(x) >= len(y) >= len(z) >= len(x) - 1`` (digits are appended in
        X, Y, Z order), otherwise the stream is not realisable.
        """
        for s in (x, y, z):
            if not s.isdigit():
                raise ValueError("axis prefixes must be decimal digits")
        if not (len(x) >= len(y) >= len(z) >= len(x) - 1):
            raise ValueError(
                f"unrealisable axis depths ({len(x)},{len(y)},{len(z)}): "
                "digits append in X,Y,Z order")
        out = []
        for i in range(len(x)):
            out.append(x[i])
            if i < len(y):
                out.append(y[i])
            if i < len(z):
                out.append(z[i])
        return "".join(out)

    @classmethod
    def depths(cls, vector: str) -> tuple[int, int, int]:
        p = cls.deinterleave(vector)
        return (len(p["X"]), len(p["Y"]), len(p["Z"]))

    @staticmethod
    def interval(prefix: str) -> tuple[Fraction, Fraction]:
        """Exact half-open decimal interval denoted by one axis prefix."""
        if prefix == "":
            return (Fraction(0), Fraction(1))
        k = len(prefix)
        lo = Fraction(int(prefix), 10 ** k)
        return (lo, lo + Fraction(1, 10 ** k))

    @classmethod
    def intervals(cls, vector: str) -> dict:
        return {ax: cls.interval(p)
                for ax, p in cls.deinterleave(vector).items()}

    @classmethod
    def contains(cls, prefix_vector: str, extended_vector: str) -> bool:
        """Prefix-containment law: Omega(K || E) subset-of Omega(K).

        True iff ``extended_vector`` extends ``prefix_vector`` digit-for-digit,
        in which case every axis interval of the extension nests inside the
        prefix's (proved exactly with :class:`fractions.Fraction`).
        """
        if not extended_vector.startswith(prefix_vector):
            return False
        pin = cls.intervals(prefix_vector)
        ein = cls.intervals(extended_vector)
        return all(pin[ax][0] <= ein[ax][0] and ein[ax][1] <= pin[ax][1]
                   for ax in AXES)

    @classmethod
    def append_digits(cls, vector: str, digits: str) -> str:
        """Append refinement digits (consumed in X, Y, Z stream order)."""
        if not digits.isdigit():
            raise ValueError("refinement digits must be decimal")
        return vector + digits

    @classmethod
    def local_triangle(cls, vector: str) -> dict:
        """Primary local-triangle candidate: lambda = (1 - x - y, x, y), h = z.

        ``x``, ``y``, ``z`` are the lower bounds of the axis intervals. Valid
        only when ``x + y <= 1`` (always true for proper decimal prefixes,
        since x, y < 1, but the simplex condition is still checked).
        """
        iv = cls.intervals(vector)
        x, y, z = iv["X"][0], iv["Y"][0], iv["Z"][0]
        if x + y > 1:
            raise ValueError(f"outside simplex: x+y = {float(x + y)}")
        return {"lambda": (1 - x - y, x, y), "height": z}


#: The typed candidate registry. Order is historical (production first).
CANDIDATES: tuple[DecoderCandidate, ...] = (
    DecoderCandidate(
        candidate_id="BASE100_FOLD_MOD20_V1",
        status="LOCKED_PRODUCTION_KNOWN_DEFECT",
        parse="five base-100 tokens folded little-endian to n",
        face_rule="face = n % 20; path = base-8 digits of n // 20",
        known_defect=(
            "100 == 0 (mod 20), so n % 20 equals the final folded token "
            "mod 20: final tokens 23, 43, 63, 83 all select face 3. The "
            "face is chosen by one token, not the address."),
        best_training_residual_km=None,
        residual_over_quantization=None,
        notes=("v8.2.0 production path (spatialization.py). Frozen for "
               "release integrity; not repaired in place on the "
               "reconciliation branch."),
    ),
    DecoderCandidate(
        candidate_id="FIELD_SPLIT_V1",
        status="REJECTED_FOR_SOURCE_DECODE",
        parse=("final token = 10*phase + shell (8 -> 0 phase closure); "
               "face = region_token // 5; intra-face = region_token % 5"),
        face_rule="face = region_token // 5 (exact 100 = 20 x 5 split)",
        known_defect=(
            "Geometrically admissible (face 17 contains the training "
            "anchor's admissible band) but no in-face rule met the "
            "declared quantization standard."),
        best_training_residual_km=857.0,
        residual_over_quantization=None,
        notes="Preregistered operator ablation, 2026-07 session receipts.",
    ),
    DecoderCandidate(
        candidate_id="BARY_DIGIT_V1",
        status="REJECTED_FOR_SOURCE_DECODE",
        parse=("token3 = 10a + b, final = 10u + shell; "
               "lambda = normalize(a, b, u)"),
        face_rule="720-combination preregistered search over face/role maps",
        known_defect=(
            "Best training-anchor residual 218 km ~= 400x the declared "
            "0.5 km quantization: inadmissible by the operator's own "
            "standard; residual shrank monotonically with decoder DOF "
            "(overfitting signature)."),
        best_training_residual_km=218.0,
        residual_over_quantization=400.0,
        notes="Orange-slice collinearity holds but is parse-invariant.",
    ),
    DecoderCandidate(
        candidate_id="CW_INTERLEAVED_XYZ_FLATTENED_V1",
        status="REJECTED_FOR_SOURCE_DECODE",
        parse=("radix-10 column flattening: X = d0 d3 d6... read as one "
               "completed decimal fraction per axis (REJECTED by the "
               "R10.8.4 lock: triplets are recursive levels, not columns)"),
        face_rule=(
            "UNSPECIFIED by the parse; 20 faces x 6 orderings x 4 families "
            "were enumerated instead."),
        known_defect=(
            "Flattening discards the per-level fold history. Face-local "
            "barycentric pipeline in the sealed frame: best training-anchor "
            "residual 260.5 km = 37x the 7.1 km quantization; 0 of 1920 "
            "configurations within 100 km; chance-level. Labelled "
            "WRONG_MODEL_TESTED for the recursive codec."),
        best_training_residual_km=260.5,
        residual_over_quantization=37.0,
        notes=("Superseded 2026-07-25 by CW_RECURSIVE_XYZ_LEVELS_V1 "
               "(cwatlas.r1084). The column arithmetic itself remains "
               "exact; only its interpretation as completed fractions is "
               "rejected."),
    ),
    DecoderCandidate(
        candidate_id="CW_RECURSIVE_XYZ_LEVELS_V1",
        status="REJECTED_FOR_SOURCE_DECODE",
        parse=("ordered XYZ triplets, one hierarchical refinement level "
               "each: (d0,d1,d2), (d3,d4,d5), ...; partial final levels "
               "explicit; implemented in cwatlas.r1084"),
        face_rule=(
            "no face token in the vector; face context supplied by the "
            "five declared root-relative codebooks (finite ambiguity)"),
        known_defect=(
            "Placement not achieved: 480 sealed-frame configurations, "
            "0 contain the training anchor in the final level-3 cell; "
            "best min-distance 248 km (C0); 10/9 compensation profiles "
            "worsen it (426 km) while 81/80 and 55/54 controls do better "
            "(206/191 km), so 10/9 is not distinguished. Radially, no "
            "declared root profile places the Z-path (5,6,3) at the "
            "surface."),
        best_training_residual_km=248.0,
        residual_over_quantization=None,
        notes=("Structure lane VERIFIED but the interpretation was "
               "REJECTED by the R10.8.5 locked correction (2026-07-26): "
               "raw decimal digits are not recursive instructions; the "
               "integer converts to a 30-bit binary packet first. Code "
               "retained in cwatlas.r1084 as the receipted rejected "
               "experiment. See docs/proofs/r1084-recursive-coordinate-"
               "recovery/ and r1085-octal-packet-recovery/."),
    ),
    DecoderCandidate(
        candidate_id="CW_OCTAL_PACKET_F5_Q22_S3_V1",
        status="LOCKED_INTERPRETATION_STRUCTURAL_ONLY",
        parse=("decimal integer -> 30-bit binary -> F5 (face) | Q22 "
               "(11 quaternary refinement levels) | S3 (shell 0..7); "
               "equivalently 10 octal digits = 9 spatial + 1 shell; "
               "implemented since R12 (r12.icosapacket, r12.icosarefine) "
               "and reused verbatim"),
        face_rule="F5 field IS the face token (source-face id 0..19)",
        known_defect=(
            "Placement not achieved under the sealed R10.8.2 freeze: "
            "0 of 20 codebook x family contexts contain the training "
            "anchor in the level-11 cell (~3.4 km edge); best approx "
            "min-distance ~2,683 km. Octal-domain structural check: the "
            "decimal orange-slice line does not survive conversion "
            "(shells 7,3,7; only 9 of 11 path levels shared)."),
        best_training_residual_km=2683.0,
        residual_over_quantization=None,
        notes=("Grammar lane EXACT: Stonehenge word verifies bit-for-bit "
               "(face 4, path 3,3,0,1,2,0,2,1,2,1,1, shell 3; octree "
               "X=83, Y=80, Z=461; round-trips). Nine-digit and longer "
               "vector families kept separate (31-34-bit words exceed "
               "the 30-bit grammar; no version bridge proven). See "
               "docs/proofs/r1085-octal-packet-recovery/."),
    ),
)

_BY_ID = {c.candidate_id: c for c in CANDIDATES}


def candidate(candidate_id: str) -> DecoderCandidate:
    """Look up one typed candidate profile."""
    try:
        return _BY_ID[candidate_id]
    except KeyError:
        raise KeyError(
            f"unknown decoder candidate {candidate_id!r}; "
            f"known: {sorted(_BY_ID)}") from None
