"""Workspace: one research project = one directory.

Layout::

    <workspace>/
        workspace.db      SQLite: metadata, object registry, jobs, exports
        sources/          imported files, stored under sha256 prefix names
        artifacts/        job outputs / derived results, content-addressed
        manifests/        experiment run manifests (JSON)
        backups/          db backup taken on every open
        reports/          generated markdown reports
        bundles/          reproducibility bundle zips

Data-safety rules implemented here:
* atomic saves — every file write goes through temp-file + os.replace;
* backup on open — the db is copied to backups/ before first use;
* schema_version row + migration hook (``_MIGRATIONS``);
* no silent destructive overwrite — writing a different payload to an
  existing object id requires ``overwrite=True``, otherwise WorkspaceError;
* deterministic artifact ids — sha256 of canonical JSON (or file bytes);
* checksums recorded for every imported file.
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import shutil
import sqlite3
import uuid
from pathlib import Path
from typing import Any, Callable, Iterable

from rgcs_core.provenance import (json_dumps, sha256_file, sha256_of_jsonable,
                                  to_jsonable)

WORKSPACE_SCHEMA_VERSION = 1

OBJECT_KINDS = ("specimen", "model", "experiment", "source", "result",
                "note", "figure")


class WorkspaceError(RuntimeError):
    pass


def _utcnow() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def atomic_write_text(path: Path, text: str) -> None:
    """Write text atomically: temp file in the same directory + os.replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS objects (
    object_id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    content_sha256 TEXT NOT NULL,
    json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS files (
    sha256 TEXT PRIMARY KEY,
    relpath TEXT NOT NULL,
    original_name TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    imported_at TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    finished_at TEXT,
    progress REAL NOT NULL DEFAULT 0.0,
    params_json TEXT NOT NULL,
    result_artifact TEXT,
    error TEXT,
    log TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS export_history (
    export_id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    path TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""

# Migration hook: index = from-version; function receives the connection and
# must bring the schema to from-version + 1.
_MIGRATIONS: dict[int, Callable[[sqlite3.Connection], None]] = {}


class Workspace:
    """Open with :meth:`create` or :meth:`open`; call :meth:`close` when done."""

    def __init__(self, root: Path, conn: sqlite3.Connection):
        self.root = Path(root)
        self._conn = conn

    # -- lifecycle -----------------------------------------------------
    @classmethod
    def create(cls, root: str | Path, name: str) -> "Workspace":
        root = Path(root)
        if (root / "workspace.db").exists():
            raise WorkspaceError(f"workspace already exists at {root}")
        for sub in ("sources", "artifacts", "manifests", "backups",
                    "reports", "bundles"):
            (root / sub).mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(root / "workspace.db")
        conn.executescript(_SCHEMA_SQL)
        with conn:
            conn.execute("INSERT INTO meta VALUES ('schema_version', ?)",
                         (str(WORKSPACE_SCHEMA_VERSION),))
            conn.execute("INSERT INTO meta VALUES ('name', ?)", (name,))
            conn.execute("INSERT INTO meta VALUES ('created_at', ?)",
                         (_utcnow(),))
        return cls(root, conn)

    @classmethod
    def open(cls, root: str | Path, backup: bool = True) -> "Workspace":
        root = Path(root)
        db = root / "workspace.db"
        if not db.exists():
            raise WorkspaceError(f"no workspace at {root}")
        # Corruption gate BEFORE the on-open backup, so a corrupt db is
        # never archived as a "good" backup (QA-D-05 / QA-D-23).
        conn = sqlite3.connect(db)
        try:
            cls._check_integrity(conn, db)
        except WorkspaceError:
            conn.close()
            raise
        if backup:
            stamp = _utcnow().replace(":", "").replace("+0000", "Z")
            dest = root / "backups" / f"workspace-{stamp}.db"
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not dest.exists():
                shutil.copy2(db, dest)
        ws = cls(root, conn)
        try:
            ws._migrate()
        except sqlite3.Error as exc:
            conn.close()
            raise WorkspaceError(
                f"workspace database at {db} is damaged ({exc}); "
                f"a backup may be restorable via "
                f"Workspace.restore_latest_backup({str(root)!r})") from exc
        return ws

    @staticmethod
    def _check_integrity(conn: sqlite3.Connection, db: Path) -> None:
        """Raise WorkspaceError if the sqlite file is corrupt/not a db
        (QA-D-05: never let a raw sqlite3.DatabaseError escape open())."""
        try:
            rows = conn.execute("PRAGMA quick_check").fetchall()
        except sqlite3.Error as exc:
            raise WorkspaceError(
                f"workspace database at {db} is corrupt or not a valid "
                f"SQLite file ({exc}); a backup may be restorable via "
                f"Workspace.restore_latest_backup") from exc
        if not rows or rows[0][0] != "ok":
            detail = "; ".join(str(r[0]) for r in rows[:3]) or "no result"
            raise WorkspaceError(
                f"workspace database at {db} failed integrity check "
                f"({detail}); a backup may be restorable via "
                f"Workspace.restore_latest_backup")

    @classmethod
    def list_backups(cls, root: str | Path) -> list[Path]:
        """Backup db files for a workspace, newest first."""
        return sorted((Path(root) / "backups").glob("workspace-*.db"),
                      reverse=True)

    @classmethod
    def restore_latest_backup(cls, root: str | Path) -> "Workspace":
        """Recover a corrupt workspace from the newest intact backup.

        The corrupt workspace.db is preserved as workspace.db.corrupt-<ts>
        (never deleted); the newest backup that passes the integrity check
        is copied into place and opened. Raises WorkspaceError when no
        intact backup exists."""
        root = Path(root)
        db = root / "workspace.db"
        candidates = cls.list_backups(root)
        if not candidates:
            raise WorkspaceError(f"no backups to restore under {root}")
        chosen: Path | None = None
        for cand in candidates:
            conn = sqlite3.connect(cand)
            try:
                cls._check_integrity(conn, cand)
                chosen = cand
                break
            except WorkspaceError:
                continue
            finally:
                conn.close()
        if chosen is None:
            raise WorkspaceError(
                f"no intact backup found under {root / 'backups'} "
                f"({len(candidates)} candidates, all corrupt)")
        if db.exists():
            stamp = _utcnow().replace(":", "").replace("+0000", "Z")
            os.replace(db, db.with_name(f"workspace.db.corrupt-{stamp}"))
        shutil.copy2(chosen, db)
        return cls.open(root, backup=False)

    def _migrate(self) -> None:
        row = self._conn.execute(
            "SELECT value FROM meta WHERE key='schema_version'").fetchone()
        if row is None:
            raise WorkspaceError("workspace db has no schema_version row")
        version = int(row[0])
        if version > WORKSPACE_SCHEMA_VERSION:
            raise WorkspaceError(
                f"workspace schema {version} is newer than this build "
                f"({WORKSPACE_SCHEMA_VERSION}); refusing to open")
        while version < WORKSPACE_SCHEMA_VERSION:
            step = _MIGRATIONS.get(version)
            if step is None:
                raise WorkspaceError(f"no migration from schema {version}")
            with self._conn:
                step(self._conn)
                version += 1
                self._conn.execute(
                    "UPDATE meta SET value=? WHERE key='schema_version'",
                    (str(version),))

    def close(self) -> None:
        self._conn.close()

    # -- metadata ------------------------------------------------------
    @property
    def name(self) -> str:
        row = self._conn.execute(
            "SELECT value FROM meta WHERE key='name'").fetchone()
        return row[0] if row else "(unnamed)"

    @property
    def schema_version(self) -> int:
        row = self._conn.execute(
            "SELECT value FROM meta WHERE key='schema_version'").fetchone()
        return int(row[0])

    # -- object registry -------------------------------------------------
    def put_object(self, kind: str, name: str, payload: dict[str, Any],
                   object_id: str | None = None,
                   overwrite: bool = False) -> str:
        if kind not in OBJECT_KINDS:
            raise WorkspaceError(f"unknown object kind {kind!r}")
        payload = to_jsonable(payload)
        sha = sha256_of_jsonable(payload)
        object_id = object_id or f"{kind}-{sha[:12]}"
        existing = self._conn.execute(
            "SELECT content_sha256 FROM objects WHERE object_id=?",
            (object_id,)).fetchone()
        if existing is not None:
            if existing[0] == sha:
                return object_id  # identical content: no-op, not an overwrite
            if not overwrite:
                raise WorkspaceError(
                    f"object {object_id} exists with different content; "
                    f"pass overwrite=True to replace (no silent overwrite)")
        now = _utcnow()
        with self._conn:
            self._conn.execute(
                "INSERT INTO objects VALUES (?,?,?,?,?,?,?) "
                "ON CONFLICT(object_id) DO UPDATE SET name=excluded.name, "
                "updated_at=excluded.updated_at, "
                "content_sha256=excluded.content_sha256, json=excluded.json",
                (object_id, kind, name, now, now, sha, json_dumps(payload)))
        return object_id

    def get_object(self, object_id: str) -> dict[str, Any]:
        row = self._conn.execute(
            "SELECT kind, name, created_at, updated_at, content_sha256, json "
            "FROM objects WHERE object_id=?", (object_id,)).fetchone()
        if row is None:
            raise WorkspaceError(f"no object {object_id}")
        return {"object_id": object_id, "kind": row[0], "name": row[1],
                "created_at": row[2], "updated_at": row[3],
                "content_sha256": row[4], "payload": json.loads(row[5])}

    def list_objects(self, kind: str | None = None) -> list[dict[str, Any]]:
        q = ("SELECT object_id, kind, name, created_at, content_sha256 "
             "FROM objects")
        args: tuple = ()
        if kind is not None:
            q += " WHERE kind=?"
            args = (kind,)
        q += " ORDER BY created_at, object_id"
        return [{"object_id": r[0], "kind": r[1], "name": r[2],
                 "created_at": r[3], "content_sha256": r[4]}
                for r in self._conn.execute(q, args)]

    # -- imported files (sources) ----------------------------------------
    def import_file(self, src: str | Path, note: str = "") -> dict[str, Any]:
        """Copy a file into sources/ under a checksum name; record sha256."""
        src = Path(src)
        sha = sha256_file(str(src))
        rel = f"sources/{sha[:2]}/{sha}{src.suffix}"
        dest = self.root / rel
        if not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            tmp = dest.with_name(dest.name + f".{uuid.uuid4().hex}.tmp")
            shutil.copy2(src, tmp)
            os.replace(tmp, dest)
        with self._conn:
            self._conn.execute(
                "INSERT OR IGNORE INTO files VALUES (?,?,?,?,?,?)",
                (sha, rel, src.name, src.stat().st_size, _utcnow(), note))
        return {"sha256": sha, "relpath": rel, "original_name": src.name}

    def list_files(self) -> list[dict[str, Any]]:
        return [{"sha256": r[0], "relpath": r[1], "original_name": r[2],
                 "size_bytes": r[3], "imported_at": r[4], "note": r[5]}
                for r in self._conn.execute(
                    "SELECT * FROM files ORDER BY imported_at")]

    # -- artifacts (content-addressed, deterministic ids) ------------------
    def write_artifact(self, payload: Any, kind: str = "result",
                       suffix: str = ".json") -> dict[str, str]:
        """Write a JSON artifact; the id is the sha256 of its canonical JSON
        (deterministic: same content -> same id -> same path)."""
        payload = to_jsonable(payload)
        sha = sha256_of_jsonable(payload)
        artifact_id = f"{kind}-{sha[:16]}"
        rel = f"artifacts/{artifact_id}{suffix}"
        path = self.root / rel
        if not path.exists():  # identical content already stored
            atomic_write_text(path, json_dumps(payload, indent=2))
        return {"artifact_id": artifact_id, "relpath": rel, "sha256": sha}

    def read_artifact(self, artifact_id: str) -> Any:
        matches = list((self.root / "artifacts").glob(f"{artifact_id}*"))
        if not matches:
            raise WorkspaceError(f"no artifact {artifact_id}")
        return json.loads(matches[0].read_text())

    def list_artifacts(self) -> list[dict[str, Any]]:
        out = []
        adir = self.root / "artifacts"
        for p in sorted(adir.glob("*")) if adir.exists() else []:
            if p.name.startswith("."):
                continue
            out.append({"artifact_id": p.stem, "relpath": f"artifacts/{p.name}",
                        "size_bytes": p.stat().st_size})
        return out

    # -- manifests --------------------------------------------------------
    def write_manifest(self, manifest: dict[str, Any],
                       overwrite: bool = False) -> Path:
        run_id = manifest.get("run_id", "RUN-UNNAMED")
        path = self.root / "manifests" / f"{run_id}.json"
        if path.exists() and not overwrite:
            existing = json.loads(path.read_text())
            if sha256_of_jsonable(to_jsonable(existing)) != \
                    sha256_of_jsonable(to_jsonable(manifest)):
                raise WorkspaceError(
                    f"manifest {run_id} exists with different content; "
                    f"refusing silent overwrite")
        atomic_write_text(path, json_dumps(to_jsonable(manifest), indent=2))
        return path

    # -- jobs (persistence; live state is in jobs.manager) -----------------
    def record_job(self, job_id: str, name: str, status: str,
                   params: dict[str, Any], progress: float = 0.0,
                   result_artifact: str | None = None,
                   error: str | None = None, log: str = "") -> None:
        finished = _utcnow() if status in ("succeeded", "failed",
                                           "cancelled") else None
        with self._conn:
            self._conn.execute(
                "INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?,?) "
                "ON CONFLICT(job_id) DO UPDATE SET status=excluded.status, "
                "finished_at=excluded.finished_at, progress=excluded.progress,"
                " result_artifact=excluded.result_artifact, "
                "error=excluded.error, log=excluded.log",
                (job_id, name, status, _utcnow(), finished, progress,
                 json_dumps(to_jsonable(params)), result_artifact, error, log))

    def list_jobs(self) -> list[dict[str, Any]]:
        return [{"job_id": r[0], "name": r[1], "status": r[2],
                 "created_at": r[3], "finished_at": r[4], "progress": r[5],
                 "result_artifact": r[7], "error": r[8]}
                for r in self._conn.execute(
                    "SELECT * FROM jobs ORDER BY created_at")]

    # -- export history -----------------------------------------------------
    def record_export(self, kind: str, path: str | Path, sha256: str) -> str:
        export_id = f"exp-{uuid.uuid4().hex[:12]}"
        with self._conn:
            self._conn.execute(
                "INSERT INTO export_history VALUES (?,?,?,?,?)",
                (export_id, kind, str(path), sha256, _utcnow()))
        return export_id

    def list_exports(self) -> list[dict[str, Any]]:
        return [{"export_id": r[0], "kind": r[1], "path": r[2],
                 "sha256": r[3], "created_at": r[4]}
                for r in self._conn.execute(
                    "SELECT * FROM export_history ORDER BY created_at")]
