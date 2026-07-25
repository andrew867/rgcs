"""P57 -- the ``cw-atlas`` command-line interface.

A thin :mod:`argparse` front end over the framework-agnostic service layer
(:mod:`cwatlas.service`). Every subcommand prints a single JSON object to
stdout, so the CLI composes cleanly with ``jq`` and downstream tooling and
carries the same CRS + epoch + claim-class receipt the service returns.

Subcommands::

    cw-atlas encode    --lat --lon [--body --frame --epoch] --uncertainty ...
    cw-atlas decode    <vector> [--codec ...]
    cw-atlas legacy    <raw> [--digits/--no-digits]
    cw-atlas roundtrip --lat --lon --uncertainty ...
    cw-atlas export    --point lat,lon[,height] [...] --uncertainty ...
    cw-atlas verify    (--vector <vector> | --bundle <path>)

Invocation forms::

    python -m cwatlas.cli <subcommand> ...

Malformed arguments are handled by argparse (exit code 2). A well-formed but
rejected request (bad codec, missing input) prints a typed error object and
exits 1. A decode of a malformed vector is a *typed refusal* printed at exit 0 --
the boundary never crashes.

Nothing here reads a wall-clock; epochs are decimal-year strings passed in.

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional, Sequence

from cwatlas import service

#: Phase identity.
PHASE_ID = "P57"
TRANCHE = "T08"

PROG = "cw-atlas"


def _emit(result: dict) -> None:
    """Print a result as a single deterministic JSON object."""
    print(json.dumps(result, indent=2, sort_keys=True))


def _parse_point(text: str) -> dict:
    """Parse a ``lat,lon`` or ``lat,lon,height`` argument into components."""
    parts = [p.strip() for p in text.split(",")]
    if len(parts) not in (2, 3):
        raise argparse.ArgumentTypeError(
            f"point must be 'lat,lon' or 'lat,lon,height', got {text!r}")
    try:
        lat = float(parts[0])
        lon = float(parts[1])
        height = float(parts[2]) if len(parts) == 3 else None
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"point components must be numbers: {exc}") from exc
    return {"latitude_deg": lat, "longitude_deg": lon, "height_m": height}


def _add_point_args(sub: argparse.ArgumentParser, *, with_point: bool) -> None:
    """Shared frame/epoch/body/uncertainty options."""
    sub.add_argument("--body", default="EARTH", help="reference body id")
    sub.add_argument("--frame", default="CRS84", help="coordinate reference system id")
    sub.add_argument("--epoch", default="2020.0", help="decimal-year epoch string")
    sub.add_argument("--codec", default="CW-GEO-1",
                     choices=list(service.SUPPORTED_CODECS), help="canonical codec")
    sub.add_argument("--commit", default=None, help="software commit to record")


def build_parser() -> argparse.ArgumentParser:
    """Build the ``cw-atlas`` argument parser."""
    parser = argparse.ArgumentParser(
        prog=PROG,
        description="CW Atlas bidirectional geocoder CLI (JSON output).")
    subs = parser.add_subparsers(dest="command", required=True)

    # encode
    p_enc = subs.add_parser("encode", help="encode a declared point to a vector")
    p_enc.add_argument("--lat", type=float, required=True, help="latitude in degrees")
    p_enc.add_argument("--lon", type=float, required=True, help="longitude in degrees")
    p_enc.add_argument("--uncertainty", type=float, required=True,
                       help="explicit uncertainty in metres (no hidden default)")
    p_enc.add_argument("--height", type=float, default=None, help="height in metres")
    p_enc.add_argument("--shell", type=int, default=None, help="shell state 0..8")
    _add_point_args(p_enc, with_point=False)

    # decode
    p_dec = subs.add_parser("decode", help="decode a canonical vector to a point")
    p_dec.add_argument("vector", help="the canonical CW vector string")
    p_dec.add_argument("--codec", default=None,
                       choices=list(service.SUPPORTED_CODECS),
                       help="force a codec (else read from the vector)")

    # legacy
    p_leg = subs.add_parser("legacy", help="search legacy codecs over a raw string")
    p_leg.add_argument("raw", help="the raw found vector string")
    p_leg.add_argument("--digits", dest="digits", action="store_true", default=True,
                       help="search the digits-only view (default)")
    p_leg.add_argument("--no-digits", dest="digits", action="store_false",
                       help="search the whitespace-normalized view instead")

    # roundtrip
    p_rt = subs.add_parser("roundtrip", help="encode then decode and report residual")
    p_rt.add_argument("--lat", type=float, required=True, help="latitude in degrees")
    p_rt.add_argument("--lon", type=float, required=True, help="longitude in degrees")
    p_rt.add_argument("--uncertainty", type=float, required=True,
                      help="explicit uncertainty in metres")
    p_rt.add_argument("--height", type=float, default=None, help="height in metres")
    p_rt.add_argument("--shell", type=int, default=None, help="shell state 0..8")
    _add_point_args(p_rt, with_point=False)

    # export
    p_exp = subs.add_parser("export", help="encode a batch into an audit bundle")
    p_exp.add_argument("--point", type=_parse_point, action="append", required=True,
                       metavar="LAT,LON[,HEIGHT]",
                       help="a point; repeat --point for a batch")
    p_exp.add_argument("--uncertainty", type=float, required=True,
                       help="explicit uncertainty in metres for every point")
    _add_point_args(p_exp, with_point=True)

    # verify
    p_ver = subs.add_parser("verify", help="verify a vector or an audit bundle")
    grp = p_ver.add_mutually_exclusive_group(required=True)
    grp.add_argument("--vector", help="a canonical vector to verify")
    grp.add_argument("--bundle", help="path to an audit-bundle JSON file to verify")

    return parser


def _cmd_encode(args) -> int:
    result = service.encode_point(
        body_id=args.body, frame_id=args.frame, epoch=args.epoch,
        latitude_deg=args.lat, longitude_deg=args.lon,
        uncertainty_m=args.uncertainty, height_m=args.height,
        shell_state=args.shell, codec=args.codec, software_commit=args.commit)
    _emit(result)
    return 0


def _cmd_decode(args) -> int:
    _emit(service.decode_vector(args.vector, codec=args.codec))
    return 0


def _cmd_legacy(args) -> int:
    _emit(service.legacy_search(args.raw, use_digits=args.digits))
    return 0


def _cmd_roundtrip(args) -> int:
    result = service.round_trip(
        body_id=args.body, frame_id=args.frame, epoch=args.epoch,
        latitude_deg=args.lat, longitude_deg=args.lon,
        uncertainty_m=args.uncertainty, height_m=args.height,
        shell_state=args.shell, codec=args.codec, software_commit=args.commit)
    _emit(result)
    return 0


def _cmd_export(args) -> int:
    points = []
    for p in args.point:
        points.append({
            "body_id": args.body,
            "frame_id": args.frame,
            "epoch": args.epoch,
            "latitude_deg": p["latitude_deg"],
            "longitude_deg": p["longitude_deg"],
            "height_m": p["height_m"],
            "uncertainty_m": args.uncertainty,
        })
    _emit(service.export_bundle(points, software_commit=args.commit,
                                codec=args.codec))
    return 0


def _cmd_verify(args) -> int:
    if args.vector is not None:
        _emit(service.verify_vector(args.vector))
        return 0
    # --bundle: verify a serialized audit bundle from a JSON file.
    from cwatlas import audit_bundle
    try:
        with open(args.bundle, "r", encoding="utf-8") as fh:
            bundle = json.load(fh)
    except (OSError, ValueError) as exc:
        _emit({"operation": "verify", "valid": False,
               "error": f"cannot read bundle: {exc}"})
        return 1
    valid = audit_bundle.verify_bundle(bundle)
    _emit({"operation": "verify", "valid": bool(valid),
           "source_vector_geographic_semantics": "NOT_CLAIMED"})
    return 0


_DISPATCH = {
    "encode": _cmd_encode,
    "decode": _cmd_decode,
    "legacy": _cmd_legacy,
    "roundtrip": _cmd_roundtrip,
    "export": _cmd_export,
    "verify": _cmd_verify,
}


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Parse ``argv`` and dispatch a subcommand. Returns a process exit code.

    Malformed arguments raise ``SystemExit(2)`` via argparse. A well-formed but
    rejected request prints a typed error object and returns 1.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = _DISPATCH[args.command]
    try:
        return handler(args)
    except service.ServiceError as exc:
        _emit({"operation": args.command, "error": str(exc),
               "claim_class": "REFUSAL",
               "source_vector_geographic_semantics": "NOT_CLAIMED"})
        return 1


def cli_report() -> dict:
    """P57 CLI declaration receipt."""
    return {
        "module": "cwatlas.cli",
        "phase_id": PHASE_ID,
        "tranche": TRANCHE,
        "prog": PROG,
        "subcommands": sorted(_DISPATCH),
        "output_format": "JSON",
        "claim_class": "CANONICAL_ROUND_TRIP",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "CW_ATLAS_CLI_JSON_OVER_SERVICE_LAYER",
        "what_this_does_not_say": (
            "The CLI is a JSON front end over the service layer; it decodes no "
            "source vector to a real location and adds no claim the service "
            "does not already make."),
    }


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
