"""Frequency Key Studio exports: render receipt, session PDF sheet,
recipe JSON, YouTube metadata sheet, and bundle zip."""
from __future__ import annotations

import datetime as _dt
import zipfile
from pathlib import Path

from rgcs_core.provenance import json_dumps, sha256_file, sha256_of_jsonable

from rgcs_desktop.services import pdf_sheets, sonic_audio
from rgcs_desktop.services.export_receipts import software_versions
from rgcs_desktop.services.schemas import validate_instance
from rgcs_desktop.services.sonic_audio import binaural_pair
from rgcs_desktop.services.sonic_recipes import USER_NOTE


def render_session_wav(session: dict, out_path: Path,
                       duration_s: float | None = None) -> dict:
    """Render a session to WAV and return a schema-valid render
    receipt. ``duration_s`` overrides for short previews/demos."""
    from rgcs_desktop.services.sonic_timeline import render_session
    work = dict(session)
    if duration_s is not None:
        work["duration_s"] = float(duration_s)
        from rgcs_desktop.services.sonic_timeline import \
            standard_session_shape
        beat = _main_beat(session)
        work["segments"] = standard_session_shape(beat, float(duration_s))
    audio, stats = render_session(work)
    out_path = sonic_audio.write_wav(out_path, audio,
                                     stats["sample_rate"])
    receipt = {
        "receipt_id": f"RND-{work['session_id']}",
        "session_id": work["session_id"],
        "sample_rate": int(stats["sample_rate"]),
        "duration_s": float(work["duration_s"]),
        "peak": stats["peak"],
        "rms": stats["rms"],
        "normalized": bool(stats["normalized"]),
        "outputs": [{"path": out_path.name,
                     "sha256": sha256_file(str(out_path)),
                     "kind": "wav"}],
        "input_sha256": sha256_of_jsonable(work),
        "output_sha256": sha256_file(str(out_path)),
        "software": software_versions(),
        "generated_utc": _dt.datetime.now(_dt.timezone.utc)
                            .isoformat(timespec="seconds"),
    }
    errors = validate_instance(receipt, "render_receipt.schema.json")
    if errors:
        raise RuntimeError("render receipt failed its own schema: "
                           + "; ".join(errors))
    return receipt


def _main_beat(session: dict) -> float:
    for layer in session.get("layers") or []:
        if layer.get("beat_hz"):
            return float(layer["beat_hz"])
    segments = session.get("segments") or []
    if segments:
        return float(segments[-1].get("beat_end_hz", 4.0)) or 4.0
    return 4.0


def _main_carrier(session: dict) -> float | None:
    for layer in session.get("layers") or []:
        if layer.get("carrier_hz"):
            return float(layer["carrier_hz"])
    return None


def export_recipe_json(session: dict, out_path: Path) -> Path:
    """Canonical, deterministic session/recipe JSON with content hash."""
    body = dict(session)
    body.pop("sha256", None)
    body["sha256"] = sha256_of_jsonable(body)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json_dumps(body, indent=2, sort_keys=True),
                        encoding="utf-8")
    return out_path


def export_session_pdf(session: dict, receipt: dict,
                       out_path: Path) -> Path:
    """Session sheet per 14_TEMPLATES/SESSION_PDF_TEMPLATE.md."""
    carrier = _main_carrier(session)
    beat = _main_beat(session)
    pair_rows = [("carrier (Hz)", carrier), ("beat (Hz)", beat)]
    if carrier:
        left, right = binaural_pair(carrier, beat)
        pair_rows += [("left (Hz)", left), ("right (Hz)", right)]

    seg_rows = [[s["kind"], s["duration_s"],
                 s.get("beat_start_hz"), s.get("beat_end_hz"),
                 s.get("curve", "linear")]
                for s in session.get("segments", [])]
    layer_rows = [[la["layer_id"], la["type"], la.get("carrier_hz"),
                   la.get("beat_hz"), la.get("gain_db"),
                   la.get("pan", 0.0)]
                  for la in session.get("layers", [])]
    render_rows = [
        ("sample rate (Hz)", receipt.get("sample_rate")),
        ("duration (s)", receipt.get("duration_s")),
        ("peak", receipt.get("peak")),
        ("RMS", receipt.get("rms")),
        ("normalized", receipt.get("normalized")),
        ("WAV sha256", receipt.get("output_sha256")),
    ]
    sections = [
        ("Recipe", pdf_sheets.rows_block([
            ("session ID", session.get("session_id")),
            ("intent / claimed use", session.get("intent")),
            ("family", session.get("family")),
        ])),
        ("Carrier and beat", pdf_sheets.rows_block(pair_rows)),
        ("Segment timeline", pdf_sheets.table_block(
            ["segment", "duration (s)", "beat start (Hz)",
             "beat end (Hz)", "curve"], seg_rows)),
        ("Layers", pdf_sheets.table_block(
            ["layer", "type", "carrier (Hz)", "beat (Hz)", "gain (dB)",
             "pan"], layer_rows)),
        ("Render stats", pdf_sheets.rows_block(render_rows)),
        ("Source notes", pdf_sheets.paragraph(
            ", ".join(filter(None, session.get("source_ids", [])))
            or "none recorded")),
        ("User notes", pdf_sheets.paragraph(
            session.get("notes") or "—")),
    ]
    return pdf_sheets.render_sheet_pdf(
        title="RGCS Frequency Key Studio — Session Sheet",
        subtitle=str(session.get("title", "")),
        sections=sections,
        boundary=USER_NOTE + " Claimed uses are recorded from sources "
                 "or user intent; they are not verified outcomes.",
        out_path=Path(out_path),
        input_hash=receipt.get("input_sha256"))


