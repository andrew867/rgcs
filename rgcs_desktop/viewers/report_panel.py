"""Report generator + reproducibility bundle export panel."""
from __future__ import annotations

from PySide6.QtWidgets import (QHBoxLayout, QLabel, QLineEdit,
                               QPlainTextEdit, QPushButton, QVBoxLayout)

from rgcs_desktop.services.bundle import export_bundle, verify_bundle
from rgcs_desktop.services.report import generate_report
from rgcs_desktop.viewers.base import Panel


class ReportPanel(Panel):
    TITLE = "Report / export"

    def __init__(self, context, parent=None):
        super().__init__(context, parent)
        layout = QVBoxLayout(self)
        row = QHBoxLayout()
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Report title (optional)")
        row.addWidget(self.title_edit)
        self.report_btn = QPushButton("Generate markdown report")
        self.report_btn.clicked.connect(self.generate)
        row.addWidget(self.report_btn)
        self.bundle_btn = QPushButton("Export reproducibility bundle (zip)")
        self.bundle_btn.clicked.connect(self.export)
        row.addWidget(self.bundle_btn)
        layout.addLayout(row)
        self.status = QLabel("—")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        layout.addWidget(self.preview)
        self.last_report = None
        self.last_bundle = None

    def generate(self):
        ws = self.context.workspace
        path = generate_report(ws, self.title_edit.text() or None)
        self.last_report = path
        self.preview.setPlainText(path.read_text())
        self.status.setText(f"report written: {path}")
        self.context.notify_workspace_changed()
        return path

    def export(self):
        ws = self.context.workspace
        path = export_bundle(ws)
        self.last_bundle = path
        check = verify_bundle(path)
        self.status.setText(
            f"bundle written: {path} — verify: "
            f"{'OK' if check['ok'] else 'CHECKSUM MISMATCH'} "
            f"({check['n_members']} members)")
        self.context.notify_workspace_changed()
        return path

    def inspector_info(self):
        return {"properties": {"last report": str(self.last_report or "—"),
                               "last bundle": str(self.last_bundle or "—")},
                "classification": "Derived (report reproduces stored labels)",
                "units": "n/a",
                "provenance": "bundle: workspace.db + sources + artifacts + "
                              "manifests + CHECKSUMS.json + VERSIONS.json"}
