"""Frequency Key Studio — Recipe Library page (search + render)."""
from __future__ import annotations

from PySide6.QtWidgets import (QHBoxLayout, QLabel, QLineEdit,
                               QPushButton, QTableWidget,
                               QTableWidgetItem, QVBoxLayout, QWidget)

from rgcs_desktop.services.sonic_recipes import (RecipeError,
                                                 load_recipes,
                                                 recipe_to_session,
                                                 search_recipes)

COLUMNS = ["recipe", "title", "family", "carrier (Hz)", "beat (Hz)",
           "minutes", "layers", "intent", "source basis"]


class RecipeLibraryPage(QWidget):
    def __init__(self, context, status_cb, parent=None):
        super().__init__(parent)
        self.context = context
        self._status_cb = status_cb
        self._rows: list[dict] = []

        layout = QVBoxLayout(self)
        row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText(
            "search by text, frequency, or family — e.g. schumann, 925, "
            "gateway_style")
        self.search.textChanged.connect(self.refresh_table)
        row.addWidget(self.search, stretch=1)
        self.render_btn = QPushButton("Render selected (short preview)")
        self.render_btn.clicked.connect(self.render_selected)
        row.addWidget(self.render_btn)
        self.batch_btn = QPushButton("Batch render shown")
        self.batch_btn.clicked.connect(self.batch_render_shown)
        row.addWidget(self.batch_btn)
        layout.addLayout(row)

        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table, stretch=1)
        self.status = QLabel("Claimed uses and source-language intents "
                             "are recorded from sources, not endorsed.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.refresh_table()

    def refresh_table(self, *_a) -> None:
        text = self.search.text().strip()
        try:
            freq = float(text)
            rows = search_recipes(frequency_hz=freq)
        except ValueError:
            rows = search_recipes(text) if text else load_recipes()
            if text and not rows:
                rows = search_recipes(family=text)
        self._rows = rows
        self.table.setRowCount(len(rows))
        for r, rec in enumerate(rows):
            values = [rec["recipe_id"], rec["title"], rec["family"],
                      f"{rec['carrier_hz']:g}", f"{rec['beat_hz']:g}",
                      rec["duration_min"], ", ".join(rec["layers"]),
                      rec["intent"], rec["source_basis"]]
            for c, value in enumerate(values):
                self.table.setItem(r, c, QTableWidgetItem(str(value)))
        self.table.resizeColumnsToContents()

    def selected_recipe(self) -> dict | None:
        rows = {i.row() for i in self.table.selectedIndexes()}
        if not rows:
            return None
        return self._rows[min(rows)]

    def render_selected(self, *_a, duration_s: float = 15.0):
        recipe = self.selected_recipe()
        if recipe is None:
            self._status_cb("select a recipe first")
            return None
        from rgcs_desktop.services.sonic_exports import render_session_wav
        from rgcs_desktop.viewers.design_studio_common import (
            export_dir, record_export_safe)
        try:
            session = recipe_to_session(recipe, duration_s=duration_s)
        except RecipeError as exc:
            self._status_cb(f"refused: {exc}")
            return None
        out = export_dir(self.context) / "sonic"
        wav = out / f"{recipe['recipe_id']}_preview.wav"
        receipt = render_session_wav(session, wav)
        record_export_safe(self.context, "sonic_wav", wav)
        self._status_cb(
            f"preview rendered: {wav.name} (peak {receipt['peak']:.3f})")
        return wav

    def batch_render_shown(self, *_a, duration_s: float = 15.0):
        """Batch-render every recipe currently shown in the table."""
        from rgcs_desktop.services.sonic_exports import batch_render
        from rgcs_desktop.viewers.design_studio_common import (
            export_dir, record_export_safe)
        ids = [rec["recipe_id"] for rec in self._rows]
        if not ids:
            self._status_cb("no recipes shown to batch-render")
            return None
        out = export_dir(self.context) / "sonic" / "batch"
        manifest = batch_render(ids, out, duration_s=duration_s)
        rendered = [r for r in manifest["results"]
                    if r["status"] == "rendered"]
        for result in rendered:
            record_export_safe(self.context, "sonic_wav",
                               out / result["wav"])
        self._status_cb(
            f"batch: {len(rendered)}/{len(manifest['results'])} "
            f"rendered -> {out}")
        return manifest
