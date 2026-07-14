"""Settings panel: units and default paths."""
from __future__ import annotations

from PySide6.QtWidgets import (QComboBox, QFormLayout, QLabel, QLineEdit,
                               QPushButton, QVBoxLayout)

from rgcs_desktop.viewers.base import Panel


class SettingsPanel(Panel):
    TITLE = "Settings"

    def __init__(self, context, parent=None):
        super().__init__(context, parent)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        s = self.context.settings
        self.freq_unit = QComboBox()
        self.freq_unit.addItems(["Hz", "kHz"])
        self.freq_unit.setCurrentText(s.frequency_unit)
        self.ws_dir = QLineEdit(s.default_workspace_dir)
        form.addRow("Frequency display unit", self.freq_unit)
        form.addRow("Default workspace directory", self.ws_dir)
        form.addRow(QLabel(
            "Note: internal units are fixed by docs/NOTATION_AND_UNITS.md "
            "(mm, Hz, s, g); this only changes display."))
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.clicked.connect(self.apply)
        form.addRow(self.apply_btn)
        layout.addLayout(form)
        layout.addStretch(1)

    def apply(self) -> None:
        s = self.context.settings
        s.frequency_unit = self.freq_unit.currentText()
        s.default_workspace_dir = self.ws_dir.text()
        self.status_message.emit("settings saved")

    def inspector_info(self):
        s = self.context.settings
        return {"properties": {"frequency unit": s.frequency_unit,
                               "workspace dir": s.default_workspace_dir},
                "classification": "—",
                "units": "display only; core units are fixed",
                "provenance": "QSettings (org RGCS, app rgcs_desktop)"}
