"""Model browser/editor: lists docs/model_registry.yaml entries with
classification badges; selected entry shows equation, inputs, sources."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QHBoxLayout, QLineEdit, QPlainTextEdit,
                               QSplitter, QTreeWidget, QTreeWidgetItem,
                               QVBoxLayout, QWidget)

import yaml

from rgcs_desktop.services import registry
from rgcs_desktop.services.formatting import classification_label
from rgcs_desktop.viewers.base import Panel
from rgcs_desktop.widgets import ClassificationBadge


class ModelEditorPanel(Panel):
    TITLE = "Models"

    def __init__(self, context, parent=None):
        super().__init__(context, parent)
        layout = QVBoxLayout(self)
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Filter models…")
        self.filter_edit.textChanged.connect(self._populate)
        layout.addWidget(self.filter_edit)
        split = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(split)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["id", "name", "classification", "module"])
        self.tree.currentItemChanged.connect(self._show_model)
        split.addWidget(self.tree)
        right = QWidget()
        rv = QVBoxLayout(right)
        self.badge = ClassificationBadge("Derived")
        rv.addWidget(self.badge)
        self.detail = QPlainTextEdit()
        self.detail.setReadOnly(True)
        rv.addWidget(self.detail)
        split.addWidget(right)
        self._current: dict | None = None
        self._populate()

    def _populate(self) -> None:
        needle = self.filter_edit.text().lower()
        self.tree.clear()
        for m in registry.models():
            cls = str(m.get("classification", "Derived"))
            text = f"{m.get('id','')} {m.get('name','')} {cls}".lower()
            if needle and needle not in text:
                continue
            item = QTreeWidgetItem([m.get("id", ""), m.get("name", ""),
                                    cls, m.get("module_target", "")])
            item.setData(0, Qt.ItemDataRole.UserRole, m)
            label = classification_label(cls)
            item.setForeground(2, Qt.GlobalColor.darkGray)
            self.tree.addTopLevelItem(item)
        for i in range(4):
            self.tree.resizeColumnToContents(i)

    def _show_model(self, item, _prev=None) -> None:
        if item is None:
            return
        m = item.data(0, Qt.ItemDataRole.UserRole)
        self._current = m
        self.badge.set_classification(str(m.get("classification", "Derived")))
        self.detail.setPlainText(yaml.safe_dump(m, sort_keys=False))
        self.inspector_changed.emit()

    def select_model(self, model_id: str) -> None:
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item.text(0) == model_id:
                self.tree.setCurrentItem(item)
                return

    def model_count(self) -> int:
        return self.tree.topLevelItemCount()

    def inspector_info(self):
        m = self._current or {}
        return {"properties": {"id": m.get("id", ""),
                               "name": m.get("name", ""),
                               "equation": m.get("equation", ""),
                               "module": m.get("module_target", "")},
                "classification": str(m.get("classification", "")),
                "units": ", ".join(
                    f"{i.get('symbol')}: {i.get('unit')}"
                    for i in m.get("inputs", []) if isinstance(i, dict)),
                "provenance": str(m.get("source", ""))}
