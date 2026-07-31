"""R10.61 -- catalog, transport and stream tests. No network required.

The crawler takes its fetcher by injection, so the whole catalog lane is
exercised against a local fake index. The allowlist tests are the
security boundary and run offline by construction.
"""

import gzip
import os

import numpy as np
import pytest

from rgcs_archive import catalog as C
from rgcs_archive import streams as S
from rgcs_archive import transport as T
from rgcs_archive.cli import MISSIONS, main

FAKE_INDEX = """<html><head><title>Index of /FTP/vela5b/raw</title></head>
<body><h1>Index of /FTP/vela5b/raw</h1><pre>
<a href="?C=N;O=D">Name</a>
<img src="/icons/back.gif"> <a href="/FTP/vela5b/">Parent Directory</a>   -
<img src="/icons/folder.gif"> <a href="1969/">1969/</a>   1996-09-05 23:51    -
<img src="/icons/folder.gif"> <a href="b00/">b00/</a>     1996-09-06 00:09    -
<a href="all_bad.README">all_bad.README</a>   1994-08-01 10:25  2.0K
<a href="all_bad.dat">all_bad.dat</a>         1995-02-14 15:48  8.0M
<a href="http://evil.example.com/x">offsite</a> 1999-01-01 00:00  1.0K
</pre><hr></body></html>"""

APACHE_INDEX = """<pre>
<a href="a.raw.Z">a.raw.Z</a>   14-Feb-1995 15:48  2.5M
</pre>"""


# ------------------------------------------------- allowlist boundary

@pytest.mark.parametrize("url,ok", [
    ("https://heasarc.gsfc.nasa.gov/FTP/vela5b/raw/", True),
    ("https://heasarc.gsfc.nasa.gov/FTP/vela5b/raw/1969/x.Z", True),
    ("https://heasarc.gsfc.nasa.gov/FTP/vela5b/raw/../../rosat/", False),
    ("https://heasarc.gsfc.nasa.gov/FTP/rosat/", False),
    ("https://evil.example.com/FTP/vela5b/", False),
    ("http://heasarc.gsfc.nasa.gov/FTP/vela5b/", False),   # http, not https
    ("file:///etc/passwd", False),
])
def test_allowlist(url, ok):
    assert C.is_allowed(url) is ok


def test_traversal_cannot_escape_a_root():
    with pytest.raises(C.CatalogError):
        C.assert_allowed(
            "https://heasarc.gsfc.nasa.gov/FTP/vela5b/raw/../../secret/")


def test_offsite_links_in_an_index_are_discarded():
    e = C.parse_index(FAKE_INDEX,
                      "https://heasarc.gsfc.nasa.gov/FTP/vela5b/raw/")
    assert all("evil.example.com" not in x["url"] for x in e)
    assert all(x["url"].startswith(
        "https://heasarc.gsfc.nasa.gov/FTP/vela5b/raw/") for x in e)


# ----------------------------------------------------- index parsing

def test_iso_dates_do_not_leak_the_year_into_the_size():
    """The defect that reported a 4.9 GiB archive as 24 MiB."""
    e = {x["name"]: x for x in C.parse_index(
        FAKE_INDEX, "https://heasarc.gsfc.nasa.gov/FTP/vela5b/raw/")}
    assert e["all_bad.README"]["reported_size"] == 2048
    assert e["all_bad.dat"]["reported_size"] == 8 * 1024 ** 2
    assert e["all_bad.dat"]["reported_size"] != 1995        # not the year
    assert e["all_bad.README"]["reported_date"] == "1994-08-01 10:25"


def test_classic_apache_dates_still_parse():
    e = C.parse_index(APACHE_INDEX,
                      "https://heasarc.gsfc.nasa.gov/FTP/vela5b/raw/")
    assert e[0]["reported_size"] == int(2.5 * 1024 ** 2)


