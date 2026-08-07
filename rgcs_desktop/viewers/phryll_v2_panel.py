"""Phryll Generator Designer v2 panel: crystal-first parametric CAD.

Enter measured crystal dimensions + Eye coordinate, choose fit and coil
settings, generate the custom cone + coil sleeve, inspect fit and Eye
alignment, export the full bundle. Reference profiles are advisory —
the generated geometry is primary and never a scaled stock mesh."""
from __future__ import annotations

from PySide6.QtWidgets import (QComboBox, QDoubleSpinBox, QFormLayout,
                               QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                               QPlainTextEdit, QPushButton, QSpinBox,
                               QVBoxLayout)

from rgcs_core.provenance import json_dumps

from rgcs_desktop.services.design_studio import MODEL_OUTPUT
from rgcs_desktop.services.phryll_v2.coil_sleeve import (
    AWG_DIAMETER_MM, CoilSleeveError, generate_crossed_coil_paths)
from rgcs_desktop.services.phryll_v2.cone_generator import make_cone_design
from rgcs_desktop.services.phryll_v2.crystal_profile import (
    ProfileError, normalize_crystal_profile, validate_eye_coordinate)
from rgcs_desktop.services.phryll_v2.pipeline import generate_full_design
from rgcs_desktop.viewers.base import Panel
from rgcs_desktop.viewers.design_studio_common import (export_dir,
                                                       record_export_safe,
                                                       studio_state)
from rgcs_desktop.widgets import ClassificationBadge

BOUNDARY = ("Generated geometry is a model output and engineering "
            "plan. Reference profiles are advisory. Source-language "
            "pulse notes are recorded, not validated.")


