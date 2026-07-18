"""Evidence Ledger panel (v4.7, A70): read-only browser over the
canonical store's evidence tables — CSCP and PMWR rows included.

The panel READS the canonical store (the same source the workbook is
generated from); it never edits evidence. Claim boundaries are shown
per row, and the footer restates the standing physical status.
"""
from __future__ import annotations

from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QLabel,
                               QTableWidget, QTableWidgetItem,
                               QVBoxLayout)

from rgcs_desktop.viewers.base import Panel

_COLUMNS = ("id", "kind", "evidence_class", "provenance")


class EvidenceLedgerPanel(Panel):
    TITLE = "Evidence ledger"

    def __init__(self, context, parent=None):
        super().__init__(context, parent)
        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        top.addWidget(QLabel("Table:"))
        self.table_pick = QComboBox()
        top.addWidget(self.table_pick, 1)
        layout.addLayout(top)
        self.grid = QTableWidget(0, len(_COLUMNS))
        self.grid.setHorizontalHeaderLabels(_COLUMNS)
        self.grid.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.grid, 1)
        self.boundary = QLabel(
            "SOFTWARE evidence only — every physical hypothesis in "
            "the v4.6/v4.7 programmes is UNTESTED. No row here is a "
            "measurement.")
        self.boundary.setWordWrap(True)
        layout.addWidget(self.boundary)
        self._store = None
        self.table_pick.currentTextChanged.connect(self._fill)
        self._load()

    def _load(self) -> None:
        try:
            from rgcs_workbench.canonical import build
            self._store = build()
            names = sorted(self._store.tables)
            self.table_pick.addItems(names)
            if "cspc_candidates" in names:
                self.table_pick.setCurrentText("cspc_candidates")
        except Exception as exc:  # noqa: BLE001 — panel must not
            #                       crash startup if a lane is absent
            self.boundary.setText(f"canonical store unavailable: {exc}")

    def _fill(self, table: str) -> None:
        if not self._store or not table:
            return
        rows = self._store.rows(table, include_private=False)
        self.grid.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, col in enumerate(_COLUMNS):
                self.grid.setItem(i, j, QTableWidgetItem(
                    str(row.get(col, ""))))
        self.status_message.emit(
            f"{table}: {len(rows)} public rows")

    def inspector_info(self):
        table = self.table_pick.currentText()
        return {
            "properties": {"table": table,
                           "rows": self.grid.rowCount()},
            "classification": "SOFTWARE evidence view; every physical "
                              "hypothesis UNTESTED",
            "units": "n/a (registry rows)",
            "provenance": "rgcs_workbench.canonical.build() — the "
                          "same store the workbook is generated from; "
                          "public rows only",
        }
