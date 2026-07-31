"""R10.61A -- framing profiles, evidence layer, LAT adapter, formatting."""

import numpy as np
import pytest

from rgcs_archive import evidence as E
from rgcs_archive import fermi_lat as L
from rgcs_archive import framing as F

REC = F.FIXTURE_RECORD


# --------------------------------------------- the core correction

def test_123_is_already_a_legal_width():
    """The claim R10.61 got wrong. 126 was never forced."""
    assert F.legal_width(123)
    assert 123 == 21 + 3 * 34


def test_strictly_greater_is_not_the_same_as_at_or_above():
    assert F.smallest_legal_width_at_or_above(123) == 123
    assert F.first_legal_width_strictly_greater(123) == 126
    for w in (21, 24, 123, 126):
        assert F.first_legal_width_strictly_greater(w) == w + 3


# ------------------------------------------------------ profiles

def test_fp_a_minimal_no_padding():
    p = F.fp_a(REC)
    assert p["envelope_width_bits"] == 123 and p["pad_bits"] == 0
    assert p["D"] == 34 and p["legal_splits"] == 35
    assert p["octal_payload"] == \
        "64542306375724625654273330377576404214647"
    assert p["octal_digits"] == 41
    assert p["padding"] == "NO_PADDING"
    assert p["status"] == "ACTIVE_CANDIDATE"


def test_fp_b_strict_next():
    p = F.fp_b(REC)
    assert p["envelope_width_bits"] == 126 and p["pad_bits"] == 3
    assert p["D"] == 35 and p["legal_splits"] == 36
    assert p["octal_payload"] == \
        "064542306375724625654273330377576404214647"
    assert p["padding"] == "PAD_STRICT_NEXT"
    assert "strictly greater" in p["rule"].lower()


def test_fp_c_edge_fields():
    p = F.fp_c(REC)
    assert p["container_bits"] == 132
    assert p["edge_prefix_bits"] == "010"
    assert p["edge_suffix_bits"] == "001"
    assert p["envelope_width_bits"] == 126
    assert p["D"] == 35 and p["legal_splits"] == 36
    assert p["octal_payload"] == \
        "365444442152520604177466460607536105260021"
    assert p["padding"] == "BIT_FIELD_STRIP"


def test_fp_c_is_not_fp_b():
    """Bit-field stripping is NOT decimal-character stripping."""
    b, c = F.fp_b(REC), F.fp_c(REC)
    assert b["envelope_width_bits"] == c["envelope_width_bits"] == 126
    assert b["D"] == c["D"] == 35
    assert b["octal_payload"] != c["octal_payload"]


def test_fp_d_is_diagnostic_only():
    p = F.fp_d(REC)
    assert p["status"] == "DIAGNOSTIC_ONLY"
    assert p["rgcs_route_authority"] is False
    assert p["envelope_width_bits"] == 132
    assert p["D"] is None and p["legal_splits"] is None


def test_fp_e_is_superseded_and_never_autoselects():
    p = F.fp_e()
    assert p["status"] == "SUPERSEDED"
    assert p["must_never_autoselect"] is True
    assert p["octal_payload"] == F.FP_E_PAYLOAD
    assert "octal space" in p["rule"].lower()


# ---------------------------------------------------- no winner

def test_no_profile_is_selected():
    a = F.all_profiles(REC)
    assert a["selected_profile"] is None
    assert set(a["route_capable"]) == {"FP-A", "FP-B", "FP-C"}
    assert "FP-D" not in a["route_capable"]
    assert "FP-E" not in a["route_capable"]


def test_forbidden_promotion_grounds_are_enumerated():
    a = F.all_profiles(REC)
    for g in ("readable_text", "smooth_route", "famous_place",
              "preferred_state_triple", "smaller_geometry_residual",
              "better_looking_visualization"):
        assert g in a["forbidden_promotion_grounds"]


def test_every_profile_names_its_id():
    for p in F.all_profiles(REC)["profiles"]:
        assert p["framing_profile_id"].startswith("FP-")


def test_all_three_route_profiles_satisfy_the_width_law():
    for pid in F.ROUTE_PROFILES:
        p = F.profile(REC, pid)
        assert p["envelope_width_bits"] == 21 + 3 * p["D"]
        assert p["legal_splits"] == p["D"] + 1
        assert p["octal_digits"] == p["envelope_width_bits"] // 3


def test_bad_record_is_refused():
    with pytest.raises(F.FramingError):
        F.fp_a("12345")
    with pytest.raises(F.FramingError):
        F.profile(REC, "FP-Z")


# ---------------------------------------- the formatting regression

def test_human_bytes_uses_a_decimal_point_not_a_thousands_separator():
    """R10.61 printed '4,912 GiB' for 4.912 GiB -- a 1000x overstatement."""
    s = E.human_bytes(5_274_187_869)
    assert s == "4.912 GiB"
    assert "," not in s
    assert s != "4,912 GiB"


@pytest.mark.parametrize("n,expect", [
    (0, "0 B"), (1023, "1023 B"),
    (1024, "1.000 KiB"),
    (1024 ** 2, "1.000 MiB"),
    (1024 ** 3, "1.000 GiB"),
    (1024 ** 4, "1.000 TiB"),
])
def test_human_bytes_scales(n, expect):
    assert E.human_bytes(n) == expect


def test_no_shipped_doc_repeats_the_bad_figure():
    import glob
    import os
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for p in glob.glob(os.path.join(root, "docs", "*.md")):
        text = open(p, encoding="utf-8", errors="replace").read()
        assert "4,912 GiB" not in text, p


