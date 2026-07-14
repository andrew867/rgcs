"""Avoided-crossing explorer: interactive coupling-strength g sweep."""
from __future__ import annotations

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDoubleSpinBox, QFormLayout, QGroupBox,
                               QHBoxLayout, QLabel, QSlider, QVBoxLayout)

from rgcs_core.coupled_modes import avoided_crossing_sweep, coupled_two_mode

from rgcs_desktop.plots import make_plot, plot_series
from rgcs_desktop.viewers.base import Panel
from rgcs_desktop.widgets import ClassificationBadge


class AvoidedCrossingPanel(Panel):
    TITLE = "Avoided crossing"

    def __init__(self, context, parent=None):
        super().__init__(context, parent)
        self._last: dict | None = None
        layout = QHBoxLayout(self)
        controls = QGroupBox("Two-mode coupling")
        form = QFormLayout(controls)
        self.f_b = QDoubleSpinBox()
        self.f_b.setRange(1, 1e6); self.f_b.setValue(4096.0)
        self.span = QDoubleSpinBox()
        self.span.setRange(1, 1e5); self.span.setValue(400.0)
        self.q_a = QDoubleSpinBox()
        self.q_a.setRange(1, 1e7); self.q_a.setValue(1000.0)
        self.q_b = QDoubleSpinBox()
        self.q_b.setRange(1, 1e7); self.q_b.setValue(1000.0)
        self.g_slider = QSlider(Qt.Orientation.Horizontal)
        self.g_slider.setRange(0, 500)  # 0..50 Hz in 0.1 Hz steps
        self.g_slider.setValue(100)
        self.g_label = QLabel("g = 10.0 Hz")
        form.addRow("Fixed mode f_B (Hz)", self.f_b)
        form.addRow("Sweep half-span (Hz)", self.span)
        form.addRow("Q_A", self.q_a)
        form.addRow("Q_B", self.q_b)
        form.addRow(self.g_label, self.g_slider)
        self.split_label = QLabel("—")
        self.ratio_label = QLabel("—")
        form.addRow("Min splitting (2g)", self.split_label)
        form.addRow("Strong-coupling ratio R_g", self.ratio_label)
        self.badge = ClassificationBadge("Derived")
        form.addRow("Classification", self.badge)
        layout.addWidget(controls)

        self.plot = make_plot("Avoided crossing (g sweep)",
                              "uncoupled f_A (Hz)", "hybrid frequency (Hz)")
        layout.addWidget(self.plot, stretch=1)

        self.g_slider.valueChanged.connect(self.compute)
        for w in (self.f_b, self.span, self.q_a, self.q_b):
            w.valueChanged.connect(self.compute)
        self.compute()

    @property
    def g_hz(self) -> float:
        return self.g_slider.value() / 10.0

    def compute(self) -> dict:
        g = self.g_hz
        self.g_label.setText(f"g = {g:.1f} Hz")
        f_b = self.f_b.value()
        grid = np.linspace(f_b - self.span.value(), f_b + self.span.value(),
                           241)
        sweep = avoided_crossing_sweep(grid, f_b, g)
        onres = coupled_two_mode(f_b, f_b, g, self.q_a.value(),
                                 self.q_b.value())
        self.plot.clear()
        plot_series(self.plot, sweep["f_a_hz"], sweep["upper_hz"],
                    color="#1258a8", width=2)
        plot_series(self.plot, sweep["f_a_hz"], sweep["lower_hz"],
                    color="#b26a00", width=2)
        plot_series(self.plot, grid, grid, color="#999999", width=1)
        plot_series(self.plot, grid, np.full_like(grid, f_b),
                    color="#999999", width=1)
        self.split_label.setText(
            f"{sweep['min_splitting_hz']:.3f} Hz")
        self.ratio_label.setText(
            f"{onres['strong_coupling_ratio']:.3f} "
            f"({'strong' if onres['strong_coupling_ratio'] > 1 else 'weak'})")
        self.badge.set_classification(str(sweep["classification"]))
        self._last = {"sweep": sweep, "on_resonance": onres, "g_hz": g}
        self.inspector_changed.emit()
        return self._last

    def inspector_info(self):
        d = self._last or {}
        onres = d.get("on_resonance", {})
        return {"properties": {"g (Hz)": d.get("g_hz"),
                               "splitting 2g (Hz)": onres.get("splitting_hz"),
                               "coupling rate |K| = 2 pi g (rad/s)":
                                   onres.get("coupling_rate_s"),
                               "R_g": onres.get("strong_coupling_ratio")},
                "classification": str(
                    d.get("sweep", {}).get("classification", "Derived")),
                "units": "Hz; rates 1/s",
                "provenance": "rgcs_core.coupled_modes (RGCS-M.23–M.27)"}
