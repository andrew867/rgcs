"""Frequency Key Studio — Timeline Editor page (v1.1).

Edit session segments directly (kind, duration, beat ramp, curve).
When enabled, the custom timeline replaces the standard shape in the
New Session wizard. Invalid timelines are refused with the reason."""
from __future__ import annotations

from PySide6.QtWidgets import (QCheckBox, QComboBox, QHBoxLayout, QLabel,
                               QPushButton, QTableWidget,
                               QTableWidgetItem, QVBoxLayout, QWidget)

from rgcs_desktop.services.sonic_timeline import (RAMP_CURVES,
                                                  SEGMENT_KINDS,
                                                  TimelineError,
                                                  validate_session)

COLUMNS = ["kind", "duration (s)", "beat start (Hz)", "beat end (Hz)",
           "curve"]

DEFAULT_ROWS = [
    ("intro", 60.0, 10.0, 10.0, "linear"),
    ("relax", 120.0, 10.0, 10.0, "linear"),
    ("ramp_down", 180.0, 10.0, 7.83, "cosine"),
    ("hold", 720.0, 7.83, 7.83, "linear"),
    ("outro", 120.0, 7.83, 7.83, "linear"),
]


class TimelineEditorPage(QWidget):
    def __init__(self, context, status_cb, parent=None):
        super().__init__(parent)
        self.context = context
        self._status_cb = status_cb

        layout = QVBoxLayout(self)
        self.enabled = QCheckBox(
            "Use this custom timeline in New Session (replaces the "
            "standard shape)")
        layout.addWidget(self.enabled)

        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        layout.addWidget(self.table, stretch=1)

        row = QHBoxLayout()
        add_btn = QPushButton("Add segment")
        add_btn.clicked.connect(lambda: self._add_row())
        row.addWidget(add_btn)
        remove_btn = QPushButton("Remove selected")
        remove_btn.clicked.connect(self._remove_selected)
        row.addWidget(remove_btn)
        self.check_btn = QPushButton("Validate timeline")
        self.check_btn.clicked.connect(self.validate)
        row.addWidget(self.check_btn)
        row.addStretch(1)
        layout.addLayout(row)

        self.status = QLabel("Segment kinds: " + ", ".join(SEGMENT_KINDS))
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        for values in DEFAULT_ROWS:
            self._add_row(values)

    def _add_row(self, values=("hold", 60.0, 7.83, 7.83, "linear")):
        r = self.table.rowCount()
        self.table.insertRow(r)
        kind = QComboBox()
        kind.addItems(SEGMENT_KINDS)
        kind.setCurrentText(values[0])
        self.table.setCellWidget(r, 0, kind)
        for c, v in enumerate(values[1:4], start=1):
            self.table.setItem(r, c, QTableWidgetItem(f"{v:g}"))
        curve = QComboBox()
        curve.addItems(RAMP_CURVES)
        curve.setCurrentText(values[4])
        self.table.setCellWidget(r, 4, curve)

    def _remove_selected(self):
        rows = sorted({i.row() for i in self.table.selectedIndexes()},
                      reverse=True)
        for r in rows:
            self.table.removeRow(r)

    def segments(self) -> list[dict]:
        out = []
        for r in range(self.table.rowCount()):
            def _num(col: int) -> float:
                item = self.table.item(r, col)
                try:
                    return float(item.text()) if item else 0.0
                except ValueError:
                    return 0.0
            out.append({
                "kind": self.table.cellWidget(r, 0).currentText(),
                "duration_s": _num(1),
                "beat_start_hz": _num(2),
                "beat_end_hz": _num(3),
                "curve": self.table.cellWidget(r, 4).currentText(),
            })
        return out

    def validate(self, *_a) -> bool:
        segments = self.segments()
        total = sum(s["duration_s"] for s in segments)
        probe = {"segments": segments, "duration_s": total}
        try:
            validate_session(probe)
        except TimelineError as exc:
            self.status.setText(f"Refused: {exc}")
            self._status_cb(f"timeline refused: {exc}")
            return False
        self.status.setText(
            f"Timeline valid: {len(segments)} segments, "
            f"{total / 60:.1f} min total, ends at "
            f"{segments[-1]['beat_end_hz']:g} Hz")
        self._status_cb("custom timeline valid")
        return True

    def custom_segments(self) -> list[dict] | None:
        """The custom timeline when enabled and valid, else None."""
        if not self.enabled.isChecked():
            return None
        segments = self.segments()
        if not segments:
            return None
        total = sum(s["duration_s"] for s in segments)
        try:
            validate_session({"segments": segments, "duration_s": total})
        except TimelineError:
            return None
        return segments
