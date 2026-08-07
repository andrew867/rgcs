"""Annular Ring Designer panel: ring geometry, masks, probes, diagrams,
and engineering-sheet export. Defaults to the RGCS 37-cell fixture."""
from __future__ import annotations

from PySide6.QtWidgets import (QDoubleSpinBox, QFormLayout, QGroupBox,
                               QHBoxLayout, QLabel, QLineEdit,
                               QPlainTextEdit, QPushButton, QSpinBox,
                               QVBoxLayout)

from rgcs_core.provenance import json_dumps

from rgcs_desktop.services.annular_ring import (
    RingError, active_cells, derive_ring_cells, render_engineering_pdf,
    render_ring_scad, render_ring_svg, validate_active_mask,
    write_active_mask_csv, write_phase_map_csv)
from rgcs_desktop.services.design_studio import (MODEL_OUTPUT,
                                                 claim_boundary,
                                                 new_object_id)
from rgcs_desktop.services.export_receipts import write_receipt
from rgcs_desktop.viewers.base import Panel
from rgcs_desktop.viewers.design_studio_common import (
    export_dir, record_export_safe, studio_state)
from rgcs_desktop.widgets import ClassificationBadge


class AnnularRingPanel(Panel):
    TITLE = "Annular Ring Designer"

    def __init__(self, context, parent=None):
        super().__init__(context, parent)
        self._design: dict | None = None
        self._last_error: str | None = None

        layout = QHBoxLayout(self)
        left = QVBoxLayout()

        geo_box = QGroupBox("Ring geometry (RGCS default fixture)")
        form = QFormLayout(geo_box)
        self.od = QDoubleSpinBox()
        self.od.setRange(10.0, 5000.0)
        self.od.setValue(288.0)
        form.addRow("Outer diameter (mm)", self.od)
        self.idm = QDoubleSpinBox()
        self.idm.setRange(1.0, 5000.0)
        self.idm.setValue(188.0)
        form.addRow("Inner diameter (mm)", self.idm)
        self.cells = QSpinBox()
        self.cells.setRange(3, 720)
        self.cells.setValue(37)
        form.addRow("Cell count", self.cells)
        self.blanked = QLineEdit("33, 34, 35, 36")
        form.addRow("Blanked cells", self.blanked)
        self.probes = QLineEdit("P1:0, P2:9, P3:18")
        form.addRow("Probes (label:cell)", self.probes)
        self.base_hz = QDoubleSpinBox()
        self.base_hz.setRange(1.0, 1e6)
        self.base_hz.setDecimals(3)
        self.base_hz.setValue(4096.0)
        form.addRow("Drive base (Hz)", self.base_hz)
        self.key_hz = QDoubleSpinBox()
        self.key_hz.setRange(0.0, 1e6)
        self.key_hz.setDecimals(3)
        self.key_hz.setValue(925.0)
        form.addRow("Modulation key (Hz)", self.key_hz)
        self.material = QLineEdit("FR4")
        form.addRow("Material", self.material)
        left.addWidget(geo_box)

        self.badge = ClassificationBadge(MODEL_OUTPUT)
        left.addWidget(self.badge)
        self.compute_btn = QPushButton("Validate ring")
        self.compute_btn.clicked.connect(self.compute)
        left.addWidget(self.compute_btn)
        self.export_btn = QPushButton(
            "Export ring pack (SVG + SCAD + CSV + PDF)")
        self.export_btn.clicked.connect(self.export_all)
        left.addWidget(self.export_btn)
        left.addStretch(1)
        layout.addLayout(left)

        right = QVBoxLayout()
        self.status = QLabel("37 cells, 33 active, 4 blanked — the default "
                             "RGCS prototype fixture.")
        self.status.setWordWrap(True)
        right.addWidget(self.status)
        self.detail = QPlainTextEdit()
        self.detail.setReadOnly(True)
        right.addWidget(self.detail, stretch=1)
        layout.addLayout(right, stretch=1)

        for w in (self.od, self.idm, self.base_hz, self.key_hz):
            w.valueChanged.connect(self.compute)
        self.cells.valueChanged.connect(self.compute)
        self.blanked.textChanged.connect(self.compute)
        self.probes.textChanged.connect(self.compute)
        self.compute()

    # -- parsing -----------------------------------------------------------
    def _parse_blanked(self) -> list[int]:
        out = []
        for token in self.blanked.text().split(","):
            token = token.strip()
            if token.isdigit():
                out.append(int(token))
        return sorted(set(out))

    def _parse_probes(self) -> list[dict]:
        probes = []
        for token in self.probes.text().split(","):
            token = token.strip()
            if ":" in token:
                label, _, cell = token.partition(":")
                if cell.strip().isdigit():
                    probes.append({"label": label.strip(),
                                   "cell": int(cell.strip())})
        return probes

    def current_design(self) -> dict | None:
        return self._design

    # -- compute -----------------------------------------------------------
    def compute(self, *_a) -> dict | None:
        n = self.cells.value()
        blanked = [b for b in self._parse_blanked() if b < n]
        mask = [i not in blanked for i in range(n)]
        design_id = (self._design or {}).get("design_id") \
            or new_object_id("RING")
        design = {
            "schema_version": "1.0.0",
            "design_id": design_id,
            "od_mm": self.od.value(),
            "id_mm": self.idm.value(),
            "cell_count": n,
            "active_mask": mask,
            "blanked_cells": blanked,
            "probe_plan": {"probes": [p for p in self._parse_probes()
                                      if p["cell"] < n]},
            "drive": {"base_hz": self.base_hz.value(),
                      "modulation_key_hz": self.key_hz.value()},
            "material": self.material.text().strip() or "unspecified",
            "classification": MODEL_OUTPUT,
        }
        try:
            cells = derive_ring_cells(design["od_mm"], design["id_mm"], n)
            validate_active_mask(mask, n)
            act = active_cells(design)
        except RingError as exc:
            self._last_error = str(exc)
            self._design = None
            self.status.setText(f"Refused: {exc}")
            self.status_message.emit(f"ring design refused: {exc}")
            self.detail.setPlainText("")
            self.inspector_changed.emit()
            return None
        self._last_error = None
        self._design = design
        studio_state(self.context)["ring_design"] = design
        span = float(cells[0]["span_deg_exact"])
        self.status.setText(
            f"{n} cells × {span:.4f}° close exactly · {len(act)} active, "
            f"{len(blanked)} blanked · annulus width "
            f"{(design['od_mm'] - design['id_mm']) / 2:g} mm")
        self.detail.setPlainText(
            json_dumps({k: v for k, v in design.items()
                        if k != "active_mask"},
                       indent=2, sort_keys=True))
        self.inspector_changed.emit()
        return design

    # -- exports -----------------------------------------------------------
    def export_all(self) -> dict:
        design = self._design or self.compute()
        if design is None:
            self.status_message.emit(
                f"export blocked: {self._last_error or 'no design'}")
            return {}
        out = export_dir(self.context)
        did = design["design_id"]
        svg_receipt = render_ring_svg(design, out / f"{did}_ring.svg")
        scad_path = out / f"{did}.scad"
        scad_path.parent.mkdir(parents=True, exist_ok=True)
        scad_path.write_text(render_ring_scad(design), encoding="utf-8")
        phase = write_phase_map_csv(design, out / f"{did}_phase_map.csv")
        mask = write_active_mask_csv(design, out / f"{did}_active_mask.csv")
        pdf_receipt = render_engineering_pdf(
            design, out / f"{did}_engineering_sheet.pdf")
        write_receipt(pdf_receipt, out / f"{did}.receipt.json")
        exports = {"svg": out / f"{did}_ring.svg", "scad": scad_path,
                   "phase_csv": phase, "mask_csv": mask,
                   "pdf": out / f"{did}_engineering_sheet.pdf",
                   "receipt": out / f"{did}.receipt.json"}
        for kind, path in (("design_studio_svg", exports["svg"]),
                           ("design_studio_scad", scad_path),
                           ("design_studio_pdf", exports["pdf"])):
            record_export_safe(self.context, kind, path)
        self.status_message.emit(
            f"ring pack exported ({len(exports)} files) -> {out}")
        self.inspector_changed.emit()
        assert svg_receipt["outputs"]
        return exports

    def inspector_info(self):
        d = self._design or {}
        return {"properties": {
                    "design": d.get("design_id", "—"),
                    "OD / ID (mm)": (f"{d.get('od_mm')} / {d.get('id_mm')}"
                                     if d else "—"),
                    "cells": d.get("cell_count"),
                    "active": (len(active_cells(d)) if d else None),
                    "blanked": len(d.get("blanked_cells", [])),
                    "refusal": self._last_error or "none"},
                "classification": MODEL_OUTPUT,
                "units": "mm / deg / Hz",
                "provenance": claim_boundary("ring_design")}
