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

    # render
    from rgcs_desktop.services.sonic_exports import (
        export_bundle, export_recipe_json, export_session_pdf,
        export_youtube_metadata_sheet, render_session_wav, verify_bundle)
    try:
        recipe = recipe_by_id(args.recipe_id)
        session = recipe_to_session(recipe, duration_s=args.duration)
    except RecipeError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    stem = recipe["recipe_id"]
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
