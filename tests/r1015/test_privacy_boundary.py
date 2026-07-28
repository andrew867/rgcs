"""R10.15 Phase A02 — public/private boundary denial tests.

These tests must FAIL if private path-vector material ever enters the
tracked tree. They are deliberately adversarial: the positive control
plants a synthetic private-shaped wire and requires detection.
"""

import pathlib

import pytest

from rgcs_surface_wave.privacy import (PRIVATE_CAPTURE_SHA256,
                                       PRIVATE_STRUCTURE,
                                       PRIVATE_WIRE_LIST_SHA256,
                                       TRANSPORT_HYPOTHESES,
                                       WIRE_SIGNATURE,
                                       public_wire_allowlist,
                                       scan_tracked, would_leak)

ROOT = pathlib.Path(__file__).resolve().parents[2]


def test_tracked_tree_is_clean():
    """THE gate: no private wire, phrase, or path in tracked files."""
    s = scan_tracked(ROOT)
    assert s["clean"], s["findings"][:10]
    assert s["files_scanned"] > 100


def test_detects_planted_private_shaped_wire():
    """Positive control: an unknown wire signature must be caught."""
    planted = "16" + "9" * 9 + "3"
    assert planted not in public_wire_allowlist()
    hits = would_leak(f"the value {planted} appears here")
    assert any(h["kind"] == "UNKNOWN_WIRE_SIGNATURE" for h in hits)
    assert all("value" not in h or h.get("value_withheld")
               for h in hits)


def test_detects_wires_well_beyond_the_observed_lengths():
    """The private transport hypothesis allows lengths beyond the
    observed 9-11 digits, so detection must reach well past them."""
    for n_mid in (6, 8, 12, 17):
        planted = "16" + "7" * n_mid + "3"
        assert WIRE_SIGNATURE.search(planted), n_mid
        assert would_leak(planted), n_mid


def test_detection_length_band_is_bounded_and_declared():
    """DECLARED LIMITATION, recorded rather than hidden.

    An unbounded "16...3" regex matched 1563 ordinary numbers in
    committed CSV data, so the signature is bounded to 9-20 digit
    standalone tokens. Wires outside that band are NOT caught by the
    regex; they are covered by the aggregate commitments and by
    review. This test pins the bound so it cannot drift silently.
    """
    assert not WIRE_SIGNATURE.search("16773")            # 5 digits
    assert not WIRE_SIGNATURE.search("16" + "7" * 25 + "3")
    assert WIRE_SIGNATURE.search("16" + "7" * 6 + "3")   # 9 digits
    assert WIRE_SIGNATURE.search("16" + "7" * 17 + "3")  # 20 digits
    # and it must not fire inside a float, which is what caused the
    # original false-positive flood
    assert not WIRE_SIGNATURE.search("0.16777773")
    assert not WIRE_SIGNATURE.search("3.16777773e-05")


def test_public_corpus_is_not_flagged():
    """Negative control: already-public wires must not trip the scan."""
    allow = public_wire_allowlist()
    assert len(allow) >= 40
    for w in list(allow)[:20]:
        assert not [h for h in would_leak(w)
                    if h["kind"] == "UNKNOWN_WIRE_SIGNATURE"]


def test_detects_forbidden_phrases():
    for phrase in ("PATH_VECTOR_LEDGER", "RAW_CAPTURE_UNCHANGED",
                   "EOT @15:40"):
        assert would_leak(f"see {phrase} for details")


def test_commitments_are_recorded_and_not_invertible():
    for h in (PRIVATE_CAPTURE_SHA256, PRIVATE_WIRE_LIST_SHA256):
        assert len(h) == 64 and int(h, 16) >= 0
    # structure only, never values
    assert PRIVATE_STRUCTURE["wire_count"] == 17
    assert PRIVATE_STRUCTURE["overlap_with_public_corpus"] == 0
    blob = str(PRIVATE_STRUCTURE)
    assert not WIRE_SIGNATURE.search(blob)


def test_no_per_wire_digests_are_stored():
    """A per-wire digest would be brute-forceable and is forbidden."""
    src = (ROOT / "rgcs_surface_wave" / "privacy.py").read_text(
        encoding="utf-8")
    import re
    digests = re.findall(r"\b[0-9a-f]{64}\b", src)
    assert len(digests) == 2, ("only the two aggregate commitments may "
                               "appear", digests)


def test_transport_hypotheses_are_separated():
    """R10.15 override: the R10.13 fixed-core reading must not be
    applied to the private lane."""
    h = TRANSPORT_HYPOTHESES
    assert h["H_FIXED_CORE_R1013"]["scope"].startswith("PUBLIC")
    assert h["H_VARIABLE_CORE_R1015"]["scope"].startswith("PRIVATE")
    assert "must not inherit" in h["H_VARIABLE_CORE_R1015"]["rule"]
    assert "8129" in h["H_FIXED_CORE_R1013"]["immutable_result"]


def test_private_pack_directory_is_untracked():
    import subprocess
    out = subprocess.run(["git", "-C", str(ROOT), "ls-files"],
                         capture_output=True, text=True, timeout=180)
    assert "PATH_VECTOR" not in out.stdout
    assert "10_PRIVATE" not in out.stdout
