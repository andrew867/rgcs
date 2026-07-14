"""Right-hand inspector: properties, classification, units, provenance."""
from __future__ import annotations

from PySide6.QtWidgets import (QFormLayout, QGroupBox, QLabel,
                               QPlainTextEdit, QScrollArea, QVBoxLayout,
                               QWidget)

from rgcs_desktop.widgets import ClassificationBadge


class InspectorDock(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        self.badge = ClassificationBadge("Derived")
        outer.addWidget(self.badge)
        self.props_box = QGroupBox("Properties")
        self.props_form = QFormLayout(self.props_box)
        outer.addWidget(self.props_box)
        self.units_label = QLabel()
        self.units_label.setWordWrap(True)
        units_box = QGroupBox("Units")
        uv = QVBoxLayout(units_box)
        uv.addWidget(self.units_label)
        outer.addWidget(units_box)
        self.prov_label = QLabel()
        self.prov_label.setWordWrap(True)
        prov_box = QGroupBox("Provenance")
        pv = QVBoxLayout(prov_box)
        pv.addWidget(self.prov_label)
        outer.addWidget(prov_box)
        outer.addStretch(1)

    def show_info(self, info: dict) -> None:
        cls = str(info.get("classification") or "—")
        if cls and cls != "—":
            self.badge.set_classification(cls)
            self.badge.setVisible(True)
        else:
            self.badge.setVisible(False)
        while self.props_form.rowCount():
            self.props_form.removeRow(0)
        for k, v in (info.get("properties") or {}).items():
            value_label = QLabel(str(v))
            value_label.setWordWrap(True)
            self.props_form.addRow(QLabel(str(k)), value_label)
        self.units_label.setText(str(info.get("units") or "—"))
        self.prov_label.setText(str(info.get("provenance") or "—"))
