"""Crystal Validator panel: measured inputs -> validation, derived
geometry, diagram, and certification exports."""
from __future__ import annotations

import json

from PySide6.QtWidgets import (QComboBox, QDoubleSpinBox, QFormLayout,
                               QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                               QPlainTextEdit, QPushButton, QSpinBox,
                               QVBoxLayout)

from rgcs_core.provenance import json_dumps

from rgcs_desktop.services.certification import render_certification_pdf
from rgcs_desktop.services.crystal_validator import (
    derive_crystal_geometry, export_specimen_json, make_crystal_diagram,
    validate_specimen)
from rgcs_desktop.services.design_studio import claim_boundary
from rgcs_desktop.services.export_receipts import write_receipt
from rgcs_desktop.viewers.base import Panel
from rgcs_desktop.viewers.design_studio_common import (
    EXAMPLE_SPECIMEN, export_dir, record_export_safe, studio_state)
from rgcs_desktop.widgets import ClassificationBadge

MATERIALS = ["quartz", "amethyst", "calcite", "fluorite", "obsidian",
             "glass", "other"]


class CrystalValidatorPanel(Panel):
    TITLE = "Crystal Validator"

    def __init__(self, context, parent=None):
        super().__init__(context, parent)
        self._validation = None
        self._derived: dict = {}
        self._exports: dict = {}

        layout = QHBoxLayout(self)
        left = QVBoxLayout()

        form_box = QGroupBox("Measured inputs")
        form = QFormLayout(form_box)
        self.specimen_id = QLineEdit("CRY-NEW")
        form.addRow("Specimen ID", self.specimen_id)
        self.material = QComboBox()
        self.material.addItems(MATERIALS)
        form.addRow("Material family", self.material)
        self.length = QDoubleSpinBox()
        self.length.setRange(0.0, 10000.0)
        self.length.setDecimals(2)
        self.length.setValue(0.0)
        form.addRow("Length (mm)", self.length)
        self.diameter = QDoubleSpinBox()
        self.diameter.setRange(0.0, 10000.0)
        self.diameter.setDecimals(2)
        form.addRow("Diameter (mm, 0 = none)", self.diameter)
        self.width = QDoubleSpinBox()
        self.width.setRange(0.0, 10000.0)
        self.width.setDecimals(2)
        form.addRow("Width (mm, 0 = none)", self.width)
        self.facets = QSpinBox()
        self.facets.setRange(0, 24)
        form.addRow("Facet count (0 = not counted)", self.facets)
        self.angle = QDoubleSpinBox()
        self.angle.setRange(-1.0, 179.0)
        self.angle.setDecimals(1)
        self.angle.setValue(-1.0)
        self.angle.setSpecialValueText("not measured")
        form.addRow("Termination angle (deg)", self.angle)
        self.mass = QDoubleSpinBox()
        self.mass.setRange(0.0, 100000.0)
        self.mass.setDecimals(1)
        form.addRow("Mass (g, 0 = not weighed)", self.mass)
        self.nodes = QLineEdit()
        self.nodes.setPlaceholderText("measured nodes mm, comma separated")
        form.addRow("Nodes (mm)", self.nodes)
        self.unc_length = QDoubleSpinBox()
        self.unc_length.setRange(0.0, 100.0)
        self.unc_length.setDecimals(3)
        self.unc_length.setValue(0.5)
        form.addRow("Length uncertainty (mm)", self.unc_length)
        self.unc_width = QDoubleSpinBox()
        self.unc_width.setRange(0.0, 100.0)
        self.unc_width.setDecimals(3)
        self.unc_width.setValue(0.5)
        form.addRow("Width uncertainty (mm)", self.unc_width)
        self.operator = QLineEdit()
        form.addRow("Operator", self.operator)
        left.addWidget(form_box)

        self.badge = ClassificationBadge("MEASURED_INPUT")
        left.addWidget(self.badge)

        buttons = QHBoxLayout()
        self.validate_btn = QPushButton("Validate geometry")
        self.validate_btn.clicked.connect(self.validate)
        buttons.addWidget(self.validate_btn)
        self.example_btn = QPushButton("Load example")
        self.example_btn.clicked.connect(self.load_example)
        buttons.addWidget(self.example_btn)
        left.addLayout(buttons)
        self.export_btn = QPushButton("Generate certification sheet "
                                      "(PDF + JSON + SVG)")
        self.export_btn.clicked.connect(self.export_all)
        self.export_btn.setEnabled(False)
        left.addWidget(self.export_btn)
        left.addStretch(1)
        layout.addLayout(left)

        right = QVBoxLayout()
        self.status = QLabel("Enter length, width/diameter, material, and "
                             "uncertainty to begin.")
        self.status.setWordWrap(True)
        right.addWidget(self.status)
        self.detail = QPlainTextEdit()
        self.detail.setReadOnly(True)
        right.addWidget(self.detail, stretch=1)
        layout.addLayout(right, stretch=1)

        for w in (self.length, self.diameter, self.width, self.mass,
                  self.unc_length, self.unc_width, self.angle):
            w.valueChanged.connect(self._live_update)
        self.facets.valueChanged.connect(self._live_update)
        self.nodes.textChanged.connect(self._live_update)

    # -- specimen assembly -------------------------------------------------
    def current_specimen(self) -> dict:
        dims: dict = {"length_mm": self.length.value()}
        if self.diameter.value() > 0:
            dims["diameter_mm"] = self.diameter.value()
        if self.width.value() > 0:
            dims["width_mm"] = self.width.value()
        if self.facets.value() > 0:
            dims["facet_count"] = self.facets.value()
        if self.angle.value() >= 0:
            dims["termination_angle_deg"] = self.angle.value()
        specimen = {
            "schema_version": "1.0.0",
            "specimen_id": self.specimen_id.text().strip() or "CRY-NEW",
            "material_family": self.material.currentText(),
            "dimensions": dims,
            "uncertainty": {"length_mm": self.unc_length.value(),
                            "width_mm": self.unc_width.value()},
            "provenance": {"entered_by": self.operator.text().strip()
                           or "unrecorded",
                           "method": "manual entry (Design Studio)"},
            "classification": "MEASURED_INPUT",
        }
        if self.mass.value() > 0:
            specimen["mass_g"] = self.mass.value()
        nodes = self._parse_nodes()
        if nodes:
            specimen["measured_nodes_mm"] = nodes
        if self.operator.text().strip():
            specimen["operator"] = self.operator.text().strip()
        return specimen

    def _parse_nodes(self) -> list[float]:
        out = []
        for token in self.nodes.text().split(","):
            token = token.strip()
            if not token:
                continue
            try:
                out.append(float(token))
            except ValueError:
                pass
        return out

    def set_specimen(self, specimen: dict) -> None:
        dims = specimen.get("dimensions", {})
        self.specimen_id.setText(specimen.get("specimen_id", "CRY-NEW"))
        material = specimen.get("material_family", "other")
        idx = self.material.findText(material)
        self.material.setCurrentIndex(idx if idx >= 0
                                      else self.material.count() - 1)
        self.length.setValue(dims.get("length_mm", 0.0))
        self.diameter.setValue(dims.get("diameter_mm", 0.0))
        self.width.setValue(dims.get("width_mm", 0.0))
        self.facets.setValue(dims.get("facet_count", 0))
        self.angle.setValue(dims.get("termination_angle_deg", -1.0))
        self.mass.setValue(specimen.get("mass_g", 0.0))
        self.nodes.setText(", ".join(
            f"{n:g}" for n in specimen.get("measured_nodes_mm", [])))
        unc = specimen.get("uncertainty", {})
        self.unc_length.setValue(unc.get("length_mm", 0.5))
        self.unc_width.setValue(unc.get("width_mm", 0.5))
        self.operator.setText(specimen.get("operator", ""))

    def load_example(self) -> None:
        self.set_specimen(EXAMPLE_SPECIMEN)
        self.validate()

    # -- validation / derivation -------------------------------------------
    def _live_update(self, *_a) -> None:
        if self.length.value() > 0 and (self.diameter.value() > 0
                                        or self.width.value() > 0):
            self.validate(quiet=True)

    def validate(self, quiet: bool = False) -> bool:
        specimen = self.current_specimen()
        self._validation = validate_specimen(specimen)
        if self._validation.ok:
            self._derived = derive_crystal_geometry(specimen)
            studio_state(self.context)["specimen"] = specimen
            studio_state(self.context)["derived"] = self._derived
            missing = self._validation.missing_optional
            self.status.setText(
                "Geometry valid."
                + (f" Needs measurement: {', '.join(missing)}."
                   if missing else "")
                + (f" Warnings: {'; '.join(self._validation.warnings)}"
                   if self._validation.warnings else ""))
            self.detail.setPlainText(
                json_dumps(self._derived, indent=2, sort_keys=True))
            self.badge.set_classification("MEASURED_INPUT")
            self.export_btn.setEnabled(True)
            if not quiet:
                self.status_message.emit(
                    f"specimen {specimen['specimen_id']}: geometry valid")
        else:
            self._derived = {}
            self.status.setText("Invalid: "
                                + "; ".join(self._validation.errors))
            self.detail.setPlainText("")
            self.export_btn.setEnabled(False)
            if not quiet:
                self.status_message.emit(
                    f"specimen invalid: {'; '.join(self._validation.errors)}")
        self.inspector_changed.emit()
        return self._validation.ok

    # -- exports -----------------------------------------------------------
    def export_all(self) -> dict:
        if not self.validate(quiet=True):
            self.status_message.emit("export blocked: specimen invalid")
            return {}
        specimen = self.current_specimen()
        sid = specimen["specimen_id"]
        out = export_dir(self.context)
        json_path = export_specimen_json(specimen, self._derived,
                                         out / f"specimen_{sid}.json")
        svg_path = make_crystal_diagram(specimen,
                                        out / f"specimen_{sid}_geometry.svg")
        receipt = render_certification_pdf(
            specimen, self._derived,
            out / f"specimen_{sid}_certificate.pdf")
        receipt_path = write_receipt(receipt,
                                     out / f"specimen_{sid}.receipt.json")
        for kind, path in (("design_studio_specimen", json_path),
                           ("design_studio_svg", svg_path),
                           ("design_studio_pdf",
                            out / f"specimen_{sid}_certificate.pdf"),
                           ("design_studio_receipt", receipt_path)):
            record_export_safe(self.context, kind, path)
        self._exports = {"json": json_path, "svg": svg_path,
                         "pdf": out / f"specimen_{sid}_certificate.pdf",
                         "receipt": receipt_path}
        self.status_message.emit(
            f"exported {sid}: certificate PDF, JSON receipt, SVG -> {out}")
        self.inspector_changed.emit()
        return self._exports

    def inspector_info(self):
        v = self._validation
        props = {
            "status": (v.summary() if v else "not validated"),
            "aspect ratio": self._derived.get("aspect_ratio"),
            "volume (cm^3)": self._derived.get("volume_estimate_cm3"),
            "density check": self._derived.get("density_check"),
            "axial half-wave (Hz)": self._derived.get("axial_half_wave_hz"),
        }
        if self._exports:
            props["last export"] = str(self._exports.get("pdf", ""))
        return {"properties": props,
                "classification": "MEASURED_INPUT + MODEL_OUTPUT (derived)",
                "units": "mm / g / Hz / cm^3",
                "provenance": claim_boundary("certification")}
