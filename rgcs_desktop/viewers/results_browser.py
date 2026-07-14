"""Results / artifact browser: content-addressed artifacts with JSON view."""
from __future__ import annotations

import json

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QListWidget, QListWidgetItem, QPlainTextEdit,
                               QSplitter, QVBoxLayout)

from rgcs_desktop.viewers.base import Panel


class ResultsBrowserPanel(Panel):
    TITLE = "Results"

    def __init__(self, context, parent=None):
        super().__init__(context, parent)
        layout = QVBoxLayout(self)
        split = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(split)
        self.listing = QListWidget()
        self.listing.currentItemChanged.connect(self._show)
        split.addWidget(self.listing)
        self.viewer = QPlainTextEdit()
        self.viewer.setReadOnly(True)
        split.addWidget(self.viewer)
        self._current: dict | None = None
        self.refresh()

    def refresh(self) -> None:
        ws = self.context.workspace
        self.listing.clear()
        if ws is None:
            return
        for a in ws.list_artifacts():
            item = QListWidgetItem(
                f"{a['artifact_id']}  ({a['size_bytes']} B)")
            item.setData(Qt.ItemDataRole.UserRole, a["artifact_id"])
            self.listing.addItem(item)

    def artifact_ids(self) -> list[str]:
        return [self.listing.item(i).data(Qt.ItemDataRole.UserRole)
                for i in range(self.listing.count())]

    def _show(self, item, _prev=None) -> None:
        if item is None:
            return
        artifact_id = item.data(Qt.ItemDataRole.UserRole)
        payload = self.context.workspace.read_artifact(artifact_id)
        self._current = {"artifact_id": artifact_id, "payload": payload}
        self.viewer.setPlainText(json.dumps(payload, indent=2)[:100000])
        self.inspector_changed.emit()

    def inspector_info(self):
        c = self._current or {}
        payload = c.get("payload", {})
        cls = (payload.get("classification")
               if isinstance(payload, dict) else "") or "Derived"
        return {"properties": {"artifact_id": c.get("artifact_id", ""),
                               "kind": payload.get("kind", "")
                               if isinstance(payload, dict) else ""},
                "classification": str(cls),
                "units": "see artifact fields (unit-suffixed names)",
                "provenance": "content-addressed artifact "
                              "(id = sha256 of canonical JSON)"}
