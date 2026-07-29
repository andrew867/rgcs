"""R10.28 Agent 04 — the long message payload.

THE PRINCIPAL FINDING: this is not a message. It is a CODEC SELF-TEST
VECTOR, and it says so once you concatenate the alphanumeric blocks:

    34567890 ABCDEFGHIJKLMNOPQRSTUVWXYZ
    THE QUICK BROWN FOX JUMPED OVER THE LAZY DOG.
    123 45678901234567890

A digit ramp, the COMPLETE A-Z alphabet, a pangram, and another digit
ramp. That is the classic "did every symbol survive the round trip"
pattern, and the source claim agrees: "digits at end correct encoded and
decoded". The seed's own status field says "test corpus only, not Earth
coordinate".

CONSEQUENCE FOR THE CODEC: the symbol set exercised is 0-9 plus A-Z --
exactly **36 symbols**. The source notes say "36-bit". Those are two
different claims that the number 36 could be pointing at, and a corpus
whose entire content is a base-36 alphabet enumeration is evidence for
the ALPHABET reading. This is recorded as a HYPOTHESIS, not adopted:
it does not follow from a coincidence of the number 36, and no
partition in :mod:`r1028.codec36` depends on it.

What is NOT claimed: that the leading numeric blocks decode to anything.
They are tested and reported, and they do not.
"""

from __future__ import annotations

import string

RAW_BLOCKS = [
    "2839754287695473209543634976",
    "5498765984363210636894683",
    "678967654732987654321012",
    "34567890ABCDEFGHIJKLMNOP",
    "QRSTUVWXYZTHE",
    "QUICKBROWNFOXJUMPED",
    "OVERTHELAZYDOG.123",
    "45678901234567890",
]

PANGRAM_WORDS = ("THE", "QUICK", "BROWN", "FOX", "JUMPED", "OVER",
                 "THE", "LAZY", "DOG")

BASE36_ALPHABET = string.digits + string.ascii_uppercase


def joined() -> str:
    return "".join(RAW_BLOCKS)


def classify_blocks() -> list:
    rows = []
    for i, b in enumerate(RAW_BLOCKS):
        digits = sum(c.isdigit() for c in b)
        alpha = sum(c.isalpha() for c in b)
        rows.append({
            "block_index": i, "block": b, "length": len(b),
            "digits": digits, "letters": alpha,
            "kind": ("NUMERIC" if alpha == 0 else
                     "ALPHANUMERIC" if digits else "ALPHABETIC"),
            "octal_legal": all(c in "01234567" for c in b) if not alpha
                           else False,
        })
    return rows


def alphabet_coverage() -> dict:
    text = joined()
    letters = {c for c in text if c.isalpha()}
    digits = {c for c in text if c.isdigit()}
    missing = set(string.ascii_uppercase) - letters
    return {
        "distinct_letters": len(letters),
        "alphabet_complete": not missing,
        "missing_letters": sorted(missing),
        "distinct_digits": len(digits),
        "missing_digits": sorted(set(string.digits) - digits),
        "distinct_symbols": len(letters | digits),
        "base36_symbol_count": len(BASE36_ALPHABET),
        "exercises_full_base36_symbol_set":
            not missing and not (set(string.digits) - digits),
    }


def pangram_check() -> dict:
    text = joined()
    found = [w for w in dict.fromkeys(PANGRAM_WORDS) if w in text]
    return {
        "pangram_words_present": found,
        "pangram_complete": len(found) == len(set(PANGRAM_WORDS)),
        "is_test_pattern": len(found) == len(set(PANGRAM_WORDS)),
    }


def numeric_block_decode_attempts() -> list:
    """Test the leading numeric blocks as 36-bit / octal payloads."""
    from r1028.codec36 import OCTAL_DIGITS, to_blocks
    rows = []
    for i, b in enumerate(RAW_BLOCKS):
        if any(c.isalpha() for c in b):
            rows.append({
                "block_index": i, "block": b,
                "attempt": "NOT_NUMERIC",
                "result": "SKIPPED_ALPHANUMERIC_TEST_PATTERN",
                "decoded": False})
            continue
        octal_legal = all(c in "01234567" for c in b)
        v = int(b)
        blocks = to_blocks(v)
        octal = format(v, "o")
        rows.append({
            "block_index": i, "block": b,
            "attempt": "DECIMAL_TO_36BIT_BLOCKS",
            "octal_digits": len(octal),
            "blocks_needed": len(blocks),
            "exact_multiple_of_12_octal_digits":
                len(octal) % OCTAL_DIGITS == 0,
            "readable_as_octal_string": octal_legal,
            "result": ("NO_CLEAN_36_BIT_FRAMING"
                       if len(octal) % OCTAL_DIGITS else
                       "CLEAN_36_BIT_FRAMING"),
            "decoded": False})
    return rows


def report() -> dict:
    cov = alphabet_coverage()
    pan = pangram_check()
    return {
        "schema": "rgcs.r1028.long-payload.v1",
        "payload_id": "R1028_LONG_MESSAGE_PAGE10",
        "blocks": classify_blocks(),
        "alphabet_coverage": cov,
        "pangram": pan,
        "numeric_attempts": numeric_block_decode_attempts(),
        "principal_finding": (
            "CODEC_SELF_TEST_VECTOR_NOT_A_MESSAGE: the alphanumeric "
            "blocks concatenate to a digit ramp, the complete A-Z "
            "alphabet, the pangram 'THE QUICK BROWN FOX JUMPED OVER THE "
            "LAZY DOG.', and a further digit ramp"),
        "base36_hypothesis": (
            "the corpus exercises exactly the 36-symbol base-36 alphabet "
            "(0-9 A-Z); the source notes say '36-bit'. HYPOTHESIS ONLY: "
            "the number 36 may refer to the ALPHABET, not the word "
            "width. Not adopted; no partition depends on it."),
        "verdict": "R10_28_LONG_PAYLOAD_IDENTIFIED_AS_TEST_PATTERN",
        "message_decoded": False,
        "is_earth_coordinate": False,
    }
