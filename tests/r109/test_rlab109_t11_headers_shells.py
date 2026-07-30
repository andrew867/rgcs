"""R10.9 acceptance — T11 candidates, headers, shells, authority, earth."""

from __future__ import annotations

import pytest

from r109 import authority, header_recovery as hdr, shell_semantics as shells
from r109 import t11_candidates as t11
from r109.registry import REGISTRY_V2, fit_anchors, record
from r109.types import CodecTypeError, WireAddress

PAIRS = [(1643789253, 165876523), (1672875493, 168930443)]


# ------------------------------------------------------------------ T11
def test_t11_bounded_space_declared_and_finite():
    space = t11.candidate_space()
    assert len(space) == 46
    assert len({c.candidate_id for c in space}) == 46
    for c in space:
        assert c.assumptions


def test_t11_evaluation_honest_and_no_special_cases():
    report = t11.evaluate(PAIRS)
    assert report["candidate_count"] == 46
    # Recorded result of the bounded search: no candidate satisfies
    # BOTH training pairs. Aliases would be retained if any survived;
    # the unknown interleave stays UNRESOLVED either way.
    assert report["status"] in ("UNIQUE", "ALIASES",
                                "NO_CANDIDATE_IN_BOUNDED_SPACE")
    assert report["status"] == "NO_CANDIDATE_IN_BOUNDED_SPACE"
    # every per-pair record present (nothing silently skipped)
    for r in report["results"]:
        assert len(r["pair_results"]) == len(PAIRS)


def test_t11_candidates_are_reversible_where_they_decode():
    for cand in t11.candidate_space():
        for refined_raw, _ in PAIRS:
            d = cand.decode(refined_raw)
            if d is None:
                continue
            assert cand.encode(d) == refined_raw


def test_t11_never_uses_location_names():
    import inspect
    src = inspect.getsource(t11)
    for banned in ("Stonehenge", "Toronto", "Montreal", "Montréal",
                   "Erie", "stonehenge", "toronto", "montreal", "erie"):
        assert banned not in src


# -------------------------------------------------------------- headers
def test_primary_header_list_and_recovery_status():
    assert hdr.PRIMARY_HEADER_LIST == (3, 5, 6, 7, 8, 9, 10, 12, 15)
    assert hdr.RECOVERY_STATUS == "NOT_RECOVERED_FROM_HISTORY"
    aliases = hdr.alias_set()
    assert [a.value for a in aliases] == list(hdr.PRIMARY_HEADER_LIST)
    for a in aliases:
        assert a.evidence_class == "UNRESOLVED"
        assert "UNKNOWN" in a.semantics                  # no invented labels
        assert int(a.binary6, 2) == a.value


def test_frequency_key_list_cannot_enter_header_parser():
    with pytest.raises(hdr.HeaderError):
        hdr.assert_not_header([24])
    with pytest.raises(hdr.HeaderError):
        hdr.parse_header_candidate(97)
    # primary values pass through with unknown semantics
    out = hdr.parse_header_candidate(15)
    assert out["in_primary_historical_list"] is True
    assert "UNKNOWN" in out["semantics"]


def test_group_codes_stay_source_reported():
    from r109.types import LUNA, SOL_GROUP, TERRA, SolGroup
    assert SOL_GROUP.group_code == 16 and SOL_GROUP.member_code is None
    assert TERRA.member_code == 5 and LUNA.member_code == 7
    with pytest.raises(CodecTypeError):
        SolGroup(16, 5, "EXACT_ARITHMETIC")   # cannot upgrade evidence class


# ---------------------------------------------------------------- shells
def test_shell3_band_permits_topographic_depth_variation():
    band = shells.crustal_band("terra")
    assert band.contains_depth(-10.9)     # sea floor
    assert band.contains_depth(0.0)       # land zero
    assert band.contains_depth(8.8)       # mountain
    assert not band.contains_depth(30.0)
    luna = shells.crustal_band("luna")
    assert luna.thickness_km() != band.thickness_km()   # body-specific


def test_shell7_is_orbit_class():
    oc = shells.OrbitClass()
    assert oc.classify(7) and not oc.classify(3)


def test_shell_marker_firewall_reports_do_not_collapse():
    wire = WireAddress.from_raw(165879243, "t")
    rep = shells.shell_marker_report(wire, extracted_s3=3)
    assert rep["decimal_terminal_marker"]["digit"] == 3
    assert rep["binary_s3_field"]["value"] == 3
    assert rep["marker_equals_s3_proved"] is False
    with pytest.raises(CodecTypeError):
        shells.refuse_marker_collapse()


def test_outer_in_inner_out_agree_under_declared_profiles():
    for pid in shells.candidate_profile_ids():
        rep = shells.outer_in_inner_out_agreement(pid)
        assert rep["all_close"], rep


# ------------------------------------------------------------- registry
def test_registry_preserves_superseded_and_locks_holdout():
    raws = {r.raw for r in REGISTRY_V2}
    for must in (165876523, 1643789253, 167849523, 165879243, 168729543,
                 168500683, 168930443, 1672875493, 1658274383, 1658792343,
                 167854923):
        assert must in raws
    assert record(167854923).status == "DO_NOT_RETUNE"
    assert record(1658792343).status == "DO_NOT_FIT_REACQUIRE"
    fit = {r.raw for r in fit_anchors()}
    assert fit == {165876523, 167849523, 165879243, 168930443}
    assert 167854923 not in fit and 1658274383 not in fit


# ------------------------------------------------------------ authority
def test_authority_registry_validates():
    assert authority.validate()["valid"]
    assert authority.entry("R109-MTL-02-SUPERSEDED").evidence_class == "SUPERSEDED"
    assert authority.entry("R109-PKT-05").evidence_class == "UNRESOLVED"
