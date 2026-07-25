"""P23 -- checksums, versioning, and error detection for CW vectors.

A canonical CW address travels as a text string: it may be re-typed, copied
across a lossy channel, or version-drifted against the software that reads it.
This module gives the atlas three deterministic guards over that string, and
nothing more:

* **Checksum.** A version-tagged SHA-256 digest binds a payload string. A
  single corrupted, inserted, or deleted character makes :func:`verify` return
  ``False``. The digest is deterministic (``hashlib`` only, no wall-clock, no
  randomness), so a clean checkout reproduces every tag byte-for-byte.
* **Version marker.** Every checksum tag carries the checksum-format version,
  and every CW vector carries its codec id and codec version. A tag written by
  a different checksum version, or a vector whose codec/version does not match
  what the reader expects, is detected by :func:`require_version` rather than
  silently mis-parsed.
* **Typo detection.** A Damm check digit over the vector's decimal payload
  catches every single-digit error and every adjacent transposition -- the two
  commonest hand-transcription mistakes -- deterministically.

Nothing here interprets a coordinate or a source vector. A checksum says a
string is intact; it says nothing about what the string *means*.

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED
"""

from __future__ import annotations

import hashlib
import re

from cwatlas import claims

#: Checksum-format version. Bump this only when the digest construction below
#: changes; :func:`verify` rejects a tag written under a different version.
CHECKSUM_VERSION = "cwck1"

#: Number of hex characters retained from the SHA-256 digest. 16 hex chars =
#: 64 bits of collision resistance -- ample for transcription-error detection.
DIGEST_HEX_LEN = 16

#: Separator between a payload and its appended checksum tag in a full vector.
CHECKSUM_SEP = "*"

#: The Damm operation table (fully anti-symmetric quasigroup, order 10). It
#: detects all single-digit errors and all adjacent transpositions.
_DAMM_TABLE = (
    (0, 3, 1, 7, 5, 9, 8, 6, 4, 2),
    (7, 0, 9, 2, 1, 5, 4, 8, 6, 3),
    (4, 2, 0, 6, 8, 7, 1, 3, 5, 9),
    (1, 7, 5, 0, 9, 8, 3, 4, 2, 6),
    (6, 1, 2, 3, 0, 4, 5, 9, 7, 8),
    (3, 6, 7, 4, 2, 0, 9, 5, 8, 1),
    (5, 8, 6, 9, 7, 2, 0, 1, 3, 4),
    (8, 9, 4, 5, 3, 6, 2, 0, 1, 7),
    (9, 4, 3, 8, 6, 1, 7, 2, 0, 5),
    (2, 5, 8, 1, 4, 3, 6, 7, 9, 0),
)


class ChecksumError(ValueError):
    """Raised on a malformed checksum tag or a detected version mismatch."""


def checksum(payload: str) -> str:
    """Return a version-tagged, deterministic checksum for ``payload``.

    The tag is ``<CHECKSUM_VERSION>:<first DIGEST_HEX_LEN hex of sha256>``.
    Deterministic: the same payload always yields the same tag.
    """
    if not isinstance(payload, str):
        raise ChecksumError(f"payload must be a string, got {type(payload)!r}")
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"{CHECKSUM_VERSION}:{digest[:DIGEST_HEX_LEN]}"


def verify(payload: str, tag: str) -> bool:
    """``True`` iff ``tag`` is a current-version checksum matching ``payload``.

    A tag written under a different checksum version, a corrupted payload, or a
    corrupted tag all return ``False`` -- never a silent pass.
    """
    if not isinstance(tag, str) or ":" not in tag:
        return False
    version, _, digest = tag.partition(":")
    if version != CHECKSUM_VERSION:
        return False
    expected = checksum(payload)
    # Constant-time compare of two equal-length hex strings.
    return _constant_time_eq(tag, expected) and bool(digest)


def _constant_time_eq(a: str, b: str) -> bool:
    """Length-independent constant-time string comparison."""
    if len(a) != len(b):
        return False
    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)
    return result == 0


def append_checksum(payload: str) -> str:
    """Return ``payload`` with its checksum tag appended after ``CHECKSUM_SEP``."""
    return f"{payload}{CHECKSUM_SEP}{checksum(payload)}"


