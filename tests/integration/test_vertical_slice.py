"""Vertical-slice integration test (quality gate 6).

Drives the real app objects headless (QT_QPA_PLATFORM=offscreen):
create workspace -> import a specimen -> compute compact-mode spectrum ->
define an experiment (validated manifest) -> run a coherence-analysis job
on experiments/sample_data (background worker process) -> display/collect
results -> export reproducibility bundle.
"""
from __future__ import annotations

import json
import os
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_CSV = (REPO_ROOT / "experiments" / "sample_data" / "golden_coherence"
              / "case_c_decaying_sinusoid.csv")
SAMPLE_MANIFEST = (REPO_ROOT / "experiments" / "sample_data"
                   / "modal_survey_run_manifest.json")


@pytest.fixture(scope="module")
def slice_env(tmp_path_factory):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    from rgcs_desktop.app.context import AppContext
    from rgcs_desktop.app.main_window import MainWindow
    root = tmp_path_factory.mktemp("slice") / "workspace"
    ctx = AppContext()
    # 1. create workspace
    ctx.create_workspace(root, "vertical-slice")
    win = MainWindow(ctx)
    win.show()
    yield {"app": app, "ctx": ctx, "win": win, "root": root}
    win.close()


def test_step_1_workspace_created(slice_env):
    ws = slice_env["ctx"].workspace
    assert (ws.root / "workspace.db").exists()
    assert ws.schema_version == 1
    # reopening takes a backup (data-safety requirement)
    from rgcs_desktop.workspaces import Workspace
    probe = Workspace.open(ws.root)
    probe.close()
    assert list((ws.root / "backups").glob("workspace-*.db"))


def test_step_2_import_specimen(slice_env):
    win = slice_env["win"]
    editor = win.panels["Specimen editor"]
    editor.specimen_id.setText("SP-SLICE-Q154")
    editor.c_length.setValue(154.05)
    editor.c_dw.setValue(34.0)
    editor.c_dn.setValue(25.0)
    editor.c_measured_mass.setText("154.0")
    object_id = editor.save_specimen()
    ws = slice_env["ctx"].workspace
    obj = ws.get_object(object_id)
    assert obj["kind"] == "specimen"
    payload = obj["payload"]
    assert payload["geometry"]["length_mm"] == pytest.approx(154.05)
    # binding rule: measured node is None -> stored as null, displayed as
    # 'not measured'
    assert payload["derived"]["node_positions"]["measured_node_mm"] is None
    assert editor.measured_label.text() == "not measured"
    # also import a source file with checksum
    sources = win.panels["Sources"]
    info = sources.import_file(str(SAMPLE_MANIFEST), note="sample manifest")
    assert len(info["sha256"]) == 64
    assert (ws.root / info["relpath"]).exists()


def test_step_3_compute_spectrum(slice_env):
    win = slice_env["win"]
    panel = win.panels["Compact-mode spectrum"]
    panel.f_b.setValue(4096.0)
    panel.n_max.setValue(6)
    spec = panel.compute()
    assert spec["modes"], "spectrum must contain modes"
    for mode in spec["modes"]:
        f = mode["frequency"]
        assert {"mean", "lo_1sigma", "hi_1sigma"} <= set(f)  # UncertainValue
    assert "Hypothesis" in str(spec["classification"])
    artifact_id = panel.save_result()
    assert artifact_id is not None
    stored = slice_env["ctx"].workspace.read_artifact(artifact_id)
    assert stored["spectrum"]["base_frequency_hz"] == pytest.approx(4096.0)


def test_step_4_define_experiment_validated_manifest(slice_env):
    win = slice_env["win"]
    builder = win.panels["Experiment builder"]
    builder.refresh()
    assert builder.specimen_combo.count() >= 1
    builder.run_id.setText("RUN-SLICE-0001")
    builder.hypotheses.setText("H-01, H-09")
    builder.n_runs.setValue(120)
    builder.duration_s.setValue(120.0)
    builder.drive_off_s.setValue(30.0)  # post_drive_ratio = 3.0 >= 2.5
    builder.data_csv.setText(str(SAMPLE_CSV))
    manifest, errors = builder.build_and_validate()
    assert errors == [], f"manifest must validate: {errors}"
    object_id = builder.save_experiment()
    assert object_id is not None
    path = slice_env["ctx"].workspace.root / "manifests" / \
        "RUN-SLICE-0001.json"
    assert path.exists()
    # the saved manifest re-validates with the shared registry
    from rgcs_desktop.services.schemas import validate_manifest_file
    assert validate_manifest_file(path) == []
    # gates on this manifest allow coherence-claim workflows
    from rgcs_desktop.services.gates import coherence_claim_gate
    assert coherence_claim_gate(manifest).ok


