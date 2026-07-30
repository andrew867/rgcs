"""``python -m r1053`` -- the RGCS V1 map workbench, standalone.

This lane is runnable without reading the rest of the repository::

    python -m r1053 --help
    python -m r1053 parse 168930443
    python -m r1053 map 168930443
    python -m r1053 path 167849523 168930443
    python -m r1053 polygon 165876523,165892743,165892763,165892783
    python -m r1053 serve

``parse``    structural receipt for one vector: binary, octal, fields,
             branch, frame, claim class, blockers.
``map``      one-vector map.
``path``     two vectors: great-circle route, distance, bearing, midpoint.
``polygon``  three or more: area, perimeter, centroid, live builder.
``serve``    loopback HTTP server so generated maps can fetch basemap
             tiles; a ``file://`` page cannot.

Every command prints the same numbers it draws, so the picture and the
arithmetic can be checked against each other. And every command states
the boundary: the geometry is verified, the vertex positions are not.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from r1053 import (certificate, kernel, ledger, pathmap, polygon,
                   polygon_page)

DEFAULT_MAPS = os.path.join("internal-docs", "RGCS_R10_53_V1_EARTH_ROOT",
                            "maps")


def _latlon(text):
    if not text:
        return None
    lat, lon = text.split(",")
    return (float(lat), float(lon))


def _cmd_path(args) -> int:
    rec = pathmap.path_between(args.vector_a, args.vector_b,
                               _latlon(args.a_latlon),
                               _latlon(args.b_latlon))
    out = args.out or os.path.join(
        DEFAULT_MAPS, f"rgcs_path_{args.vector_a}_{args.vector_b}.html")
    vendor = os.path.relpath(os.path.join(DEFAULT_MAPS, "vendor"),
                             os.path.dirname(os.path.abspath(out)))
    pathmap.render_html(rec, out, vendor_rel=vendor.replace(os.sep, "/"))
    A, B = rec["endpoints"]
    cc = pathmap.cross_check(A["lat"], A["lon"], B["lat"], B["lon"])
    print(f"from  {A['vector']}  {A['lat']:.6f}, {A['lon']:.6f}"
          f"   [{A['coordinate_source']}]  {A['label']}")
    print(f"      octal {A['octal10']}  branch {A['branch_octal']}"
          f"  face {A['source_face']}")
    print(f"to    {B['vector']}  {B['lat']:.6f}, {B['lon']:.6f}"
          f"   [{B['coordinate_source']}]  {B['label']}")
    print(f"      octal {B['octal10']}  branch {B['branch_octal']}"
          f"  face {B['source_face']}")
    print()
    print(f"distance        {rec['distance_km']:.3f} km "
          f"({rec['cell_edges_depth9']:.2f} depth-9 cell edges)")
    print(f"initial bearing {rec['initial_bearing_deg']:.2f} deg")
    print(f"midpoint        {rec['midpoint'][0]:.6f}, "
          f"{rec['midpoint'][1]:.6f}")
    print(f"cross-check     3 formulas agree: {cc['agree']} "
          f"(spread {cc['max_disagreement_km']:.2e} km)")
    print(f"same branch     {rec['same_branch']}")
    print()
    print(f"map written     {out}  ({os.path.getsize(out):,} B)")
    print()
    print("NOTE: the PATH is exact great-circle geometry. The endpoint")
    print("POSITIONS are projector output and remain underdetermined")
    print("under V1-B01/B02 -- they are candidates, not located targets.")
    if args.json:
        print()
        print(json.dumps({k: v for k, v in rec.items() if k != "polyline"},
                         indent=2))
    return 0


def _cmd_polygon(args) -> int:
    words = [w for chunk in args.vectors for w in chunk.replace(",", " ").split()]
    rec = polygon.build(words, reorder=args.reorder)
    out = args.out or os.path.join(DEFAULT_MAPS, "rgcs_polygon.html")
    vendor = os.path.relpath(os.path.join(DEFAULT_MAPS, "vendor"),
                             os.path.dirname(os.path.abspath(out)))
    polygon_page.render(out, initial=[v["vector"] for v in rec["vertices"]],
                        vendor_rel=vendor.replace(os.sep, "/"))
    for i, v in enumerate(rec["vertices"]):
        print(f"  {i + 1:2d}. {v['vector']}  {v['lat']:10.6f}, {v['lon']:11.6f}"
              f"  [{v['coordinate_source']}]  {v['label']}")
    print()
    print(f"vertices        {rec['vertex_count']}  ({rec['vertex_order']})")
    print(f"perimeter       {rec['perimeter_km']:,.3f} km")
    if rec["is_simple"]:
        print(f"area            {rec['area_km2']:,.3f} km2")
        print(f"  cross-check   {rec['area_km2_cross_check']:,.3f} km2 "
              f"(rel diff {rec['area_methods_agree_rel']:.2e})")
    else:
        print(f"area            NOT REPORTED - polygon self-intersects at "
              f"edge pairs {rec['self_intersections']}")
        print("                a self-crossing ring has no well-defined "
              "interior; try --reorder")
    print(f"centroid        {rec['centroid'][0]:.6f}, {rec['centroid'][1]:.6f}")
    print(f"branches        {', '.join(rec['branches'])}"
          f"  (all same: {rec['all_same_branch']})")
    print()
    print(f"map written     {out}  ({os.path.getsize(out):,} B)")
    print("serve it with:  python -m r1053 serve-maps")
    print()
    print("NOTE: the polygon geometry is exact for these vertices. The")
    print("VERTEX POSITIONS are projector output and remain")
    print("underdetermined under V1-B01/B02.")
    if args.json:
        print()
        print(json.dumps(rec, indent=2))
    return 0


BOUNDARY = (
    "The tool verifies geometry. It does not verify that a candidate "
    "vertex is physically true.")


def _cmd_parse(args) -> int:
    """Structural receipt for one vector."""
    cert = certificate.address_certificate(args.vector)
    if args.json:
        print(json.dumps(cert, indent=2))
        return 0
    w, f = cert["wire"], cert["fields"]
    print(f"vector          {w['decimal']}")
    print(f"lane            {w['lane']}  ({w['width_bits']}-bit direct word)")
    print(f"binary30        {w['binary30']}")
    print(f"octal10         {w['octal10']}")
    print(f"branch          {w['branch_octal']}"
          f"{'  (British)' if w['branch_octal'] == '117' else ''}"
          f"{'  (North American)' if w['branch_octal'] == '120' else ''}")
    print(f"F5 / Q22 / S3   {f['F5']} / {f['Q22']} / {f['S3_m3']}"
          f"   (S3 is the check digit, not geometry)")
    print(f"source face     {f['source_face']}  = (F5 + 14) % 20")
    print(f"Q22 path        {' '.join(str(x) for x in f['q22_path'])}")
    lab = cert["label"]["active"]
    if lab:
        print(f"active label    {lab}")
    if cert["label"]["retired"]:
        r = cert["label"]["retired"]
        print(f"retired label   {r['retired_label']}  ({r['status']})")
    p = cert["projection"]
    print(f"V1 projection   {p['v1_pinned_lat']:.6f}, "
          f"{p['v1_pinned_lon']:.6f}")
    if "pinning_gap_km" in p:
        print(f"  operator alt  {p['operator_supplied_lat']:.6f}, "
              f"{p['operator_supplied_lon']:.6f}"
              f"   gap {p['pinning_gap_km']:,.1f} km")
    print(f"claim class     {', '.join(cert['claim_class'])}")
    print(f"blockers        {', '.join(cert['blockers'])}")
    print()
    print(BOUNDARY)
    return 0


def _cmd_map(args) -> int:
    """One-vector map: a degenerate path from the point to itself."""
    rec = pathmap.path_between(args.vector, args.vector,
                               _latlon(args.latlon), _latlon(args.latlon))
    out = args.out or os.path.join(DEFAULT_MAPS,
                                   f"rgcs_map_{args.vector}.html")
    vendor = os.path.relpath(os.path.join(DEFAULT_MAPS, "vendor"),
                             os.path.dirname(os.path.abspath(out)))
    polygon_page.render(out, initial=[str(args.vector).strip()],
                        vendor_rel=vendor.replace(os.sep, "/"))
    A = rec["endpoints"][0]
    print(f"vector          {A['vector']}  {A['label']}")
    print(f"octal           {A['octal10']}  branch {A['branch_octal']}")
    print(f"position        {A['lat']:.6f}, {A['lon']:.6f}"
          f"   [{A['coordinate_source']}]")
    print(f"map written     {out}  ({os.path.getsize(out):,} B)")
    print("serve it with:  python -m r1053 serve")
    print()
    print(BOUNDARY)
    return 0


def _cmd_certificate(args) -> int:
    print(json.dumps(certificate.address_certificate(args.vector), indent=2))
    return 0


def _cmd_serve_maps(args) -> int:
    """Serve a directory over loopback so map pages can fetch tiles.

    A ``file://`` page cannot load the basemap, so viewing a path map
    means serving it. Loopback only, matching the workbench default.
    """
    import functools
    import http.server
    handler = functools.partial(http.server.SimpleHTTPRequestHandler,
                                directory=args.directory)
    srv = http.server.ThreadingHTTPServer((args.host, args.port), handler)
    print(f"serving {args.directory} at http://{args.host}:{args.port}/")
    print("Ctrl-C to stop")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog="python -m r1053",
        description="RGCS V1 coordinate tools")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("path", help="two-vector great-circle path map")
    sp.add_argument("vector_a")
    sp.add_argument("vector_b")
    sp.add_argument("-o", "--out", help="output .html path")
    sp.add_argument("--a-latlon", help="override endpoint A as 'lat,lon'")
    sp.add_argument("--b-latlon", help="override endpoint B as 'lat,lon'")
    sp.add_argument("--json", action="store_true", help="also print JSON")
    sp.set_defaults(fn=_cmd_path)

    sg = sub.add_parser("polygon",
                        help="N-vector polygon: area, perimeter, centroid")
    sg.add_argument("vectors", nargs="+",
                    help="3+ vectors, comma- or space-separated")
    sg.add_argument("-o", "--out", help="output .html path")
    sg.add_argument("--reorder", action="store_true",
                    help="order vertices by bearing from their centroid")
    sg.add_argument("--json", action="store_true", help="also print JSON")
    sg.set_defaults(fn=_cmd_polygon)

    sr = sub.add_parser("parse", help="structural receipt for one vector")
    sr.add_argument("vector")
    sr.add_argument("--json", action="store_true", help="full certificate")
    sr.set_defaults(fn=_cmd_parse)

    sm = sub.add_parser("map", help="one-vector map")
    sm.add_argument("vector")
    sm.add_argument("-o", "--out", help="output .html path")
    sm.add_argument("--latlon", help="override the position as 'lat,lon'")
    sm.set_defaults(fn=_cmd_map)

    sc = sub.add_parser("certificate", help="typed address certificate")
    sc.add_argument("vector")
    sc.set_defaults(fn=_cmd_certificate)

    for name, helptext in (("serve", "serve generated maps over loopback"),
                           ("serve-maps", "alias for serve")):
        sv = sub.add_parser(name, help=helptext)
        sv.add_argument("directory", nargs="?", default=DEFAULT_MAPS)
        sv.add_argument("--host", default="127.0.0.1")
        sv.add_argument("--port", type=int, default=8791)
        sv.set_defaults(fn=_cmd_serve_maps)

    args = p.parse_args(argv)
    try:
        return args.fn(args)
    except polygon.PolygonError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except kernel.DirectLaneError as exc:
        print(f"error: {exc}", file=sys.stderr)
        if any(str(getattr(args, a, "")).strip() in ledger.GATED_WIDE_ENVELOPE
               for a in ("vector", "vector_a", "vector_b")):
            print("this is a gated wide-envelope record (blocker V1-B07); "
                  "it is refused, never truncated", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