def export_youtube_metadata_sheet(session: dict, out_path: Path) -> Path:
    """Title/description draft per the YouTube metadata template."""
    carrier = _main_carrier(session)
    beat = _main_beat(session)
    layers = ", ".join(la["type"] for la in session.get("layers", []))
    minutes = float(session.get("duration_s", 0)) / 60.0
    if carrier:
        left, right = binaural_pair(carrier, beat)
        title = (f"{carrier:g} Hz + {beat:g} Hz "
                 f"{session.get('intent', '').strip() or 'Session'} "
                 f"Binaural Beat | RGCS Frequency Key Studio")
        pair = f"- Left: {left:g} Hz\n- Right: {right:g} Hz\n"
    else:
        title = (f"{beat:g} Hz {session.get('intent', 'Session')} | "
                 f"RGCS Frequency Key Studio")
        pair = ""
    text = (
        f"Title:\n{title}\n\n"
        f"Description:\nRendered with RGCS Frequency Key Studio.\n\n"
        f"Recipe:\n- Carrier: {carrier:g} Hz\n- Beat: {beat:g} Hz\n"
        f"{pair}- Layers: {layers}\n- Duration: {minutes:g} min\n\n"
        f"{USER_NOTE}\n" if carrier else
        f"Title:\n{title}\n\nDescription:\nRendered with RGCS Frequency "
        f"Key Studio.\n\nRecipe:\n- Beat: {beat:g} Hz\n- Layers: "
        f"{layers}\n- Duration: {minutes:g} min\n\n{USER_NOTE}\n")
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")
    return out_path


def export_bundle(session: dict, outputs: list[Path],
                  out_zip: Path) -> Path:
    """Zip the session's export set with a manifest + checksums."""
    out_zip = Path(out_zip)
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "bundle_kind": "frequency_key_studio_session",
        "session_id": session.get("session_id"),
        "title": session.get("title"),
        "software": software_versions(),
        "files": {p.name: sha256_file(str(p)) for p in outputs
                  if Path(p).is_file()},
        "note": USER_NOTE,
        "generated_utc": _dt.datetime.now(_dt.timezone.utc)
                            .isoformat(timespec="seconds"),
    }
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in outputs:
            p = Path(p)
            if p.is_file():
                zf.write(p, p.name)
        zf.writestr("MANIFEST.json",
                    json_dumps(manifest, indent=2, sort_keys=True))
    return out_zip


def verify_bundle(out_zip: Path) -> dict:
    """Re-hash bundle members against the embedded manifest."""
    import hashlib
    import json as _json
    with zipfile.ZipFile(out_zip) as zf:
        manifest = _json.loads(zf.read("MANIFEST.json"))
        mismatched = []
        for name, recorded in manifest.get("files", {}).items():
            actual = hashlib.sha256(zf.read(name)).hexdigest()
            if actual != recorded:
                mismatched.append(name)
    return {"ok": not mismatched, "n_members": len(manifest.get("files", {})),
            "mismatched": mismatched}


# ---------------------------------------------------- v1.1 batch render

def batch_render(recipe_ids: list[str], out_dir: Path,
                 duration_s: float | None = None) -> dict:
    """Render several seed recipes in one pass. Per-recipe failures are
    recorded, never silently dropped; a batch manifest with checksums
    lands beside the renders."""
    from rgcs_desktop.services.sonic_recipes import (RecipeError,
                                                     recipe_by_id,
                                                     recipe_to_session)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for recipe_id in recipe_ids:
        try:
            recipe = recipe_by_id(recipe_id)
            session = recipe_to_session(recipe, duration_s=duration_s)
            wav = out_dir / f"{recipe_id}.wav"
            receipt = render_session_wav(session, wav,
                                         duration_s=duration_s)
            results.append({"recipe_id": recipe_id, "status": "rendered",
                            "wav": wav.name,
                            "sha256": receipt["output_sha256"],
                            "peak": receipt["peak"],
                            "rms": receipt["rms"]})
        except (RecipeError, Exception) as exc:  # noqa: BLE001
            results.append({"recipe_id": recipe_id, "status": "failed",
                            "error": str(exc)})
    manifest = {
        "batch_kind": "frequency_key_studio_batch",
        "software": software_versions(),
        "results": results,
        "generated_utc": _dt.datetime.now(_dt.timezone.utc)
                            .isoformat(timespec="seconds"),
    }
    (out_dir / "batch_manifest.json").write_text(
        json_dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest
