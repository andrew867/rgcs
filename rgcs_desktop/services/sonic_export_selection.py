"""Frequency Studio export selection: write only the file types the
user asked for (v8.5.2 export UX).

``export_selected(session, kinds, out_dir)`` writes exactly the chosen
kinds; ``expected_export_files`` names the files beforehand so the UI
can show what an export will produce. A single-kind selection produces
that one file — never the whole bundle. No Qt imports here.
"""
from __future__ import annotations

import json
from pathlib import Path

from rgcs_desktop.services.sonic_exports import (export_bundle,
                                                 export_recipe_json,
                                                 export_session_pdf,
                                                 export_youtube_metadata_sheet,
                                                 render_session_wav,
                                                 verify_bundle)

EXPORT_KINDS = ("recipe_json", "session_json", "wav_preview", "wav_full",
                "session_pdf", "youtube_txt", "bundle_zip")

PREVIEW_DURATION_S = 12.0


class ExportSelectionError(ValueError):
    """An unknown export kind or an empty selection was requested."""


def _filenames(session: dict) -> dict:
    sid = session.get("session_id", "session")
    return {
        "recipe_json": f"{sid}.recipe.json",
        "session_json": f"{sid}.session.json",
        "wav_preview": f"{sid}_preview.wav",
        "wav_full": f"{sid}.wav",
        "session_pdf": f"{sid}_session_sheet.pdf",
        "youtube_txt": f"{sid}_youtube.txt",
        "bundle_zip": f"{sid}_bundle.zip",
    }


def _check_kinds(kinds) -> list[str]:
    kinds = list(kinds)
    if not kinds:
        raise ExportSelectionError("select at least one export type")
    unknown = [k for k in kinds if k not in EXPORT_KINDS]
    if unknown:
        raise ExportSelectionError(
            f"unknown export type(s): {', '.join(unknown)}; expected "
            f"{', '.join(EXPORT_KINDS)}")
    return kinds


def expected_export_files(session: dict, kinds) -> list[str]:
    """Filenames the selection will write, before writing anything.

    The bundle also materializes its member files (WAV, recipe JSON,
    PDF, YouTube draft) next to the zip, so they are listed too.
    """
    kinds = set(_check_kinds(kinds))
    if "bundle_zip" in kinds:
        kinds |= {"wav_full", "recipe_json", "session_pdf",
                  "youtube_txt"}
    names = _filenames(session)
    return [names[k] for k in EXPORT_KINDS if k in kinds]


COLLISION_MODES = ("overwrite", "increment")


def _resolve_collisions(out_dir: Path, names: dict, kinds: set,
                        mode: str) -> dict:
    """Auto-increment planned filenames that already exist."""
    if mode == "overwrite":
        return names
    resolved = dict(names)
    for kind in kinds:
        base = Path(names[kind])
        stem = base.name[: -len("".join(base.suffixes))] \
            if base.suffixes else base.stem
        suffix = "".join(base.suffixes)
        candidate = names[kind]
        n = 2
        while (out_dir / candidate).exists():
            candidate = f"{stem}_{n}{suffix}"
            n += 1
        resolved[kind] = candidate
    return resolved


def export_selected(session: dict, kinds, out_dir: str | Path,
                    preview_duration_s: float = PREVIEW_DURATION_S,
                    on_collision: str = "overwrite") -> dict:
    """Write the selected export kinds into ``out_dir``.

    Returns {kind: Path} for every file written, plus "receipt" (the
    render receipt) when a render happened and "provenance" (app
    version, git commit, input hash). The session sheet PDF always
    reports a real render: if the full WAV is not part of the
    selection, the render still runs and its stats feed the PDF, but
    the WAV itself is not kept. ``on_collision``: "overwrite" replaces
    existing files, "increment" writes name_2, name_3, …
    """
    if on_collision not in COLLISION_MODES:
        raise ExportSelectionError(
            f"unknown collision mode {on_collision!r}; expected "
            f"{' or '.join(COLLISION_MODES)}")
    kinds = set(_check_kinds(kinds))
    if "bundle_zip" in kinds:
        kinds |= {"wav_full", "recipe_json", "session_pdf",
                  "youtube_txt"}
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    names = _resolve_collisions(out_dir, _filenames(session), kinds,
                                on_collision)
    written: dict = {}
    work = dict(session)

    receipt = None
    if "wav_full" in kinds:
        wav = out_dir / names["wav_full"]
        receipt = render_session_wav(work, wav)
        work["exports"] = {"wav": wav.name}
        written["wav_full"] = wav
    if "wav_preview" in kinds:
        preview = out_dir / names["wav_preview"]
        preview_receipt = render_session_wav(
            work, preview, duration_s=preview_duration_s)
        if receipt is None:
            receipt = preview_receipt
        written["wav_preview"] = preview
    if "session_pdf" in kinds and receipt is None:
        # honest stats without keeping the WAV: render, report, discard
        scratch = out_dir / f".{names['wav_full']}.tmp"
        try:
            receipt = render_session_wav(work, scratch)
        finally:
            scratch.unlink(missing_ok=True)

    if "recipe_json" in kinds:
        written["recipe_json"] = export_recipe_json(
            work, out_dir / names["recipe_json"])
    if "session_json" in kinds:
        target = out_dir / names["session_json"]
        target.write_text(json.dumps(work, indent=2, sort_keys=True)
                          + "\n", encoding="utf-8")
        written["session_json"] = target
    if "session_pdf" in kinds:
        written["session_pdf"] = export_session_pdf(
            work, receipt, out_dir / names["session_pdf"])
    if "youtube_txt" in kinds:
        written["youtube_txt"] = export_youtube_metadata_sheet(
            work, out_dir / names["youtube_txt"])
    if "bundle_zip" in kinds:
        members = [written[k] for k in ("wav_full", "recipe_json",
                                        "session_pdf", "youtube_txt")]
        zip_path = export_bundle(work, members,
                                 out_dir / names["bundle_zip"])
        check = verify_bundle(zip_path)
        if not check["ok"]:
            raise RuntimeError(
                f"bundle checksum verification failed: {check}")
        written["bundle_zip"] = zip_path

    if receipt is not None:
        written["receipt"] = receipt
    from rgcs_core.provenance import sha256_of_jsonable

    from rgcs_desktop.services.export_receipts import (git_commit,
                                                       software_versions)
    body = dict(session)
    body.pop("sha256", None)
    written["provenance"] = {
        "software": software_versions(),
        "git_commit": git_commit(),
        "input_sha256": sha256_of_jsonable(body),
    }
    return written
