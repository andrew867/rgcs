"""Frequency Key Library panel: sourced, classified, testable key
records with live sideband preview."""
from __future__ import annotations

from PySide6.QtWidgets import (QDoubleSpinBox, QHBoxLayout, QLabel,
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QVBoxLayout)

from rgcs_desktop.services.coil_pulse import sidebands
from rgcs_desktop.services.design_studio import claim_boundary
from rgcs_desktop.services.frequency_keys_lib import (custom_key_record,
                                                      load_keys)
from rgcs_desktop.viewers.base import Panel

COLUMNS = ["key (Hz)", "label", "family", "source status",
           "math relations", "null / downgrade criteria"]


class FrequencyKeyPanel(Panel):
    TITLE = "Frequency Key Library"

    def __init__(self, context, parent=None):
        super().__init__(context, parent)
        self._selected: dict | None = None
        self._custom: list[dict] = []

        layout = QVBoxLayout(self)
        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemSelectionChanged.connect(self._selection_changed)
        layout.addWidget(self.table, stretch=1)

        row = QHBoxLayout()
        row.addWidget(QLabel("Custom key (Hz):"))
        self.custom_value = QDoubleSpinBox()
        self.custom_value.setRange(0.001, 1e6)
        self.custom_value.setDecimals(3)
        self.custom_value.setValue(777.0)
        row.addWidget(self.custom_value)
        self.add_custom_btn = QPushButton("Add as custom")
        self.add_custom_btn.clicked.connect(self.add_custom)
        row.addWidget(self.add_custom_btn)
        row.addStretch(1)
        layout.addLayout(row)

        self.sideband_label = QLabel("select a key to preview sidebands "
                                     "around 4096 Hz")
        self.sideband_label.setWordWrap(True)
        layout.addWidget(self.sideband_label)

        boundary = QLabel(claim_boundary("frequency_key"))
        boundary.setWordWrap(True)
        boundary.setStyleSheet("color: #555; font-style: italic;")
        layout.addWidget(boundary)

        self._reload()

    def _reload(self) -> None:
        records = self.keys()
        self.table.setRowCount(len(records))
        for r, rec in enumerate(records):
            values = [f"{rec['key_hz']:g}", rec["label"], rec["family"],
                      rec["source_status"], rec["math_relations"],
                      rec["null_criteria"]]
            for c, value in enumerate(values):
                self.table.setItem(r, c, QTableWidgetItem(str(value)))
        self.table.resizeColumnsToContents()

    def keys(self) -> list[dict]:
        return load_keys() + self._custom

    def _selection_changed(self) -> None:
        rows = {i.row() for i in self.table.selectedIndexes()}
        if not rows:
            return
        rec = self.keys()[min(rows)]
        self._selected = rec
        table = sidebands(4096.0, float(rec["key_hz"]))
        first = table[0]
        lower = (f"{first['lower_hz']:g}" if first["lower_hz"] is not None
                 else "below 0 (omitted)")
        self.sideband_label.setText(
            f"{rec['label']} [{rec['source_status']}] — sidebands around "
            f"4096 Hz: {lower} / {first['upper_hz']:g} Hz"
            + (f" · {rec['math_relations']}" if rec["math_relations"]
               else ""))
        self.inspector_changed.emit()

    def select_key_hz(self, key_hz: float) -> None:
        for row, rec in enumerate(self.keys()):
            if abs(float(rec["key_hz"]) - key_hz) < 1e-6:
                self.table.selectRow(row)
                return
        raise KeyError(f"{key_hz} Hz not in the library")

    def add_custom(self) -> dict:
        rec = custom_key_record(self.custom_value.value())
        self._custom.append(rec)
        self._reload()
        self.table.selectRow(self.table.rowCount() - 1)
        self.status_message.emit(
            f"custom key {rec['key_hz']:g} Hz added (status: custom — "
            f"no source status)")
        return rec

    def inspector_info(self):
        rec = self._selected or {}
        return {"properties": {
                    "registered keys": len(load_keys()),
                    "custom keys": len(self._custom),
                    "selected": rec.get("label", "—"),
                    "source status": rec.get("source_status", "—"),
                    "tests": rec.get("tests", "—")},
                "classification": "Source claim / candidate per key record",
                "units": "Hz",
                "provenance": claim_boundary("frequency_key")}
