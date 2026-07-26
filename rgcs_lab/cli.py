"""Unified ``rgcs-lab`` CLI (also ``python -m rgcs_lab``).

Core numerical subcommands (golay, frames, memory, dual-pole,
lattice, metasurface) keep the Codex lane's canonical behavior and
argument surface and execute the Codex cores directly. The hub
subcommands (doctor, serve, modules, coordinate, predictions) come
from the Cursor lane and go through the adapter layer.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

from rgcs_lab import PRODUCT_NAME, __version__
from rgcs_lab.dual_pole import audit_file
from rgcs_lab.frames import rotation_receipt
from rgcs_lab.golay import demo as golay_demo
from rgcs_lab.lattice import LatticeConfig, simulate
from rgcs_lab.memory import run_benchmark
from rgcs_lab.metasurface import MetasurfaceConfig, sweep
from rgcs_lab.receipts import dumps


def _print_result(obj) -> None:
    if hasattr(obj, "to_dict"):
        print(json.dumps(obj.to_dict(), indent=2))
    else:
        print(json.dumps(obj, indent=2))


# ---------------------------------------------------------------- hub


def cmd_doctor(_args) -> int:
    from rgcs_lab.adapters import coordinate
    from rgcs_lab.common.privacy import privacy_banner
    from rgcs_lab.common.status import module_catalog

    print(PRODUCT_NAME, __version__)
    print(privacy_banner())
    print("modules:", ", ".join(m["id"] for m in module_catalog()))
    print("coordinate:", coordinate.doctor())
    print(dumps({"package": "rgcs-lab", "version": __version__,
                 "status": "OK", "commands": [
                     "golay demo", "frames example", "memory benchmark",
                     "dual-pole audit", "lattice run", "metasurface sweep",
                     "coordinate decode|roundtrip", "predictions freeze|verify",
                     "modules", "serve"]}), end="")
    return 0


def cmd_serve(args) -> int:
    from rgcs_lab.common.privacy import PrivacyDefaults, privacy_banner

    privacy = PrivacyDefaults()
    host = args.host or privacy.bind_host
    port = args.port or privacy.bind_port
    if host not in ("127.0.0.1", "localhost", "::1") and not args.allow_remote:
        print(
            "refused: refusing non-loopback bind without --allow-remote "
            f"(requested host={host})",
            file=sys.stderr,
        )
        return 2
    try:
        import uvicorn
    except ImportError:
        print(
            "uvicorn/fastapi required: pip install 'rgcs[workbench]'",
            file=sys.stderr,
        )
        return 3
    from rgcs_lab.api import create_app

    print(f"serving {PRODUCT_NAME} on http://{host}:{port}/")
    print(privacy_banner())
    uvicorn.run(create_app(), host=host, port=port, log_level="info")
    return 0


def cmd_modules(_args) -> int:
    from rgcs_lab.common.status import module_catalog

    _print_result({"modules": module_catalog()})
    return 0


def cmd_coordinate(args) -> int:
    from rgcs_lab.adapters import coordinate

    if args.action == "decode":
        _print_result(coordinate.decode(args.value))
        return 0
    if args.action == "roundtrip":
        result = coordinate.roundtrip(args.value)
        _print_result(result)
        return 0 if result.status.value == "GREEN" else 5
    return 2


def cmd_pred(args) -> int:
    from rgcs_lab.adapters import services

    doc = json.loads(Path(args.path).read_text(encoding="utf-8"))
    if args.action == "freeze":
        _print_result(services.predictions_freeze(doc))
    else:
        _print_result(services.predictions_verify(doc))
    return 0


# --------------------------------------------------- codex core lane


def cmd_golay_demo(args) -> int:
    flips = list(range(args.random_flips)) if args.random_flips is not None else args.flip
    print(dumps(golay_demo(args.address, flips)))
    return 0


def cmd_frames_example(args) -> int:
    if args.name == "earth-south-up":
        rec = rotation_receipt("earth-east-north-up", "earth-south-up",
                               [0.0, 0.0, 1.0], math.pi)
    else:
        rec = rotation_receipt("identity", "identity",
                               [0.0, 0.0, 1.0], 0.0)
    print(dumps(rec))
    return 0


def cmd_memory_benchmark(args) -> int:
    corpus = args.corpus
    if corpus is None:
        from rgcs_lab.adapters.services import default_memory_corpus

        corpus = str(default_memory_corpus())
    print(dumps(run_benchmark(corpus, args.query, args.top_k)))
    return 0


def cmd_dual_pole_audit(args) -> int:
    rec = audit_file(args.claim)
    return_code = 0 if rec["status"] != "RED" else 2
    print(dumps(rec))
    return return_code


def cmd_lattice_run(args) -> int:
    cfg = LatticeConfig(steps=args.steps, dt_s=args.dt_s,
                        coupling_rad_s=args.coupling_rad_s,
                        damping_s=args.damping_s,
                        drive_amplitude=args.drive_amplitude,
                        directed_phase_rad=args.directed_phase_rad)
    print(dumps(simulate(cfg)))
    return 0


def cmd_metasurface_sweep(args) -> int:
    cfg = MetasurfaceConfig(points=args.points, f_min_hz=args.f_min_hz,
                            f_max_hz=args.f_max_hz)
    print(dumps(sweep(cfg)))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="rgcs-lab", description=PRODUCT_NAME)
    sub = p.add_subparsers(dest="command", required=True)

    d = sub.add_parser("doctor", help="local health and privacy defaults")
    d.set_defaults(fn=cmd_doctor)

    s = sub.add_parser("serve", help="local FastAPI workbench (loopback default)")
    s.add_argument("--host", default=None)
    s.add_argument("--port", type=int, default=None)
    s.add_argument("--allow-remote", action="store_true")
    s.set_defaults(fn=cmd_serve)

    m = sub.add_parser("modules", help="list hub modules and status badges")
    m.set_defaults(fn=cmd_modules)

    c = sub.add_parser("coordinate")
    csub = c.add_subparsers(dest="action", required=True)
    cd = csub.add_parser("decode")
    cd.add_argument("value")
    cd.set_defaults(fn=cmd_coordinate)
    cr = csub.add_parser("roundtrip")
    cr.add_argument("value")
    cr.set_defaults(fn=cmd_coordinate)

    golay = sub.add_parser("golay")
    gs = golay.add_subparsers(dest="golay_command", required=True)
    gd = gs.add_parser("demo")
    gd.add_argument("--address", type=int, default=165876523)
    gd.add_argument("--flip", type=int, action="append", default=[])
    gd.add_argument("--random-flips", type=int,
                    help="deterministic public demo: flips bits 0..N-1")
    gd.set_defaults(fn=cmd_golay_demo)

    frames = sub.add_parser("frames")
    fs = frames.add_subparsers(dest="frames_command", required=True)
    fe = fs.add_parser("example")
    fe.add_argument("name", choices=["earth-south-up", "identity"])
    fe.set_defaults(fn=cmd_frames_example)

    memory = sub.add_parser("memory")
    ms = memory.add_subparsers(dest="memory_command", required=True)
    mb = ms.add_parser("benchmark")
    mb.add_argument("corpus", nargs="?", default=None,
                    help="corpus directory (default: packaged hub corpus)")
    mb.add_argument("--query", default="energy provenance claim")
    mb.add_argument("--top-k", type=int, default=3)
    mb.set_defaults(fn=cmd_memory_benchmark)

    dp = sub.add_parser("dual-pole")
    ds = dp.add_subparsers(dest="dual_pole_command", required=True)
    da = ds.add_parser("audit")
    da.add_argument("claim")
    da.set_defaults(fn=cmd_dual_pole_audit)

    lattice = sub.add_parser("lattice")
    ls = lattice.add_subparsers(dest="lattice_command", required=True)
    lr = ls.add_parser("run")
    lr.add_argument("config", nargs="?", help="reserved for integration adapters")
    lr.add_argument("--steps", type=int, default=100)
    lr.add_argument("--dt-s", type=float, default=0.01)
    lr.add_argument("--coupling-rad-s", type=float, default=1.0)
    lr.add_argument("--damping-s", type=float, default=0.0)
    lr.add_argument("--drive-amplitude", type=float, default=0.0)
    lr.add_argument("--directed-phase-rad", type=float, default=0.0)
    lr.set_defaults(fn=cmd_lattice_run)

    meta = sub.add_parser("metasurface")
    mts = meta.add_subparsers(dest="metasurface_command", required=True)
    sw = mts.add_parser("sweep")
    sw.add_argument("config", nargs="?", help="reserved for integration adapters")
    sw.add_argument("--points", type=int, default=9)
    sw.add_argument("--f-min-hz", type=float, default=1.0e9)
    sw.add_argument("--f-max-hz", type=float, default=4.0e9)
    sw.set_defaults(fn=cmd_metasurface_sweep)

    pred = sub.add_parser("predictions")
    psub = pred.add_subparsers(dest="action", required=True)
    pf = psub.add_parser("freeze")
    pf.add_argument("path")
    pf.set_defaults(fn=cmd_pred)
    pv = psub.add_parser("verify")
    pv.add_argument("path")
    pv.set_defaults(fn=cmd_pred)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.fn(args))


if __name__ == "__main__":
    raise SystemExit(main())
