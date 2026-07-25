"""P22 — Nine-digit triplet and shell candidate codecs.

Two ways to read a nine-digit string, implemented side by side and *neither
promoted* over the other:

* ``CW-TRIPLET9-1`` — a **symmetric** fixed triplet ``XXX|YYY|ZZZ``: three
  three-digit groups, each an integer ``0..999``. It round-trips exactly.

* ``CW-SHELL9-LEGACY`` — an **asymmetric** legacy reading
  ``XXX|YYY|ZZ|S``: two three-digit groups, a two-digit group, and a single
  shell digit. It is retained **only as a failed/conditional legacy codec**
  (``LEGACY_CONDITIONAL``). It does **not** round-trip cleanly: the legacy
  reading conditionally applies the source ``8 -> 0`` shell closure, which is
  lossy (a shell digit of ``8`` decodes to ``0``, so ``8`` and ``0`` collide).
  It is kept for provenance — so history is not overwritten — not for use.

Both codecs emit ``MATHEMATICAL_TRANSLATION`` candidates: a nine-digit string
is re-expressed arithmetically, and nothing about meaning, geography, or a
source vector is asserted. Which partition (if any) a source intended is
underdetermined; the registry (P24) surfaces both as an alias set and refuses
to force one pin.
"""

from __future__ import annotations

import hashlib
from typing import Sequence

from cwatlas.claims import ClaimClass, ClaimError
from cwatlas.codec_base100 import CodecResult

#: CodecResult status strings (subset of codec_result.schema.json enum).
STATUS_OK_ALIAS_SET = "OK_ALIAS_SET"
STATUS_INVALID = "INVALID"

#: The non-schema marker for the legacy codec's conditional retention.
LEGACY_CONDITIONAL = "LEGACY_CONDITIONAL"

#: A nine-digit fixed frame.
NINE = 9
_ASCII_DIGITS = frozenset("0123456789")


def _nine_digits(raw: object) -> bool:
    return (
        isinstance(raw, str)
        and len(raw) == NINE
        and all(ch in _ASCII_DIGITS for ch in raw)
    )


def _receipt_id(codec_id: str, version: str, raw: object) -> str:
    key = raw if isinstance(raw, str) else repr(raw)
    digest = hashlib.sha256(
        f"{codec_id}|{version}|{key}".encode("utf-8")).hexdigest()[:16]
    return f"rcpt:{codec_id}:{digest}"


# --- CW-TRIPLET9-1: symmetric XXX|YYY|ZZZ, round-trips exactly ----------------

class Triplet9Codec:
    """``CW-TRIPLET9-1`` — three three-digit groups; exact round-trip."""

    codec_id = "CW-TRIPLET9-1"
    version = "1.0.0"
    is_legacy_candidate = True
    round_trips = True
    group_sizes = (3, 3, 3)
    #: Number of representable inputs: 1000 * 1000 * 1000.
    search_space_count = 1_000_000_000
    #: Deterministic relative admissibility (not a probability). A clean
    #: round-trip reading scores above the lossy legacy reading.
    base_score = 0.5

    def encode(self, value: Sequence[int]) -> str:
        groups = tuple(value)
        if len(groups) != 3:
            raise ClaimError(
                f"{self.codec_id} expects 3 groups (XXX|YYY|ZZZ), got "
                f"{len(groups)}.")
        for i, g in enumerate(groups):
            if isinstance(g, bool) or not isinstance(g, int):
                raise ClaimError(
                    f"{self.codec_id} group {i} must be an int, got {g!r}.")
            if not 0 <= g <= 999:
                raise ClaimError(
                    f"{self.codec_id} group {i}={g} out of range [0, 999].")
        x, y, z = groups
        return f"{x:03d}{y:03d}{z:03d}"

    def decode(self, raw: str) -> CodecResult:
        if not _nine_digits(raw):
            return CodecResult(
                status=STATUS_INVALID,
                codec_id=self.codec_id,
                candidates=(),
                receipt_id=_receipt_id(self.codec_id, self.version, raw),
                warnings=(
                    f"{self.codec_id} malformed: expected exactly {NINE} "
                    f"ASCII digits; refused (no silent repair).",),
            )
        x, y, z = int(raw[0:3]), int(raw[3:6]), int(raw[6:9])
        candidate = {
            "codec_id": self.codec_id,
            "version": self.version,
            "claim_class": ClaimClass.MATHEMATICAL_TRANSLATION.value,
            "groups": [x, y, z],
            "group_sizes": list(self.group_sizes),
            "round_trips": True,
            "score": self.base_score,
            "uncertainty": round(1.0 - self.base_score, 6),
            "search_space_count": self.search_space_count,
        }
        return CodecResult(
            status=STATUS_OK_ALIAS_SET,
            codec_id=self.codec_id,
            candidates=(candidate,),
            receipt_id=_receipt_id(self.codec_id, self.version, raw),
        )


# --- CW-SHELL9-LEGACY: asymmetric XXX|YYY|ZZ|S, does NOT round-trip cleanly ---

