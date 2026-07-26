"""CLI entry: ``rgcs-lab`` / ``python -m rgcs_lab``."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from rgcs_lab import PRODUCT_NAME, __version__
from rgcs_lab.adapters import coordinate, frames, golay
from rgcs_lab.adapters import services
from rgcs_lab.common.privacy import PrivacyDefaults, privacy_banner
from rgcs_lab.common.status import module_catalog


def _print(obj) -> None:
    if hasattr(obj, "to_dict"):
        print(json.dumps(obj.to_dict(), indent=2))
    else:
        print(json.dumps(obj, indent=2))


def cmd_doctor(_: argparse.Namespace) -> int:
    print(PRODUCT_NAME, __version__)
    print(privacy_banner())
    print("modules:", ", ".join(m["id"] for m in module_catalog()))
    print("coordinate:", coordinate.doctor())
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
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


def cmd_coordinate(args: argparse.Namespace) -> int:
    if args.action == "decode":
        _print(coordinate.decode(args.value))
        return 0
    if args.action == "roundtrip":
        result = coordinate.roundtrip(args.value)
        _print(result)
        return 0 if result.status.value == "GREEN" else 5
    return 2


def cmd_golay(args: argparse.Namespace) -> int:
    _print(golay.demo(flips_per_block=args.random_flips, seed=args.seed))
    return 0


def cmd_frames(args: argparse.Namespace) -> int:
    _print(frames.example(args.example))
    return 0


def cmd_memory(args: argparse.Namespace) -> int:
    _print(services.memory_benchmark(args.query))
    return 0


def cmd_dual(args: argparse.Namespace) -> int:
    claim = json.loads(Path(args.path).read_text(encoding="utf-8"))
    _print(services.dual_pole_audit(claim))
    return 0


def cmd_lattice(args: argparse.Namespace) -> int:
    _print(services.lattice_run(args.model))
    return 0


def cmd_meta(args: argparse.Namespace) -> int:
    _print(services.metasurface_sweep())
    return 0


def cmd_pred(args: argparse.Namespace) -> int:
    doc = json.loads(Path(args.path).read_text(encoding="utf-8"))
    if args.action == "freeze":
        _print(services.predictions_freeze(doc))
    else:
        _print(services.predictions_verify(doc))
    return 0


def cmd_modules(_: argparse.Namespace) -> int:
    _print({"modules": module_catalog()})
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="rgcs-lab", description=PRODUCT_NAME)
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("doctor", help="local health and privacy defaults")
    d.set_defaults(func=cmd_doctor)

    s = sub.add_parser("serve", help="local FastAPI workbench (loopback default)")
    s.add_argument("--host", default=None)
    s.add_argument("--port", type=int, default=None)
    s.add_argument("--allow-remote", action="store_true")
    s.set_defaults(func=cmd_serve)

    m = sub.add_parser("modules", help="list hub modules and status badges")
    m.set_defaults(func=cmd_modules)

    c = sub.add_parser("coordinate")
    csub = c.add_subparsers(dest="action", required=True)
    cd = csub.add_parser("decode")
    cd.add_argument("value")
    cd.set_defaults(func=cmd_coordinate)
    cr = csub.add_parser("roundtrip")
    cr.add_argument("value")
    cr.set_defaults(func=cmd_coordinate)

    g = sub.add_parser("golay")
    g.add_argument("demo", nargs="?", default="demo")
    g.add_argument("--random-flips", type=int, default=1)
    g.add_argument("--seed", type=int, default=1)
    g.set_defaults(func=cmd_golay)

    f = sub.add_parser("frames")
    f.add_argument("example", nargs="?", default="earth-south-up")
    f.set_defaults(func=cmd_frames)

    mem = sub.add_parser("memory")
    mem.add_argument("benchmark", nargs="?", default="benchmark")
    mem.add_argument("--query", default="golay bit flips transport wrapper")
    mem.set_defaults(func=cmd_memory)

    dp = sub.add_parser("dual-pole")
    dp.add_argument("audit")
    dp.add_argument("path")
    dp.set_defaults(func=cmd_dual)

    lat = sub.add_parser("lattice")
    lat.add_argument("run")
    lat.add_argument("model", nargs="?", default="counterrotating-ring")
    lat.set_defaults(func=cmd_lattice)

    meta = sub.add_parser("metasurface")
    meta.add_argument("sweep")
    meta.set_defaults(func=cmd_meta)

    pred = sub.add_parser("predictions")
    psub = pred.add_subparsers(dest="action", required=True)
    pf = psub.add_parser("freeze")
    pf.add_argument("path")
    pf.set_defaults(func=cmd_pred)
    pv = psub.add_parser("verify")
    pv.add_argument("path")
    pv.set_defaults(func=cmd_pred)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
