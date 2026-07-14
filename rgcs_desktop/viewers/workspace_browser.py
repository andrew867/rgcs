"""Workspace browser: all registered objects, files and export history."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QTableWidget,
                               QTableWidgetItem, QTabWidget, QVBoxLayout)

from rgcs_desktop.viewers.base import Panel


def _fill(table: QTableWidget, headers: list[str], rows: list[list[str]]):
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.setRowCount(len(rows))
    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            item = QTableWidgetItem(str(val))
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(r, c, item)
    table.resizeColumnsToContents()


class WorkspaceBrowserPanel(Panel):
    TITLE = "Workspace"

    def __init__(self, context, parent=None):
        super().__init__(context, parent)
        layout = QVBoxLayout(self)
        head = QHBoxLayout()
        self.title_label = QLabel()
        head.addWidget(self.title_label)
        head.addStretch(1)
        layout.addLayout(head)
        self.tabs = QTabWidget()
        self.objects_table = QTableWidget()
        self.files_table = QTableWidget()
        self.exports_table = QTableWidget()
        self.tabs.addTab(self.objects_table, "Objects")
        self.tabs.addTab(self.files_table, "Imported files")
        self.tabs.addTab(self.exports_table, "Export history")
        layout.addWidget(self.tabs)
        self.refresh()

    def refresh(self) -> None:
        ws = self.context.workspace
        if ws is None:
            self.title_label.setText("No workspace open")
            return
        self.title_label.setText(
            f"Workspace '{ws.name}' — schema v{ws.schema_version} — {ws.root}")
        objs = ws.list_objects()
        _fill(self.objects_table,
              ["id", "kind", "name", "created", "sha256"],
              [[o["object_id"], o["kind"], o["name"], o["created_at"],
                o["content_sha256"][:16] + "…"] for o in objs])
        _fill(self.files_table,
              ["sha256", "original name", "size", "imported", "note"],
              [[f["sha256"][:16] + "…", f["original_name"], f["size_bytes"],
                f["imported_at"], f["note"]] for f in ws.list_files()])
        _fill(self.exports_table,
              ["when", "kind", "path", "sha256"],
              [[e["created_at"], e["kind"], e["path"], e["sha256"][:16] + "…"]
               for e in ws.list_exports()])
        self.inspector_changed.emit()

    def inspector_info(self):
        ws = self.context.workspace
        if ws is None:
            return super().inspector_info()
        return {
            "properties": {"name": ws.name, "root": str(ws.root),
                           "objects": len(ws.list_objects()),
                           "schema_version": ws.schema_version},
            "classification": "—",
            "units": "n/a",
            "provenance": "SQLite object registry with content sha256 per object",
        }
