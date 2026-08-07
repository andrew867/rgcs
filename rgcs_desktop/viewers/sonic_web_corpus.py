"""Frequency Key Studio — Web/YouTube Corpus page (metadata only).

Paste title/description metadata; the parser extracts frequencies with
roles and claimed-use tags. There is deliberately no downloader here
(DR-004): the page consumes text the user already has."""
from __future__ import annotations

from PySide6.QtWidgets import (QHBoxLayout, QLabel, QLineEdit,
                               QPlainTextEdit, QPushButton, QVBoxLayout,
                               QWidget)

from rgcs_core.provenance import json_dumps

from rgcs_desktop.services.sonic_ingest import (IngestError,
                                                parse_video_metadata)


class WebCorpusPage(QWidget):
    def __init__(self, context, status_cb, parent=None):
        super().__init__(parent)
        self.context = context
        self._status_cb = status_cb
        self._last_record: dict | None = None

        layout = QVBoxLayout(self)
        note = QLabel("Metadata only: titles, descriptions, URLs. No "
                      "audio is downloaded. Claimed uses are recorded "
                      "from source text, not endorsed.")
        note.setWordWrap(True)
        note.setStyleSheet("font-style: italic; color: #555;")
        layout.addWidget(note)

        self.url = QLineEdit()
        self.url.setPlaceholderText("source URL")
        layout.addWidget(self.url)
        self.title = QLineEdit()
        self.title.setPlaceholderText(
            "video/page title, e.g. 528Hz + 6.3 Hz Astral Projection "
            "Binaural Beat")
        layout.addWidget(self.title)
        self.description = QPlainTextEdit()
        self.description.setPlaceholderText("description text (optional)")
        self.description.setMaximumHeight(120)
        layout.addWidget(self.description)

        row = QHBoxLayout()
        self.parse_btn = QPushButton("Parse metadata")
        self.parse_btn.clicked.connect(self.parse)
        row.addWidget(self.parse_btn)
        row.addStretch(1)
        layout.addLayout(row)

        self.result = QPlainTextEdit()
        self.result.setReadOnly(True)
        layout.addWidget(self.result, stretch=1)

    def parse(self, *_a) -> dict | None:
        record = {"url": self.url.text().strip(),
                  "platform": "web",
                  "title": self.title.text().strip(),
                  "description": self.description.toPlainText().strip()}
        try:
            parsed = parse_video_metadata(record)
        except IngestError as exc:
            self._status_cb(f"parse refused: {exc}")
            self.result.setPlainText(f"Refused: {exc}")
            return None
        self._last_record = parsed
        self.result.setPlainText(
            json_dumps(parsed, indent=2, sort_keys=True))
        n = len(parsed["extracted_frequencies_hz"])
        self._status_cb(
            f"parsed metadata: {n} frequencies, claimed uses: "
            f"{', '.join(parsed['claimed_uses']) or 'none'}")
        return parsed

    @property
    def last_record(self) -> dict | None:
        return self._last_record