def test_directories_and_files_are_distinguished():
    e = {x["name"]: x for x in C.parse_index(
        FAKE_INDEX, "https://heasarc.gsfc.nasa.gov/FTP/vela5b/raw/")}
    assert e["1969"]["is_dir"] and e["b00"]["is_dir"]
    assert not e["all_bad.dat"]["is_dir"]


def test_crawl_uses_the_injected_fetcher_and_estimates():
    calls = []

    def fetch(u):
        calls.append(u)
        return FAKE_INDEX if u.endswith("/raw/") else "<pre></pre>"

    files = C.crawl("https://heasarc.gsfc.nasa.gov/FTP/vela5b/raw/",
                    fetch, max_depth=1)
    assert calls and all(C.is_allowed(u) for u in calls)
    est = C.estimate(files)
    assert est["files"] == 2
    assert est["known_bytes"] == 2048 + 8 * 1024 ** 2


def test_a_failing_directory_is_recorded_not_swallowed():
    def fetch(u):
        raise OSError("boom")
    out = C.crawl("https://heasarc.gsfc.nasa.gov/FTP/vela5b/raw/", fetch)
    assert out and "error" in out[0]


# -------------------------------------------------------- transport

def test_format_detection_is_by_magic_not_extension():
    assert T.detect_format(b"\x1f\x9d\x90rest") == "compress_z"
    assert T.detect_format(gzip.compress(b"x")) == "gzip"
    assert T.detect_format(b"SIMPLE  =                    T") == "fits"
    assert T.detect_format(b"nope") == "unknown"
    # a .Z-named file that is really gzip must report gzip
    assert T.detect_format(gzip.compress(b"y")) != "compress_z"


def test_gzip_round_trips_with_both_hashes():
    payload = b"vela" * 500
    d = T.decompress(gzip.compress(payload))
    assert d["data"] == payload
    assert d["input_format"] == "gzip"
    assert d["compressed_sha256"] != d["decompressed_sha256"]
    assert d["decompressed_sha256"] == T.sha256_bytes(payload)


def test_decompression_bomb_is_refused(monkeypatch):
    monkeypatch.setattr(T, "MAX_DECOMPRESSED_BYTES", 64)
    with pytest.raises(T.TransportError, match="exceeds"):
        T.decompress(gzip.compress(b"x" * 4096))


def test_filenames_are_sanitised():
    assert "/" not in T.safe_name("../../etc/passwd")
    assert "\\" not in T.safe_name(r"..\..\win.ini")
    assert T.safe_name("") == "unnamed"
    assert T.safe_name("01_05aug1969.raw.Z") == "01_05aug1969.raw.Z"


def test_cache_path_is_content_addressed(tmp_path):
    sha = "a" * 64
    p1 = T.cache_path(str(tmp_path), sha, "x.Z")
    p2 = T.cache_path(str(tmp_path), sha, "x.Z")
    assert p1 == p2 and sha in os.path.basename(p1)


def test_download_refuses_a_url_outside_the_allowlist(tmp_path):
    with pytest.raises(C.CatalogError):
        T.download("https://evil.example.com/x.Z", str(tmp_path))


# ---------------------------------------------------------- streams

def _tiny_fits(path):
    from astropy.io import fits
    n = 32
    cols = fits.ColDefs([
        fits.Column(name="TIME", format="1D", array=np.arange(n, dtype=float)),
        fits.Column(name="C1CNTS", format="1E",
                    array=np.arange(n, dtype=np.float32)),
        fits.Column(name="C2CNTS", format="1E",
                    array=(np.arange(n, dtype=np.float32) * 2)),
    ])
    h = fits.BinTableHDU.from_columns(cols, name="RATE")
    h.header["TELESCOP"] = "VELA 5B"
    fits.HDUList([fits.PrimaryHDU(), h]).writeto(path, overwrite=True)
    return path


