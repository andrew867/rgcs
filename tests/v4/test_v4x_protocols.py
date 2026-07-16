"""E-lane protocol package tests (gates G21-G30)."""

import numpy as np
import pytest

from rscs2_core import protocols_v4x as pv
from rscs2_core.research_records import make_record


def test_all_campaigns_present_with_gates():
    P = pv.build_protocols()
    assert set(P) == {f"E{i:02d}" for i in range(1, 10)}
    for rec in P.values():
        assert "required_status" in rec["safety_gate"]
        assert rec["preregistration_id"].startswith("PREREG-")
        assert rec["controls"] and rec["channels"]


def test_ethics_gate_blocks_human_campaigns():
    P = pv.build_protocols()
    for rid in ("E06", "E07"):
        assert P[rid]["status"] == "ETHICS_APPROVAL_REQUIRED"
    for rid in ("E01", "E02", "E03", "E04", "E05", "E08", "E09"):
        assert P[rid]["status"] == "PROTOCOL_READY_HARDWARE_REQUIRED"


def test_coverage_disposes_every_ewh_id():
    cov = pv.coverage_map()
    need = [f"E{i:03d}" for i in range(1, 28)] \
        + [f"W{i:03d}" for i in range(1, 18)] \
        + [f"H{i:03d}" for i in range(1, 18)]
    missing = [k for k in need if k not in cov]
    assert not missing, missing


def test_ring_down_synthetic_recovery():
    t, y = pv.synth_ring_down(4096.0, 5000.0, 65536.0, 2.0,
                              noise=0.01)
    out = pv.analyze_ring_down(t, y)
    assert out["f0_hz"] == pytest.approx(4096.0, abs=1.0)
    assert out["q"] == pytest.approx(5000.0, rel=0.15)
    assert out["synthetic_validated"]


def test_blind_labels_deterministic_and_balanced():
    a = pv.blind_labels(12, ["exposed", "sham", "no-crystal"], 42)
    b = pv.blind_labels(12, ["exposed", "sham", "no-crystal"], 42)
    assert a["sealed_map"] == b["sealed_map"]
    counts = {}
    for c in a["sealed_map"].values():
        counts[c] = counts.get(c, 0) + 1
    assert set(counts.values()) == {4}


def test_synthetic_never_measured():
    with pytest.raises(ValueError):
        make_record("MeasurementRecord", "X1", "fake", "experimental",
                    "EXPERIMENTALLY_MEASURED", ["MEAS"],
                    synthetic=True, raw_hash="x", instrument="x",
                    calibration_id="x", protocol_version="x",
                    randomization="x", blinding="x",
                    safety_gate_id="x")