def split_checksum(vector: str) -> tuple[str, str]:
    """Split a checksummed vector into ``(payload, tag)``.

    Raises :class:`ChecksumError` if no checksum separator is present.
    """
    if not isinstance(vector, str) or CHECKSUM_SEP not in vector:
        raise ChecksumError(
            f"vector carries no {CHECKSUM_SEP!r} checksum separator")
    payload, _, tag = vector.rpartition(CHECKSUM_SEP)
    return payload, tag


def verify_vector(vector: str) -> bool:
    """``True`` iff a checksummed ``vector`` is intact and current-version."""
    try:
        payload, tag = split_checksum(vector)
    except ChecksumError:
        return False
    return verify(payload, tag)


# -- version markers ---------------------------------------------------------

#: Pattern for the ``codec=<id>`` and ``v=<version>`` markers a CW vector
#: payload carries. Kept permissive on the value side.
_CODEC_RE = re.compile(r"(?:^|;)codec=([^;*]+)")
_VERSION_RE = re.compile(r"(?:^|;)v=([^;*]+)")


def parse_codec_version(vector: str) -> tuple[str, str]:
    """Extract ``(codec_id, codec_version)`` from a vector payload.

    Raises :class:`ChecksumError` if either marker is absent -- a vector with
    no declared codec/version is not silently defaulted.
    """
    payload = vector
    if CHECKSUM_SEP in vector:
        payload = split_checksum(vector)[0]
    codec_m = _CODEC_RE.search(payload)
    version_m = _VERSION_RE.search(payload)
    if not codec_m or not version_m:
        raise ChecksumError(
            "vector is missing a codec= or v= version marker; refusing to "
            "assume a default codec or version")
    return codec_m.group(1), version_m.group(1)


def require_version(vector: str, expected_codec: str, expected_version: str) -> None:
    """Raise :class:`ChecksumError` unless the vector's codec/version match.

    A version mismatch is a detected error, not a warning: later phases must
    not decode a vector under a codec version it was not written for.
    """
    codec_id, codec_version = parse_codec_version(vector)
    if codec_id != expected_codec or codec_version != expected_version:
        raise ChecksumError(
            f"version mismatch: vector declares codec={codec_id!r} "
            f"v={codec_version!r}, reader expected codec={expected_codec!r} "
            f"v={expected_version!r}")


# -- typo detection (Damm check digit) --------------------------------------

def _digits_of(text: str) -> str:
    """The decimal digits of ``text`` in order (other characters dropped)."""
    return "".join(ch for ch in text if ch.isdigit())


def damm_check_digit(text: str) -> int:
    """Damm check digit over the decimal digits of ``text`` (0..9).

    Detects every single-digit error and every adjacent transposition.
    """
    interim = 0
    for ch in _digits_of(text):
        interim = _DAMM_TABLE[interim][int(ch)]
    return interim


def damm_is_valid(text_with_check: str) -> bool:
    """``True`` iff the trailing Damm check digit of ``text_with_check`` holds.

    A correct digit string appended with its Damm check digit yields an overall
    Damm value of 0.
    """
    return damm_check_digit(text_with_check) == 0


def checksums_report() -> dict:
    """What this module claims -- and, deliberately, what it does not."""
    return {
        "module": "cwatlas.checksums",
        "phase_id": "P23",
        "checksum_version": CHECKSUM_VERSION,
        "digest": "sha256",
        "digest_hex_len": DIGEST_HEX_LEN,
        "guards": [
            "version-tagged checksum: a corrupted vector fails verify()",
            "version marker: a codec/version mismatch is detected",
            "Damm check digit: single-digit and transposition typos detected",
        ],
        "claim_class": claims.ClaimClass.CANONICAL_ROUND_TRIP.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "CW_VECTOR_CHECKSUM_VERSION_AND_TYPO_GUARDS_DETERMINISTIC",
        "what_this_does_not_say": (
            "A passing checksum means a string is intact; it says nothing "
            "about what the string means or whether any source vector is "
            "geographic. No physical validation is claimed."),
    }
