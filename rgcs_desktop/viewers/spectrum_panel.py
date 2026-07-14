"""Compact-mode spectrum panel: rgcs_core.compact_modes with 1-sigma bands.

Hypothesis H-01 content — badge is mandatory; frequencies are
UncertainValue and are rendered as intervals/bands only.
"""
from __future__ import annotations

from PySide6.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox,
                               QFormLayout, QGroupBox, QHBoxLayout, QLabel,
                               QPushButton, QSpinBox, QVBoxLayout, QWidget)

from rgcs_core.compact_modes import compact_mode_spectrum
from rgcs_core.uncertainty import (DEFAULT_WAVE_SPEED_M_S,
                                   DEFAULT_WAVE_SPEED_U_REL, UncertainValue)

from rgcs_desktop.plots import make_plot, plot_spectrum_with_bands
from rgcs_desktop.services.formatting import format_uncertain
from rgcs_desktop.viewers.base import Panel
from rgcs_desktop.widgets import ClassificationBadge, UncertainValueLabel


class SpectrumPanel(Panel):
    TITLE = "Compact-mode spectrum"

    def __init__(self, context, parent=None):
        super().__init__(context, parent)
        self._spectrum: dict | None = None
        layout = QHBoxLayout(self)
        controls = QGroupBox("Parameters")
        form = QFormLayout(controls)
        self.f_b = QDoubleSpinBox()
        self.f_b.setRange(0, 1e6); self.f_b.setValue(4096.0)
        self.u_f_b = QDoubleSpinBox()
        self.u_f_b.setRange(0, 1e5); self.u_f_b.setValue(0.5)
        self.v_chi = QDoubleSpinBox()
        self.v_chi.setRange(1, 1e5); self.v_chi.setValue(DEFAULT_WAVE_SPEED_M_S)
        self.u_v_rel = QDoubleSpinBox()
        self.u_v_rel.setDecimals(3); self.u_v_rel.setRange(0, 1)
        self.u_v_rel.setSingleStep(0.01)
        self.u_v_rel.setValue(DEFAULT_WAVE_SPEED_U_REL)
        self.radius = QDoubleSpinBox()
        self.radius.setRange(0.1, 1e4); self.radius.setValue(100.0)
        self.n_max = QSpinBox(); self.n_max.setRange(1, 64)
        self.n_max.setValue(8)
        self.parity = QComboBox()
        self.parity.addItems(["all", "odd", "even"])
        self.zero_mode = QCheckBox("include zero mode (n = 0)")
        self.zero_mode.setChecked(True)
        form.addRow("Base frequency f_b (Hz)", self.f_b)
        form.addRow("u(f_b) (Hz)", self.u_f_b)
        form.addRow("Compact wave speed v_chi (m/s)", self.v_chi)
        form.addRow("u_rel(v_chi)", self.u_v_rel)
        form.addRow("Compact radius R_chi (mm)", self.radius)
        form.addRow("n_max", self.n_max)
        form.addRow("Parity", self.parity)
        form.addRow(self.zero_mode)
        form.addRow(QLabel("Note: the 100 mm default radius is a "
                           "placeholder (D-21)."))
        self.compute_btn = QPushButton("Compute spectrum")
        self.compute_btn.clicked.connect(self.compute)
        form.addRow(self.compute_btn)
        self.badge = ClassificationBadge("Hypothesis")
        form.addRow("Classification", self.badge)
        self.kappa_label = UncertainValueLabel(unit="Hz")
        form.addRow("kappa_chi", self.kappa_label)
        self.zero_label = QLabel("—")
        form.addRow("Zero mode present", self.zero_label)
        layout.addWidget(controls)

        self.plot = make_plot("Compact-mode spectrum (1σ bands)",
                              "mode index n", "frequency (Hz)")
        layout.addWidget(self.plot, stretch=1)
        self.compute()

    def compute(self) -> dict:
        v = UncertainValue(self.v_chi.value(), self.u_v_rel.value())
        spec = compact_mode_spectrum(
            base_frequency_hz=self.f_b.value(),
            v_chi=v,
            compact_radius_mm=self.radius.value(),
            n_max=self.n_max.value(),
            parity=self.parity.currentText(),
            include_zero_mode=self.zero_mode.isChecked(),
            u_base_frequency_hz=self.u_f_b.value())
        self._spectrum = spec
        self.badge.set_classification(
            str(spec.get("classification", "Hypothesis H-01")))
        self.kappa_label.set_value(spec["kappa_chi_hz"])
        self.zero_label.setText(str(spec["zero_mode_present"]))
        plot_spectrum_with_bands(self.plot, spec["modes"])
        self.inspector_changed.emit()
        return spec

    @property
    def spectrum(self) -> dict | None:
        return self._spectrum

    def save_result(self) -> str | None:
        """Store the current spectrum as a workspace artifact."""
        if self._spectrum is None or self.context.workspace is None:
            return None
        art = self.context.workspace.write_artifact(
            {"kind": "compact_mode_spectrum", "spectrum": self._spectrum},
            kind="result")
        self.context.workspace.put_object(
            "result", "compact-mode spectrum",
            {"artifact_id": art["artifact_id"], "sha256": art["sha256"],
             "classification": str(self._spectrum.get("classification"))},
            object_id=f"result-{art['artifact_id']}", overwrite=True)
        self.context.notify_workspace_changed()
        return art["artifact_id"]

    def inspector_info(self):
        s = self._spectrum or {}
        props = {"f_b (Hz)": s.get("base_frequency_hz"),
                 "parity": s.get("parity"),
                 "zero mode": s.get("zero_mode_present")}
        if "kappa_chi_hz" in s:
            props["kappa_chi"] = format_uncertain(s["kappa_chi_hz"], "Hz")
        return {"properties": props,
                "classification": str(s.get("classification",
                                            "Hypothesis H-01")),
                "units": "Hz (frequencies), mm (radius), m/s (wave speed)",
                "provenance": "rgcs_core.compact_modes (RGCS-M.13/M.15/M.17)"}
