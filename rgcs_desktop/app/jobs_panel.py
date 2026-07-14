"""Bottom dock: background jobs (progress, cancel), logs and warnings."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QHBoxLayout, QPlainTextEdit, QPushButton,
                               QTableWidget, QTableWidgetItem, QTabWidget,
                               QVBoxLayout, QWidget)

from rgcs_desktop.jobs import JobManager


class JobsPanel(QWidget):
    def __init__(self, job_manager: JobManager, parent=None):
        super().__init__(parent)
        self.jm = job_manager
        self._warned: set[str] = set()
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        jobs_tab = QWidget()
        jv = QVBoxLayout(jobs_tab)
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["job id", "name", "status", "progress", "last log line"])
        jv.addWidget(self.table)
        row = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancel selected")
        self.cancel_btn.clicked.connect(self._cancel_selected)
        row.addWidget(self.cancel_btn)
        row.addStretch(1)
        jv.addLayout(row)
        self.tabs.addTab(jobs_tab, "Jobs")
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.tabs.addTab(self.log_view, "Log")
        self.warn_view = QPlainTextEdit()
        self.warn_view.setReadOnly(True)
        self.tabs.addTab(self.warn_view, "Warnings")
        layout.addWidget(self.tabs)
        self.jm.job_updated.connect(self.refresh)
        self.refresh()

    def log(self, message: str) -> None:
        self.log_view.appendPlainText(message)

    def warn(self, message: str) -> None:
        self.warn_view.appendPlainText(message)

    def _cancel_selected(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            return
        job_id = self.table.item(row, 0).text()
        self.jm.cancel(job_id)

    def refresh(self, *_args) -> None:
        jobs = self.jm.jobs()
        self.table.setRowCount(len(jobs))
        for r, rec in enumerate(jobs):
            vals = [rec.job_id, rec.name, rec.status.value,
                    f"{rec.progress:.0%}",
                    rec.log_lines[-1] if rec.log_lines else ""]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(str(v))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(r, c, item)
            if rec.error and rec.job_id not in self._warned:
                self._warned.add(rec.job_id)
                self.warn(f"{rec.job_id} failed; error preserved as artifact "
                          f"{rec.error_artifact}")
        self.table.resizeColumnsToContents()
