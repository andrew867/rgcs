"""Coil and Pulse Designer panel: wire/coil estimates, pulse tables,
sidebands, and build-sheet export."""
from __future__ import annotations

from PySide6.QtWidgets import (QComboBox, QDoubleSpinBox, QFormLayout,
                               QGroupBox, QHBoxLayout, QLabel,
                               QPlainTextEdit, QPushButton, QSpinBox,
                               QVBoxLayout)

from rgcs_core.provenance import json_dumps

from rgcs_desktop.services.coil_pulse import (
    PULSE_MODES, PulseError, classify_key, design_estimates,
    generate_pulse_table, render_coil_pulse_pdf, sidebands)
from rgcs_desktop.services.design_studio import (MODEL_OUTPUT,
                                                 claim_boundary,
                                                 new_object_id)
from rgcs_desktop.services.export_receipts import write_receipt
from rgcs_desktop.services.frequency_keys_lib import load_keys
from rgcs_desktop.viewers.base import Panel
from rgcs_desktop.viewers.design_studio_common import (
    export_dir, record_export_safe, studio_state)
from rgcs_desktop.widgets import ClassificationBadge


class CoilPulsePanel(Panel):
    TITLE = "Coil / Pulse Designer"

    def __init__(self, context, parent=None):
        super().__init__(context, parent)
        self._design: dict | None = None
        self._last_error: str | None = None

        layout = QHBoxLayout(self)
        left = QVBoxLayout()

        coil_box = QGroupBox("Coil inputs")
        form = QFormLayout(coil_box)
        self.gauge = QSpinBox()
        self.gauge.setRange(10, 40)
        self.gauge.setValue(26)
        form.addRow("Wire gauge (AWG)", self.gauge)
        self.wire_material = QComboBox()
        self.wire_material.addItems(["copper", "silver", "aluminum",
                                     "nichrome"])
        form.addRow("Wire material", self.wire_material)
        self.radius = QDoubleSpinBox()
        self.radius.setRange(1.0, 1000.0)
        self.radius.setValue(25.0)
        form.addRow("Coil radius (mm)", self.radius)
        self.height = QDoubleSpinBox()
        self.height.setRange(0.0, 1000.0)
        self.height.setValue(40.0)
        form.addRow("Coil height (mm)", self.height)
        self.turns = QSpinBox()
        self.turns.setRange(1, 100000)
        self.turns.setValue(200)
        form.addRow("Turns", self.turns)
        self.count = QSpinBox()
        self.count.setRange(1, 64)
        self.count.setValue(2)
        form.addRow("Number of coils", self.count)
        left.addWidget(coil_box)

        pulse_box = QGroupBox("Pulse programme")
        pform = QFormLayout(pulse_box)
        self.base_hz = QDoubleSpinBox()
        self.base_hz.setRange(1.0, 1e6)
        self.base_hz.setDecimals(3)
        self.base_hz.setValue(4096.0)
        pform.addRow("Base carrier (Hz)", self.base_hz)
        self.key_combo = QComboBox()
        for rec in load_keys():
            self.key_combo.addItem(
                f"{rec['label']} ({rec['source_status']})",
                float(rec["key_hz"]))
        self.key_combo.addItem("custom…", None)
        idx = self.key_combo.findText("925 Hz (mathematical relation)")
        if idx >= 0:
            self.key_combo.setCurrentIndex(idx)
        pform.addRow("Modulation key", self.key_combo)
        self.custom_key = QDoubleSpinBox()
        self.custom_key.setRange(0.0, 1e6)
        self.custom_key.setDecimals(3)
        self.custom_key.setEnabled(False)
        pform.addRow("Custom key (Hz)", self.custom_key)
        self.mode = QComboBox()
        self.mode.addItems(PULSE_MODES)
        self.mode.setCurrentText("am_key")
        pform.addRow("Pulse mode", self.mode)
        self.duty = QDoubleSpinBox()
        self.duty.setRange(0.01, 1.0)
        self.duty.setSingleStep(0.05)
        self.duty.setValue(0.5)
        pform.addRow("Duty cycle", self.duty)
        self.voltage = QDoubleSpinBox()
        self.voltage.setRange(0.1, 1e4)
        self.voltage.setValue(45.0)
        pform.addRow("Voltage limit (V)", self.voltage)
        self.current = QDoubleSpinBox()
        self.current.setRange(0.01, 1e3)
        self.current.setValue(2.0)
        pform.addRow("Current limit (A)", self.current)
        left.addWidget(pulse_box)

        self.badge = ClassificationBadge(MODEL_OUTPUT)
        left.addWidget(self.badge)
        self.compute_btn = QPushButton("Calculate coil")
        self.compute_btn.clicked.connect(self.compute)
        left.addWidget(self.compute_btn)
        self.export_btn = QPushButton("Export build sheet (PDF + receipt)")
        self.export_btn.clicked.connect(self.export_build_sheet)
        left.addWidget(self.export_btn)
        left.addStretch(1)
        layout.addLayout(left)

        right = QVBoxLayout()
        self.status = QLabel("Choose a generator assembly and wire gauge "
                             "to calculate coil estimates.")
        self.status.setWordWrap(True)
        right.addWidget(self.status)
        self.key_warning = QLabel("")
        self.key_warning.setWordWrap(True)
        self.key_warning.setStyleSheet("color: #b26a00;")
        right.addWidget(self.key_warning)
        self.detail = QPlainTextEdit()
        self.detail.setReadOnly(True)
        right.addWidget(self.detail, stretch=1)
        layout.addLayout(right, stretch=1)

        self.key_combo.currentIndexChanged.connect(self._key_changed)
        for w in (self.radius, self.height, self.base_hz, self.duty,
                  self.custom_key, self.voltage, self.current):
            w.valueChanged.connect(self.compute)
        for w in (self.turns, self.count, self.gauge):
            w.valueChanged.connect(self.compute)
        self.mode.currentIndexChanged.connect(self.compute)
        self.compute()

    def _key_changed(self, *_a) -> None:
        self.custom_key.setEnabled(self.key_combo.currentData() is None)
        self.compute()

    def selected_key_hz(self) -> float:
        data = self.key_combo.currentData()
        return float(data) if data is not None else self.custom_key.value()

    def current_design(self) -> dict | None:
        return self._design

    def compute(self, *_a) -> dict | None:
        key_hz = self.selected_key_hz()
        assembly = (studio_state(self.context)
                    .get("phyrll_design") or {}).get("design_id", "ASM-NEW")
        design_id = (self._design or {}).get("design_id") \
            or new_object_id("CPD")
        design = {
            "schema_version": "1.0.0",
            "design_id": design_id,
            "source_assembly_id": assembly,
            "wire": {"gauge_awg": self.gauge.value(),
                     "material": self.wire_material.currentText()},
            "coil": {"radius_mm": self.radius.value(),
                     "height_mm": self.height.value(),
                     "turns": self.turns.value(),
                     "count": self.count.value()},
            "pulse": {"base_hz": self.base_hz.value(),
                      "modulation_key_hz": key_hz,
                      "mode": self.mode.currentText(),
                      "duty_cycle": self.duty.value()},
            "limits": {"voltage_v": self.voltage.value(),
                       "current_a": self.current.value()},
            "classification": MODEL_OUTPUT,
        }
        try:
            design["estimates"] = design_estimates(design)
            design["sidebands"] = sidebands(design["pulse"]["base_hz"],
                                            key_hz)
            pulse_table = generate_pulse_table(design["pulse"])
        except PulseError as exc:
            self._last_error = str(exc)
            self._design = None
            self.status.setText(f"Refused: {exc}")
            self.status_message.emit(f"coil/pulse refused: {exc}")
            self.detail.setPlainText("")
            self.inspector_changed.emit()
            return None
        self._last_error = None
        self._design = design
        studio_state(self.context)["coil_pulse_design"] = design
        key_info = classify_key(key_hz)
        self.key_warning.setText(key_info["warning"] or "")
        est = design["estimates"]
        first = design["sidebands"][0]
        self.status.setText(
            f"wire ≈ {est['wire_length_m']:.1f} m, "
            f"R ≈ {est['resistance_ohm']:.2f} Ω · sidebands "
            f"{first['lower_hz']:g} / {first['upper_hz']:g} Hz")
        self.detail.setPlainText(
            "estimates:\n"
            + json_dumps(est, indent=2, sort_keys=True)
            + "\n\nsidebands:\n"
            + json_dumps(design["sidebands"], indent=2)
            + "\n\npulse table:\n"
            + json_dumps(pulse_table, indent=2))
        self.inspector_changed.emit()
        return design

    def export_build_sheet(self):
        design = self._design or self.compute()
        if design is None:
            self.status_message.emit(
                f"export blocked: {self._last_error or 'no design'}")
            return None
        out = export_dir(self.context)
        path = out / f"{design['design_id']}_build_sheet.pdf"
        receipt = render_coil_pulse_pdf(design, path)
        write_receipt(receipt,
                      out / f"{design['design_id']}.receipt.json")
        record_export_safe(self.context, "design_studio_pdf", path)
        self.status_message.emit(f"coil/pulse build sheet written: {path}")
        return path

    def inspector_info(self):
        d = self._design or {}
        est = d.get("estimates", {})
        sb = (d.get("sidebands") or [{}])[0]
        return {"properties": {
                    "design": d.get("design_id", "—"),
                    "assembly": d.get("source_assembly_id", "—"),
                    "wire length (m)": est.get("wire_length_m"),
                    "resistance (ohm)": est.get("resistance_ohm"),
                    "first sidebands (Hz)":
                        (f"{sb.get('lower_hz')} / {sb.get('upper_hz')}"
                         if sb else "—"),
                    "refusal": self._last_error or "none"},
                "classification": MODEL_OUTPUT,
                "units": "m / ohm / Hz / V / A",
                "provenance": claim_boundary("build_sheet")}
