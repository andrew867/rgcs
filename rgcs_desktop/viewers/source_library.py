"""Source library: import reference files (sha256 recorded), citations,
provenance panel, and the drive source-preset catalog rendered under a
Source-claim banner (binding requirement)."""
from __future__ import annotations

import json

from PySide6.QtWidgets import (QFileDialog, QFormLayout, QGroupBox,
                               QHBoxLayout, QLineEdit, QListWidget,
                               QListWidgetItem, QPlainTextEdit, QPushButton,
                               QSplitter, QVBoxLayout, QWidget)
from PySide6.QtCore import Qt

from rgcs_core.drive import source_preset_catalog

from rgcs_desktop.viewers.base import Panel
from rgcs_desktop.widgets import ClassificationBadge, SourceClaimBanner


class SourceLibraryPanel(Panel):
    TITLE = "Sources"

    def __init__(self, context, parent=None):
        super().__init__(context, parent)
        layout = QVBoxLayout(self)
        split = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(split)

        # left: source list + import
        left = QWidget()
        lv = QVBoxLayout(left)
        self.source_list = QListWidget()
        self.source_list.currentItemChanged.connect(self._show_source)
        lv.addWidget(self.source_list)
        btns = QHBoxLayout()
        self.import_btn = QPushButton("Import file…")
        self.import_btn.clicked.connect(self._import_dialog)
        btns.addWidget(self.import_btn)
        lv.addLayout(btns)
        split.addWidget(left)

        # right: citation form + provenance + preset catalog
        right = QWidget()
        rv = QVBoxLayout(right)
        cite_box = QGroupBox("Citation / provenance")
        form = QFormLayout(cite_box)
        self.cite_key = QLineEdit()
        self.cite_title = QLineEdit()
        self.cite_origin = QLineEdit()
        self.cite_note = QLineEdit()
        form.addRow("Citation key (e.g. RG-04)", self.cite_key)
        form.addRow("Title", self.cite_title)
        form.addRow("Origin", self.cite_origin)
        form.addRow("Classification note", self.cite_note)
        self.save_cite_btn = QPushButton("Register citation")
        self.save_cite_btn.clicked.connect(self._register_citation)
        form.addRow(self.save_cite_btn)
        rv.addWidget(cite_box)

        self.provenance_view = QPlainTextEdit()
        self.provenance_view.setReadOnly(True)
        rv.addWidget(self.provenance_view)

        preset_box = QGroupBox("Drive source presets (from source material)")
        pv = QVBoxLayout(preset_box)
        catalog = source_preset_catalog()
        pv.addWidget(SourceClaimBanner())
        pv.addWidget(ClassificationBadge(catalog.get("classification",
                                                     "Source claim")))
        self.preset_view = QPlainTextEdit()
        self.preset_view.setReadOnly(True)
        self.preset_view.setPlainText(
            json.dumps(catalog.get("presets", {}), indent=2))
        pv.addWidget(self.preset_view)
        rv.addWidget(preset_box)
        split.addWidget(right)
        self.refresh()

    # -- actions ---------------------------------------------------------
    def _import_dialog(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import source file")
        if path:
            self.import_file(path)

    def import_file(self, path: str, note: str = "") -> dict:
        """Programmatic import (used by tests): copies + records sha256."""
        info = self.context.workspace.import_file(path, note=note)
        self.context.workspace.put_object(
            "source", info["original_name"],
            {"file": info, "citation": None,
             "classification": "Source claim (imported reference material)"},
            object_id=f"source-{info['sha256'][:12]}", overwrite=True)
        self.refresh()
        self.status_message.emit(f"imported {info['original_name']} "
                                 f"(sha256 {info['sha256'][:12]}…)")
        return info

    def _register_citation(self) -> None:
        item = self.source_list.currentItem()
        if item is None:
            return
        object_id = item.data(Qt.ItemDataRole.UserRole)
        ws = self.context.workspace
        obj = ws.get_object(object_id)
        payload = obj["payload"]
        payload["citation"] = {
            "key": self.cite_key.text(),
            "title": self.cite_title.text(),
            "origin": self.cite_origin.text(),
            "classification_note": self.cite_note.text(),
        }
        ws.put_object("source", obj["name"], payload, object_id=object_id,
                      overwrite=True)
        self.refresh()

    def _show_source(self, item, _prev=None) -> None:
        if item is None:
            return
        obj = self.context.workspace.get_object(
            item.data(Qt.ItemDataRole.UserRole))
        self.provenance_view.setPlainText(json.dumps(obj["payload"], indent=2))
        self.inspector_changed.emit()

    def refresh(self) -> None:
        ws = self.context.workspace
        self.source_list.clear()
        if ws is None:
            return
        for o in ws.list_objects("source"):
            item = QListWidgetItem(f"{o['name']}  ({o['object_id']})")
            item.setData(Qt.ItemDataRole.UserRole, o["object_id"])
            self.source_list.addItem(item)

    def inspector_info(self):
        item = self.source_list.currentItem()
        props = {}
        if item is not None and self.context.workspace is not None:
            obj = self.context.workspace.get_object(
                item.data(Qt.ItemDataRole.UserRole))
            f = obj["payload"].get("file", {})
            props = {"name": obj["name"], "sha256": f.get("sha256", ""),
                     "stored at": f.get("relpath", "")}
        return {"properties": props,
                "classification": "Source claim (imported reference material)",
                "units": "n/a",
                "provenance": "files copied verbatim; sha256 recorded on import"}