class Shell9LegacyCodec:
    """``CW-SHELL9-LEGACY`` — asymmetric triplet/triplet/pair/shell.

    Retained for provenance only. Marked ``LEGACY_CONDITIONAL``: the legacy
    reading conditionally applies the source ``8 -> 0`` shell closure, which is
    lossy — a shell digit of ``8`` decodes to ``0`` — so the codec does not
    round-trip cleanly and must not be used to make a decode.
    """

    codec_id = "CW-SHELL9-LEGACY"
    version = "1.0.0-legacy"
    is_legacy_candidate = True
    round_trips = False
    legacy_status = LEGACY_CONDITIONAL
    group_sizes = (3, 3, 2, 1)
    #: Representable inputs before closure: 1000 * 1000 * 100 * 9.
    search_space_count = 900_000_000
    base_score = 0.25

    def encode(self, value: Sequence[int]) -> str:
        groups = tuple(value)
        if len(groups) != 4:
            raise ClaimError(
                f"{self.codec_id} expects 4 groups (XXX|YYY|ZZ|S), got "
                f"{len(groups)}.")
        bounds = ((0, 999), (0, 999), (0, 99), (0, 8))
        for i, (g, (lo, hi)) in enumerate(zip(groups, bounds)):
            if isinstance(g, bool) or not isinstance(g, int):
                raise ClaimError(
                    f"{self.codec_id} group {i} must be an int, got {g!r}.")
            if not lo <= g <= hi:
                raise ClaimError(
                    f"{self.codec_id} group {i}={g} out of range [{lo}, {hi}].")
        x, y, z, s = groups
        return f"{x:03d}{y:03d}{z:02d}{s:01d}"

    def decode(self, raw: str) -> CodecResult:
        if not _nine_digits(raw):
            return CodecResult(
                status=STATUS_INVALID,
                codec_id=self.codec_id,
                candidates=(),
                receipt_id=_receipt_id(self.codec_id, self.version, raw),
                warnings=(
                    f"{self.codec_id} malformed: expected exactly {NINE} "
                    f"ASCII digits; refused (no silent repair).",),
            )
        x, y, z = int(raw[0:3]), int(raw[3:6]), int(raw[6:8])
        shell_raw = int(raw[8:9])
        # The lossy, conditional legacy behavior: 8 -> 0 closure applied here.
        shell_resolved = 0 if shell_raw == 8 else shell_raw
        candidate = {
            "codec_id": self.codec_id,
            "version": self.version,
            "claim_class": ClaimClass.MATHEMATICAL_TRANSLATION.value,
            "groups": [x, y, z, shell_resolved],
            "group_sizes": list(self.group_sizes),
            "shell_raw": shell_raw,
            "shell_resolved": shell_resolved,
            "round_trips": False,
            "legacy_status": self.legacy_status,
            "score": self.base_score,
            "uncertainty": round(1.0 - self.base_score, 6),
            "search_space_count": self.search_space_count,
        }
        return CodecResult(
            status=STATUS_OK_ALIAS_SET,
            codec_id=self.codec_id,
            candidates=(candidate,),
            receipt_id=_receipt_id(self.codec_id, self.version, raw),
            warnings=(
                f"{self.codec_id} is {LEGACY_CONDITIONAL}: it does NOT "
                f"round-trip cleanly (conditional 8->0 shell closure is "
                f"lossy). Retained for provenance, not for use.",),
        )


TRIPLET9 = Triplet9Codec()
SHELL9 = Shell9LegacyCodec()

#: The codec objects this module contributes to the registry (P24).
CODECS = (TRIPLET9, SHELL9)


def codec_triplet9_report() -> dict:
    """P22 declaration receipt. Two readings, neither promoted; nothing measured."""
    return {
        "phase_id": "P22",
        "what_this_is": (
            "a nine-digit fixed triplet (CW-TRIPLET9-1, XXX|YYY|ZZZ) and an "
            "asymmetric legacy reading (CW-SHELL9-LEGACY, XXX|YYY|ZZ|S); both "
            "emit MATHEMATICAL_TRANSLATION candidates and neither is promoted."),
        "claim_class": ClaimClass.MATHEMATICAL_TRANSLATION.value,
        "codecs": {
            TRIPLET9.codec_id: {
                "version": TRIPLET9.version,
                "group_sizes": list(TRIPLET9.group_sizes),
                "round_trips": True,
                "search_space_count": TRIPLET9.search_space_count,
            },
            SHELL9.codec_id: {
                "version": SHELL9.version,
                "group_sizes": list(SHELL9.group_sizes),
                "round_trips": False,
                "legacy_status": SHELL9.legacy_status,
                "search_space_count": SHELL9.search_space_count,
                "note": (
                    "retained for provenance only; the conditional 8->0 shell "
                    "closure is lossy so this codec does not round-trip "
                    "cleanly and must not be used to produce a decode."),
            },
        },
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "GREEN_R10_8_1_P22_NINE_DIGIT_TRIPLET_AND_SHELL_CANDIDATES",
    }
