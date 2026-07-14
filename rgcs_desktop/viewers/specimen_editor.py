"""Specimen / geometry editor: crystal and spiral forms, derived quantities,
SCAD export preview (text) and a 2D projection preview (pyqtgraph).

Binding display rules: node positions use 'not measured' when
measured_node_mm is None; axial half-wave renders as an interval
(UncertainValue); default angles carry a Source-claim note.
"""
from __future__ import annotations

import json
import math

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QComboBox, QDoubleSpinBox, QFormLayout,
                               QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                               QPlainTextEdit, QPushButton, QSpinBox,
                               QSplitter, QTabWidget, QVBoxLayout, QWidget)

from rgcs_core.geometry import (CrystalGeometry, SpiralGeometry,
                                crystal_geometry, node_positions,
                                spiral_curve, spiral_metrics)
from rgcs_core.harmonics import axial_half_wave

from rgcs_desktop.plots import make_plot, plot_series
from rgcs_desktop.services.formatting import (format_node_mm,
                                              format_uncertain)
from rgcs_desktop.services.scad import crystal_scad, spiral_scad
from rgcs_desktop.viewers.base import Panel
from rgcs_desktop.widgets import ClassificationBadge, UncertainValueLabel


def _dspin(lo: float, hi: float, value: float, decimals: int = 3,
           step: float = 1.0) -> QDoubleSpinBox:
    s = QDoubleSpinBox()
    s.setRange(lo, hi)
    s.setDecimals(decimals)
    s.setSingleStep(step)
    s.setValue(value)
    return s


