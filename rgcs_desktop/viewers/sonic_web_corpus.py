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
        self.add_btn = QPushButton("Add to corpus")
        self.add_btn.clicked.connect(self.add_to_corpus)
        row.addWidget(self.add_btn)
        self.cluster_btn = QPushButton("Cluster corpus")
        self.cluster_btn.clicked.connect(self.cluster)
        row.addWidget(self.cluster_btn)
        self.export_btn = QPushButton("Export corpus CSV")
        self.export_btn.clicked.connect(self.export_csv)
        row.addWidget(self.export_btn)
        row.addStretch(1)
        self.corpus_label = QLabel("corpus: 0 records")
        row.addWidget(self.corpus_label)
        layout.addLayout(row)

        self.result = QPlainTextEdit()
        self.result.setReadOnly(True)
        layout.addWidget(self.result, stretch=1)
        self._refresh_corpus_label()

    def _corpus_path(self):
        from rgcs_desktop.viewers.design_studio_common import export_dir
        return export_dir(self.context) / "corpus" / "sonic_corpus.json"

    def _store(self):
        from rgcs_desktop.services.sonic_corpus import CorpusStore
        return CorpusStore(self._corpus_path())

    def _refresh_corpus_label(self) -> None:
        try:
            n = len(self._store().records)
        except Exception:
            n = 0
        self.corpus_label.setText(f"corpus: {n} records")

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
        from rgcs_desktop.services.sonic_corpus import recommend_recipes
        recs = recommend_recipes(parsed)
        text = json_dumps(parsed, indent=2, sort_keys=True)
        if recs:
            lines = [f"- {r['recipe']['recipe_id']} "
                     f"({r['recipe']['title']}) score {r['score']}: "
                     + "; ".join(r["reasons"]) for r in recs]
            text += "\n\nrecommended seed recipes:\n" + "\n".join(lines)
        self.result.setPlainText(text)
        n = len(parsed["extracted_frequencies_hz"])
        self._status_cb(
            f"parsed metadata: {n} frequencies, claimed uses: "
            f"{', '.join(parsed['claimed_uses']) or 'none'}; "
            f"{len(recs)} recipe recommendation(s)")
        return parsed

    def add_to_corpus(self, *_a) -> bool:
        if self._last_record is None and self.parse() is None:
            return False
        store = self._store()
        added = store.add(self._last_record)
        store.save()
        self._refresh_corpus_label()
        self._status_cb("added to corpus" if added
                        else "already in corpus (duplicate URL)")
        return added

    def cluster(self, *_a):
        from rgcs_desktop.services.sonic_corpus import cluster_corpus
        store = self._store()
        if not store.records:
            self._status_cb("corpus is empty — parse and add records "
                            "first")
            return []
        clusters = cluster_corpus(store.records)
        lines = []
        for i, cluster in enumerate(clusters):
            rep = cluster["representative"]
            lines.append(f"cluster {i + 1} (n={cluster['size']}, "
                         f"signature {cluster['signature']}): "
                         f"{rep.get('title', '')[:70]}")
        self.result.setPlainText("\n".join(lines))
        self._status_cb(f"{len(clusters)} cluster(s) across "
                        f"{len(store.records)} records")
        return clusters

    def export_csv(self, *_a):
        store = self._store()
        if not store.records:
            self._status_cb("corpus is empty — nothing to export")
            return None
        out = self._corpus_path().with_suffix(".csv")
        path = store.to_csv(out)
        self._status_cb(f"corpus CSV exported: {path}")
        return path

    @property
    def last_record(self) -> dict | None:
        return self._last_record
