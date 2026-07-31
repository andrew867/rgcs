"""``python -m rgcs_archive`` -- the archive codec workbench CLI."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

from rgcs_archive import catalog as C
from rgcs_archive import streams as S
from rgcs_archive import text_lanes as TL
from rgcs_archive import transport as T
from rgcs_archive import wide_envelope as W

MISSIONS = {
    "vela5b": {
        "root": "https://heasarc.gsfc.nasa.gov/FTP/vela5b/raw/",
        "status": "IMPLEMENTED",
        "product": "All Sky Monitor X-ray FITS, NOT the original serial "
                   "radio telemetry and NOT the gamma-ray detector bitstream",
        "compression": "legacy Unix .Z (LZW)",
        "channels": "two X-ray energy channels (C1CNTS, C2CNTS)",
        "spin_period_s": 64, "orbit_period_h": 112,
        "caveat": "instrument temperature and gain variation produce large "
                  "artificial periodic structure; ~0.1% of the historical "
                  "data was corrupted in a transfer (see all_bad.dat)",
    },
    "voyager2_pws": {"root": "https://pds.nasa.gov/", "status": "ADAPTER_STUB",
                     "product": "PDS4 raw waveform bundle",
                     "blocker": "PDS4 label reader not implemented"},
    "batse": {"root": "https://heasarc.gsfc.nasa.gov/docs/cgro/",
              "status": "ADAPTER_STUB", "product": "burst trigger products",
              "blocker": "trigger package reader not implemented"},
    "fermi_gbm": {"root": "https://fermi.gsfc.nasa.gov/ssc/data/",
                  "status": "ADAPTER_STUB",
                  "product": "TTE / CTIME / CSPEC",
                  "blocker": "trigger package reader not implemented"},
}

CACHE_DEFAULT = os.path.join("internal-docs", "RGCS_R10_61_ARCHIVE", "cache")


def _client():
    import httpx
    return httpx.Client(timeout=C.DEFAULT_TIMEOUT_S,
                        headers={"User-Agent": C.USER_AGENT},
                        follow_redirects=True)


def _fetcher(cl, dry):
    def fetch(u):
        if dry:
            raise RuntimeError("dry-run: no network")
        time.sleep(C.DEFAULT_DELAY_S)
        r = cl.get(u)
        r.raise_for_status()
        return r.text
    return fetch


def cmd_mission_list(a):
    for k, v in MISSIONS.items():
        print(f"{k:14s} {v['status']:14s} {v['product'][:56]}")
    return 0


def cmd_adapter_info(a):
    m = MISSIONS.get(a.mission)
    if not m:
        print(f"unknown mission {a.mission!r}", file=sys.stderr)
        return 2
    print(json.dumps({a.mission: m}, indent=2))
    return 0


def cmd_catalog(a):
    m = MISSIONS[a.mission]
    cl = _client()
    try:
        entries = C.crawl(m["root"], _fetcher(cl, a.dry_run),
                          max_depth=a.depth)
    finally:
        cl.close()
    files = [e for e in entries if not e.get("is_dir") and "error" not in e]
    print(f"{len(files)} files catalogued under {m['root']}")
    for e in files[:a.limit]:
        print(f"  {e['reported_size'] or '?':>10}  {e['url']}")
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump(entries, fh, indent=2)
        print(f"manifest -> {a.out}")
    return 0


def cmd_estimate(a):
    m = MISSIONS[a.mission]
    cl = _client()
    try:
        entries = C.crawl(m["root"], _fetcher(cl, a.dry_run), max_depth=a.depth)
    finally:
        cl.close()
    print(json.dumps(C.estimate(entries), indent=2))
    return 0


def cmd_download(a):
    cl = _client()
    try:
        for url in a.urls:
            d = T.download(url, a.cache, client=cl,
                           quota_bytes=a.quota_mib * 1024 ** 2)
            print(json.dumps(d, indent=2))
    finally:
        cl.close()
    return 0


def cmd_inspect(a):
    path = a.path
    with open(path, "rb") as fh:
        head = fh.read(16)
    fmt = T.detect_format(head)
    if fmt in ("compress_z", "gzip", "bzip2", "xz"):
        with open(path, "rb") as fh:
            dc = T.decompress(fh.read(), fmt)
        path = path + ".decompressed"
        with open(path, "wb") as fh:
            fh.write(dc["data"])
        print(json.dumps({k: v for k, v in dc.items() if k != "data"},
                         indent=2))
    print(json.dumps(S.inspect_fits(path), indent=2))
    return 0


def cmd_derive(a):
    if a.recipe == "ARCHIVE_BYTES":
        _, r = S.archive_bytes(a.path)
    elif a.recipe == "FITS_COLUMN_RAW":
        _, r = S.fits_column_raw(a.path, a.hdu, a.column)
    elif a.recipe == "COUNT_CHANNEL_STREAM":
        _, r = S.count_channel_stream(a.path, a.hdu, a.columns, a.interleave)
    else:
        print(f"recipe {a.recipe} not wired to the CLI yet", file=sys.stderr)
        return 2
    print(json.dumps(r, indent=2))
    return 0


def cmd_parse_long(a):
    p = W.parse_record(a.record)
    print(json.dumps(p, indent=2))
    return 0


def cmd_route(a):
    p = W.parse_record(a.record)
    splits = W.enumerate_splits(p["payload_octal"])
    print(f"record {p['record']}")
    print(f"{p['width_law']}   pad {p['pad_bits']} bits "
          f"({p['pad_convention']})")
    print(f"payload octal {p['payload_octal']}")
    print(f"\n{len(splits)} legal splits, none selected\n")
    print(f"{'dL':>3} {'dR':>3} | {'E3':>2} {'S_tor':>5} {'S_pol':>5} "
          f"{'S_rad':>5} | chain_L / chain_R")
    for s in splits:
        print(f"{s['d_left']:>3} {s['d_right']:>3} | {s['E3']:>2} "
              f"{s['S_tor']:>5} {s['S_pol']:>5} {s['S_rad']:>5} | "
              f"{s['chain_left'][:14]:<14} {s['chain_right'][:14]}")
    print(f"\nauthority: {splits[0]['authority']}   "
          f"pivot: {splits[0]['pivot_semantics']}")
    return 0


def cmd_scan_text(a):
    print(json.dumps(TL.assess(a.payload_octal, trials=a.trials), indent=2))
    return 0


def cmd_verify(a):
    r = W.fixture_receipt()
    for k, c in r["checks"].items():
        print(f"  {k:20s} {'MATCH' if c['match'] else 'FAIL'}  {c['computed']}")
    print(f"\nall_match: {r['all_match']}")
    print(f"payload sha256: {r['payload_sha256']}")
    return 0 if r["all_match"] else 1


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="python -m rgcs_archive",
                                description="RGCS archive codec workbench")
    p.add_argument("--dry-run", action="store_true",
                   help="never touch the network")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("mission-list").set_defaults(fn=cmd_mission_list)
    s = sub.add_parser("adapter-info"); s.add_argument("mission")
    s.set_defaults(fn=cmd_adapter_info)

    for name, fn in (("catalog", cmd_catalog), ("estimate", cmd_estimate)):
        s = sub.add_parser(name)
        s.add_argument("mission", choices=list(MISSIONS))
        s.add_argument("--depth", type=int, default=1)
        s.add_argument("--limit", type=int, default=20)
        s.add_argument("--out")
        s.set_defaults(fn=fn)

    s = sub.add_parser("download")
    s.add_argument("urls", nargs="+")
    s.add_argument("--cache", default=CACHE_DEFAULT)
    s.add_argument("--quota-mib", type=int, default=64)
    s.set_defaults(fn=cmd_download)

    s = sub.add_parser("inspect"); s.add_argument("path")
    s.set_defaults(fn=cmd_inspect)

    s = sub.add_parser("derive")
    s.add_argument("path")
    s.add_argument("--recipe", default="ARCHIVE_BYTES", choices=S.RECIPES)
    s.add_argument("--hdu", type=int, default=1)
    s.add_argument("--column", default="C1CNTS")
    s.add_argument("--columns", nargs="+", default=["C1CNTS", "C2CNTS"])
    s.add_argument("--interleave", default="alternating",
                   choices=S.INTERLEAVINGS)
    s.set_defaults(fn=cmd_derive)

    s = sub.add_parser("parse-long"); s.add_argument("record")
    s.set_defaults(fn=cmd_parse_long)
    s = sub.add_parser("route"); s.add_argument("record")
    s.add_argument("--all-splits", action="store_true", default=True)
    s.set_defaults(fn=cmd_route)
    s = sub.add_parser("scan-text"); s.add_argument("payload_octal")
    s.add_argument("--trials", type=int, default=100)
    s.set_defaults(fn=cmd_scan_text)
    sub.add_parser("verify").set_defaults(fn=cmd_verify)

    a = p.parse_args(argv)
    try:
        return a.fn(a)
    except (C.CatalogError, T.TransportError, S.StreamError,
            W.EnvelopeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
