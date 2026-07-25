"""P29 — Backend API and CLI integration (the real application boundary).

R10.8.2's engine is a set of green library modules (root certificate, frozen
calibration, forward/inverse source geocoders, candidate ensemble, overlay
contract). P29 exposes that engine through the **real application boundary the
operator drives**: a pure-stdlib :mod:`argparse` command-line interface. There
is no web framework here — ``fastapi``/``flask`` are unavailable and out of scope
— so the "backend API" is a deterministic CLI whose every subcommand prints
machine-readable JSON and returns a process exit code.

Subcommands
-----------
``root``
    Resolve the locked two-layer root certificate at ``(epoch, shell)``.
``calibration``
    Freeze the two-anchor calibration and print the sealed receipt.
``encode``
    Map selection -> source-style vector (the inverse geocoder, P22): a body
    ``(lat, lon, shell)`` under a named frozen profile becomes a five-token
    source-style address plus its quantization/non-uniqueness honesty fields.
``decode``
    Source vector -> pin / cell / region / alias set (the forward geocoder,
    P21). Always a pin or region, never a bare refusal, never invented precision.
``inspect``
    Structural inspection of a source vector: tokens, wire display, codec id —
    no location is committed.
``batch``
    Decode many source vectors in one deterministic pass.
``receipt``
    Emit an evidence receipt / seal manifest (the governance claims taxonomy and
    the module declaration seals). ``--module NAME`` emits one module's report.

Governance
----------
Every subcommand's JSON carries the three seals (``PHYSICAL_VALIDATION`` /
``PHYSICAL_EFFECTS`` / ``SOURCE_ORIGIN`` NOT-CLAIMED/NOT-VALIDATED) and
``measured_here == "nothing"``. A candidate is at most ``CALIBRATED_CANDIDATE``:
the CLI never prints a result as ``MEASURED``/``REPLICATED`` and never prints a
validated source origin. Locked decisions are never reopened; a frozen parameter
is never retuned here. Tranche T07 modules (holdout registry, no-retune,
description-length ledger, prospective challenge) are imported **lazily** and
guarded, so the CLI degrades gracefully when that sibling tranche has not landed.

This is a ``SOFTWARE_RESULT`` boundary over the engine. It measures nothing and
validates no source origin.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional, Sequence

from cwatlas.r1082 import claims as _claims
from cwatlas.r1082 import (
    geocode_forward,
    geocode_inverse,
    overlay_spec,
    result_states,
    root_certificate,
)
from cwatlas.r1082.route_core import RouteError, parse_five_token
from cwatlas.r1082.semantic_expand import SHELL_MAX, SHELL_MIN

CLI_ID = "CW-R1082-CLI"
CLI_VERSION = "1.0.0"

#: The result-class values that a candidate boundary must never emit.
_FORBIDDEN_RESULT_LEAKS = frozenset({"MEASURED", "REPLICATED"})

#: The four T07 modules imported lazily. Absent -> the CLI still runs.
_T07_MODULES = (
    "holdout_registry", "no_retune", "search_ledger", "prospective_challenge")

#: The common seals stamped onto every CLI payload.
_SEALS = {
    "measured_here": "nothing",
    "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
    "physical_effects": "PHYSICAL_EFFECTS_NOT_CLAIMED",
    "source_origin": "SOURCE_ORIGIN_NOT_VALIDATED",
    "max_evidence": _claims.MAX_CANDIDATE_EVIDENCE.value,
}


class CLIError(RuntimeError):
    """A user-facing CLI error (bad arguments or an out-of-range request)."""


# -- helpers ----------------------------------------------------------------

def _seal(payload: dict) -> dict:
    """Stamp the governance seals onto a payload (idempotent)."""
    out = dict(payload)
    for key, val in _SEALS.items():
        out.setdefault(key, val)
    return out


def _guard_no_measured_leak(payload: dict) -> None:
    """Refuse to emit any result typed as MEASURED / REPLICATED or origin-valid.

    The evidence firewall as an output guard: a candidate is a software result
    under a declared calibration, never a measured fact, and the source origin
    is never validated. Any leak routes through the governance refusal.
    """
    blob = json.dumps(payload, default=str)

    # Scan every evidence_class value for a measurement class.
    def _walk(obj):
        if isinstance(obj, dict):
            ev = obj.get("evidence_class")
            if isinstance(ev, str) and ev in _FORBIDDEN_RESULT_LEAKS:
                _claims.refuse_candidate_as_measured(ev)
            for v in obj.values():
                _walk(v)
        elif isinstance(obj, list):
            for v in obj:
                _walk(v)
    _walk(payload)
    if '"SOURCE_ORIGIN_VALIDATED"' in blob:
        _claims.refuse_source_origin_validated()


def _emit(payload: dict, out=None) -> int:
    """Serialize a sealed, firewall-checked payload as deterministic JSON."""
    if out is None:
        out = sys.stdout
    sealed = _seal(payload)
    _guard_no_measured_leak(sealed)
    out.write(json.dumps(sealed, sort_keys=True, indent=2, default=float))
    out.write("\n")
    return 0


def _check_shell(shell: int) -> None:
    if not SHELL_MIN <= shell <= SHELL_MAX:
        raise CLIError(f"shell {shell} out of range [{SHELL_MIN}, {SHELL_MAX}].")


def _select_profile(kind: str, family: Optional[str] = None):
    """Resolve a ``--profile`` choice into a frozen-profile handle (or None).

    ``none``   -> no calibration (a lone candidate becomes a REGION, not a pin);
    ``all``    -> the all-families stub (an alias set, never a false single pin);
    ``single`` -> a single-family stub (a calibrated candidate point);
    ``frozen`` -> the real frozen T05 profile if importable, else the all stub.
    """
    if kind == "none":
        return None
    if kind == "all":
        return geocode_forward.default_frozen_stub()
    if kind == "single":
        return (geocode_forward.single_family_stub(family) if family
                else geocode_forward.single_family_stub())
    if kind == "frozen":
        return geocode_forward.load_frozen_profile()
    raise CLIError(f"unknown profile kind {kind!r}")


def _t07_reports() -> dict:
    """Collect T07 module declaration reports if importable (lazy, guarded)."""
    found: dict = {}
    for name in _T07_MODULES:
        try:  # pragma: no cover - exercised only once T07 lands
            import importlib
            mod = importlib.import_module(f"cwatlas.r1082.{name}")
        except Exception:  # noqa: BLE001 - sibling tranche absent: skip cleanly
            continue
        fn = getattr(mod, f"{name}_report", None)
        if callable(fn):
            try:  # pragma: no cover
                found[name] = fn()
            except Exception:  # noqa: BLE001
                found[name] = {"status": "report_unavailable"}
    return found


# -- subcommand handlers ----------------------------------------------------

def cmd_root(args) -> dict:
    """Resolve the locked two-layer root certificate at ``(epoch, shell)``."""
    _check_shell(args.shell)
    cert = root_certificate.resolve_or_refuse(
        args.epoch, args.shell, body_id=args.body)
    if cert.is_refusal():
        return {
            "command": "root", "cli_id": CLI_ID, "cli_version": CLI_VERSION,
            "in_validity": False, "result_type": cert.result_class,
            "profile_id": root_certificate.PROFILE_ID,
            "epoch_year": cert.epoch_year, "shell_index": cert.shell_index,
            "radius_m": cert.radius_m, "reason": cert.reason,
            "note": "out of field-model validity; no direction is invented",
        }
    return {
        "command": "root", "cli_id": CLI_ID, "cli_version": CLI_VERSION,
        "in_validity": True,
        "certificate": cert.to_earth_root_profile_dict(),
        "certificate_hash": cert.certificate_hash,
        "evidence_class": cert.evidence_class,
        "shell_supplies_radius": True, "altitude_missing": False,
    }


def cmd_calibration(args) -> dict:
    """Freeze the two-anchor calibration and print the sealed receipt.

    Uses the real T05 calibration when importable; the freeze is deterministic,
    so a clean checkout reproduces the freeze hash.
    """
    try:
        from cwatlas.r1082 import calibration_fit, calibration_freeze
        fit = calibration_fit.fit_all()
        frozen = calibration_freeze.freeze_calibration(
            fit, epoch_choice=args.epoch)
        return {
            "command": "calibration", "cli_id": CLI_ID,
            "cli_version": CLI_VERSION,
            "profile_id": calibration_freeze.PROFILE_ID,
            "receipt": frozen.receipt(),
            "receipt_verifies": frozen.verify(),
            "frozen_parameters": list(_claims.FROZEN_PARAMETERS),
            "retuning_forbidden": True,
            "freeze_precedes_holdout": True,
            "evidence_class": _claims.EvidenceClass.CALIBRATED_CANDIDATE.value,
        }
    except Exception as exc:  # noqa: BLE001 - degrade to the declaration seal
        return {
            "command": "calibration", "cli_id": CLI_ID,
            "cli_version": CLI_VERSION,
            "profile_id": "EARTH_ROOT_D_V1",
            "status": "CALIBRATION_ENGINE_UNAVAILABLE",
            "reason": str(exc),
            "frozen_parameters": list(_claims.FROZEN_PARAMETERS),
            "retuning_forbidden": True,
            "evidence_class": _claims.EvidenceClass.SOFTWARE_RESULT.value,
        }


def cmd_encode(args) -> dict:
    """Map selection -> source-style vector (the inverse geocoder)."""
    _check_shell(args.shell)
    profile = _select_profile(args.profile, family=args.family)
    if profile is None:
        raise CLIError(
            "encode requires a NAMED frozen profile (the fitted orientation and "
            "retained family come from the calibration); use "
            "--profile single|all|frozen, not none.")
    inv = geocode_inverse.inverse_geocode(
        args.lat, args.lon, args.shell, profile,
        family_name=args.family, coarse_epoch=args.coarse_epoch,
        fine_epoch=args.fine_epoch)
    payload = inv.to_serializable()
    payload.update({
        "command": "encode", "cli_id": CLI_ID, "cli_version": CLI_VERSION,
        "evidence_class": _claims.EvidenceClass.CALIBRATED_CANDIDATE.value,
        "shell_supplies_radius": True, "altitude_missing": False,
    })
    return payload


def cmd_decode(args) -> dict:
    """Source vector -> pin / cell / region / alias set (the forward geocoder)."""
    _check_shell(args.shell)
    profile = _select_profile(args.profile, family=args.family)
    fwd = geocode_forward.geocode(
        args.vector, profile, shell=args.shell, epoch_year=args.epoch,
        body=args.body)
    payload = fwd.to_serializable()
    payload.update({
        "command": "decode", "cli_id": CLI_ID, "cli_version": CLI_VERSION,
        "result_class_explanation": fwd.reason,
        "api_code": fwd.map_result.api_code if fwd.map_result else None,
        "evidence_class": _claims.EvidenceClass.CALIBRATED_CANDIDATE.value
        if fwd.is_candidate()
        else _claims.EvidenceClass.SOFTWARE_RESULT.value,
        "shell_supplies_radius": True, "altitude_missing": False,
    })
    return payload


def cmd_inspect(args) -> dict:
    """Structural inspection of a source vector (no location committed)."""
    try:
        rc = parse_five_token(args.vector)
    except RouteError as exc:
        mr = result_states.classify(
            valid=False, candidate_count=0, calibration_available=False)
        return {
            "command": "inspect", "cli_id": CLI_ID, "cli_version": CLI_VERSION,
            "input": args.vector, "valid": False,
            "result_type": mr.result_class.value, "api_code": mr.api_code,
            "reason": f"INVALID_SOURCE_VECTOR: {exc}",
            "evidence_class": mr.evidence_class.value,
        }
    return {
        "command": "inspect", "cli_id": CLI_ID, "cli_version": CLI_VERSION,
        "input": args.vector, "valid": True,
        "tokens": list(rc.tokens), "wire": rc.to_wire(), "raw": rc.raw,
        "codec_id": rc.codec_id,
        "note": ("structural parse only: a source vector is not a decoded "
                 "location; use `decode` to place a candidate."),
        "evidence_class": _claims.EvidenceClass.DERIVED_MATHEMATICS.value,
    }


def cmd_batch(args) -> dict:
    """Decode many source vectors in one deterministic pass."""
    _check_shell(args.shell)
    vectors = list(args.vectors or [])
    if args.input:
        text = (sys.stdin.read() if args.input == "-"
                else open(args.input, encoding="utf-8").read())
        stripped = text.strip()
        if stripped.startswith("["):
            vectors.extend(str(v) for v in json.loads(stripped))
        else:
            vectors.extend(
                ln.strip() for ln in stripped.splitlines() if ln.strip())
    if not vectors:
        raise CLIError("batch requires at least one vector "
                       "(--vectors ... or --input FILE/-).")
    profile = _select_profile(args.profile, family=args.family)
    results = []
    for vec in vectors:
        fwd = geocode_forward.geocode(
            vec, profile, shell=args.shell, epoch_year=args.epoch,
            body=args.body)
        results.append({
            "source_vector": vec,
            "result_type": fwd.result_type,
            "candidate_count": len(fwd.candidates),
            "region": fwd.region,
            "receipt_hash": fwd.receipt.get("receipt_hash"),
        })
    return {
        "command": "batch", "cli_id": CLI_ID, "cli_version": CLI_VERSION,
        "count": len(results), "profile": args.profile,
        "results": results,
        "evidence_class": _claims.EvidenceClass.CALIBRATED_CANDIDATE.value,
    }


#: The lightweight module reports the default receipt manifest aggregates.
_RECEIPT_MODULES = {
    "claims": _claims.claims_report,
    "cli": lambda: cli_report(),
    "geocode_forward": geocode_forward.geocode_forward_report,
    "geocode_inverse": geocode_inverse.geocode_inverse_report,
    "overlay_spec": overlay_spec.overlay_spec_report,
    "root_certificate": root_certificate.root_certificate_report,
}


def cmd_receipt(args) -> dict:
    """Emit an evidence receipt: the claims taxonomy and module seals."""
    if args.module:
        try:
            import importlib
            mod = importlib.import_module(f"cwatlas.r1082.{args.module}")
        except Exception as exc:  # noqa: BLE001
            raise CLIError(f"no such module {args.module!r}: {exc}") from exc
        fn = getattr(mod, f"{args.module}_report", None)
        if not callable(fn):
            raise CLIError(f"module {args.module!r} has no report function")
        return {
            "command": "receipt", "cli_id": CLI_ID, "cli_version": CLI_VERSION,
            "module": args.module, "report": fn(),
        }
    manifest = {name: fn() for name, fn in _RECEIPT_MODULES.items()}
    t07 = _t07_reports()
    if t07:
        manifest["t07"] = t07
    return {
        "command": "receipt", "cli_id": CLI_ID, "cli_version": CLI_VERSION,
        "profile_id": "EARTH_ROOT_D_V1",
        "claim_taxonomy": _claims.claims_report(),
        "module_seals": {
            name: {
                "verdict": rep.get("verdict"),
                "measured_here": rep.get("measured_here"),
                "source_origin": rep.get("source_origin"),
            } for name, rep in manifest.items() if isinstance(rep, dict)
            and "verdict" in rep
        },
        "t07_present": sorted(t07),
    }


# -- parser -----------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Build the argparse CLI (pure stdlib; no network, no server)."""
    p = argparse.ArgumentParser(
        prog="cwatlas-r1082",
        description=("RGCS R10.8.2 locked-root source-map atlas CLI. Every "
                     "result is a software candidate under a declared, frozen "
                     "calibration — never a measured fact, never a validated "
                     "source origin."))
    p.add_argument("--version", action="version",
                   version=f"{CLI_ID} {CLI_VERSION}")
    sub = p.add_subparsers(dest="command", required=True)

    pr = sub.add_parser("root", help="resolve the two-layer root certificate")
    pr.add_argument("--epoch", type=float, default=2020.0)
    pr.add_argument("--shell", type=int, default=3)
    pr.add_argument("--body", default="EARTH")
    pr.set_defaults(func=cmd_root)

    pc = sub.add_parser("calibration", help="freeze calibration + print receipt")
    pc.add_argument("--epoch", type=float, default=2020.0,
                    help="the frozen epoch_choice (a frozen parameter)")
    pc.set_defaults(func=cmd_calibration)

    pe = sub.add_parser("encode", help="map selection -> source-style vector")
    pe.add_argument("--lat", type=float, required=True)
    pe.add_argument("--lon", type=float, required=True)
    pe.add_argument("--shell", type=int, default=3)
    pe.add_argument("--profile", choices=("single", "all", "frozen"),
                    default="single")
    pe.add_argument("--family", default=None)
    pe.add_argument("--coarse-epoch", dest="coarse_epoch", type=int,
                    default=None)
    pe.add_argument("--fine-epoch", dest="fine_epoch", type=int, default=None)
    pe.set_defaults(func=cmd_encode)

    pd = sub.add_parser("decode", help="source vector -> pin/cell/region/alias")
    pd.add_argument("--vector", required=True)
    pd.add_argument("--shell", type=int, default=3)
    pd.add_argument("--epoch", type=float, default=2020.0)
    pd.add_argument("--body", default="EARTH")
    pd.add_argument("--profile", choices=("none", "single", "all", "frozen"),
                    default="none")
    pd.add_argument("--family", default=None)
    pd.set_defaults(func=cmd_decode)

    pi = sub.add_parser("inspect", help="structural inspection of a vector")
    pi.add_argument("--vector", required=True)
    pi.set_defaults(func=cmd_inspect)

    pb = sub.add_parser("batch", help="decode many source vectors at once")
    pb.add_argument("--vectors", nargs="+", default=None)
    pb.add_argument("--input", default=None,
                    help="a file of vectors (one per line or a JSON array); "
                         "use '-' for stdin")
    pb.add_argument("--shell", type=int, default=3)
    pb.add_argument("--epoch", type=float, default=2020.0)
    pb.add_argument("--body", default="EARTH")
    pb.add_argument("--profile", choices=("none", "single", "all", "frozen"),
                    default="none")
    pb.add_argument("--family", default=None)
    pb.set_defaults(func=cmd_batch)

    prc = sub.add_parser("receipt", help="emit an evidence receipt / seals")
    prc.add_argument("--module", default=None,
                     help="emit one module's declaration report")
    prc.set_defaults(func=cmd_receipt)

    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Entry point. Returns 0 on success, non-zero on a handled error."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        payload = args.func(args)
    except CLIError as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2
    except (RouteError, ValueError) as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2
    except _claims.R1082ClaimError as exc:
        # A governance refusal is a deliberate, correct outcome — surfaced, not
        # crashed. Exit non-zero so a pipeline notices the refusal.
        sys.stderr.write(f"refused: {exc}\n")
        return 3
    return _emit(payload)


