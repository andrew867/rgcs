"""Frequency Studio session library: file-backed CRUD over the
workspace ``library/frequency_sessions`` tree.

Layout inside a workspace:

    library/frequency_sessions/factory/...   installed factory content
                                             (never written here)
    library/frequency_sessions/user/         user sessions (saves land
                                             here)
    library/trash/                           deleted sessions (delete is
                                             a move, never a hard
                                             delete)

Every load runs both gates — the frequency_session JSON schema and the
timeline structural check — so a session that opens is a session that
renders. Saves are atomic and preserve the session's schema_version.
No Qt imports here.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

from rgcs_desktop.services.design_studio import new_object_id
from rgcs_desktop.services.schemas import validate_instance
from rgcs_desktop.services.sonic_timeline import (TimelineError,
                                                  validate_session)

SESSIONS_RELPATH = "library/frequency_sessions"
USER_RELPATH = SESSIONS_RELPATH + "/user"
FACTORY_RELPATH = SESSIONS_RELPATH + "/factory"
TRASH_RELPATH = "library/trash"
AUTOSAVE_RELPATH = "library/autosave"


class SessionStoreError(RuntimeError):
    """A session file failed a gate or a CRUD operation is invalid."""


def load_session_file(path: str | Path) -> dict:
    """Read + gate a session file (shared by the UI and the CLI).

    Runs the JSON parse, the frequency_session schema (incl. the
    schema-major gate), and the timeline structural check. Raises
    SessionStoreError with a stated reason — never a raw traceback.
    """
    path = Path(path)
    try:
        body = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise SessionStoreError(f"cannot read session file: {exc}") \
            from exc
    except json.JSONDecodeError as exc:
        raise SessionStoreError(f"not valid JSON: {exc}") from exc
    if not isinstance(body, dict):
        raise SessionStoreError("session file must contain a JSON object")
    errors = validate_instance(body, "frequency_session.schema.json")
    if errors:
        raise SessionStoreError(
            "session file invalid: " + "; ".join(errors[:8]))
    try:
        validate_session(body)
    except TimelineError as exc:
        raise SessionStoreError(f"session timeline invalid: {exc}") \
            from exc
    return body


def _safe_stem(text: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", text).strip("._-")
    return stem or "session"


class SessionStore:
    """CRUD over one workspace's session library."""

    def __init__(self, workspace_root: str | Path):
        self.root = Path(workspace_root)

    # ------------------------------------------------------------ dirs
    @property
    def user_dir(self) -> Path:
        return self.root / USER_RELPATH

    @property
    def factory_dir(self) -> Path:
        return self.root / FACTORY_RELPATH

    @property
    def trash_dir(self) -> Path:
        return self.root / TRASH_RELPATH

    # --------------------------------------------------------- listing
    def list_sessions(self) -> list[dict]:
        """Factory + user sessions with search/sort metadata."""
        favorites = self.favorites()
        rows: list[dict] = []
        for origin, base in (("factory", self.factory_dir),
                             ("user", self.user_dir)):
            if not base.is_dir():
                continue
            for path in sorted(base.rglob("*.json")):
                try:
                    body = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue
                if not isinstance(body, dict) or "session_id" not in body:
                    continue
                meta = body.get("meta") or {}
                carrier = beat = None
                for layer in body.get("layers", []):
                    if layer.get("type") in ("binaural", "monaural",
                                             "isochronic"):
                        carrier = layer.get("carrier_hz")
                        beat = layer.get("beat_hz",
                                         layer.get("pulse_hz"))
                        break
                sid = body.get("session_id", "")
                row_origin = origin
                if origin == "user" and meta.get("imported"):
                    row_origin = "imported"
                rows.append({
                    "path": str(path),
                    "origin": row_origin,
                    "session_id": sid,
                    "title": body.get("title", path.stem),
                    "family": body.get("family", ""),
                    "category": (meta.get("tags")
                                 or meta.get("source_name")
                                 or body.get("family", "")),
                    "tags": " ".join(
                        str(t) for t in (body.get("source_ids") or [])),
                    "carrier_hz": carrier,
                    "beat_hz": beat,
                    "duration_s": body.get("duration_s"),
                    "n_layers": len(body.get("layers", [])),
                    "favorite": sid in favorites,
                    "mtime": path.stat().st_mtime,
                })
        return rows

    # ------------------------------------------------ favorites (v8.5.3)
    @property
    def _favorites_path(self) -> Path:
        return self.root / "library" / "favorites.json"

    def favorites(self) -> set[str]:
        try:
            body = json.loads(self._favorites_path
                              .read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return set()
        return set(body.get("session_ids", []))

    def toggle_favorite(self, session_id: str) -> bool:
        """Flip favorite state; returns the new state."""
        favs = self.favorites()
        state = session_id not in favs
        if state:
            favs.add(session_id)
        else:
            favs.discard(session_id)
        self._favorites_path.parent.mkdir(parents=True, exist_ok=True)
        self._favorites_path.write_text(
            json.dumps({"schema_version": "1.0.0",
                        "session_ids": sorted(favs)},
                       indent=2) + "\n", encoding="utf-8")
        return state

    # ------------------------------------------------------------ CRUD
    def open(self, path: str | Path) -> dict:
        return load_session_file(path)

    def save(self, session: dict, path: str | Path | None = None) -> Path:
        """Validate + write. Default target is the user library."""
        errors = validate_instance(session,
                                   "frequency_session.schema.json")
        if errors:
            raise SessionStoreError(
                "refusing to save an invalid session: "
                + "; ".join(errors[:8]))
        try:
            validate_session(session)
        except TimelineError as exc:
            raise SessionStoreError(
                f"refusing to save: timeline invalid: {exc}") from exc
        if path is None:
            sid = session.get("session_id") or new_object_id("SES")
            path = self.user_dir / f"{_safe_stem(sid)}.session.json"
        path = Path(path)
        try:
            in_factory = path.resolve().is_relative_to(
                self.factory_dir.resolve())
        except OSError:
            in_factory = False
        if in_factory:
            raise SessionStoreError(
                "factory sessions are read-only — use Save As to make "
                "your own copy in the user library")
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(session, indent=2, sort_keys=True)
                       + "\n", encoding="utf-8")
        tmp.replace(path)
        return path

    def save_as(self, session: dict, title: str | None = None) -> Path:
        """Save under a new file named for the title (user library)."""
        work = dict(session)
        if title:
            work["title"] = title
        name = _safe_stem(work.get("title")
                          or work.get("session_id")
                          or "session")
        target = self.user_dir / f"{name}.session.json"
        n = 2
        while target.exists():
            target = self.user_dir / f"{name}_{n}.session.json"
            n += 1
        return self.save(work, target)

    def duplicate(self, path: str | Path) -> Path:
        """Copy a session (factory or user) with a fresh session ID."""
        body = self.open(path)
        body["session_id"] = new_object_id("SES")
        body["title"] = f"{body.get('title', 'session')} (copy)"
        return self.save_as(body)

    def delete(self, path: str | Path) -> Path:
        """Move a session to the workspace trash (never hard-delete)."""
        path = Path(path)
        if not path.is_file():
            raise SessionStoreError(f"no session file at {path}")
        self.trash_dir.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        target = self.trash_dir / f"{stamp}_{path.name}"
        n = 2
        while target.exists():
            target = self.trash_dir / f"{stamp}_{n}_{path.name}"
            n += 1
        path.replace(target)
        return target

    # ------------------------------------------------- autosave (v8.5.3)
    @property
    def autosave_dir(self) -> Path:
        return self.root / AUTOSAVE_RELPATH

    def autosave(self, session: dict,
                 source_path: str | Path | None = None) -> Path:
        """Write a crash-recovery copy of an unsaved session.

        No validation gate: a mid-edit session must still be
        recoverable. The original file path (if any) rides along so
        recovery can offer to restore it in place.
        """
        sid = _safe_stem(session.get("session_id") or "session")
        self.autosave_dir.mkdir(parents=True, exist_ok=True)
        target = self.autosave_dir / f"{sid}.autosave.json"
        body = {"autosave_kind": "rgcs.session_autosave/v1",
                "source_path": str(source_path) if source_path else None,
                "session": session}
        tmp = target.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n",
                       encoding="utf-8")
        tmp.replace(target)
        return target

    def list_autosaves(self) -> list[dict]:
        """Recovery candidates, newest first: {path, session, source_path}."""
        if not self.autosave_dir.is_dir():
            return []
        out = []
        for path in sorted(self.autosave_dir.glob("*.autosave.json"),
                           key=lambda p: p.stat().st_mtime,
                           reverse=True):
            try:
                body = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            session = body.get("session")
            if isinstance(session, dict):
                out.append({"path": str(path), "session": session,
                            "source_path": body.get("source_path")})
        return out

    def clear_autosave(self, session_id: str) -> None:
        target = self.autosave_dir / \
            f"{_safe_stem(session_id)}.autosave.json"
        if target.exists():
            target.unlink()

    def import_session(self, src: str | Path) -> Path:
        """Copy an external session file into the user library.

        The file passes both gates first. If its session_id collides
        with an existing user session, a fresh ID is minted.
        """
        body = load_session_file(src)
        sid = body.get("session_id", "")
        existing = {row["session_id"] for row in self.list_sessions()
                    if row["origin"] in ("user", "imported")}
        if sid in existing:
            body["session_id"] = new_object_id("SES")
        body.setdefault("meta", {})["imported"] = True
        return self.save_as(body, body.get("title"))