# ------------------------------------------------- evidence layer

def _cand(**kw):
    base = dict(source_artifact="x.fits", source_hash="a" * 64,
                representation_recipe="FITS_COLUMN_RAW",
                framing_profile="FP-B", decoder_profile="sixbit_dec",
                null_family="permutation", hypothesis_count=132,
                result_class="NULL_COMPATIBLE")
    base.update(kw)
    return E.candidate(**base)


def test_candidate_carries_every_required_field():
    c = _cand()
    for f in E.REQUIRED_FIELDS:
        assert f in c
    assert c["candidate_id"] and len(c["candidate_id"]) == 16


def test_result_class_is_constrained():
    with pytest.raises(E.EvidenceError):
        _cand(result_class="DISCOVERY")
    with pytest.raises(E.EvidenceError):
        _cand(result_class="MESSAGE_CONFIRMED")


def test_supersede_does_not_launder_status():
    c = _cand(result_class="RGCS_ENVELOPE_CANDIDATE")
    s = E.supersede(c, "framing profile corrected", replaced_by="cand-2")
    assert s["superseded"] is True and s["queryable"] is True
    assert s["correction_history"][-1]["prior_result_class"] == \
        "RGCS_ENVELOPE_CANDIDATE"
    assert s["correction_history"][-1]["reason"]
    assert c.get("superseded") is None          # original untouched


def test_ledger_counts_superseded_records_too():
    rows = [_cand(), E.supersede(_cand(framing_profile="FP-A"), "r")]
    led = E.ledger_summary(rows)
    assert led["candidates"] == 2 and led["superseded"] == 1
    assert led["all_carry_full_provenance"]
    assert set(led["by_framing_profile"]) == {"FP-A", "FP-B"}


# ------------------------------------------------- LAT LS-002 lane

def _fake_ft1(path, n=400, seed=3):
    from astropy.io import fits
    rng = np.random.default_rng(seed)
    t = np.cumsum(rng.exponential(0.5, n)) + 3.0e8
    cols = fits.ColDefs([
        fits.Column(name="TIME", format="1D", array=t),
        fits.Column(name="ENERGY", format="1E",
                    array=rng.uniform(50, 5000, n).astype(np.float32)),
        fits.Column(name="RA", format="1E",
                    array=rng.uniform(0, 360, n).astype(np.float32)),
        fits.Column(name="DEC", format="1E",
                    array=rng.uniform(-90, 90, n).astype(np.float32)),
        fits.Column(name="EVENT_CLASS", format="1J",
                    array=np.full(n, 128)),
    ])
    h = fits.BinTableHDU.from_columns(cols, name="EVENTS")
    fits.HDUList([fits.PrimaryHDU(), h]).writeto(path, overwrite=True)
    return path


def test_ft1_inspect_reports_present_and_absent_columns(tmp_path):
    p = _fake_ft1(str(tmp_path / "ft1.fits"))
    ins = L.inspect_ft1(p)
    assert ins["rows"] == 400 and ins["required_present"]
    assert "TIME" in ins["known_columns_present"]
    assert "ZENITH_ANGLE" in ins["known_columns_absent"]
    assert "CONSIDERED TO BE photons" in ins["interpretation"]


def test_photon_streams_derive_the_primary_lane(tmp_path):
    p = _fake_ft1(str(tmp_path / "ft1.fits"))
    s = L.photon_streams(p)
    assert s["events"] == 400
    assert s["inter_arrival"]["count"] == 399
    assert s["inter_arrival"]["non_positive"] == 0
    assert s["log_delta"]["count"] > 0
    assert s["derived_from"].startswith("TIME column")
    assert s["lossy"] is False
    assert len(s["source_hash"]) == 64


def test_energy_band_cut_is_recorded_on_the_receipt(tmp_path):
    p = _fake_ft1(str(tmp_path / "ft1.fits"))
    s = L.photon_streams(p, energy_band_mev=(100, 300))
    assert s["cut"]["energy_band_mev"] == [100, 300]
    assert s["events"] < 400
    assert 100 <= s["energy_mev"]["min"] and s["energy_mev"]["max"] < 300


def test_time_window_cut_is_recorded(tmp_path):
    p = _fake_ft1(str(tmp_path / "ft1.fits"))
    full = L.photon_streams(p)
    lo, hi = full["time_window"]
    s = L.photon_streams(p, tmin=lo, tmax=lo + (hi - lo) / 2)
    assert s["events"] < full["events"]
    assert s["cut"]["tmin"] == lo


def test_a_file_without_TIME_is_refused(tmp_path):
    from astropy.io import fits
    p = str(tmp_path / "bad.fits")
    h = fits.BinTableHDU.from_columns(fits.ColDefs([
        fits.Column(name="NOPE", format="1J", array=np.arange(4))]))
    fits.HDUList([fits.PrimaryHDU(), h]).writeto(p, overwrite=True)
    with pytest.raises(L.LatError, match="TIME"):
        L.inspect_ft1(p)


def test_controls_are_available_and_named():
    assert "time_shuffled" in L.CONTROLS
    assert "off_source_region" in L.CONTROLS
    d = np.array([0.1, 0.5, 0.2, 0.9])
    sh = L.time_shuffled_null(d)
    assert sh["preserves"] == "interval multiset"
    assert sh["count"] == 4
    po = L.poisson_null(2.0, 100)
    assert po["control"] == "matched_poisson" and po["count"] == 100


def test_energy_bands_are_frozen():
    assert L.ENERGY_BANDS_MEV[0] == (30, 100)
    assert len(L.ENERGY_BANDS_MEV) == 5