def test_inspect_reports_schema_without_semantics(tmp_path):
    p = _tiny_fits(str(tmp_path / "t.fits"))
    ins = S.inspect_fits(p)
    assert ins["hdu_count"] == 2
    t = ins["hdus"][1]
    assert t["rows"] == 32
    assert [c["name"] for c in t["columns"]] == ["TIME", "C1CNTS", "C2CNTS"]
    assert t["TELESCOP"] == "VELA 5B"


def test_archive_bytes_is_reversible_and_hashed(tmp_path):
    p = _tiny_fits(str(tmp_path / "t.fits"))
    data, r = S.archive_bytes(p)
    assert r["lossy"] is False and r["inverse"] == "identity"
    assert data == open(p, "rb").read()
    assert r["sha256"] == T.sha256_bytes(data)


def test_column_raw_round_trips_through_the_recorded_dtype(tmp_path):
    p = _tiny_fits(str(tmp_path / "t.fits"))
    data, r = S.fits_column_raw(p, 1, "C1CNTS")
    assert r["endianness"] == "big" and r["lossy"] is False
    back = np.frombuffer(data, dtype=np.dtype(r["dtype"]))
    assert np.allclose(back, np.arange(32))


def test_count_stream_declares_its_interleave_and_lossiness(tmp_path):
    p = _tiny_fits(str(tmp_path / "t.fits"))
    for il in ("channel_1_only", "alternating", "difference", "sum"):
        _, r = S.count_channel_stream(p, 1, ["C1CNTS", "C2CNTS"], il)
        assert r["interleave"] == il
        assert r["lossy"] is True and r["lossy_reason"]
    with pytest.raises(S.StreamError, match="undeclared"):
        S.count_channel_stream(p, 1, ["C1CNTS", "C2CNTS"], "made_up")


def test_mark_space_threshold_grid_is_frozen():
    vals = list(range(100))
    _, r = S.mark_space_stream(vals, 0.5)
    assert r["threshold_quantile"] == 0.5 and r["lossy"] is True
    with pytest.raises(S.StreamError, match="not on the frozen grid"):
        S.mark_space_stream(vals, 0.6234)


def test_bitplane_keeps_its_plane_index():
    data = (np.arange(16, dtype=">u2")).tobytes()
    _, r = S.bitplane_stream(data, 16, 3)
    assert r["plane"] == 3 and r["lossy"] is True
    with pytest.raises(S.StreamError):
        S.bitplane_stream(data, 16, 99)


def test_every_recipe_receipt_carries_provenance(tmp_path):
    p = _tiny_fits(str(tmp_path / "t.fits"))
    for _, r in (S.archive_bytes(p), S.fits_column_raw(p, 1, "C1CNTS")):
        for k in ("recipe", "sha256", "bytes", "lossy"):
            assert k in r


# -------------------------------------------------------------- CLI

def test_mission_list_and_adapter_info(capsys):
    assert main(["mission-list"]) == 0
    out = capsys.readouterr().out
    assert "vela5b" in out and "IMPLEMENTED" in out
    assert "ADAPTER_STUB" in out          # unfinished adapters say so
    assert main(["adapter-info", "vela5b"]) == 0
    assert "All Sky Monitor" in capsys.readouterr().out


def test_adapter_stubs_declare_their_blocker():
    for name in ("voyager2_pws", "batse", "fermi_gbm"):
        assert MISSIONS[name]["status"] == "ADAPTER_STUB"
        assert MISSIONS[name]["blocker"]


def test_cli_verify_runs_the_fixture(capsys):
    assert main(["verify"]) == 0
    assert "all_match: True" in capsys.readouterr().out


def test_cli_route_prints_all_36_and_selects_none(capsys):
    from rgcs_archive.wide_envelope import FIXTURE_RECORD
    assert main(["route", FIXTURE_RECORD]) == 0
    out = capsys.readouterr().out
    assert "36 legal splits, none selected" in out
    assert "STRUCTURAL_PARSE_ONLY" in out


def test_cli_rejects_a_bad_record(capsys):
    assert main(["parse-long", "12345"]) == 2
    assert "error" in capsys.readouterr().err
