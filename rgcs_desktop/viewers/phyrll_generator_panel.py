"""Phyrll Generator Designer panel: custom-fit holder from the selected
validated specimen; SCAD/STL/build-sheet exports."""
from __future__ import annotations

from PySide6.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox,
                               QFormLayout, QGroupBox, QHBoxLayout, QLabel,
                               QLineEdit, QPlainTextEdit, QPushButton,
                               QVBoxLayout)

from rgcs_core.provenance import json_dumps

from rgcs_desktop.services.design_studio import (MODEL_OUTPUT,
                                                 claim_boundary,
                                                 new_object_id)
from rgcs_desktop.services.export_receipts import write_receipt
from rgcs_desktop.services.phyrll_generator import (
    DesignError, derive_holder_geometry, export_scad,
    export_stl_if_available, openscad_available, render_build_sheet_pdf)
from rgcs_desktop.viewers.base import Panel
from rgcs_desktop.viewers.design_studio_common import (
    EXAMPLE_SPECIMEN, export_dir, record_export_safe, studio_state)
from rgcs_desktop.widgets import ClassificationBadge


class PhyrllGeneratorPanel(Panel):
    TITLE = "Phyrll Generator Designer"

    def __init__(self, context, parent=None):
        super().__init__(context, parent)
        self._design: dict | None = None
        self._exports: dict = {}

        layout = QHBoxLayout(self)
        left = QVBoxLayout()

        src_box = QGroupBox("Source specimen")
        sv = QVBoxLayout(src_box)
        self.source_label = QLabel("no specimen selected")
        self.source_label.setWordWrap(True)
        sv.addWidget(self.source_label)
        self.use_current_btn = QPushButton("Use validated specimen")
        self.use_current_btn.clicked.connect(self.use_current_specimen)
        sv.addWidget(self.use_current_btn)
        left.addWidget(src_box)

        fit_box = QGroupBox("Fit controls")
        form = QFormLayout(fit_box)
        self.clearance = QDoubleSpinBox()
        self.clearance.setRange(0.0, 25.0)
        self.clearance.setDecimals(2)
        self.clearance.setSingleStep(0.1)
        self.clearance.setValue(0.4)
        form.addRow("Clearance (mm)", self.clearance)
        self.wall = QDoubleSpinBox()
        self.wall.setRange(0.5, 50.0)
        self.wall.setDecimals(2)
        self.wall.setValue(3.0)
        form.addRow("Wall thickness (mm)", self.wall)
        self.base = QDoubleSpinBox()
        self.base.setRange(0.5, 50.0)
        self.base.setDecimals(2)
        self.base.setValue(4.0)
        form.addRow("Base thickness (mm)", self.base)
        self.material = QComboBox()
        self.material.addItems(["PLA", "PETG", "ABS"])
        form.addRow("Material", self.material)
        self.channel_enabled = QCheckBox("Coil channel")
        self.channel_enabled.setChecked(True)
        form.addRow(self.channel_enabled)
        self.channel_width = QDoubleSpinBox()
        self.channel_width.setRange(0.5, 20.0)
        self.channel_width.setValue(2.0)
        form.addRow("Channel width (mm)", self.channel_width)
        self.channel_depth = QDoubleSpinBox()
        self.channel_depth.setRange(0.1, 20.0)
        self.channel_depth.setValue(1.5)
        form.addRow("Channel depth (mm)", self.channel_depth)
        self.label_text = QLineEdit()
        self.label_text.setPlaceholderText("embossed label (optional)")
        form.addRow("Label", self.label_text)
        left.addWidget(fit_box)

        self.badge = ClassificationBadge(MODEL_OUTPUT)
        left.addWidget(self.badge)

        self.scad_btn = QPushButton("Generate SCAD")
        self.scad_btn.clicked.connect(self.generate_scad)
        left.addWidget(self.scad_btn)
        stl_label = ("Generate STL" if openscad_available()
                     else "Generate STL (OpenSCAD not installed)")
        self.stl_btn = QPushButton(stl_label)
        self.stl_btn.clicked.connect(self.generate_stl)
        left.addWidget(self.stl_btn)
        self.sheet_btn = QPushButton("Export build sheet (PDF)")
        self.sheet_btn.clicked.connect(self.export_build_sheet)
        left.addWidget(self.sheet_btn)
        left.addStretch(1)
        layout.addLayout(left)

        right = QVBoxLayout()
        self.status = QLabel("Select a validated crystal before generating "
                             "a custom-fit holder.")
        self.status.setWordWrap(True)
        right.addWidget(self.status)
        self.detail = QPlainTextEdit()
        self.detail.setReadOnly(True)
        right.addWidget(self.detail, stretch=1)
        layout.addLayout(right, stretch=1)

        for w in (self.clearance, self.wall, self.base,
                  self.channel_width, self.channel_depth):
            w.valueChanged.connect(self._recompute)
        self.channel_enabled.toggled.connect(self._recompute)

    # -- specimen source ---------------------------------------------------
    def _specimen(self) -> dict | None:
        return studio_state(self.context).get("specimen")

    def use_current_specimen(self) -> None:
        specimen = self._specimen()
        if specimen is None:
            self.status.setText(
                "No validated specimen yet — validate one in the Crystal "
                "Validator (or use its 'Load example' button). Using the "
                "built-in example for now.")
            studio_state(self.context)["specimen"] = dict(EXAMPLE_SPECIMEN)
            specimen = self._specimen()
        self.source_label.setText(
            f"specimen {specimen['specimen_id']} — "
            f"L {specimen['dimensions']['length_mm']:g} mm, "
            f"{'D' if 'diameter_mm' in specimen['dimensions'] else 'W'} "
            f"{specimen['dimensions'].get('diameter_mm', specimen['dimensions'].get('width_mm')):g} mm")
        self._recompute()

    # -- geometry ----------------------------------------------------------
    def _params(self) -> dict:
        return {
            "clearance_mm": self.clearance.value(),
            "wall_thickness_mm": self.wall.value(),
            "base_thickness_mm": self.base.value(),
            "coil_channel": {
                "enabled": self.channel_enabled.isChecked(),
                "width_mm": self.channel_width.value(),
                "depth_mm": self.channel_depth.value(),
            },
        }

    def _recompute(self, *_a) -> dict | None:
        specimen = self._specimen()
        if specimen is None:
            return None
        try:
            geometry = derive_holder_geometry(specimen, self._params())
        except DesignError as exc:
            self._design = None
            self.status.setText(f"Refused: {exc}")
            self.status_message.emit(f"holder design refused: {exc}")
            self.detail.setPlainText("")
            self.inspector_changed.emit()
            return None
        design_id = (self._design or {}).get("design_id") \
            or new_object_id("PHY")
        self._design = {
            "schema_version": "1.0.0",
            "design_id": design_id,
            "source_specimen_id": specimen["specimen_id"],
            "clearance_mm": self.clearance.value(),
            "holder_style": "cradle",
            "wall_thickness_mm": self.wall.value(),
            "base_thickness_mm": self.base.value(),
            "material": self.material.currentText(),
            "holder_geometry": geometry,
            "coil_channels": geometry.get("coil_channel", {}),
            "label_text": self.label_text.text().strip(),
            "exports": {k: str(v) for k, v in self._exports.items()},
            "classification": MODEL_OUTPUT,
        }
        studio_state(self.context)["phyrll_design"] = self._design
        self.status.setText(
            f"cavity {geometry['cavity_length_mm']:g} × "
            f"{geometry['cavity_width_mm']:g} mm, outer "
            f"{geometry['outer_length_mm']:g} × "
            f"{geometry['outer_width_mm']:g} × "
            f"{geometry['outer_height_mm']:g} mm")
        self.detail.setPlainText(
            json_dumps(self._design, indent=2, sort_keys=True))
        self.inspector_changed.emit()
        return self._design

    def current_design(self) -> dict | None:
        return self._design or self._recompute()

    # -- exports -----------------------------------------------------------
    def generate_scad(self):
        design = self.current_design()
        if design is None:
            self.status_message.emit("no design to export")
            return None
        out = export_dir(self.context)
        path = out / f"{design['design_id']}.scad"
        receipt = export_scad(design, path)
        self._exports["scad"] = path
        design["exports"]["scad"] = str(path)
        write_receipt(receipt, out / f"{design['design_id']}.receipt.json")
        record_export_safe(self.context, "design_studio_scad", path)
        self.status_message.emit(f"SCAD written: {path}")
        return path

    def generate_stl(self):
        design = self.current_design()
        if design is None:
            self.status_message.emit("no design to export")
            return None
        scad = self._exports.get("scad") or self.generate_scad()
        out = export_dir(self.context)
        stl = out / f"{design['design_id']}.stl"
        receipt = export_stl_if_available(scad, stl)
        if receipt["status"] == "rendered":
            self._exports["stl"] = stl
            design["exports"]["stl"] = str(stl)
            record_export_safe(self.context, "design_studio_stl", stl)
            self.status_message.emit(f"STL rendered: {stl}")
        else:
            self.status_message.emit(
                f"STL {receipt['status']}: {receipt['reason']}")
        return receipt

    def export_build_sheet(self):
        design = self.current_design()
        if design is None:
            self.status_message.emit("no design to export")
            return None
        out = export_dir(self.context)
        path = out / f"{design['design_id']}_build_sheet.pdf"
        receipt = render_build_sheet_pdf(design, path)
        self._exports["build_sheet"] = path
        write_receipt(receipt,
                      out / f"{design['design_id']}_build.receipt.json")
        record_export_safe(self.context, "design_studio_pdf", path)
        self.status_message.emit(f"build sheet written: {path}")
        return path

    def inspector_info(self):
        d = self._design or {}
        g = d.get("holder_geometry", {})
        return {"properties": {
                    "design": d.get("design_id", "—"),
                    "source specimen": d.get("source_specimen_id", "—"),
                    "cavity (mm)": (f"{g.get('cavity_length_mm', 0):g} × "
                                    f"{g.get('cavity_width_mm', 0):g}"
                                    if g else "—"),
                    "OpenSCAD": ("available" if openscad_available()
                                 else "not installed (STL unavailable)"),
                    "exports": ", ".join(sorted(self._exports)) or "none"},
                "classification": MODEL_OUTPUT,
                "units": "mm",
                "provenance": claim_boundary("build_sheet")}
