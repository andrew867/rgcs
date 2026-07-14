"""Phase/coherence time-series analyzer.

Loads a CSV, runs the coherence job in a background process, and plots
C_w (with the window baseline), amplitude, and phase. Coherence-claim
workflows are gated: post_drive_ratio >= 2.5 and n_runs >= 100 (from the
associated run manifest) must hold before claim-related actions enable.
"""
from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtWidgets import (QComboBox, QDoubleSpinBox, QFileDialog,
                               QFormLayout, QGroupBox, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QTabWidget,
                               QVBoxLayout, QWidget)

from rgcs_core.coherence import DEFAULT_HOP_S, DEFAULT_WINDOW_S

from rgcs_desktop.plots import make_plot, plot_series
from rgcs_desktop.services.gates import coherence_claim_gate
from rgcs_desktop.viewers.base import Panel
from rgcs_desktop.widgets import ClassificationBadge


class CoherenceAnalyzerPanel(Panel):
    TITLE = "Coherence analyzer"

    def __init__(self, context, parent=None):
        super().__init__(context, parent)
        self._result: dict | None = None
        self._job_id: str | None = None
        self._manifest: dict | None = None
        layout = QHBoxLayout(self)

        controls = QGroupBox("Analysis")
        form = QFormLayout(controls)
        self.csv_path = QLineEdit()
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._browse)
        row = QHBoxLayout()
        row.addWidget(self.csv_path)
        row.addWidget(browse)
        form.addRow("Time-series CSV", row)
        self.i_col = QLineEdit("I")
        self.q_col = QLineEdit("Q")
        self.sig_col = QLineEdit()
        self.sig_col.setPlaceholderText("real signal column (if no I/Q)")
        form.addRow("I column", self.i_col)
        form.addRow("Q column", self.q_col)
        form.addRow("Signal column", self.sig_col)
        self.window_s = QDoubleSpinBox()
        self.window_s.setDecimals(5)
        self.window_s.setRange(1e-5, 10.0)
        self.window_s.setValue(DEFAULT_WINDOW_S)
        self.hop_s = QDoubleSpinBox()
        self.hop_s.setDecimals(5)
        self.hop_s.setRange(1e-5, 10.0)
        self.hop_s.setValue(DEFAULT_HOP_S)
        form.addRow("Window w (s)", self.window_s)
        form.addRow("Hop (s)", self.hop_s)
        self.run_btn = QPushButton("Run analysis (background job)")
        self.run_btn.clicked.connect(self.run_analysis)
        form.addRow(self.run_btn)
        self.status_label = QLabel("idle")
        form.addRow("Job status", self.status_label)
        self.badge = ClassificationBadge(
            "Derived (not evidence by itself)")
        form.addRow("Classification", self.badge)

        gate_box = QGroupBox("Coherence-claim gate (manifest required)")
        gv = QFormLayout(gate_box)
        self.manifest_path = QLineEdit()
        mb = QPushButton("Load manifest…")
        mb.clicked.connect(self._browse_manifest)
        mrow = QHBoxLayout()
        mrow.addWidget(self.manifest_path)
        mrow.addWidget(mb)
        gv.addRow("Run manifest", mrow)
        self.gate_label = QLabel("no manifest loaded — claim workflows "
                                 "disabled")
        self.gate_label.setWordWrap(True)
        gv.addRow(self.gate_label)
        self.claim_btn = QPushButton("Mark as coherence-claim candidate")
        self.claim_btn.setEnabled(False)
        self.claim_btn.clicked.connect(self._mark_claim)
        gv.addRow(self.claim_btn)
        form.addRow(gate_box)
        layout.addWidget(controls)

        plots = QTabWidget()
        self.c_plot = make_plot("Windowed coherence C_w", "t (s)", "C_w")
        self.a_plot = make_plot("Amplitude", "t (s)", "|z|")
        self.p_plot = make_plot("Instantaneous phase", "t (s)", "phi (rad)")
        plots.addTab(self.c_plot, "Coherence")
        plots.addTab(self.a_plot, "Amplitude")
        plots.addTab(self.p_plot, "Phase")
        layout.addWidget(plots, stretch=1)

        self.context.job_manager.job_finished.connect(self._job_finished)

    # -- actions ----------------------------------------------------------
    def _browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Time-series CSV",
                                              filter="CSV (*.csv)")
        if path:
            self.csv_path.setText(path)

    def _browse_manifest(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Run manifest",
                                              filter="JSON (*.json)")
        if path:
            self.load_manifest(path)

    def load_manifest(self, path: str) -> None:
        self.manifest_path.setText(path)
        try:
            self._manifest = json.loads(
                Path(path).read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
            # QA-D-07: report malformed manifests instead of crashing.
            self._manifest = None
            self.gate_label.setText(
                f"manifest could not be read ({exc}); claim workflows "
                f"disabled")
            self.claim_btn.setEnabled(False)
            return
        self._update_gate()

    def _update_gate(self) -> None:
        if self._manifest is None:
            self.gate_label.setText("no manifest loaded — claim workflows "
                                    "disabled")
            self.claim_btn.setEnabled(False)
            return
        gate = coherence_claim_gate(self._manifest)
        self.gate_label.setText(gate.summary())
        self.claim_btn.setEnabled(gate.ok)

    @property
    def claim_workflow_enabled(self) -> bool:
        return self.claim_btn.isEnabled()

    def _mark_claim(self) -> None:
        # records intent only; actual claims go through the statistics plan
        if self._result is None:
            self.status_message.emit("run an analysis first")
            return
        self.context.workspace.put_object(
            "note", "coherence-claim candidate",
            {"result": self._result.get("input", {}),
             "gate": "passed (post_drive_ratio >= 2.5, n_runs >= 100)",
             "classification": "Hypothesis (candidate only; not evidence)"},
            overwrite=True)
        self.status_message.emit("claim candidate recorded")

    def run_analysis(self, *, wait: bool = False) -> str:
        params = {"csv_path": self.csv_path.text(),
                  "window_s": self.window_s.value(),
                  "hop_s": self.hop_s.value()}
        if self.sig_col.text().strip():
            params["signal_column"] = self.sig_col.text().strip()
        else:
            params["i_column"] = self.i_col.text().strip()
            params["q_column"] = self.q_col.text().strip()
        self._job_id = self.context.job_manager.submit(
            "coherence_analysis", params, name="coherence analysis")
        self.status_label.setText(f"running ({self._job_id})")
        if wait:
            self.context.job_manager.wait(self._job_id, timeout_s=120.0)
        return self._job_id

    def _job_finished(self, job_id: str) -> None:
        if job_id != self._job_id:
            return
        rec = self.context.job_manager.job(job_id)
        self.status_label.setText(rec.status.value)
        if rec.result is not None:
            self._result = rec.result
            self._plot_result(rec.result)
            self.inspector_changed.emit()

    def _plot_result(self, r: dict) -> None:
        c = r["coherence"]
        self.c_plot.clear()
        plot_series(self.c_plot, c["t_s"], c["c_w"], color="#1258a8", width=2)
        # baseline reported together with (C, w)
        baseline = c["baseline"]
        plot_series(self.c_plot, [c["t_s"][0], c["t_s"][-1]],
                    [baseline, baseline], color="#b26a00", width=1.5)
        self.c_plot.setTitle(
            f"C_w (window {c['window_s']*1e3:.1f} ms, "
            f"baseline {baseline:.3f})")
        a = r["amplitude"]
        self.a_plot.clear()
        plot_series(self.a_plot, a["t_s"], a["a"], color="#1258a8")
        p = r["phase"]
        self.p_plot.clear()
        plot_series(self.p_plot, p["t_s"], p["phi_rad"], color="#1258a8")

    @property
    def result(self) -> dict | None:
        return self._result

    def inspector_info(self):
        r = self._result or {}
        c = r.get("coherence", {})
        return {"properties": {
                    "input": r.get("input", {}).get("csv_path", ""),
                    "sha256": r.get("input", {}).get("sha256", "")[:16],
                    "C max": c.get("c_max"),
                    "baseline": c.get("baseline"),
                    "window (s)": c.get("window_s"),
                    "phase linearity": r.get("phase", {}).get(
                        "phase_linearity"),
                    "onset (s)": r.get("onset_time_s"),
                    "decay (s)": r.get("decay_time_s")},
                "classification": str(r.get("classification",
                                            "Derived (not evidence)")),
                "units": "s, dimensionless C in [0,1], rad",
                "provenance": "rgcs_core.coherence (golden-analysis params); "
                              "report (C, w, baseline) together"}
