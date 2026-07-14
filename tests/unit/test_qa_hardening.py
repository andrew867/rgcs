"""Tests for the QA hardening pass (Sub-Agent 09), covering:

QA-D-05  corrupt workspace db -> WorkspaceError (never raw sqlite3
         errors), no corrupt backup archived, backup restore path;
QA-D-06  CSV loader user-facing errors + finiteness gate;
QA-D-07  manifest JSON errors reported, not raised raw;
QA-D-12  coherence metric edge-case guards;
QA-D-13  non-finite input gate in the coherence pipeline;
QA-D-03  unified initial-phase estimator.
"""

import json
import sqlite3

import numpy as np
import pytest

from rgcs_desktop.workspaces import Workspace, WorkspaceError
from rgcs_desktop.jobs.workers import _load_timeseries_csv
from rgcs_desktop.services.schemas import validate_manifest_file
from rgcs_core.coherence import (analytic_signal, coherence_series,
                                 coherence_decay_time,
                                 instantaneous_frequency,
                                 initial_phase_estimate)


# ---------------------------------------------------------------- QA-D-05
def _make_ws(tmp_path, name="wsA"):
    ws = Workspace.create(tmp_path / name, name)
    ws.put_object("note", "n1", {"text": "hello"})
    ws.close()
    return tmp_path / name


@pytest.mark.parametrize("corruption", ["zero_header", "truncate", "garbage"])
def test_corrupt_workspace_raises_workspace_error(tmp_path, corruption):
    root = _make_ws(tmp_path)
    db = root / "workspace.db"
    data = db.read_bytes()
    if corruption == "zero_header":
        db.write_bytes(b"\x00" * 100 + data[100:])
    elif corruption == "truncate":
        db.write_bytes(data[: len(data) // 3])
    else:
        db.write_bytes(b"this is not a sqlite database at all" * 50)
    with pytest.raises(WorkspaceError):
        Workspace.open(root)


def test_corrupt_db_is_not_archived_as_backup(tmp_path):
    root = _make_ws(tmp_path)
    (root / "workspace.db").write_bytes(b"garbage" * 100)
    before = Workspace.list_backups(root)
    with pytest.raises(WorkspaceError):
        Workspace.open(root)
    assert Workspace.list_backups(root) == before


def test_restore_latest_backup_recovers_workspace(tmp_path):
    root = _make_ws(tmp_path)
    # a normal open creates a backup
    Workspace.open(root).close()
    assert Workspace.list_backups(root)
    # corrupt the live db
    (root / "workspace.db").write_bytes(b"\x00" * 4096)
    with pytest.raises(WorkspaceError):
        Workspace.open(root)
    ws = Workspace.restore_latest_backup(root)
    try:
        objs = ws.list_objects()
        assert any(o["name"] == "n1" for o in objs)
    finally:
        ws.close()
    # the corrupt file is preserved, not deleted
    assert list(root.glob("workspace.db.corrupt-*"))


def test_restore_without_backups_raises(tmp_path):
    root = _make_ws(tmp_path, "wsB")
    for b in Workspace.list_backups(root):
        b.unlink()
    with pytest.raises(WorkspaceError, match="no backups"):
        Workspace.restore_latest_backup(root)


# ---------------------------------------------------------------- QA-D-06
def test_csv_loader_empty_file(tmp_path):
    p = tmp_path / "e.csv"
    p.write_text("")
    with pytest.raises(ValueError, match="empty"):
        _load_timeseries_csv(str(p))


def test_csv_loader_header_only(tmp_path):
    p = tmp_path / "h.csv"
    p.write_text("t_s,I,Q\n")
    with pytest.raises(ValueError, match="no data rows"):
        _load_timeseries_csv(str(p))


def test_csv_loader_binary(tmp_path):
    p = tmp_path / "b.csv"
    p.write_bytes(bytes(range(256)) * 8)
    with pytest.raises(ValueError, match="not a text CSV"):
        _load_timeseries_csv(str(p))


def test_csv_loader_ragged_row(tmp_path):
    p = tmp_path / "r.csv"
    p.write_text("t_s,I,Q\n0.0,1.0,0.0\n0.1,2.0\n")
    with pytest.raises(ValueError, match="row 3"):
        _load_timeseries_csv(str(p))


def test_csv_loader_non_numeric(tmp_path):
    p = tmp_path / "n.csv"
    p.write_text("t_s,I,Q\n0.0,one,0.0\n")
    with pytest.raises(ValueError, match="non-numeric"):
        _load_timeseries_csv(str(p))


def test_csv_loader_rejects_nan_inf(tmp_path):
    p = tmp_path / "f.csv"
    p.write_text("t_s,I,Q\n0.0,nan,0.0\n0.1,1.0,inf\n")
    with pytest.raises(ValueError, match="non-finite"):
        _load_timeseries_csv(str(p))


def test_csv_loader_happy_path(tmp_path):
    p = tmp_path / "ok.csv"
    p.write_text("t_s,I,Q\n0.0,1.0,0.0\n0.1,0.0,1.0\n")
    cols = _load_timeseries_csv(str(p))
    assert set(cols) == {"t_s", "I", "Q"}
    assert cols["I"].tolist() == [1.0, 0.0]


# ---------------------------------------------------------------- QA-D-07
def test_validate_manifest_file_malformed_json(tmp_path):
    p = tmp_path / "m.json"
    p.write_text("{not json")
    errs = validate_manifest_file(p)
    assert errs and "not valid JSON" in errs[0]


def test_validate_manifest_file_binary(tmp_path):
    p = tmp_path / "m.json"
    p.write_bytes(b"\xff\xfe\x00\x01" * 10)
    errs = validate_manifest_file(p)
    assert errs and "not UTF-8" in errs[0]


# ------------------------------------------------------------ QA-D-12/13
def test_instantaneous_frequency_single_sample_guard():
    with pytest.raises(ValueError, match="at least 2 samples"):
        instantaneous_frequency(np.array([1.0 + 0j]), 100.0)


def test_coherence_decay_time_empty_guard():
    with pytest.raises(ValueError, match="non-empty"):
        coherence_decay_time(np.array([]), np.array([]), 0.05)


def test_coherence_series_rejects_non_finite():
    z = np.ones(1000, dtype=complex)
    z[500] = np.inf
    with pytest.raises(ValueError, match="non-finite"):
        coherence_series(z, 1000.0)


def test_analytic_signal_rejects_nan():
    x = np.ones(100)
    x[3] = np.nan
    with pytest.raises(ValueError, match="non-finite"):
        analytic_signal(x)


# ---------------------------------------------------------------- QA-D-03
def test_initial_phase_estimate_is_arg_z0_mod_2pi():
    t = np.arange(1000) / 1e5
    phi0 = -1.2
    z = np.exp(1j * (2 * np.pi * 5000.0 * t + phi0))
    est = initial_phase_estimate(z)
    assert est == pytest.approx(phi0 % (2 * np.pi), abs=1e-9)
    assert 0.0 <= est < 2 * np.pi
