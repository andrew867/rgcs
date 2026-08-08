"""Frequency Key Studio — Session Library page (v8.5.2, filters v8.5.3).

Lists the workspace session library (factory + user + imported) with
origin badges, favorites, search (title / category / tags / session id
/ frequency), origin filters, and sorting. Open loads a session into
the editor, duplicate copies it into the user library with a fresh ID,
delete moves it to the workspace trash. Factory files stay read-only —
editing one goes through duplicate."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QLineEdit,
                               QPushButton, QTableWidget,
                               QTableWidgetItem, QVBoxLayout, QWidget)

COLUMNS = ["★", "title", "origin", "carrier (Hz)", "beat (Hz)",
           "duration (min)", "category", "session id"]

FILTERS = ("All", "Factory", "User", "Imported", "Recent", "Favorite")
SORTS = ("Name", "Last opened", "Category", "Duration")


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
            "search title / category / tags / session id / frequency "
            "(e.g. 7.83)")
        self.search.textChanged.connect(self.refresh)
        top.addWidget(self.search, stretch=1)
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(FILTERS)
        self.filter_combo.currentIndexChanged.connect(self.refresh)
        top.addWidget(self.filter_combo)
        self.sort_combo = QComboBox()
        for s in SORTS:
            self.sort_combo.addItem(f"Sort: {s}", s)
        self.sort_combo.currentIndexChanged.connect(self.refresh)
        top.addWidget(self.sort_combo)
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
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table, stretch=1)

        row = QHBoxLayout()
        open_btn = QPushButton("Open")
        open_btn.clicked.connect(self.open_selected)
        row.addWidget(open_btn)
        fav_btn = QPushButton("Toggle favorite")
        fav_btn.clicked.connect(self.toggle_favorite_selected)
        row.addWidget(fav_btn)
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

    def _matches(self, row: dict, query: str) -> bool:
        if not query:
            return True
        haystack = " ".join((row["title"], row["category"], row["tags"],
                             row["session_id"],
                             row["family"])).lower()
        if query in haystack:
            return True
        try:
            hz = float(query)
        except ValueError:
            return False
        for value in (row.get("carrier_hz"), row.get("beat_hz")):
            if value is not None and abs(float(value) - hz) < 0.51:
                return True
        return False

    def _passes_filter(self, row: dict, mode: str) -> bool:
        if mode == "All":
            return True
        if mode in ("Factory", "User", "Imported"):
            return row["origin"] == mode.lower()
        if mode == "Favorite":
            return row["favorite"]
        if mode == "Recent":
            recent = set(self.context.settings.recent_sessions)
            return row["path"] in recent
        return True

    def _sort_rows(self, rows: list[dict], mode: str) -> list[dict]:
        if mode == "Name":
            return sorted(rows, key=lambda r: r["title"].lower())
        if mode == "Category":
            return sorted(rows, key=lambda r: (r["category"].lower(),
                                               r["title"].lower()))
        if mode == "Duration":
            return sorted(rows, key=lambda r: r.get("duration_s") or 0)
        if mode == "Last opened":
            recent = self.context.settings.recent_sessions
            order = {p: i for i, p in enumerate(recent)}
            return sorted(rows, key=lambda r: (
                order.get(r["path"], len(order)),
                -(r.get("mtime") or 0)))
        return rows

    def refresh(self, *_a) -> None:
        query = self.search.text().strip().lower()
        try:
            rows = self._store().list_sessions()
        except Exception:  # noqa: BLE001 (no workspace / unreadable)
            rows = []
        mode = self.filter_combo.currentText() or "All"
        rows = [r for r in rows
                if self._matches(r, query)
                and self._passes_filter(r, mode)]
        rows = self._sort_rows(rows, self.sort_combo.currentData()
                               or "Name")
        self._rows = rows
        self.table.setRowCount(0)
        for r in rows:
            i = self.table.rowCount()
            self.table.insertRow(i)
            duration = (r.get("duration_s") or 0) / 60.0
            values = ("★" if r["favorite"] else "",
                      r["title"], r["origin"],
                      f"{r['carrier_hz']:g}" if r.get("carrier_hz")
                      else "—",
                      f"{r['beat_hz']:g}" if r.get("beat_hz") else "—",
                      f"{duration:.1f}", r["category"], r["session_id"])
            for c, value in enumerate(values):
                self.table.setItem(i, c, QTableWidgetItem(value))
        self.table.resizeColumnsToContents()

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

    def toggle_favorite_selected(self, *_a):
        row = self.selected_row()
        if row is None:
            self._status_cb("select a session first")
            return None
        state = self._store().toggle_favorite(row["session_id"])
        self._status_cb(
            f"{row['title']}: "
            f"{'added to' if state else 'removed from'} favorites")
        self.refresh()
        return state

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
