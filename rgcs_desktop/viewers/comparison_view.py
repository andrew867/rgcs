"""Comparison view: model spectrum (with 1σ bands) vs measured peaks.

Uses classify_resonance for each measured peak against the nearest model
mode — u_eps is mandatory and supplied from the model interval + the
user-entered measurement uncertainty (binding requirement). The
'engineering heuristic - not evidence' note is surfaced as a badge.
"""
from __future__ import annotations

from PySide6.QtWidgets import (QDoubleSpinBox, QFormLayout, QGroupBox,
                               QHBoxLayout, QLabel, QLineEdit, QPushButton,
                               QTableWidget, QTableWidgetItem, QVBoxLayout,
                               QWidget)

import numpy as np
import pyqtgraph as pg

from rgcs_core.compact_modes import compact_mode_spectrum
from rgcs_core.resonance import classify_resonance, epsilon_q
from rgcs_core.uncertainty import UncertainValue, default_wave_speed

from rgcs_desktop.plots import make_plot, plot_spectrum_with_bands
from rgcs_desktop.viewers.base import Panel
from rgcs_desktop.widgets import ClassificationBadge


class ComparisonPanel(Panel):
    TITLE = "Model vs measured"

    def __init__(self, context, parent=None):
        super().__init__(context, parent)
        self._rows: list[dict] = []
        layout = QHBoxLayout(self)
        left = QWidget()
        form = QFormLayout(left)
        self.f_b = QDoubleSpinBox()
        self.f_b.setRange(0, 1e6); self.f_b.setValue(4096.0)
        self.radius = QDoubleSpinBox()
        self.radius.setRange(0.1, 1e4); self.radius.setValue(100.0)
        self.measured = QLineEdit("4096, 10042.7, 12288")
        self.u_meas = QDoubleSpinBox()
        self.u_meas.setRange(0.001, 1e4); self.u_meas.setValue(2.0)
        self.q_m = QDoubleSpinBox()
        self.q_m.setRange(1, 1e7); self.q_m.setValue(5000.0)
        self.q_x = QDoubleSpinBox()
        self.q_x.setRange(1, 1e7); self.q_x.setValue(5000.0)
        form.addRow("Model base f_b (Hz)", self.f_b)
        form.addRow("Compact radius (mm)", self.radius)
        form.addRow("Measured peaks (Hz, comma)", self.measured)
        form.addRow("u(f_measured) (Hz)", self.u_meas)
        form.addRow("Q (measured mode)", self.q_m)
        form.addRow("Q (model mode)", self.q_x)
        self.compare_btn = QPushButton("Compare")
        self.compare_btn.clicked.connect(self.compare)
        form.addRow(self.compare_btn)
        self.badge = ClassificationBadge(
            "Derived — engineering heuristic - not evidence")
        form.addRow("Classification", self.badge)
        self.table = QTableWidget()
        form.addRow(self.table)
        layout.addWidget(left)
        self.plot = make_plot("Model (bands) vs measured (lines)",
                              "mode index n", "frequency (Hz)")
        layout.addWidget(self.plot, stretch=1)
        self.compare()

    def compare(self) -> list[dict]:
        spec = compact_mode_spectrum(
            base_frequency_hz=self.f_b.value(),
            v_chi=default_wave_speed(),
            compact_radius_mm=self.radius.value(),
            n_max=8)
        plot_spectrum_with_bands(self.plot, spec["modes"])
        try:
            peaks = [float(p) for p in self.measured.text().split(",")
                     if p.strip()]
        except ValueError:
            peaks = []
        rows: list[dict] = []
        for f_meas in peaks:
            # nearest model mode
            best = min(spec["modes"],
                       key=lambda m: abs(m["frequency"]["mean"] - f_meas))
            f_model = best["frequency"]["mean"]
            sigma_model = best["frequency"]["sigma"]
            if f_model <= 0:
                continue
            eps = abs(f_meas - f_model) / f_model
            # u_eps is MANDATORY: combine model sigma and measurement u
            u_eps = float(np.hypot(sigma_model, self.u_meas.value())
                          / f_model)
            cls = classify_resonance(eps, self.q_m.value(), self.q_x.value(),
                                     u_eps=max(u_eps, 1e-12))
            rows.append({"f_measured_hz": f_meas, "n": best["n"],
                         "f_model_hz": f_model, "epsilon": eps,
                         "u_epsilon": u_eps,
                         "class": cls["resonance_class"],
                         "uncertain": cls["class_uncertain"],
                         "note": cls["note"]})
            line = pg.InfiniteLine(pos=f_meas, angle=0,
                                   pen=pg.mkPen("#1e7d32", width=1.5))
            self.plot.addItem(line)
        self._rows = rows
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["f_meas (Hz)", "n", "f_model (Hz)", "epsilon", "class",
             "uncertain?"])
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, v in enumerate([f"{row['f_measured_hz']:.2f}", row["n"],
                                   f"{row['f_model_hz']:.2f}",
                                   f"{row['epsilon']:.5f}", row["class"],
                                   row["uncertain"]]):
                self.table.setItem(r, c, QTableWidgetItem(str(v)))
        self.table.resizeColumnsToContents()
        self.inspector_changed.emit()
        return rows

    def inspector_info(self):
        return {"properties": {"comparisons": len(self._rows),
                               "note": self._rows[0]["note"]
                               if self._rows else ""},
                "classification": "Derived — engineering heuristic - "
                                  "not evidence",
                "units": "Hz; epsilon dimensionless",
                "provenance": "rgcs_core.resonance.classify_resonance "
                              "(u_eps supplied by the UI, policy §3.4)"}