class SpecimenEditorPanel(Panel):
    TITLE = "Specimen editor"

    def __init__(self, context, parent=None):
        super().__init__(context, parent)
        self._last_payload: dict | None = None
        layout = QVBoxLayout(self)
        split = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(split)

        # ---- left: forms
        left = QWidget()
        lv = QVBoxLayout(left)
        self.specimen_id = QLineEdit("SP-NEW-001")
        idrow = QFormLayout()
        idrow.addRow("Specimen id", self.specimen_id)
        lv.addLayout(idrow)

        self.kind_tabs = QTabWidget()
        # crystal form
        cw = QWidget()
        cf = QFormLayout(cw)
        self.c_length = _dspin(1, 10000, 154.0)
        self.c_dw = _dspin(0.1, 1000, 34.0)
        self.c_dn = _dspin(0.1, 1000, 25.0)
        self.c_facets = QSpinBox(); self.c_facets.setRange(3, 64)
        self.c_facets.setValue(6)
        self.c_af = _dspin(0.1, 179.9, 51.843)
        self.c_am = _dspin(0.1, 179.9, 60.0)
        self.c_density = _dspin(0.01, 30, 2.65)
        self.c_dmode = QComboBox()
        self.c_dmode.addItems(["across_vertices", "across_flats"])
        self.c_amode = QComboBox()
        self.c_amode.addItems(["face_slope", "axis_to_face", "apex_included"])
        self.c_measured_node = QLineEdit()
        self.c_measured_node.setPlaceholderText(
            "measured node from female apex, mm (blank = not measured)")
        self.c_measured_mass = QLineEdit()
        self.c_measured_mass.setPlaceholderText(
            "measured mass, g (blank = not measured; required for run "
            "manifests)")
        cf.addRow("Length L (mm)", self.c_length)
        cf.addRow("Wide diameter D_w (mm)", self.c_dw)
        cf.addRow("Narrow diameter D_n (mm)", self.c_dn)
        cf.addRow("Facets N_f", self.c_facets)
        cf.addRow("Female angle (deg)", self.c_af)
        cf.addRow("Male angle (deg)", self.c_am)
        cf.addRow("Density (g/cm3)", self.c_density)
        cf.addRow("Diameter mode", self.c_dmode)
        cf.addRow("Angle mode", self.c_amode)
        cf.addRow("Measured node (mm)", self.c_measured_node)
        cf.addRow("Measured mass (g)", self.c_measured_mass)
        cf.addRow(QLabel("Note: default angles 51.843/60 deg are a "
                         "Source claim (RG-16)."))
        self.kind_tabs.addTab(cw, "Crystal")
        # spiral form
        sw = QWidget()
        sf = QFormLayout(sw)
        self.s_q = _dspin(1.0001, 100, math.e, decimals=6)
        self.s_turns = _dspin(0.1, 100, 4.0)
        self.s_r0 = _dspin(0.1, 1000, 60.0)
        self.s_h = _dspin(0.1, 1000, 80.0)
        self.s_pz = _dspin(0.01, 10, 1.5)
        self.s_omega = _dspin(0.01, 10, 1.0)
        sf.addRow("Radial ratio q per turn", self.s_q)
        sf.addRow("Turns T", self.s_turns)
        sf.addRow("Outer radius R_0 (mm)", self.s_r0)
        sf.addRow("Height H (mm)", self.s_h)
        sf.addRow("Cone exponent p_z", self.s_pz)
        sf.addRow("Phase winding Omega_s", self.s_omega)
        self.kind_tabs.addTab(sw, "Spiral cone")
        lv.addWidget(self.kind_tabs)

        btns = QHBoxLayout()
        self.compute_btn = QPushButton("Compute derived quantities")
        self.compute_btn.clicked.connect(self.compute)
        self.save_btn = QPushButton("Save specimen to workspace")
        self.save_btn.clicked.connect(self.save_specimen)
        btns.addWidget(self.compute_btn)
        btns.addWidget(self.save_btn)
        lv.addLayout(btns)

        derived_box = QGroupBox("Derived quantities")
        dv = QFormLayout(derived_box)
        self.badge = ClassificationBadge("Derived")
        dv.addRow("Classification", self.badge)
        self.mass_label = QLabel("—")
        self.volume_label = QLabel("—")
        self.node_label = QLabel("—")
        self.measured_label = QLabel("not measured")
        self.axial_label = UncertainValueLabel(unit="Hz")
        dv.addRow("Mass (g)", self.mass_label)
        dv.addRow("Volume (cm3)", self.volume_label)
        dv.addRow("Selected node (female frame)", self.node_label)
        dv.addRow("Measured node", self.measured_label)
        dv.addRow("Axial half-wave f1", self.axial_label)
        lv.addWidget(derived_box)
        lv.addStretch(1)
        split.addWidget(left)

        # ---- right: previews
        right = QTabWidget()
        self.profile_plot = make_plot("2D projection (mm)", "x (mm)", "z (mm)")
        right.addTab(self.profile_plot, "Projection preview")
        self.scad_view = QPlainTextEdit()
        self.scad_view.setReadOnly(True)
        right.addTab(self.scad_view, "SCAD export preview")
        split.addWidget(right)
        self.compute()

    # ---- geometry construction ------------------------------------------
    def crystal(self) -> CrystalGeometry:
        return CrystalGeometry(
            length_mm=self.c_length.value(),
            wide_diameter_mm=self.c_dw.value(),
            narrow_diameter_mm=self.c_dn.value(),
            facets=self.c_facets.value(),
            female_angle_deg=self.c_af.value(),
            male_angle_deg=self.c_am.value(),
            density_g_cm3=self.c_density.value(),
            diameter_mode=self.c_dmode.currentText(),
            angle_mode=self.c_amode.currentText())

    def spiral(self) -> SpiralGeometry:
        return SpiralGeometry(
            q_per_turn=self.s_q.value(), turns=self.s_turns.value(),
            outer_radius_mm=self.s_r0.value(), height_mm=self.s_h.value(),
            cone_exponent=self.s_pz.value(),
            phase_winding=self.s_omega.value())

    def _measured_node(self) -> float | None:
        text = self.c_measured_node.text().strip()
        return float(text) if text else None

    # ---- actions -----------------------------------------------------------
    def compute(self) -> dict:
        if self.kind_tabs.currentIndex() == 0:
            payload = self._compute_crystal()
        else:
            payload = self._compute_spiral()
        self._last_payload = payload
        self.inspector_changed.emit()
        return payload

    def _compute_crystal(self) -> dict:
        g = self.crystal()
        d = crystal_geometry(g)
        nodes = node_positions(g.length_mm, d["female_height_mm"],
                               d["male_height_mm"],
                               measured_from_female_mm=self._measured_node())
        f1 = axial_half_wave(g.length_mm)
        self.badge.set_classification(d["classification"])
        self.mass_label.setText(f"{d['mass_g']:.2f}")
        self.volume_label.setText(f"{d['volume_cm3']:.3f}")
        self.node_label.setText(
            f"{format_node_mm(nodes['selected_node_mm'])} "
            f"({nodes['selected_source']})")
        # measured_node_mm may be None: 'not measured', never NaN
        self.measured_label.setText(format_node_mm(nodes["measured_node_mm"]))
        self.axial_label.set_value(f1)  # interval, never a bare point
        self.scad_view.setPlainText(crystal_scad(g))
        self._plot_crystal(g, d, nodes)
        mass_text = self.c_measured_mass.text().strip()
        return {
            "kind": "crystal", "specimen_id": self.specimen_id.text(),
            "material": "alpha-quartz",
            "mass_measured_g": float(mass_text) if mass_text else None,
            "mass_predicted_g": d["mass_g"],
            "geometry": g.model_dump(),
            "derived": {"crystal": d, "node_positions": nodes,
                        "axial_half_wave": f1.to_dict()},
            "classification": d["classification"],
        }

    def _compute_spiral(self) -> dict:
        g = self.spiral()
        m = spiral_metrics(g)
        self.badge.set_classification(m["classification"])
        self.mass_label.setText("n/a (path resonator)")
        self.volume_label.setText("n/a")
        self.node_label.setText(
            f"path length {m['path_length_3d_mm']:.2f} mm")
        self.measured_label.setText("not measured")
        f1 = axial_half_wave(m["path_length_3d_mm"])
        self.axial_label.set_value(f1)
        self.scad_view.setPlainText(spiral_scad(g))
        self._plot_spiral(g)
        return {
            "kind": "spiral", "specimen_id": self.specimen_id.text(),
            "material": "conductor path",
            "geometry": g.model_dump(),
            "derived": {"spiral_metrics": m,
                        "path_half_wave": f1.to_dict()},
            "classification": m["classification"],
        }

    def save_specimen(self) -> str:
        payload = self.compute()
        object_id = self.context.workspace.put_object(
            "specimen", payload["specimen_id"], payload,
            object_id=f"specimen-{payload['specimen_id']}", overwrite=True)
        self.status_message.emit(f"saved specimen {object_id}")
        self.context.notify_workspace_changed()
        return object_id

    # ---- previews ---------------------------------------------------------
    def _plot_crystal(self, g: CrystalGeometry, d: dict, nodes: dict) -> None:
        self.profile_plot.clear()
        h_f, h_m = d["female_height_mm"], d["male_height_mm"]
        rw, rn = g.wide_diameter_mm / 2, g.narrow_diameter_mm / 2
        z = [0, h_f, g.length_mm - h_m, g.length_mm]
        xr = [0, rw, rn, 0]
        xl = [0, -rw, -rn, 0]
        plot_series(self.profile_plot, xr, z, color="#1258a8", width=2)
        plot_series(self.profile_plot, xl, z, color="#1258a8", width=2)
        sel = nodes["selected_node_mm"]
        plot_series(self.profile_plot, [-rw, rw], [sel, sel],
                    color="#b26a00", width=2)

    def _plot_spiral(self, g: SpiralGeometry) -> None:
        self.profile_plot.clear()
        c = spiral_curve(g, samples=600)
        plot_series(self.profile_plot, c["x"], c["y"],
                    color="#1258a8", width=1.5)

    def inspector_info(self):
        p = self._last_payload or {}
        derived = p.get("derived", {})
        props = {"specimen_id": p.get("specimen_id", ""),
                 "kind": p.get("kind", "")}
        if "node_positions" in derived:
            n = derived["node_positions"]
            props["selected_node_mm"] = format_node_mm(n["selected_node_mm"])
            props["measured_node_mm"] = format_node_mm(n["measured_node_mm"])
        if "axial_half_wave" in derived:
            props["axial_half_wave"] = format_uncertain(
                derived["axial_half_wave"], "Hz")
        return {"properties": props,
                "classification": p.get("classification", "Derived"),
                "units": "mm, g, cm3, Hz (docs/NOTATION_AND_UNITS.md)",
                "provenance": "rgcs_core.geometry / harmonics "
                              "(registry ids in classification string)"}