def test_step_4b_ethics_gate_blocks_human_loading(slice_env):
    win = slice_env["win"]
    builder = win.panels["Experiment builder"]
    builder.branch.setCurrentText("human_loading")
    builder.ethics_ref.setText("")
    builder.no_contact.setChecked(False)
    _manifest, errors = builder.build_and_validate()
    assert any("ethics" in e or "energized" in e for e in errors)
    builder.ethics_ref.setText("IRB-2026-042")
    builder.no_contact.setChecked(True)
    _manifest, errors = builder.build_and_validate()
    assert errors == []
    builder.branch.setCurrentText("modal_survey")  # restore


def test_step_5_coherence_job_on_sample_data(slice_env):
    win = slice_env["win"]
    ctx = slice_env["ctx"]
    panel = win.panels["Coherence analyzer"]
    panel.csv_path.setText(str(SAMPLE_CSV))
    panel.i_col.setText("I")
    panel.q_col.setText("Q")
    job_id = panel.run_analysis()
    rec = ctx.job_manager.wait(job_id, timeout_s=120.0)
    from rgcs_desktop.jobs.manager import JobStatus
    assert rec.status is JobStatus.SUCCEEDED
    assert rec.result_artifact is not None
    # deliver the finished signal so the panel plots the result
    ctx.job_manager.job_finished.emit(job_id)
    result = rec.result
    # (C, w, baseline) reported together
    coh = result["coherence"]
    assert {"c_w", "window_s", "baseline"} <= set(coh)
    assert 0.9 < coh["c_max"] <= 1.0  # decaying sinusoid: high early coherence
    assert coh["baseline"] < 0.2
    assert result["input"]["sha256"]
    # panel displayed the result (plots populated, inspector info updated)
    assert panel.result is not None
    assert panel.c_plot.plotItem.items, "coherence plot must have curves"


def test_step_6_results_collected(slice_env):
    win = slice_env["win"]
    ctx = slice_env["ctx"]
    results = win.panels["Results"]
    results.refresh()
    ids = results.artifact_ids()
    assert any(a.startswith("result-") for a in ids)
    result_objects = ctx.workspace.list_objects("result")
    assert len(result_objects) >= 2  # spectrum + coherence job


def test_step_7_reproducibility_bundle(slice_env):
    win = slice_env["win"]
    ctx = slice_env["ctx"]
    report_panel = win.panels["Report / export"]
    report_path = report_panel.generate()
    assert report_path.exists()
    text = report_path.read_text()
    assert "classification" in text.lower()
    bundle_path = report_panel.export()
    assert bundle_path.exists()
    with zipfile.ZipFile(bundle_path) as zf:
        names = zf.namelist()
        assert "workspace.db" in names
        assert "CHECKSUMS.json" in names
        assert "VERSIONS.json" in names
        assert any(n.startswith("artifacts/") for n in names)
        assert any(n.startswith("manifests/") for n in names)
        assert any(n.startswith("sources/") for n in names)
        versions = json.loads(zf.read("VERSIONS.json"))
        assert "rgcs_core_model_version" in versions
    from rgcs_desktop.services.bundle import verify_bundle
    check = verify_bundle(bundle_path)
    assert check["ok"] and check["n_members"] > 3
    # export recorded in history
    kinds = [e["kind"] for e in ctx.workspace.list_exports()]
    assert "bundle" in kinds and "report" in kinds


def test_data_safety_no_silent_overwrite(slice_env):
    ws = slice_env["ctx"].workspace
    from rgcs_desktop.workspaces import WorkspaceError
    ws.put_object("note", "n1", {"a": 1}, object_id="note-fixed")
    ws.put_object("note", "n1", {"a": 1}, object_id="note-fixed")  # same: ok
    with pytest.raises(WorkspaceError):
        ws.put_object("note", "n1", {"a": 2}, object_id="note-fixed")
    ws.put_object("note", "n1", {"a": 2}, object_id="note-fixed",
                  overwrite=True)  # explicit overwrite allowed


def test_deterministic_artifact_ids(slice_env):
    ws = slice_env["ctx"].workspace
    a1 = ws.write_artifact({"x": [1, 2, 3]}, kind="result")
    a2 = ws.write_artifact({"x": [1, 2, 3]}, kind="result")
    assert a1["artifact_id"] == a2["artifact_id"]  # content-addressed
    a3 = ws.write_artifact({"x": [1, 2, 4]}, kind="result")
    assert a3["artifact_id"] != a1["artifact_id"]
