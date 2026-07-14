"""Command palette (Ctrl+K): fuzzy-filterable action list."""
from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QLineEdit, QListWidget,
                               QListWidgetItem, QVBoxLayout)


class CommandPalette(QDialog):
    def __init__(self, actions: dict[str, Callable[[], None]], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Command palette")
        self.setModal(True)
        self.resize(520, 380)
        self._actions = actions
        layout = QVBoxLayout(self)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Type a command…")
        self.search.textChanged.connect(self._filter)
        layout.addWidget(self.search)
        self.listing = QListWidget()
        self.listing.itemActivated.connect(self._run_item)
        layout.addWidget(self.listing)
        self.search.returnPressed.connect(self._run_current)
        self._filter("")

    def action_names(self) -> list[str]:
        return sorted(self._actions)

    def _filter(self, text: str) -> None:
        text = text.lower()
        self.listing.clear()
        for name in self.action_names():
            if all(tok in name.lower() for tok in text.split()):
                self.listing.addItem(QListWidgetItem(name))
        if self.listing.count():
            self.listing.setCurrentRow(0)

    def _run_item(self, item: QListWidgetItem) -> None:
        self.run(item.text())

    def _run_current(self) -> None:
        item = self.listing.currentItem()
        if item is not None:
            self.run(item.text())

    def run(self, name: str) -> None:
        self.accept()
        fn = self._actions.get(name)
        if fn is not None:
            fn()

    def keyPressEvent(self, event):  # arrows navigate the list from the box
        if event.key() in (Qt.Key.Key_Down, Qt.Key.Key_Up):
            self.listing.keyPressEvent(event)
            return
        super().keyPressEvent(event)
