"""Frequency Key Studio — Session Library page (v8.5.2).

Lists the workspace session library (factory + user) with origin
badges; open loads a session into the editor, duplicate copies it into
the user library with a fresh ID, delete moves it to the workspace
trash. Factory files stay read-only — editing one goes through
duplicate."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (QHBoxLayout, QLabel, QLineEdit,
                               QPushButton, QTableWidget,
                               QTableWidgetItem, QVBoxLayout, QWidget)

COLUMNS = ["title", "origin", "duration (min)", "layers", "session id"]


class SessionLibraryPage(QWidget):
    def __init__(self, context, status_cb, open_cb, parent=None):
        super().__init__(parent)
        self.context = context
        self._status_cb = status_cb
        self._open_cb = open_cb
        self._rows: list[dict] = []

        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText(
            "filter by title / tag / session id")
        self.search.textChanged.connect(self.refresh)
        top.addWidget(self.search, stretch=1)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        top.addWidget(refresh_btn)
        layout.addLayout(top)

        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self.open_selected)
        layout.addWidget(self.table, stretch=1)

        row = QHBoxLayout()
        open_btn = QPushButton("Open")
        open_btn.clicked.connect(self.open_selected)
        row.addWidget(open_btn)
        dup_btn = QPushButton("Duplicate to my library")
        dup_btn.clicked.connect(self.duplicate_selected)
        row.addWidget(dup_btn)
        delete_btn = QPushButton("Delete (to workspace trash)")
        delete_btn.clicked.connect(self.delete_selected)
        row.addWidget(delete_btn)
        row.addStretch(1)
        layout.addLayout(row)

        self.status = QLabel(
            "Factory sessions are source-language records converted "
            "for audio use — claimed uses are recorded, not endorsed. "
            "Factory files are read-only; Duplicate makes an editable "
            "copy.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.refresh()

    # ------------------------------------------------------------------
    def _store(self):
        from rgcs_desktop.services.session_store import SessionStore
        ws = getattr(self.context, "workspace", None)
        root = Path(ws.root) if ws is not None else Path.cwd()
        return SessionStore(root)

    def refresh(self, *_a) -> None:
        query = self.search.text().strip().lower()
        try:
            rows = self._store().list_sessions()
        except Exception:  # noqa: BLE001 (no workspace / unreadable)
            rows = []
        if query:
            rows = [r for r in rows
                    if query in r["title"].lower()
                    or query in r["session_id"].lower()]
        self._rows = rows
        self.table.setRowCount(0)
        for r in rows:
            i = self.table.rowCount()
            self.table.insertRow(i)
            duration = (r.get("duration_s") or 0) / 60.0
            for c, value in enumerate((r["title"], r["origin"],
                                       f"{duration:.1f}",
                                       str(r["n_layers"]),
                                       r["session_id"])):
                self.table.setItem(i, c, QTableWidgetItem(value))

    def selected_row(self) -> dict | None:
        indexes = self.table.selectedIndexes()
        if not indexes:
            return None
        return self._rows[indexes[0].row()]

    def open_selected(self, *_a) -> bool:
        row = self.selected_row()
        if row is None:
            self._status_cb("select a session first")
            return False
        return self._open_cb(row["path"])

    def duplicate_selected(self, *_a):
        from rgcs_desktop.services.session_store import SessionStoreError
        row = self.selected_row()
        if row is None:
            self._status_cb("select a session first")
            return None
        try:
            path = self._store().duplicate(row["path"])
        except SessionStoreError as exc:
            self._status_cb(f"duplicate refused: {exc}")
            return None
        self._status_cb(f"duplicated -> {path.name}")
        self.refresh()
        return path

    def delete_selected(self, *_a):
        from rgcs_desktop.services.session_store import SessionStoreError
        row = self.selected_row()
        if row is None:
            self._status_cb("select a session first")
            return None
        if row["origin"] == "factory":
            self._status_cb(
                "factory sessions are not deleted — they would be "
                "restored by repair; duplicate + edit instead")
            return None
        try:
            trashed = self._store().delete(row["path"])
        except SessionStoreError as exc:
            self._status_cb(f"delete refused: {exc}")
            return None
        self._status_cb(f"moved to workspace trash: {trashed.name}")
        self.refresh()
        return trashed
