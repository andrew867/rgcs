"""Unified CLI for RGCS Recursive Infrastructure Lab."""

from __future__ import annotations

import argparse
import math

from . import __version__
from .dual_pole import audit_file
from .frames import rotation_receipt
from .golay import demo as golay_demo
from .lattice import LatticeConfig, simulate
from .memory import run_benchmark
from .metasurface import MetasurfaceConfig, sweep
from .receipts import dumps


def cmd_doctor(_args) -> int:
    print(dumps({"package": "rgcs-lab", "version": __version__,
                 "status": "OK", "commands": [
                     "golay demo", "frames example", "memory benchmark",
                     "dual-pole audit", "lattice run", "metasurface sweep"]}))
    return 0


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
    print(dumps(run_benchmark(args.corpus, args.query, args.top_k)))
    return 0


def cmd_dual_pole_audit(args) -> int:
    rec = audit_file(args.claim)
    print(dumps(rec))
    return 0 if rec["status"] != "RED" else 2


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
    p = argparse.ArgumentParser(prog="rgcs-lab")
    sub = p.add_subparsers(dest="command", required=True)
    d = sub.add_parser("doctor")
    d.set_defaults(fn=cmd_doctor)

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
    mb.add_argument("corpus")
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
    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
