"""Experiment builder: generates run manifests and validates them against
the JSON-schema set (same registry as experiments/schemas/validate.py).

Gates surfaced live: schema validity, coherence-claim gate
(post_drive_ratio >= 2.5 and n_runs >= 100) and the human-loading ethics
block. Unknown major schema_version is refused at validation.
"""
from __future__ import annotations

import json

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox,
                               QFormLayout, QGroupBox, QHBoxLayout, QLabel,
                               QLineEdit, QPlainTextEdit, QPushButton,
                               QSpinBox, QSplitter, QVBoxLayout, QWidget)

from rgcs_desktop.services.gates import all_gates
from rgcs_desktop.services.manifests import (build_run_manifest,
                                             specimen_record_from_payload)
from rgcs_desktop.services.schemas import validate_instance
from rgcs_desktop.viewers.base import Panel
from rgcs_desktop.widgets import ClassificationBadge

BRANCHES = ["modal_survey", "electrode_pulse", "sound_key", "opposed_coil",
            "human_loading", "spiral_cone", "water", "spatial_mapping"]
CONTROL_ROLES = ["active", "instrument_only", "no_specimen", "dummy_load",
                 "sham", "matched_control", "off_frequency",
                 "positive_injection"]


class ExperimentBuilderPanel(Panel):
    TITLE = "Experiment builder"

    def __init__(self, context, parent=None):
        super().__init__(context, parent)
        self._manifest: dict | None = None
        self._errors: list[str] = []
        layout = QVBoxLayout(self)
        split = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(split)

        left = QWidget()
        form = QFormLayout(left)
        self.run_id = QLineEdit("RUN-NEW-0001")
        self.branch = QComboBox(); self.branch.addItems(BRANCHES)
        self.hypotheses = QLineEdit("H-01")
        self.operator = QLineEdit("OP-01")
        self.control_role = QComboBox()
        self.control_role.addItems(CONTROL_ROLES)
        self.specimen_combo = QComboBox()
        form.addRow("Run id (RUN-…)", self.run_id)
        form.addRow("Protocol branch", self.branch)
        form.addRow("Hypothesis ids (comma)", self.hypotheses)
        form.addRow("Operator id", self.operator)
        form.addRow("Control role", self.control_role)
        form.addRow("Specimen", self.specimen_combo)

        drv = QGroupBox("Drive")
        df = QFormLayout(drv)
        self.drive_type = QComboBox()
        self.drive_type.addItems(["impulse_tap", "electrode_pulse",
                                  "acoustic_tone", "coil_pulse", "none"])
        self.session_s = QDoubleSpinBox()
        self.session_s.setRange(0.001, 1e5); self.session_s.setValue(60.0)
        self.drive_off_s = QDoubleSpinBox()
        self.drive_off_s.setDecimals(4)
        self.drive_off_s.setRange(0.0, 1e5); self.drive_off_s.setValue(30.0)
        df.addRow("Drive type", self.drive_type)
        df.addRow("Session duration (s)", self.session_s)
        df.addRow("Drive-off time (s)", self.drive_off_s)
        form.addRow(drv)

        acq = QGroupBox("Acquisition")
        af = QFormLayout(acq)
        self.fs = QDoubleSpinBox()
        self.fs.setRange(1, 1e7); self.fs.setValue(32768.0)
        self.duration_s = QDoubleSpinBox()
        self.duration_s.setRange(0.001, 1e5); self.duration_s.setValue(120.0)
        self.n_runs = QSpinBox()
        self.n_runs.setRange(1, 100000); self.n_runs.setValue(100)
        self.single_shot = QCheckBox("single shot")
        af.addRow("Sample rate (Hz)", self.fs)
        af.addRow("Acquisition duration (s)", self.duration_s)
        af.addRow("n_runs", self.n_runs)
        af.addRow(self.single_shot)
        form.addRow(acq)

        self.data_csv = QLineEdit()
        self.data_csv.setPlaceholderText(
            "time-series CSV path (required: a run without data files "
            "does not exist for analysis)")
        form.addRow("Data file (CSV)", self.data_csv)

        eth = QGroupBox("Human loading (ethics block, hard gate)")
        ef = QFormLayout(eth)
        self.ethics_ref = QLineEdit()
        self.ethics_ref.setPlaceholderText("ethics review reference")
        self.no_contact = QCheckBox("no energized contact confirmed")
        ef.addRow("Ethics review ref", self.ethics_ref)
        ef.addRow(self.no_contact)
        form.addRow(eth)

        btns = QHBoxLayout()
        self.build_btn = QPushButton("Build + validate manifest")
        self.build_btn.clicked.connect(self.build_and_validate)
        self.save_btn = QPushButton("Save experiment")
        self.save_btn.clicked.connect(self.save_experiment)
        self.save_btn.setEnabled(False)
        btns.addWidget(self.build_btn)
        btns.addWidget(self.save_btn)
        form.addRow(btns)
        split.addWidget(left)

        right = QWidget()
        rv = QVBoxLayout(right)
        self.badge = ClassificationBadge(
            "Derived (manifest structure; embedded values keep their own "
            "labels)")
        rv.addWidget(self.badge)
        self.validation_label = QLabel("not validated yet")
        self.validation_label.setWordWrap(True)
        rv.addWidget(self.validation_label)
        self.gates_label = QLabel("")
        self.gates_label.setWordWrap(True)
        rv.addWidget(self.gates_label)
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        rv.addWidget(self.preview)
        split.addWidget(right)
        self.refresh()

    # -- data ----------------------------------------------------------
    def refresh(self) -> None:
        ws = self.context.workspace
        self.specimen_combo.clear()
        if ws is None:
            return
        for o in ws.list_objects("specimen"):
            self.specimen_combo.addItem(o["name"], o["object_id"])

    def _specimen_record(self) -> dict:
        ws = self.context.workspace
        oid = self.specimen_combo.currentData()
        if oid is None:
            # minimal valid placeholder
            return {"specimen_id": "SP-UNSET", "specimen_type": "other",
                    "material": {"name": "unspecified"},
                    "provenance": {"origin": "placeholder"}}
        return specimen_record_from_payload(ws.get_object(oid)["payload"])

    def build_manifest(self) -> dict:
        duration = self.duration_s.value()
        drive_off = self.drive_off_s.value()
        post_ratio = ((duration - drive_off) / drive_off
                      if drive_off > 0 else 0.0)
        acquisition = {
            "acquisition_id": f"ACQ-{self.run_id.text().removeprefix('RUN-')}",
            "sample_rate_hz": self.fs.value(),
            "duration_s": duration,
            "single_shot": self.single_shot.isChecked(),
            "n_runs": self.n_runs.value(),
            "post_drive": {"drive_off_time_s": drive_off,
                           "post_drive_ratio": round(post_ratio, 3)},
            "channels": [
                {"channel_id": "CH1", "sensor_type": "contact_mic",
                 "units": "V", "calibration_ref": "CAL-TBD"},
            ],
        }
        drive_config = {
            "drive_id": f"DRV-{self.run_id.text().removeprefix('RUN-')}",
            "branch": self.branch.currentText(),
            "drive_type": self.drive_type.currentText(),
            "timing": {"session_duration_s": self.session_s.value(),
                       "drive_off_time_s": drive_off},
            "reference_clock": {"shared": True,
                                "source": "bench common timebase"},
        }
        human_loading = None
        if self.branch.currentText() == "human_loading":
            human_loading = {
                "ethics_review_ref": self.ethics_ref.text(),
                "no_energized_contact_confirmed": self.no_contact.isChecked(),
            }
        hyp = [h.strip() for h in self.hypotheses.text().split(",")
               if h.strip()]
        timeseries = []
        csv_path = self.data_csv.text().strip()
        if csv_path:
            timeseries.append(self._timeseries_entry(csv_path))
        return build_run_manifest(
            run_id=self.run_id.text(),
            protocol_branch=self.branch.currentText(),
            hypothesis_ids=hyp or ["EXPLORATORY"],
            operator_id=self.operator.text(),
            control_role=self.control_role.currentText(),
            specimen=self._specimen_record(),
            drive_config=drive_config,
            acquisition=acquisition,
            timeseries=timeseries,
            human_loading=human_loading)

    def _timeseries_entry(self, csv_path: str) -> dict:
        """Build a timeseries record for a CSV: sha256 + header columns."""
        from pathlib import Path

        from rgcs_desktop.services.manifests import timeseries_entry_for_csv
        header = Path(csv_path).open().readline().strip().split(",")

        def _units(name: str) -> str:
            if name == "t_s":
                return "s"
            suffix = name.rsplit("_", 1)[-1] if "_" in name else ""
            return suffix or "arb"

        columns = [{"name": n, "units": _units(n)} for n in header]
        return timeseries_entry_for_csv(csv_path, ["CH1"], self.fs.value(),
                                        columns)

    def build_and_validate(self) -> tuple[dict, list[str]]:
        manifest = self.build_manifest()
        errors = validate_instance(manifest, "run_manifest.schema.json")
        gates = all_gates(manifest)
        for name, gate in gates.items():
            if not gate.ok and name == "ethics":
                errors.extend(gate.reasons)  # ethics gate is hard
        self._manifest, self._errors = manifest, errors
        self.preview.setPlainText(json.dumps(manifest, indent=2))
        if errors:
            self.validation_label.setText(
                "INVALID:\n" + "\n".join(errors[:8]))
            self.save_btn.setEnabled(False)
        else:
            self.validation_label.setText("Schema-valid run manifest.")
            self.save_btn.setEnabled(True)
        self.gates_label.setText(
            "\n".join(f"gate {k}: {v.summary()}" for k, v in gates.items()))
        self.inspector_changed.emit()
        return manifest, errors

    def save_experiment(self) -> str | None:
        if self._manifest is None or self._errors:
            return None
        ws = self.context.workspace
        path = ws.write_manifest(self._manifest, overwrite=True)
        object_id = ws.put_object(
            "experiment", self._manifest["run_id"],
            {"manifest_path": str(path), "manifest": self._manifest,
             "classification": "Derived (planned run; no data yet)"},
            object_id=f"experiment-{self._manifest['run_id']}",
            overwrite=True)
        self.status_message.emit(f"experiment saved: {object_id}")
        self.context.notify_workspace_changed()
        return object_id

    @property
    def manifest(self) -> dict | None:
        return self._manifest

    @property
    def validation_errors(self) -> list[str]:
        return list(self._errors)

    def inspector_info(self):
        m = self._manifest or {}
        gates = all_gates(m) if m else {}
        return {"properties": {
                    "run_id": m.get("run_id", ""),
                    "branch": m.get("protocol_branch", ""),
                    "control_role": m.get("control_role", ""),
                    "schema_version": m.get("schema_version", ""),
                    "valid": not self._errors if m else False,
                    **{f"gate:{k}": v.summary() for k, v in gates.items()}},
                "classification": "Derived (manifest structure)",
                "units": "s, Hz per field suffixes "
                         "(docs/NOTATION_AND_UNITS.md 0.3)",
                "provenance": "validated against experiments/schemas "
                              "(validate.py registry)"}