class PhryllV2Panel(Panel):
    TITLE = "Phryll Generator v2"

    def __init__(self, context, parent=None):
        super().__init__(context, parent)
        self._crystal = None
        self._cone = None
        self._coil = None
        self._last_bundle = None
        self._last_error: str | None = None

        layout = QHBoxLayout(self)
        left = QVBoxLayout()

        crystal_box = QGroupBox("Crystal profile (measured)")
        form = QFormLayout(crystal_box)
        self.crystal_id = QLineEdit("CRY-DEMO-120")
        form.addRow("Crystal ID", self.crystal_id)
        self.length = QDoubleSpinBox()
        self.length.setRange(10.0, 500.0)
        self.length.setValue(120.0)
        form.addRow("Length (mm)", self.length)
        self.top_d = QDoubleSpinBox()
        self.top_d.setRange(1.0, 200.0)
        self.top_d.setValue(26.0)
        form.addRow("Top diameter (mm, 60° end)", self.top_d)
        self.base_d = QDoubleSpinBox()
        self.base_d.setRange(1.0, 200.0)
        self.base_d.setValue(39.0)
        form.addRow("Base diameter (mm, 52° end)", self.base_d)
        self.max_w = QDoubleSpinBox()
        self.max_w.setRange(1.0, 200.0)
        self.max_w.setValue(39.0)
        form.addRow("Max body width (mm)", self.max_w)
        self.facets = QSpinBox()
        self.facets.setRange(3, 24)
        self.facets.setValue(6)
        form.addRow("Facet count", self.facets)
        self.z_eye = QDoubleSpinBox()
        self.z_eye.setRange(0.0, 500.0)
        self.z_eye.setDecimals(2)
        self.z_eye.setValue(62.5)
        form.addRow("Eye coordinate z (mm)", self.z_eye)
        self.eye_unc = QDoubleSpinBox()
        self.eye_unc.setRange(0.0, 20.0)
        self.eye_unc.setDecimals(2)
        self.eye_unc.setValue(0.25)
        form.addRow("Eye uncertainty (mm)", self.eye_unc)
        left.addWidget(crystal_box)

        fit_box = QGroupBox("Fit + coil settings")
        fform = QFormLayout(fit_box)
        self.clearance = QDoubleSpinBox()
        self.clearance.setRange(0.2, 5.0)
        self.clearance.setSingleStep(0.02)
        self.clearance.setValue(0.66)
        fform.addRow("Clearance (mm)", self.clearance)
        self.wall = QDoubleSpinBox()
        self.wall.setRange(0.5, 10.0)
        self.wall.setSingleStep(0.1)
        self.wall.setValue(1.8)
        fform.addRow("Wall (mm)", self.wall)
        self.gauge = QComboBox()
        for awg in sorted(AWG_DIAMETER_MM):
            self.gauge.addItem(f"AWG {awg} "
                               f"({AWG_DIAMETER_MM[awg]:g} mm)", awg)
        self.gauge.setCurrentText("AWG 28 (0.33 mm)")
        fform.addRow("Wire", self.gauge)
        self.groove_depth = QDoubleSpinBox()
        self.groove_depth.setRange(0.0, 2.0)
        self.groove_depth.setSingleStep(0.05)
        self.groove_depth.setValue(0.25)
        fform.addRow("Groove depth (mm)", self.groove_depth)
        left.addWidget(fit_box)

        self.badge = ClassificationBadge(MODEL_OUTPUT)
        left.addWidget(self.badge)
        self.generate_btn = QPushButton("Generate cone + coil sleeve")
        self.generate_btn.clicked.connect(self.generate)
        left.addWidget(self.generate_btn)
        self.export_btn = QPushButton(
            "Export bundle (SCAD/STL/3MF/DXF/SVG/PDF/JSON)")
        self.export_btn.clicked.connect(self.export_bundle)
        left.addWidget(self.export_btn)
        left.addStretch(1)
        layout.addLayout(left)

        right = QVBoxLayout()
        self.status = QLabel("Enter measured crystal dimensions and the "
                             "Eye coordinate, then Generate.")
        self.status.setWordWrap(True)
        right.addWidget(self.status)
        self.detail = QPlainTextEdit()
        self.detail.setReadOnly(True)
        right.addWidget(self.detail, stretch=1)
        note = QLabel(BOUNDARY)
        note.setWordWrap(True)
        note.setStyleSheet("color: #555; font-style: italic;")
        right.addWidget(note)
        layout.addLayout(right, stretch=1)

        for w in (self.length, self.top_d, self.base_d, self.max_w,
                  self.z_eye, self.eye_unc, self.clearance, self.wall,
                  self.groove_depth):
            w.valueChanged.connect(self._invalidate)
        self.facets.valueChanged.connect(self._invalidate)

    # ------------------------------------------------------------------
    def _invalidate(self, *_a) -> None:
        self._cone = None
        self._coil = None

    def raw_crystal(self) -> dict:
        return {
            "schema_version": "2.0.0",
            "crystal_id": self.crystal_id.text().strip() or "CRY-NEW",
            "length_mm": self.length.value(),
            "top_diameter_mm": self.top_d.value(),
            "base_diameter_mm": self.base_d.value(),
            "max_body_width_mm": self.max_w.value(),
            "facet_count": self.facets.value(),
            "z_eye_mm": self.z_eye.value(),
            "eye_source": "user_entered",
            "eye_uncertainty_mm": self.eye_unc.value(),
            "uncertainty": {"length_mm": 0.5, "diameter_mm": 0.2},
            "provenance": {"entered_by": "Design Studio",
                           "panel": self.TITLE},
        }

    def fit_settings(self) -> dict:
        return {"clearance_mm": self.clearance.value(),
                "wall_thickness_mm": self.wall.value(),
                "print_tolerance_mm": 0.2}

    def coil_settings(self) -> dict:
        awg = self.gauge.currentData()
        return {"wire_gauge": f"AWG{awg}",
                "wire_diameter_mm": AWG_DIAMETER_MM[awg],
                "groove_depth_mm": self.groove_depth.value()}

    def generate(self, *_a):
        try:
            self._crystal = normalize_crystal_profile(self.raw_crystal())
            self._cone = make_cone_design(self._crystal,
                                          self.fit_settings())
            self._coil = generate_crossed_coil_paths(
                self._crystal, self._cone, self.coil_settings())
        except (ProfileError, CoilSleeveError) as exc:
            self._last_error = str(exc)
            self._cone = self._coil = None
            self.status.setText(f"Refused: {exc}")
            self.status_message.emit(f"phryll v2 refused: {exc}")
            self.detail.setPlainText("")
            self.inspector_changed.emit()
            return None
        self._last_error = None
        eye_check = validate_eye_coordinate(self._crystal)
        dims = self._cone.generated_dimensions
        eye = self._coil["eye_alignment"]
        spacing = self._coil["spacing"]
        self.status.setText(
            f"inner {dims['inner_base_diameter_mm']:g} → "
            f"{dims['inner_top_diameter_mm']:g} mm · outer "
            f"{dims['outer_base_diameter_mm']:g} → "
            f"{dims['outer_top_diameter_mm']:g} mm · fit "
            f"{'PASS' if self._cone.fit_report.ok else 'FAIL'} · Eye "
            f"crossing at {eye['z_cross_mm']:g} mm (residual "
            f"{eye['alignment_error_mm']:g} mm) · pitch "
            f"{spacing['groove_pitch_mm']:g} mm"
            + (f" · note: {'; '.join(eye_check.reasons)}"
               if eye_check.reasons else ""))
        self.detail.setPlainText(
            json_dumps({"cone": self._cone.to_json(),
                        "coil": self._coil}, indent=2, sort_keys=True))
        studio_state(self.context)["phryll_v2_design"] = {
            "cone": self._cone.to_json(), "coil": self._coil}
        self.inspector_changed.emit()
        return self._cone

    def export_bundle(self, *_a):
        if self._cone is None and self.generate() is None:
            self.status_message.emit(
                f"export blocked: {self._last_error or 'no design'}")
            return None
        out = export_dir(self.context) / "phryll_v2"
        result = generate_full_design(self.raw_crystal(), out,
                                      fit_settings=self.fit_settings(),
                                      coil_settings=self.coil_settings())
        self._last_bundle = result["bundle"]
        record_export_safe(self.context, "phryll_v2_bundle",
                           result["bundle"] / "MANIFEST.json")
        check = result["verification"]
        self.status_message.emit(
            f"phryll v2 bundle exported: {result['bundle']} — "
            f"{'OK' if check['ok'] else 'CHECKSUM MISMATCH'} "
            f"({check['n_members']} files, OpenSCAD "
            f"{result['openscad_status']})")
        self.inspector_changed.emit()
        return result

    def inspector_info(self):
        eye = (self._coil or {}).get("eye_alignment", {})
        spacing = (self._coil or {}).get("spacing", {})
        return {"properties": {
                    "crystal": (self._crystal.crystal_id
                                if self._crystal else "—"),
                    "fit": ("PASS" if self._cone
                            and self._cone.fit_report.ok else "—"),
                    "Eye residual (mm)":
                        eye.get("alignment_error_mm"),
                    "coil center standoff (mm)":
                        spacing.get("coil_center_standoff_mm"),
                    "groove pitch (mm)":
                        spacing.get("groove_pitch_mm"),
                    "last bundle": str(self._last_bundle or "—"),
                    "refusal": self._last_error or "none"},
                "classification": MODEL_OUTPUT,
                "units": "mm",
                "provenance": BOUNDARY}
