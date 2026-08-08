"""``rgcs-sonic``: headless Frequency Key Studio renders.

Usage:
    rgcs-sonic list
    rgcs-sonic render RGCS-SCH-0001 --duration 60 --out exports/
    rgcs-sonic beats
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="rgcs-sonic", description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="list seed recipes")
    sub.add_parser("beats", help="list beat targets")
    render = sub.add_parser("render", help="render a seed recipe")
    render.add_argument("recipe_id")
    render.add_argument("--duration", type=float, default=None,
                        help="override duration in seconds")
    render.add_argument("--out", type=Path, default=Path("."),
                        help="output directory")
    batch = sub.add_parser("batch", help="render several seed recipes")
    batch.add_argument("recipe_ids", nargs="*",
                       help="recipe ids (default: all)")
    batch.add_argument("--duration", type=float, default=None)
    batch.add_argument("--out", type=Path, default=Path("."))
    rfile = sub.add_parser(
        "render-file",
        help="render an imported frequency_session JSON file")
    rfile.add_argument("session_file", type=Path)
    rfile.add_argument("--duration", type=float, default=None,
                       help="override duration in seconds (regenerates "
                            "the standard timeline shape)")
    rfile.add_argument("--out", type=Path, default=Path("."))
    args = ap.parse_args(argv)

    from rgcs_desktop.services.sonic_recipes import (RecipeError,
                                                     load_beat_targets,
                                                     load_recipes,
                                                     recipe_by_id,
                                                     recipe_to_session)

    if args.command == "list":
        for recipe in load_recipes():
            print(f"{recipe['recipe_id']}: {recipe['title']} "
                  f"(carrier {recipe['carrier_hz']:g} Hz, beat "
                  f"{recipe['beat_hz']:g} Hz, {recipe['duration_min']} min)")
        return 0
    if args.command == "beats":
        for beat in load_beat_targets():
            print(f"{beat['hz']:g} Hz — {beat['label']} "
                  f"[{beat['status']}]: {beat['use']}")
        return 0
    if args.command == "batch":
        from rgcs_desktop.services.sonic_exports import batch_render
        ids = args.recipe_ids or [r["recipe_id"] for r in load_recipes()]
        manifest = batch_render(ids, args.out, duration_s=args.duration)
        failed = [r for r in manifest["results"]
                  if r["status"] != "rendered"]
        for result in manifest["results"]:
            if result["status"] == "rendered":
                print(f"{result['recipe_id']}: {result['wav']} "
                      f"(peak {result['peak']:.3f})")
            else:
                print(f"{result['recipe_id']}: FAILED — "
                      f"{result['error']}", file=sys.stderr)
        print(f"batch: {len(manifest['results']) - len(failed)}/"
              f"{len(manifest['results'])} rendered -> {args.out}")
        return 1 if failed else 0

    # render / render-file
    from rgcs_desktop.services.sonic_exports import (
        export_bundle, export_recipe_json, export_session_pdf,
        export_youtube_metadata_sheet, render_session_wav, verify_bundle)
    if args.command == "render-file":
        from rgcs_desktop.services.session_store import (
            SessionStoreError, load_session_file)
        try:
            session = load_session_file(args.session_file)
        except SessionStoreError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        stem = session.get("session_id", args.session_file.stem)
    else:
        try:
            recipe = recipe_by_id(args.recipe_id)
            session = recipe_to_session(recipe, duration_s=args.duration)
        except RecipeError as exc:
            print(f"refused: {exc}", file=sys.stderr)
            return 1
        stem = recipe["recipe_id"]
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    wav = out / f"{stem}.wav"
    receipt = render_session_wav(session, wav,
                                 duration_s=args.duration)
    session["exports"] = {"wav": wav.name}
    recipe_json = export_recipe_json(session, out / f"{stem}.recipe.json")
    pdf = export_session_pdf(session, receipt,
                             out / f"{stem}_session_sheet.pdf")
    meta = export_youtube_metadata_sheet(session,
                                         out / f"{stem}_youtube.txt")
    bundle = export_bundle(session, [wav, recipe_json, pdf, meta],
                           out / f"{stem}_bundle.zip")
    check = verify_bundle(bundle)
    print(f"rendered {wav} (peak {receipt['peak']:.3f}, "
          f"rms {receipt['rms']:.3f}, normalized {receipt['normalized']})")
    print(f"bundle {bundle}: "
          f"{'OK' if check['ok'] else 'CHECKSUM MISMATCH'} "
          f"({check['n_members']} members)")
    return 0 if check["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
