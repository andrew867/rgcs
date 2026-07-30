"""RCW CLI — ``rgcs-coordinate``.

Human output uses aligned labels and status badges; ``--json`` emits
canonical JSON. Exit codes distinguish the failure classes:

* 0  success
* 2  invalid input
* 3  unsupported codec or body profile
* 4  projection underdetermined (the honest current state; the result
     is still printed)
* 5  failed round-trip
* 70 internal error

``serve`` (local web workbench) ships in the projection-workbench
slice and is not present here — absent, not stubbed.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys

import rgcs_coordinate as rc
from rgcs_coordinate.codecs.federation_terra_30 import PacketError
from rgcs_coordinate.domain.claims import STANDING_CLAIMS
from rgcs_coordinate.provenance import corpus

EXIT_OK = 0
EXIT_INVALID_INPUT = 2
EXIT_UNSUPPORTED = 3
EXIT_UNDERDETERMINED = 4
EXIT_ROUNDTRIP_FAILED = 5
EXIT_INTERNAL = 70

BADGES = ("[STRUCTURAL CODEC: GREEN] "
          "[PHYSICAL PROJECTION: YELLOW UNDERDETERMINED] "
          "[STONEHENGE: TRAINING EQUALITY]")


def _print_trace(trace) -> None:
    d = trace.to_dict()
    rows = [
        ("Decimal", d["raw_decimal"]),
        ("Binary 30", d["binary30"]),
        ("Octal 10", d["octal10"]),
        ("Face", f"{d['face_id']} ({d['face_bits']}, {d['face_status']})"),
        ("Q22 bits", d["q22_bits"]),
        ("Q22 path", " ".join(map(str, d["q22_path"]))),
        ("Extracted S3", f"{d['extracted_shell']} ({d['shell_bits']})"),
        ("Spatial octal", d["spatial_octal_path"]),
        ("Morton X/Y/Z", f"{d['morton_audit']['x_index']} / "
                         f"{d['morton_audit']['y_index']} / "
                         f"{d['morton_audit']['z_index']}"),
        ("Structural", d["structural_status"]),
        ("Projection", d["physical_projection_status"]),
    ]
    if d.get("fixture_label"):
        rows.insert(1, ("Fixture", d["fixture_label"]))
    width = max(len(k) for k, _ in rows)
    print(BADGES)
    for key, value in rows:
        print(f"{key.ljust(width)}  {value}")
    print("note: Morton X/Y/Z are hierarchical path indices, not "
          "coordinates")


def _fixture_label(raw: str) -> str | None:
    for v in corpus.vectors():
        if v.raw_decimal == raw:
            if v.corrected:
                return (f"{v.label} — active shell {v.active_shell}, raw "
                        f"extraction {v.raw_extracted_shell} kept in "
                        f"provenance")
            if v.physical_label_class == "TRAINING_EQUALITY":
                return f"{v.label} (supplied training equality)"
            return v.label
    return None


def cmd_decode(args) -> int:
    trace = rc.decode_coordinate(int(args.coordinate),
                                 fixture_label=_fixture_label(
                                     str(int(args.coordinate))))
    if args.json:
        print(rc.export_trace(trace), end="")
    else:
        _print_trace(trace)
    return EXIT_OK


def cmd_encode(args) -> int:
    path = tuple(int(c) for c in args.path)
    word = rc.encode_coordinate(args.face, path, args.shell)
    if args.json:
        print(json.dumps({"face": args.face, "path": list(path),
                          "shell": args.shell, "decimal": str(word),
                          "octal": format(word, "010o")}, indent=2))
    else:
        print(f"decimal  {word}")
        print(f"octal10  {format(word, '010o')}")
    return EXIT_OK


def cmd_roundtrip(args) -> int:
    result = rc.roundtrip_coordinate(int(args.coordinate))
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        status = "EXACT" if result["exact"] else "FAILED"
        print(f"roundtrip {result['raw']} -> {result['reencoded']}: "
              f"{status}")
    return EXIT_OK if result["exact"] else EXIT_ROUNDTRIP_FAILED


def cmd_inspect_codec(args) -> int:
    from rgcs_coordinate.codecs import codec_info
    info = codec_info(args.codec)
    if args.json:
        print(json.dumps(info, indent=2))
    else:
        width = max(len(k) for k in info)
        for key, value in info.items():
            print(f"{key.ljust(width)}  {value}")
    return EXIT_OK


def cmd_project(args) -> int:
    result = rc.project_coordinate(int(args.coordinate),
                                   profile=args.profile)
    print(json.dumps(result, indent=2))
    return (EXIT_UNDERDETERMINED
            if result["status"] == "UNDERDETERMINED" else EXIT_OK)


def cmd_inverse(args) -> int:
    result = rc.inverse_project(args.lat, args.lon, args.height_km,
                                profile=args.profile)
    print(json.dumps(result, indent=2))
    return (EXIT_UNDERDETERMINED
            if result["status"] == "UNDERDETERMINED" else EXIT_OK)


def cmd_corpus_validate(args) -> int:
    if args.fixture:
        with open(args.fixture, encoding="utf-8") as fh:
            doc = json.load(fh)
        report = corpus.validate_corpus(doc)
    else:
        report = corpus.validate_corpus()
    print(json.dumps(report, indent=2))
    return EXIT_OK if report["valid"] else EXIT_INVALID_INPUT


def cmd_doctor(args) -> int:
    checks = {
        "python": platform.python_version(),
        "package_version": rc.__version__,
        "structural_codec": "OK",
        "fixtures": "OK" if corpus.validate_corpus()["valid"] else "INVALID",
    }
    try:
        import cwatlas.r1085a  # noqa: F401
        checks["projection_backend"] = "OK (cwatlas.r1085a importable)"
    except ImportError:
        checks["projection_backend"] = ("UNAVAILABLE (structural decode "
                                        "unaffected)")
    print(json.dumps(checks, indent=2))
    return EXIT_OK


def cmd_version(args) -> int:
    if args.full:
        print(json.dumps({
            "package": "rgcs-coordinate",
            "version": rc.__version__,
            "codec": rc.DEFAULT_CODEC,
            "trace_schema": "rgcs.structural-trace.v1",
            "python": platform.python_version(),
            "claims": dict(STANDING_CLAIMS),
        }, indent=2))
    else:
        print(rc.__version__)
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="rgcs-coordinate",
        description="RGCS Coordinate Workbench — structural F5|Q22|S3 "
                    "decoder and honest candidate projection.")
    sub = p.add_subparsers(dest="command", required=True)

    d = sub.add_parser("decode", help="structural decode of a packet")
    d.add_argument("coordinate")
    d.add_argument("--json", action="store_true")
    d.set_defaults(fn=cmd_decode)

    e = sub.add_parser("encode", help="fields -> packet word")
    e.add_argument("--face", type=int, required=True)
    e.add_argument("--path", required=True,
                   help="eleven quaternary digits, e.g. 33012021211")
    e.add_argument("--shell", type=int, required=True)
    e.add_argument("--json", action="store_true")
    e.set_defaults(fn=cmd_encode)

    r = sub.add_parser("roundtrip", help="decode + re-encode check")
    r.add_argument("coordinate")
    r.add_argument("--json", action="store_true")
    r.set_defaults(fn=cmd_roundtrip)

    ic = sub.add_parser("inspect-codec", help="codec metadata")
    ic.add_argument("codec")
    ic.add_argument("--json", action="store_true")
    ic.set_defaults(fn=cmd_inspect_codec)

    pr = sub.add_parser("project",
                        help="candidate physical projection (honest: "
                             "currently UNDERDETERMINED, exit 4)")
    pr.add_argument("coordinate")
    pr.add_argument("--profile", default="earth-r1085a")
    pr.set_defaults(fn=cmd_project)

    iv = sub.add_parser("inverse",
                        help="candidate inverse encode (honest: "
                             "currently UNDERDETERMINED, exit 4)")
    iv.add_argument("--lat", type=float, required=True)
    iv.add_argument("--lon", type=float, required=True)
    iv.add_argument("--height-km", type=float, default=10.0,
                    help="height above the land-zero surface")
    iv.add_argument("--profile", default="earth-r1085a")
    iv.set_defaults(fn=cmd_inverse)

    cv = sub.add_parser("corpus", help="corpus operations")
    cvs = cv.add_subparsers(dest="corpus_command", required=True)
    val = cvs.add_parser("validate",
                         help="validate fixtures against the arithmetic")
    val.add_argument("fixture", nargs="?",
                     help="fixture JSON path (default: packaged corpus)")
    val.set_defaults(fn=cmd_corpus_validate)

    doc = sub.add_parser("doctor", help="environment self-check")
    doc.set_defaults(fn=cmd_doctor)

    v = sub.add_parser("version", help="version information")
    v.add_argument("--full", action="store_true")
    v.set_defaults(fn=cmd_version)
    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.fn(args)
    except (PacketError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_INVALID_INPUT
    except KeyError as exc:
        print(f"error: {exc.args[0] if exc.args else exc}",
              file=sys.stderr)
        return EXIT_UNSUPPORTED
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_INVALID_INPUT
    except Exception as exc:                     # pragma: no cover
        print(f"internal error: {exc!r}", file=sys.stderr)
        return EXIT_INTERNAL


if __name__ == "__main__":
    raise SystemExit(main())
