"""UI smoke tests (offscreen): window opens, panels construct, command
palette lists actions, job queue processes a trivial job, cancellation
works, binding display rules hold."""
from __future__ import annotations

import time

import pytest

from rgcs_desktop.app.command_palette import CommandPalette
from rgcs_desktop.jobs.manager import JobStatus


def test_window_opens_and_panels_construct(main_window):
    assert main_window.isVisible()
    expected = {"Workspace", "Sources", "Specimen editor", "Models",
                "Compact-mode spectrum", "Avoided crossing",
                "Coherence analyzer", "Pulse designer", "Experiment builder",
                "Results", "Model vs measured", "Report / export", "Settings",
                "Evidence ledger"}
    assert expected == set(main_window.panels)
    # every panel exposes inspector info with the required keys
    for title, panel in main_window.panels.items():
        main_window.open_panel(title)
        info = panel.inspector_info()
        for key in ("properties", "classification", "units", "provenance"):
            assert key in info, f"{title} missing inspector key {key}"


def test_command_palette_lists_actions(main_window, qtbot):
    names = main_window.command_names()
    assert any(n.startswith("Open panel:") for n in names)
    assert "Workspace: create…" in names
    assert "Export: reproducibility bundle" in names
    palette = CommandPalette(main_window._actions, main_window)
    qtbot.addWidget(palette)
    assert palette.listing.count() == len(names)
    palette.search.setText("spectrum")
    shown = [palette.listing.item(i).text()
             for i in range(palette.listing.count())]
    assert all("spectrum" in s.lower() for s in shown) and shown


def test_command_palette_runs_action(main_window):
    main_window.run_command("Open panel: Pulse designer")
    assert main_window.tabs.currentWidget() is \
        main_window.panels["Pulse designer"]


def test_job_queue_processes_trivial_job(app_context):
    jm = app_context.job_manager
    job_id = jm.submit("trivial", {"steps": 4}, name="smoke trivial")
    rec = jm.wait(job_id, timeout_s=60.0)
    assert rec.status is JobStatus.SUCCEEDED
    assert rec.result == {"kind": "trivial", "steps": 4, "sum": 6}
    assert rec.progress == 1.0
    assert any("step 4/4" in line for line in rec.log_lines)
    # persisted to the workspace db
    statuses = {j["job_id"]: j["status"]
                for j in app_context.workspace.list_jobs()}
    assert statuses[job_id] == "succeeded"


def test_job_cancellation(app_context):
    jm = app_context.job_manager
    job_id = jm.submit("trivial", {"steps": 200, "delay_s": 0.1},
                       name="slow job")
    # give the worker a moment to start, then cancel
    deadline = time.time() + 30
    while time.time() < deadline:
        jm.poll()
        rec = jm.job(job_id)
        if rec.status is JobStatus.RUNNING and rec.progress > 0:
            break
        time.sleep(0.05)
    jm.cancel(job_id)
    rec = jm.job(job_id)
    assert rec.status is JobStatus.CANCELLED
    statuses = {j["job_id"]: j["status"]
                for j in app_context.workspace.list_jobs()}
    assert statuses[job_id] == "cancelled"


def test_failed_job_preserves_error_artifact(app_context):
    jm = app_context.job_manager
    job_id = jm.submit("failing", {"message": "boom"}, name="always fails")
    rec = jm.wait(job_id, timeout_s=60.0)
    assert rec.status is JobStatus.FAILED
    assert "boom" in rec.error
    assert rec.error_artifact is not None
    stored = app_context.workspace.read_artifact(rec.error_artifact)
    assert "boom" in stored["traceback"]


def test_classification_badges_present(main_window):
    from rgcs_desktop.widgets import ClassificationBadge
    spectrum = main_window.panels["Compact-mode spectrum"]
    assert isinstance(spectrum.badge, ClassificationBadge)
    assert spectrum.badge.label == "Hypothesis"
    specimen = main_window.panels["Specimen editor"]
    assert isinstance(specimen.badge, ClassificationBadge)
    pulse = main_window.panels["Pulse designer"]
    assert pulse.badge.label == "Derived"


def test_uncertain_values_render_intervals_not_points(main_window):
    specimen = main_window.panels["Specimen editor"]
    specimen.compute()
    text = specimen.axial_label.text()
    assert "±" in text and "[" in text and "(1σ)" in text
    # measured node absent -> 'not measured', never NaN
    assert specimen.measured_label.text() == "not measured"
    assert "nan" not in specimen.measured_label.text().lower()


def test_source_presets_under_source_claim_banner(main_window):
    from rgcs_desktop.widgets import SourceClaimBanner
    pulse = main_window.panels["Pulse designer"]
    banners = pulse.findChildren(SourceClaimBanner)
    assert banners, "pulse designer must show a Source-claim banner"
    sources = main_window.panels["Sources"]
    assert sources.findChildren(SourceClaimBanner)


def test_pulse_designer_exposes_pulses_per_period(main_window):
    pulse = main_window.panels["Pulse designer"]
    pulse.pulses_per_period.setValue(3)
    pulse.compute()
    assert pulse._micro["pulses_per_period"] == 3
    seq = pulse.sequence
    assert seq["exact_cycles"] in (2261, 1508, 1131)


def test_coherence_claim_gate_blocks_small_ensembles(main_window, tmp_path):
    import json
    panel = main_window.panels["Coherence analyzer"]
    assert not panel.claim_workflow_enabled  # no manifest loaded
    bad = {"acquisition": {"n_runs": 5,
                           "post_drive": {"post_drive_ratio": 1.0}}}
    p = tmp_path / "bad_manifest.json"
    p.write_text(json.dumps(bad))
    panel.load_manifest(str(p))
    assert not panel.claim_workflow_enabled
    good = {"acquisition": {"n_runs": 120,
                            "post_drive": {"post_drive_ratio": 3.0}}}
    p2 = tmp_path / "good_manifest.json"
    p2.write_text(json.dumps(good))
    panel.load_manifest(str(p2))
    assert panel.claim_workflow_enabled


def test_unknown_schema_major_version_refused():
    from rgcs_desktop.services.schemas import (SchemaVersionError,
                                               check_schema_version,
                                               validate_instance)
    check_schema_version("1.0.0")  # accepted
    check_schema_version("1.7.3")  # minor differences accepted
    with pytest.raises(SchemaVersionError):
        check_schema_version("2.0.0")
    errors = validate_instance({"schema_version": "9.0.0"})
    assert errors and "major" in errors[0]


def test_layout_persistence_roundtrip(main_window):
    geometry = bytes(main_window.saveGeometry())
    state = bytes(main_window.saveState())
    main_window.context.settings.save_layout(geometry, state)
    g2, s2 = main_window.context.settings.layout()
    assert bytes(g2) == geometry and bytes(s2) == state