def cli_report() -> dict:
    """P29 declaration receipt. A CLI boundary; measures nothing."""
    return {
        "phase_id": "P29",
        "tranche": "T08",
        "what_this_is": (
            "the backend API / CLI integration: a pure-stdlib argparse CLI that "
            "exposes the R10.8.2 engine through root, calibration, encode, "
            "decode, inspect, batch, and receipt subcommands, each printing "
            "deterministic JSON and returning a process exit code."),
        "cli_id": CLI_ID,
        "cli_version": CLI_VERSION,
        "subcommands": ["root", "calibration", "encode", "decode", "inspect",
                        "batch", "receipt"],
        "reused_engine": (
            "cwatlas.r1082.root_certificate / calibration_freeze / "
            "geocode_forward / geocode_inverse / result_states / overlay_spec "
            "(NOT reimplemented)"),
        "web_framework": "NONE (fastapi/flask unavailable; CLI-only boundary)",
        "t07_imported_lazily": True,
        "t07_modules": list(_T07_MODULES),
        "candidate_never_emitted_as_measured": True,
        "evidence_class": _claims.EvidenceClass.SOFTWARE_RESULT.value,
        "max_evidence": _claims.MAX_CANDIDATE_EVIDENCE.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "physical_effects": "PHYSICAL_EFFECTS_NOT_CLAIMED",
        "source_origin": "SOURCE_ORIGIN_NOT_VALIDATED",
        "verdict": "R1082_CLI_APPLICATION_BOUNDARY_CANDIDATE_NEVER_MEASURED",
        "what_this_does_not_say": (
            "The CLI is a software boundary over the engine. It measures "
            "nothing, asserts no physical effect, and validates no source "
            "origin; every candidate it prints is a CALIBRATED_CANDIDATE under "
            "a declared, frozen calibration."),
    }


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
