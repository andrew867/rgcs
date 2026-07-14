"""Pulse timing designer: exact-cycle families 2261 / 1508 / 1131,
envelope timings in exact ms, phase residue, micro-pulse metrics with
pulses_per_period exposed (RG-14), and source presets under a
Source-claim banner."""
from __future__ import annotations

import json

from PySide6.QtWidgets import (QComboBox, QDoubleSpinBox, QFormLayout,
                               QGroupBox, QHBoxLayout, QLabel,
                               QPlainTextEdit, QSpinBox, QVBoxLayout)

from rgcs_core.drive import (DRIVE_PRESETS, drive_sequence,
                             micro_pulse_metrics, source_preset_catalog)

from rgcs_desktop.viewers.base import Panel
from rgcs_desktop.widgets import ClassificationBadge, SourceClaimBanner

#: mode -> exact cycle family (matches rgcs_core.drive)
FAMILY = {"standard": 2261, "half_spacing": 1508, "double_rate": 1131}


class PulseDesignerPanel(Panel):
    TITLE = "Pulse designer"

    def __init__(self, context, parent=None):
        super().__init__(context, parent)
        self._sequence: dict | None = None
        self._micro: dict | None = None
        layout = QHBoxLayout(self)

        left = QVBoxLayout()
        seq_box = QGroupBox("Envelope (exact-cycle families)")
        form = QFormLayout(seq_box)
        self.mode = QComboBox()
        for m in DRIVE_PRESETS:
            self.mode.addItem(f"{m} (family {FAMILY.get(m, '?')})", m)
        self.carrier = QDoubleSpinBox()
        self.carrier.setRange(1, 1e6)
        self.carrier.setValue(4096.0)
        form.addRow("Mode", self.mode)
        form.addRow("Carrier (Hz)", self.carrier)
        self.badge = ClassificationBadge("Derived [RG-12]")
        form.addRow("Classification", self.badge)
        self.timing_label = QLabel("—")
        self.timing_label.setWordWrap(True)
        form.addRow("Exact timing", self.timing_label)
        self.residue_label = QLabel("—")
        form.addRow("Phase residue (cycles)", self.residue_label)
        left.addWidget(seq_box)

        micro_box = QGroupBox("Micro-pulse metrics (RG-14)")
        mform = QFormLayout(micro_box)
        self.pulse_width = QDoubleSpinBox()
        self.pulse_width.setRange(0.01, 1000)
        self.pulse_width.setValue(1.0)
        self.voltage = QDoubleSpinBox()
        self.voltage.setRange(0.1, 1e4)
        self.voltage.setValue(45.0)
        self.current = QDoubleSpinBox()
        self.current.setRange(0.01, 1e3)
        self.current.setValue(2.0)
        # pulses_per_period is an explicit, exposed assumption (RG-14)
        self.pulses_per_period = QSpinBox()
        self.pulses_per_period.setRange(1, 64)
        self.pulses_per_period.setValue(1)
        mform.addRow("Pulse width (µs)", self.pulse_width)
        mform.addRow("Voltage (V)", self.voltage)
        mform.addRow("Peak current (A)", self.current)
        mform.addRow("Pulses per carrier period", self.pulses_per_period)
        self.micro_label = QLabel("—")
        self.micro_label.setWordWrap(True)
        mform.addRow("Metrics", self.micro_label)
        left.addWidget(micro_box)

        preset_box = QGroupBox("Source presets")
        pv = QVBoxLayout(preset_box)
        pv.addWidget(SourceClaimBanner())
        catalog = source_preset_catalog()
        pv.addWidget(ClassificationBadge(str(catalog["classification"])))
        left.addWidget(preset_box)
        layout.addLayout(left)

        self.detail = QPlainTextEdit()
        self.detail.setReadOnly(True)
        layout.addWidget(self.detail, stretch=1)

        self.mode.currentIndexChanged.connect(self.compute)
        self.carrier.valueChanged.connect(self.compute)
        for w in (self.pulse_width, self.voltage, self.current):
            w.valueChanged.connect(self.compute)
        self.pulses_per_period.valueChanged.connect(self.compute)
        self.compute()

    def compute(self) -> dict:
        mode = self.mode.currentData()
        seq = drive_sequence(mode, self.carrier.value())
        micro = micro_pulse_metrics(
            carrier_hz=self.carrier.value(),
            pulse_width_us=self.pulse_width.value(),
            voltage_v=self.voltage.value(),
            peak_current_a=self.current.value(),
            pulses_per_period=self.pulses_per_period.value())
        self._sequence, self._micro = seq, micro
        self.badge.set_classification(str(seq["classification"]))
        self.timing_label.setText(
            f"on {seq['on_ms']} ms / spacing {seq['spacing_ms']} ms / "
            f"pause {seq['pause_ms']} ms × {seq['bursts']} bursts; "
            f"exact macro {seq['exact_macro_ms']:.6f} ms "
            f"({seq['exact_cycles']} cycles)")
        self.residue_label.setText(
            f"{seq['phase_residue_cycles']:+.6f} "
            f"(nominal {seq['nominal_cycles']} cycles; defined on cycle "
            f"counts only, D-13)")
        self.micro_label.setText(
            f"duty {micro['pulse_duty_fraction']:.6f}; "
            f"L ≈ {micro['inferred_inductance_uh']:.1f} µH; "
            f"E ≈ {micro['stored_energy_uj']:.1f} µJ; "
            f"pulses/period = {micro['pulses_per_period']}")
        self.detail.setPlainText(
            "drive_sequence:\n" + json.dumps(seq, indent=2, default=str)
            + "\n\nmicro_pulse_metrics:\n"
            + json.dumps(micro, indent=2, default=str))
        self.inspector_changed.emit()
        return seq

    @property
    def sequence(self) -> dict | None:
        return self._sequence

    def inspector_info(self):
        s = self._sequence or {}
        m = self._micro or {}
        return {"properties": {
                    "mode": s.get("mode"),
                    "exact cycles": s.get("exact_cycles"),
                    "exact macro (ms)": s.get("exact_macro_ms"),
                    "phase residue (cycles)": s.get("phase_residue_cycles"),
                    "pulses per period": m.get("pulses_per_period"),
                    "inference note": m.get("inference_note", "")},
                "classification": str(s.get("classification",
                                            "Derived [RG-12]")),
                "units": "ms / µs / Hz / V / A / µH / µJ",
                "provenance": "rgcs_core.drive (RG-12, RG-14); source "
                              "presets are Source claims"}
