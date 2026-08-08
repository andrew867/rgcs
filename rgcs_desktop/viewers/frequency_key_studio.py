"""Frequency Key Studio (RGCS Sonic Lab): the Design Studio panel.

One top-level tab hosting the studio's pages (New Session, Recipe
Library, Web Corpus) as internal sub-tabs — the same workspace, jobs
dock, and inspector as every other Design Studio panel. Timeline editor
and layer mixer are v1.1 features (PRD) and deliberately absent."""
from __future__ import annotations

from PySide6.QtWidgets import QLabel, QTabWidget, QVBoxLayout

from rgcs_desktop.services.sonic_recipes import (USER_NOTE, load_recipes)
from rgcs_desktop.viewers.base import Panel
from rgcs_desktop.viewers.sonic_new_session import NewSessionPage
from rgcs_desktop.viewers.sonic_recipe_library import RecipeLibraryPage
from rgcs_desktop.viewers.sonic_timeline_editor import TimelineEditorPage
from rgcs_desktop.viewers.sonic_web_corpus import WebCorpusPage


class FrequencyKeyStudioPanel(Panel):
    TITLE = "Frequency Key Studio"

    def __init__(self, context, parent=None):
        super().__init__(context, parent)
        layout = QVBoxLayout(self)
        heading = QLabel("RGCS Frequency Key Studio — Sonic Lab")
        heading.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(heading)

        self.pages = QTabWidget()
        self.timeline_editor = TimelineEditorPage(context, self._log)
        self.new_session = NewSessionPage(
            context, self._log,
            timeline_provider=self.timeline_editor.custom_segments)
        self.recipe_library = RecipeLibraryPage(context, self._log)
        from rgcs_desktop.viewers.sonic_session_library import \
            SessionLibraryPage
        self.session_library = SessionLibraryPage(context, self._log,
                                                  self.open_session)
        self.web_corpus = WebCorpusPage(context, self._log)
        self.pages.addTab(self.new_session, "New Session")
        self.pages.addTab(self.timeline_editor, "Timeline Editor")
        self.pages.addTab(self.recipe_library, "Recipe Library")
        self.pages.addTab(self.session_library, "Session Library")
        self.pages.addTab(self.web_corpus, "Web Corpus")
        self.pages.currentChanged.connect(
            lambda *_: self.inspector_changed.emit())
        layout.addWidget(self.pages, stretch=1)

        # v8.5.3: crash-recovery autosave + segment edits join the
        # dirty/undo tracking
        self.new_session.autosave_cb = self._autosave_current
        self.timeline_editor.table.cellChanged.connect(
            lambda *_: self.new_session._mark_dirty())
        self.timeline_editor.enabled.toggled.connect(
            lambda *_: self.new_session._mark_dirty())

    def _log(self, message: str) -> None:
        self.status_message.emit(f"sonic: {message}")
        self.inspector_changed.emit()

    # ---------------------------------------- v8.5.3 autosave/recovery
    def _autosave_current(self) -> None:
        session = self.new_session.current_session()
        if session is not None:
            self._store().autosave(session,
                                   self.new_session.session_path)

    def autosave_candidates(self) -> list[dict]:
        try:
            return self._store().list_autosaves()
        except Exception:  # noqa: BLE001 (no workspace)
            return []

    def recover_autosave(self, path=None) -> bool:
        """Load the newest (or given) autosaved session into the editor
        as an unsaved session."""
        candidates = self.autosave_candidates()
        if path is not None:
            candidates = [c for c in candidates
                          if c["path"] == str(path)]
        if not candidates:
            self._log("no autosaved session to recover")
            return False
        if not self._resolve_dirty():
            return False
        entry = candidates[0]
        source = entry.get("source_path")
        self.new_session.apply_session(entry["session"],
                                       source if source else None)
        if entry["session"].get("segments"):
            self.timeline_editor.load_segments(
                entry["session"]["segments"])
        self.new_session._dirty = True   # recovered = still unsaved
        self._log(f"recovered autosaved session "
                  f"{entry['session'].get('title', '')} — save to keep")
        self.inspector_changed.emit()
        return True

    def _clear_current_autosave(self) -> None:
        session = self.new_session.current_session() or {}
        sid = session.get("session_id")
        if sid:
            try:
                self._store().clear_autosave(sid)
            except Exception:  # noqa: BLE001
                pass

    def refresh(self) -> None:
        """Workspace changed: re-list the session library."""
        self.session_library.refresh()

    def teardown(self) -> None:
        """Stop live playback when the workspace closes/switches."""
        self.new_session.teardown()

    # -------------------------------------- v8.5.2 session CRUD actions
    # dirty_prompt is injectable for tests; the default asks the user.
    def _default_dirty_prompt(self) -> str:
        from PySide6.QtWidgets import QMessageBox
        session = self.new_session.current_session() or {}
        box = QMessageBox(self)
        box.setWindowTitle("Unsaved changes")
        box.setText(f"Save changes to "
                    f"{session.get('title', 'this session')}?")
        box.setStandardButtons(QMessageBox.StandardButton.Save
                               | QMessageBox.StandardButton.Discard
                               | QMessageBox.StandardButton.Cancel)
        answer = box.exec()
        if answer == QMessageBox.StandardButton.Save:
            return "save"
        if answer == QMessageBox.StandardButton.Discard:
            return "discard"
        return "cancel"

    dirty_prompt = None   # tests inject a callable returning save/…

    def _resolve_dirty(self) -> bool:
        """True when it is OK to proceed (saved or discarded)."""
        if not self.new_session.is_dirty:
            return True
        answer = (self.dirty_prompt or self._default_dirty_prompt)()
        if answer == "save":
            return self.save_session() is not None
        return answer == "discard"

    def _store(self):
        from pathlib import Path

        from rgcs_desktop.services.session_store import SessionStore
        ws = getattr(self.context, "workspace", None)
        root = Path(ws.root) if ws is not None else Path.cwd()
        return SessionStore(root)

    def new_session_action(self) -> bool:
        if not self._resolve_dirty():
            return False
        self.new_session.reset_identity()
        self._log("new session (unsaved)")
        return True

    def open_session(self, path=None) -> bool:
        """Open a session file into the editor (both gates)."""
        from rgcs_desktop.services.session_store import (
            SessionStoreError, load_session_file)
        if path is None:
            from PySide6.QtWidgets import QFileDialog
            start = str(self._store().user_dir)
            path, _ = QFileDialog.getOpenFileName(
                self, "Open session", start, "Session JSON (*.json)")
            if not path:
                return False
        if not self._resolve_dirty():
            return False
        try:
            session = load_session_file(path)
        except SessionStoreError as exc:
            self._log(f"open refused: {exc}")
            return False
        self.new_session.apply_session(session, path)
        if session.get("segments"):
            self.timeline_editor.load_segments(session["segments"])
        self.context.settings.add_recent_session(str(path))
        self._log(f"opened {session.get('title', path)}")
        self.inspector_changed.emit()
        return True

    def save_session(self):
        from rgcs_desktop.services.session_store import SessionStoreError
        session = self.new_session.current_session()
        if session is None:
            self._log("nothing to save")
            return None
        store = self._store()
        try:
            path = store.save(session, self.new_session.session_path)
        except SessionStoreError as exc:
            self._log(f"save refused: {exc}")
            return None
        self.new_session.mark_saved(path)
        self._clear_current_autosave()
        self.context.settings.add_recent_session(str(path))
        self._log(f"saved {path.name}")
        self.inspector_changed.emit()
        return path

    def save_session_as(self, title: str | None = None):
        from rgcs_desktop.services.session_store import SessionStoreError
        if title is None:
            from PySide6.QtWidgets import QInputDialog
            current = self.new_session.current_session() or {}
            title, ok = QInputDialog.getText(
                self, "Save session as", "Title:",
                text=current.get("title", ""))
            if not ok or not title:
                return None
        self.new_session.set_title(title)
        session = self.new_session.current_session()
        if session is None:
            return None
        try:
            path = self._store().save_as(session, title)
        except SessionStoreError as exc:
            self._log(f"save-as refused: {exc}")
            return None
        self.new_session.mark_saved(path)
        self._clear_current_autosave()
        self.context.settings.add_recent_session(str(path))
        self._log(f"saved as {path.name}")
        self.inspector_changed.emit()
        return path

    def close_session(self) -> bool:
        if not self._resolve_dirty():
            return False
        self._clear_current_autosave()   # saved or deliberately discarded
        self.new_session.reset_identity()
        self.new_session._dirty = False   # closed, nothing pending
        self._log("session closed")
        self.inspector_changed.emit()
        return True

    def duplicate_session(self):
        from rgcs_desktop.services.session_store import SessionStoreError
        source = self.new_session.session_path
        try:
            if source is not None:
                path = self._store().duplicate(source)
            else:
                session = self.new_session.current_session()
                if session is None:
                    return None
                copy = dict(session)
                from rgcs_desktop.services.design_studio import \
                    new_object_id
                copy["session_id"] = new_object_id("SES")
                copy["title"] = f"{copy.get('title', 'session')} (copy)"
                path = self._store().save_as(copy)
        except SessionStoreError as exc:
            self._log(f"duplicate refused: {exc}")
            return None
        self._log(f"duplicated -> {path.name}")
        self.inspector_changed.emit()
        return path

    def delete_session(self, path=None):
        """Move a session file to the workspace trash."""
        from rgcs_desktop.services.session_store import SessionStoreError
        target = path or self.new_session.session_path
        if target is None:
            self._log("no saved session to delete")
            return None
        try:
            trashed = self._store().delete(target)
        except SessionStoreError as exc:
            self._log(f"delete refused: {exc}")
            return None
        if path is None:
            self.new_session.reset_identity()
            self.new_session._dirty = False
        self._log(f"moved to workspace trash: {trashed.name}")
        self.inspector_changed.emit()
        return trashed

    def import_session(self, src=None) -> bool:
        from rgcs_desktop.services.session_store import SessionStoreError
        if src is None:
            from PySide6.QtWidgets import QFileDialog
            src, _ = QFileDialog.getOpenFileName(
                self, "Import session", "", "Session JSON (*.json)")
            if not src:
                return False
        try:
            path = self._store().import_session(src)
        except SessionStoreError as exc:
            self._log(f"import refused: {exc}")
            return False
        self._log(f"imported into library: {path.name}")
        return self.open_session(path)

    def inspector_info(self):
        session = self.new_session.current_session() or {}
        exports = self.new_session.last_exports
        return {"properties": {
                    "seed recipes": len(load_recipes()),
                    "current session": session.get("session_id", "—"),
                    "session file": str(self.new_session.session_path
                                        or "unsaved"),
                    "unsaved changes": self.new_session.is_dirty,
                    "session type": session.get("family", "—"),
                    "duration (min)":
                        (session.get("duration_s", 0) or 0) / 60.0,
                    "last render": str(exports.get("wav", "—")),
                },
                "classification": "Model output (rendered audio recipe)",
                "units": "Hz / s / dB",
                "provenance": USER_NOTE + " Claimed uses are recorded "
                              "from sources, not endorsed."}
